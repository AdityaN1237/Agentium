from typing import Any, Dict, List, Union
from app.agents.base import BaseAgent, AgentMetadata, MetricsModel
from app.services.embedding_service import get_embedding_service
from app.services.llm_factory import get_llm
import asyncio
from datetime import datetime
import logging
import json
import numpy as np
import os
import glob
from pathlib import Path

logger = logging.getLogger(__name__)

# Local storage paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR = BASE_DIR / "data"
EMBEDDINGS_DIR = DATA_DIR / "skill_job_matching" / "embeddings" / "jobs"

# Ensure directories exist
EMBEDDINGS_DIR.mkdir(parents=True, exist_ok=True)


class SkillJobMatchingAgent(BaseAgent):
    """
    Simple, strict matching agent based on 384-dim skill embeddings.
    
    Flow:
    1. Upload Job JSON -> Save {id, title, skills, embedding} to disk.
    2. Upload Resume -> Extract Skills -> Embed -> Match against disk.
    """
    
    def __init__(self, metadata: AgentMetadata = None):
        if not metadata:
            metadata = AgentMetadata(
                id="skill_job_matching",
                name="Skill-Job Matcher",
                description="Strict offline skill matching using MiniLM-L6-v2.",
                version="4.0.0",
                status="active",
                state="READY",
                type="matching"
            )
        super().__init__(metadata)
        self.embedding_service = get_embedding_service()

    async def _extract_skills_from_text(self, text: str) -> List[str]:
        """
        Step 6: Extract Resume Skills (From Extraction Logic).
        Also used for Job Description if skills not provided.
        """
        try:
            llm = get_llm()
            prompt = f"""
            Extract technical skills from the following text.
            
            Text: "{text[:4000]}"
            
            Return ONLY a raw JSON object with a single key "skills" containing a list of strings.
            Rules:
            - Lowercase all skills
            - Deduplicate
            - No enrichment
            - No hallucination
            
            Output format: {{ "skills": ["python", "sql", ...] }}
            """
            
            response = await llm.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            
            content = response['choices'][0]['message']['content']
            data = json.loads(content)
            return data.get("skills", [])
            
        except Exception as e:
            logger.error(f"Skill extraction failed: {e}")
            return []

    async def upload_dataset(self, data: Any) -> Dict[str, Any]:
        """
        STEP 1: Job JSON Upload
        Input: { "job_id": ..., "job_title": ..., "job_skill_set": [...] }
        """
        try:
            # Handle potential wrapping (e.g. {"jobs": [...]})
            if isinstance(data, dict):
                if "jobs" in data and isinstance(data["jobs"], list):
                    items = data["jobs"]
                elif "data" in data and isinstance(data["data"], list):
                    items = data["data"]
                else:
                    items = [data]
            elif isinstance(data, list):
                items = data
            else:
                 return {"status": "error", "message": "Invalid data format. Expected list or dict."}

            saved_count = 0
            
            for i, item in enumerate(items):
                if not isinstance(item, dict):
                    continue

                # Validate inputs with fallbacks
                job_id = item.get("job_id") or item.get("id") or item.get("_id")
                title = item.get("job_title") or item.get("title") or item.get("role")
                
                # Step 2: Extract Job Skills
                raw_skills = item.get("job_skill_set") or item.get("skills") or item.get("key_skills") or item.get("required_skills")
                
                # Debug first failure
                if not job_id and i == 0:
                    logger.warning(f"First item keys: {list(item.keys())}")
                
                final_skills = []
                if isinstance(raw_skills, list):
                     final_skills = [str(s).lower() for s in raw_skills]
                elif isinstance(raw_skills, str):
                    try:
                        parsed = json.loads(raw_skills.replace("'", '"'))
                        if isinstance(parsed, list):
                            final_skills = [str(s).lower() for s in parsed]
                        else:
                             # string is not a list
                             final_skills = [str(raw_skills).lower()]
                    except:
                         final_skills = [s.strip().lower() for s in raw_skills.split(',')]
                
                final_skills = list(set(final_skills))
                
                if not final_skills or not job_id:
                    if saved_count < 5: # Only log first few failures to avoid spam
                        logger.warning(f"Skipping item {i}: Found ID={job_id}, SkillsCount={len(final_skills)}")
                    continue
                    
                # Step 3: Create Job Embedding (MiniLM Only)
                text_to_embed = ", ".join(final_skills)
                embedding = await self.embedding_service.encode_single_async(text_to_embed)
                
                if isinstance(embedding, np.ndarray):
                    embedding = embedding.tolist()
                
                # Step 4: Save Job Embedding to Disk
                # sanitize filename
                safe_id = str(job_id).replace("/", "_").replace("\\", "_")
                job_file_path = EMBEDDINGS_DIR / f"{safe_id}.json"
                
                record = {
                    "job_id": str(job_id),
                    "job_title": title or "Unknown Role",
                    "job_skill_set": final_skills,
                    "embedding": embedding
                }
                
                with open(job_file_path, 'w') as f:
                    json.dump(record, f)
                
                saved_count += 1
            
            if saved_count == 0:
                 logger.warning("No jobs saved. Please check the JSON format.")
                 
            return {
                "status": "success",
                "message": f"Successfully processed and saved {saved_count} job profiles.",
                "count": saved_count
            }
            
        except Exception as e:
            logger.error(f"Job upload failed: {e}")
            return {"status": "error", "message": str(e)}

    async def predict_logic(self, input_data: Any) -> Any:
        """
        STEP 5-9: Resume Matching Flow
        """
        # Step 5: Input Resume Text (Passed from router/extractor)
        resume_text = input_data.get("resume_text") or input_data.get("text")
        
        if not resume_text:
            return {"status": "FAILED", "errors": ["No resume text provided"]}
            
        # Step 6: Extract Resume Skills
        extracted_skills = await self._extract_skills_from_text(resume_text)
        
        if not extracted_skills:
             return {"status": "FAILED", "errors": ["Could not extract any skills from resume"]}
             
        # Step 7: Create Resume Embedding
        text_to_embed = ", ".join(extracted_skills)
        query_embedding = await self.embedding_service.encode_single_async(text_to_embed)
        
        # Step 8: Offline Matching (Core Logic)
        matches = []
        
        # Load all job files
        # NOTE: For production with millions of jobs, we'd load this into memory once or use Vector DB.
        # For "Offline matching" plain usage, loading files is acceptable (or cached in memory).
        # We'll do simple file iteration as requested.
        
        job_files = glob.glob(str(EMBEDDINGS_DIR / "*.json"))
        
        for jf in job_files:
            try:
                with open(jf, 'r') as f:
                    job_data = json.load(f)
                
                job_emb = job_data.get("embedding")
                if not job_emb: continue
                
                # Cosine Similarity
                # A . B / |A|*|B|
                # Assuming embeddings are already unit normalized by SentenceTransformer?
                # Usually they are. If not, we normalize.
                # self.embedding_service usually returns normalized vectors.
                
                score = np.dot(query_embedding, job_emb)
                
                # Threshold >= 0.70
                if score >= 0.70:
                    matches.append({
                        "job_id": job_data["job_id"],
                        "job_title": job_data["job_title"],
                        "match_score": round(float(score), 2),
                        "matched_skills": list(set(extracted_skills).intersection(set(job_data.get("job_skill_set", []))))
                    })
            except Exception as e:
                logger.error(f"Error reading job file {jf}: {e}")
                continue
        
        # Sort by score desc
        matches.sort(key=lambda x: x["match_score"], reverse=True)
        
        # Step 9: Recommend Jobs (Return)
        return matches

    async def predict(self, input_data: Any) -> Any:
        try:
            result = await self.predict_logic(input_data)
            return {
                "status": "SUCCESS",
                "agent_id": self.metadata.id,
                "data": result
            }
        except Exception as e:
            logger.error(f"Predict error: {e}")
            return {"status": "FAILED", "errors": [str(e)]}

    # -- Unused Base Methods --
    async def validate_data_readiness(self) -> bool:
        return True
    async def index_data(self, session: Any) -> None:
        pass
    async def train_knowledge_graph(self, session: Any) -> None:
        pass
    async def calibrate_intelligence(self, session: Any) -> None:
        pass
    async def calibrate_scoring(self, session: Any) -> None:
        pass
    async def evaluate(self) -> MetricsModel:
        return MetricsModel(evaluated_at=datetime.utcnow())
