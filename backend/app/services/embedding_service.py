"""
Sentence Transformer Embedding Service.
Provides semantic embeddings for skills, resumes, and job descriptions.
Includes text preprocessing for PII removal and normalization.
"""
import os
# MUST be set before importing torch/sentence_transformers to take effect on Mac MPS
os.environ["PYTORCH_MPS_HIGH_WATERMARK_RATIO"] = "0.0"

from sentence_transformers import SentenceTransformer
import numpy as np
import re
import string
from typing import List, Union, Optional
from functools import lru_cache
import logging
import threading
import asyncio

from app.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Service for generating semantic embeddings using Sentence Transformers.
    Uses the configured model (via .env) for high-quality, fast embeddings.
    
    Includes async methods for non-blocking encoding during training.
    """
    
    _instance: Optional['EmbeddingService'] = None
    _model: Optional[SentenceTransformer] = None
    current_model_name: str = ""
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern to ensure model is loaded only once."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the embedding service. Model is lazy-loaded on first use."""
        pass
    
    def _load_model(self, model_name: str = None):
        """Load the Sentence Transformer model."""
        target_model = model_name or settings.EMBEDDING_MODEL
        
        try:
            logger.info(f"🔄 Loading embedding model: {target_model}")
            self._model = SentenceTransformer(target_model)
            self.current_model_name = target_model
            logger.info(f"✅ Embedding model loaded successfully: {target_model}")
            
        except Exception as e:
            if "MPS backend out of memory" in str(e) or "out of memory" in str(e).lower():
                logger.warning(f"⚠️ MPS Out of Memory detected. Falling back to CPU for {target_model}")
                try:
                    self._model = SentenceTransformer(target_model, device="cpu")
                    self.current_model_name = target_model
                    logger.info(f"✅ Embedding model loaded successfully (CPU Mode): {target_model}")
                    return
                except Exception as cpu_e:
                    logger.error(f"❌ Failed to load model on CPU fallback: {cpu_e}")
                    raise cpu_e
            
            logger.error(f"❌ Failed to load embedding model {target_model}: {e}")
            raise

    def preprocess_for_embedding(self, data: dict, input_type: str = "resume") -> str:
        """
        Convert structured dictionary to Canonical Text Representation.
        Strictly follows Data Contracts (02-data-contracts.md) and Text Rep (03-text-representation.md).
        
        Args:
            data: Dictionary containing resume or job fields
            input_type: "resume" or "job"
            
        Returns:
            Formatted string for embedding
        """
        if input_type == "resume":
            # Canonical Resume Format
            # Skills: Python, NLP, SQL
            # Experience: 3 years
            # Role: Backend Developer
            # Industry: Fintech
            # Education: B.Tech Computer Science
            
            skills = ", ".join(data.get("skills", []) or [])
            exp_str = f"{data.get('experience_years', 0)} years"
            role = data.get("role", "")
            industry = ", ".join(data.get("industry", []) or [])
            edu = data.get("education", "")
            
            parts = [
                f"Skills: {skills}",
                f"Experience: {exp_str}",
                f"Role: {role}",
                f"Industry: {industry}",
                f"Education: {edu}"
            ]
            
        elif input_type == "job":
            # Canonical Job Format
            # Job Title: Machine Learning Engineer
            # Required Skills: Python, NLP, ML, SQL
            # Experience Required: 2–4 years
            # Industry: Fintech
            # Responsibilities: Model training, API development
            
            title = data.get("title", "") or data.get("job_title", "")
            req_skills = ", ".join(data.get("required_skills", []) or [])
            
            # Handle min/max exp logic if present, else raw string
            if "min_experience" in data and "max_experience" in data:
                exp_req = f"{data.get('min_experience')}-{data.get('max_experience')} years"
            else:
                exp_req = str(data.get("experience_years", "")) or str(data.get("experience_required", ""))
                
            industry = data.get("industry", "") or ", ".join(data.get("industry_list", []) or [])
            resp = ", ".join(data.get("responsibilities", []) or [])
            
            parts = [
                f"Job Title: {title}",
                f"Required Skills: {req_skills}",
                f"Experience Required: {exp_req}",
                f"Industry: {industry}",
                f"Responsibilities: {resp}"
            ]
        
        else:
            return str(data)
            
        # Join non-empty parts with newlines for structure
        text = "\n".join([p for p in parts if p and not p.endswith(": ")])
        return text

    def reload_model(self, model_name: str):
        """Dynamically reload the embedding model."""
        with self._lock:
            if self.current_model_name == model_name:
                logger.info(f"Model {model_name} already loaded.")
                return
            
            logger.info(f"🔄 Switching model from {self.current_model_name} to {model_name}...")
            self._load_model(model_name)
    
    def encode(self, text: Union[str, List[str]], normalize: bool = True) -> np.ndarray:
        """
        Generate embeddings for text(s).
        
        Args:
            text: Single string or list of strings to encode
            normalize: Whether to L2 normalize embeddings (for cosine similarity)
            
        Returns:
            numpy array of embeddings with shape (n, 384)
        """
        if isinstance(text, str):
            text = [text]
        
        # Lock during inference to prevent model swap mid-execution
        with self._lock:
            if self._model is None:
                self._load_model()
                
            embeddings = self._model.encode(
                text,
                normalize_embeddings=normalize,
                show_progress_bar=False
            )
        
        return embeddings
    
    async def encode_async(self, text: Union[str, List[str]], normalize: bool = True) -> np.ndarray:
        """
        Async version of encode that runs in a thread pool to avoid blocking.
        
        Use this during training to keep the API responsive.
        """
        return await asyncio.to_thread(self.encode, text, normalize)
    
    def encode_single(self, text: str, normalize: bool = True) -> List[float]:
        """
        Generate embedding for a single text and return as list.
        
        Args:
            text: Text to encode
            normalize: Whether to normalize
            
        Returns:
            List of floats representing the embedding
        """
        embedding = self.encode(text, normalize)
        return embedding[0].tolist()
    
    async def encode_single_async(self, text: str, normalize: bool = True) -> List[float]:
        """Async version of encode_single that runs in a thread pool."""
        return await asyncio.to_thread(self.encode_single, text, normalize)
    
    def cosine_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine similarity score between -1 and 1
        """
        # If embeddings are normalized, dot product equals cosine similarity
        if isinstance(embedding1, list):
            embedding1 = np.array(embedding1)
        if isinstance(embedding2, list):
            embedding2 = np.array(embedding2)
            
        return float(np.dot(embedding1, embedding2))
    
    def batch_cosine_similarity(
        self, 
        query_embedding: np.ndarray, 
        corpus_embeddings: np.ndarray
    ) -> np.ndarray:
        """
        Calculate cosine similarity between query and multiple corpus embeddings.
        
        Args:
            query_embedding: Single query embedding
            corpus_embeddings: Matrix of corpus embeddings
            
        Returns:
            Array of similarity scores
        """
        if isinstance(query_embedding, list):
            query_embedding = np.array(query_embedding)
        if isinstance(corpus_embeddings, list):
            corpus_embeddings = np.array(corpus_embeddings)
        
        # Ensure query is 1D
        if query_embedding.ndim > 1:
            query_embedding = query_embedding.flatten()
        
        return np.dot(corpus_embeddings, query_embedding)
    
    def semantic_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate semantic similarity between two texts.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score between 0 and 1
        """
        embeddings = self.encode([text1, text2])
        similarity = self.cosine_similarity(embeddings[0], embeddings[1])
        # Convert to 0-1 range (cosine similarity can be negative)
        return (similarity + 1) / 2
    
    def find_most_similar(
        self, 
        query: str, 
        corpus: List[str], 
        top_k: int = 5
    ) -> List[tuple]:
        """
        Find most similar texts from corpus for a given query.
        
        Args:
            query: Query text
            corpus: List of candidate texts
            top_k: Number of top results to return
            
        Returns:
            List of (text, similarity_score) tuples sorted by similarity
        """
        if not corpus:
            return []
        
        query_embedding = self.encode(query)[0]
        corpus_embeddings = self.encode(corpus)
        
        similarities = self.batch_cosine_similarity(query_embedding, corpus_embeddings)
        
        # Get top-k indices
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = [
            (corpus[idx], float(similarities[idx]))
            for idx in top_indices
        ]
        
        return results
    
    def encode_skills(self, skills: List[str]) -> np.ndarray:
        """
        Generate embeddings for a list of skills.
        Optimized for skill matching tasks.
        
        Args:
            skills: List of skill names
            
        Returns:
            Matrix of skill embeddings
        """
        # Add context for better skill understanding
        skill_texts = [f"technical skill: {skill}" for skill in skills]
        return self.encode(skill_texts)
    
    async def encode_skills_async(self, skills: List[str]) -> np.ndarray:
        """Async version of encode_skills."""
        return await asyncio.to_thread(self.encode_skills, skills)
    
    def encode_job_title(self, title: str) -> List[float]:
        """
        Generate embedding for a job title with context.
        
        Args:
            title: Job title
            
        Returns:
            Embedding as list of floats
        """
        contextualized = f"job position: {title}"
        return self.encode_single(contextualized)
    
    def preprocess_text(self, text: str, remove_pii: bool = True) -> str:
        """
        Preprocess text for embedding generation.
        Removes PII (phone numbers, emails, URLs) and normalizes text.
        
        Args:
            text: Raw text to preprocess
            remove_pii: Whether to remove personally identifiable information
            
        Returns:
            Cleaned and normalized text
        """
        if not text:
            return ""
        
        # Convert to lowercase for consistent processing
        text = text.lower()
        
        if remove_pii:
            # Remove phone numbers (various formats: 10+ digits, with separators)
            text = re.sub(r'[\+]?[(]?[0-9]{1,3}[)]?[-\s\.]?[(]?[0-9]{1,4}[)]?[-\s\.]?[0-9]{1,4}[-\s\.]?[0-9]{1,9}', ' ', text)
            text = re.sub(r'\d{10,}', ' ', text)  # Long digit sequences
            
            # Remove email addresses
            text = re.sub(r'\S+@\S+\.\S+', ' ', text)
            
            # Remove URLs
            text = re.sub(r'https?://\S+|www\.\S+', ' ', text)
            
            # Remove physical addresses (simplified pattern for common formats)
            text = re.sub(r'\d+\s+[\w\s]+(?:street|st|avenue|ave|road|rd|boulevard|blvd|lane|ln|drive|dr|court|ct|way|place|pl)[,\s]*', ' ', text, flags=re.IGNORECASE)
            
            # Remove zip codes
            text = re.sub(r'\b\d{5}(?:-\d{4})?\b', ' ', text)
        
        # Remove excessive punctuation but keep meaningful ones
        text = re.sub(r'[^\w\s\-\+\#\.]', ' ', text)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def encode_resume(self, resume_text: str, preprocess: bool = True) -> List[float]:
        """
        Generate embedding for a resume with optional preprocessing.
        
        Args:
            resume_text: Full resume text
            preprocess: Whether to apply PII removal and normalization
            
        Returns:
            Embedding as list of floats
        """
        if preprocess:
            resume_text = self.preprocess_text(resume_text, remove_pii=True)
        
        # Truncate if too long (model has max sequence length)
        max_chars = 10000
        if len(resume_text) > max_chars:
            resume_text = resume_text[:max_chars]
        
        return self.encode_single(resume_text)
    
    async def encode_resume_async(self, resume_text: str, preprocess: bool = True) -> List[float]:
        """Async version of encode_resume that runs in a thread pool."""
        return await asyncio.to_thread(self.encode_resume, resume_text, preprocess)
    
    def encode_job_description(self, description: str, preprocess: bool = True) -> List[float]:
        """
        Generate embedding for a job description with optional preprocessing.
        
        Args:
            description: Full job description
            preprocess: Whether to apply normalization (PII removal less critical for jobs)
            
        Returns:
            Embedding as list of floats
        """
        if preprocess:
            # Light preprocessing for job descriptions (no PII removal needed)
            description = self.preprocess_text(description, remove_pii=False)
        
        # Truncate if too long
        max_chars = 10000
        if len(description) > max_chars:
            description = description[:max_chars]
        
        return self.encode_single(description)
    
    async def encode_job_description_async(self, description: str, preprocess: bool = True) -> List[float]:
        """Async version of encode_job_description."""
        return await asyncio.to_thread(self.encode_job_description, description, preprocess)
    
    async def encode_batch_async(self, texts: List[str], normalize: bool = True) -> np.ndarray:
        """
        Async batch encoding for multiple texts.
        Runs in thread pool to avoid blocking during training.
        """
        return await asyncio.to_thread(self.encode, texts, normalize)


# Singleton instance
@lru_cache()
def get_embedding_service() -> EmbeddingService:
    """Get the singleton embedding service instance."""
    return EmbeddingService()

