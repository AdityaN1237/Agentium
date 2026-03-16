"""
AI-Powered Job Recommendation Engine.
Uses a hybrid approach combining:
1. Semantic embeddings (Sentence Transformers)
2. Skill knowledge graph expansion
3. Multi-factor weighted scoring

This is the core intelligence for accurate job recommendations.
"""
import numpy as np
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging
import heapq

from app.services.embedding_service import get_embedding_service
from app.services.skill_expander import get_skill_expander
from app.services.config_service import config_service
from app.database import Database

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """
    Advanced recommendation engine using hybrid AI approach.
    
    Scoring Formula:
    - Semantic Similarity (resume vs job description)
    - Skill Match Score (with expansion from knowledge graph)
    - Preference Alignment Score
    """
    
    def __init__(self):
        """Initialize the recommendation engine."""
        self.embedding_service = get_embedding_service()
        self.skill_expander = get_skill_expander()
        from app.services.llm_factory import get_llm
        self.llm_factory = get_llm()

    async def recommend_jobs_for_candidate(
        self,
        candidate_id: str,
        top_k: int = 10,
        temp_candidate: Optional[Dict] = None
    ) -> Dict:
        """
        Get top job recommendations for a specific candidate.
        
        Args:
            candidate_id: Candidate's database ID
            top_k: Number of recommendations to return
            
        Returns:
            RecommendationResponse with detailed match information
        """
        db = Database.get_db()

        # Get candidate
        if temp_candidate:
            candidate = temp_candidate
        else:
            from bson import ObjectId
            candidate = await db.candidates.find_one({"_id": ObjectId(candidate_id)})
            if not candidate:
                raise ValueError(f"Candidate not found: {candidate_id}")

        # Validate candidate has meaningful data
        skills = candidate.get('skills', [])
        resume_text = candidate.get('resume_text', '')
        resume_embedding = candidate.get('resume_embedding')

        has_meaningful_data = (
            (skills and len(skills) > 0) or
            (resume_text and len(resume_text.strip()) >= 50) or
            resume_embedding
        )

        if not has_meaningful_data:
            return {
                "candidate_id": candidate_id,
                "candidate_name": candidate.get("name", "Unknown"),
                "total_jobs_analyzed": 0,
                "recommendations": [],
                "message": "Candidate profile lacks sufficient data for job matching. Please upload a complete resume.",
                "generated_at": datetime.utcnow()
            }
        
        # Get all active jobs (include jobs without is_active field for backward compatibility)
        jobs_cursor = db.jobs.find({"$or": [{"is_active": True}, {"is_active": {"$exists": False}}]})
        jobs = await jobs_cursor.to_list(length=None)
        
        if not jobs:
            return {
                "candidate_id": candidate_id,
                "candidate_name": candidate.get("name", "Unknown"),
                "total_jobs_analyzed": 0,
                "recommendations": [],
                "generated_at": datetime.utcnow()
            }
        
        # Calculate match scores for all jobs using Min-Heap for O(n log k)
        heap = []
        
        # Fetch dynamic weights (Strictly aligned to requested formula)
        # Component: Semantic Similarity (40%), Skill Match (35%), Preference Alignment (25%)
        config = config_service.get_config("skill_job_matching")
        
        # Cold Start Handling: If detected, trust semantic search (resume text) more than extracted skills
        is_cold_start = self._detect_cold_start(candidate)
        if is_cold_start:
            logger.info(f"Cold start detected for candidate {candidate_id}. Adjusting weights.")
            semantic_weight = 0.70  # Trust content more
            skill_weight = 0.20     # Trust sparse skills less
            preference_weight = 0.10
        else:
            semantic_weight = 0.40
            skill_weight = 0.35
            preference_weight = 0.25

        for job in jobs:
            try:
                match_result = await self._calculate_match_score(
                    candidate, job, semantic_weight, skill_weight, preference_weight
                )
                
                # Min-Heap stores (score, data)
                item = (match_result['match_score'], str(job['_id']), {
                    "job": job,
                    **match_result
                })
                
                if len(heap) < top_k:
                    heapq.heappush(heap, item)
                else:
                    heapq.heappushpop(heap, item)
                    
            except Exception as e:
                logger.warning(f"Error scoring job {job.get('_id')}: {e}")
                continue
        
        # Max-score first (reverse heap)
        scored_jobs = sorted(heap, key=lambda x: x[0], reverse=True)
        top_recommendations = [item[2] for item in scored_jobs]

        
        # Format response
        recommendations = []
        for rec in top_recommendations:
            job = rec['job']
            recommendations.append({
                "job": {
                    "_id": str(job["_id"]),
                    "title": job.get("title"),
                    "company": job.get("company"),
                    "location": job.get("location"),
                    "job_type": job.get("job_type"),
                    "experience_required": job.get("experience_required"),
                    "salary_range": job.get("salary_range"),
                    "description": job.get("description"),
                    "required_skills": job.get("required_skills", []),
                    "nice_to_have_skills": job.get("nice_to_have_skills", []),
                    "expanded_skills": job.get("expanded_skills"),
                    "is_active": job.get("is_active", True)
                },
                "match_score": rec['match_score'],
                "semantic_score": rec['semantic_score'],
                "skill_score": rec['skill_score'],
                "preference_score": rec['preference_score'],
                "matched_skills": rec['matched_skills'],
                "missing_skills": rec['missing_skills'],
                "match_explanation": rec['explanation']
            })
        
        return {
            "candidate_id": candidate_id,
            "candidate_name": candidate.get("name", "Ad-hoc Candidate" if temp_candidate else "Unknown"),
            "total_jobs_analyzed": len(jobs),
            "recommendations": recommendations,
            "generated_at": datetime.utcnow()
        }
    
    async def _calculate_match_score(
        self, 
        candidate: Dict, 
        job: Dict,
        semantic_weight: float,
        skill_weight: float,
        preference_weight: float
    ) -> Dict:
        """
        Calculate comprehensive match score between candidate and job.
        Following mandatory scoring engine calibration.
        
        Inspired by Two-Tower architecture: includes domain-aware matching.
        """
        # 1. SEMANTIC SIMILARITY (40%)
        semantic_score = await self._calculate_semantic_score(candidate, job)
        
        # 2. SKILL MATCH SCORE (35%)
        skill_result = self.skill_expander.get_comprehensive_match(
            candidate_skills=candidate.get('skills', []),
            candidate_preferences=candidate.get('preferences', []),
            job_title=job.get('title', ''),
            job_skills=job.get('required_skills', [])
        )
        skill_score = skill_result['skill_score']
        matched_skills = skill_result['matched_skills']
        missing_skills = skill_result['missing_skills']
        
        # 3. PREFERENCE ALIGNMENT (25%)
        # Note: skill_expander.get_comprehensive_match already calculates a preference_score
        # but we ensure it's normalized 0-1.
        preference_score = min(max(skill_result.get('preference_score', 0.5), 0.0), 1.0)
        
        # 4. DOMAIN SIMILARITY BOOST (Inspired by Two-Tower Architecture)
        # Boosts score when candidate's domain expertise matches job's domain
        domain_boost = self._calculate_domain_similarity(candidate, job, matched_skills)
        
        # CALCULATE WEIGHTED FINAL SCORE
        # final_score = (0.40 × semantic_similarity) + (0.35 × skill_match) + (0.25 × preference_match)
        base_score = (
            semantic_weight * semantic_score +
            skill_weight * skill_score +
            preference_weight * preference_score
        )
        
        # Apply domain boost (up to 10% additional score)
        final_score = base_score + (domain_boost * 0.1)
        
        # Ensure score is between 0 and 1
        final_score = min(max(final_score, 0.0), 1.0)
        
        # Generate explanation for Auditability
        explanation = self._generate_explanation(
            semantic_score, skill_score, preference_score,
            matched_skills, missing_skills, candidate, job,
            semantic_weight, skill_weight, preference_weight
        )
        
        # Explainability: Use LLM for premium explanation (World-Class Feature)
        premium_explanation = await self._generate_llm_explanation(candidate, job, final_score, matched_skills, missing_skills)

        return {
            'match_score': round(final_score, 4),
            'semantic_score': round(semantic_score, 4),
            'skill_score': round(skill_score, 4),
            'preference_score': round(preference_score, 4),
            'domain_boost': round(domain_boost, 4),
            'matched_skills': matched_skills,
            'missing_skills': missing_skills,
            'explanation': premium_explanation or explanation
        }
    
    def _calculate_domain_similarity(self, candidate: Dict, job: Dict, matched_skills: list) -> float:
        """
        Calculate domain similarity between candidate and job (Two-Tower inspired).
        
        Uses skill categories to infer domain alignment:
        - High overlap in "Backend" skills → backend job = boost
        - Frontend skills → frontend job = boost
        
        Returns a 0-1 score indicating domain match strength.
        """
        # Infer candidate's primary domain from skills
        candidate_skills = set(s.lower() for s in candidate.get('skills', []))
        job_title = job.get('title', '').lower()
        job_skills = set(s.lower() for s in job.get('required_skills', []))
        
        # Domain indicators
        backend_indicators = {'python', 'java', 'fastapi', 'django', 'spring', 'node.js', 'go', 'rust', 'postgresql', 'mongodb', 'api'}
        frontend_indicators = {'react', 'vue', 'angular', 'javascript', 'typescript', 'css', 'html', 'next.js', 'tailwind'}
        devops_indicators = {'docker', 'kubernetes', 'aws', 'terraform', 'ci/cd', 'jenkins', 'linux', 'ansible'}
        ml_indicators = {'python', 'tensorflow', 'pytorch', 'machine learning', 'deep learning', 'nlp', 'data science'}
        
        # Calculate candidate domain scores
        candidate_backend = len(candidate_skills & backend_indicators)
        candidate_frontend = len(candidate_skills & frontend_indicators)
        candidate_devops = len(candidate_skills & devops_indicators)
        candidate_ml = len(candidate_skills & ml_indicators)
        
        # Infer job domain from title and skills
        job_is_backend = 'backend' in job_title or len(job_skills & backend_indicators) >= 2
        job_is_frontend = 'frontend' in job_title or len(job_skills & frontend_indicators) >= 2
        job_is_devops = 'devops' in job_title or 'sre' in job_title or len(job_skills & devops_indicators) >= 2
        job_is_ml = 'ml' in job_title or 'machine learning' in job_title or 'data' in job_title or len(job_skills & ml_indicators) >= 2
        
        # Calculate domain match
        domain_score = 0.0
        matches = 0
        
        if job_is_backend and candidate_backend >= 2:
            domain_score += min(candidate_backend / 4, 1.0)
            matches += 1
        if job_is_frontend and candidate_frontend >= 2:
            domain_score += min(candidate_frontend / 4, 1.0)
            matches += 1
        if job_is_devops and candidate_devops >= 2:
            domain_score += min(candidate_devops / 4, 1.0)
            matches += 1
        if job_is_ml and candidate_ml >= 2:
            domain_score += min(candidate_ml / 4, 1.0)
            matches += 1
        
        # Normalize by number of matches
        if matches > 0:
            domain_score = domain_score / matches
        else:
            # Default: check if any skill overlap exists
            if matched_skills:
                domain_score = min(len(matched_skills) / 5, 0.5)
            else:
                domain_score = 0.0
        
        return min(domain_score, 1.0)

    async def _generate_llm_explanation(
        self, candidate: Dict, job: Dict, score: float, 
        matched: List[str], missing: List[str]
    ) -> str:
        """
        Generate a human-friendly explanation for the job match using LLM.
        This provides 'Why this job' transparency.
        """
        try:
            prompt = f"""You are a career coach expecting to explain a job match to a candidate.
            
            Candidate Skills: {', '.join(candidate.get('skills', [])[:10])}
            Job Title: {job.get('title')}
            Job Required Skills: {', '.join(job.get('required_skills', [])[:10])}
            
            Match Score: {score:.2f}/1.0
            
            Key Matching Skills: {', '.join(matched[:5])}
            Missing Skills: {', '.join(missing[:5])}
            
            Write a 2-sentence explanation of why this job is a good (or bad) fit. 
            Be encouraging but realistic. Focus on the skills overlap.
            """
            
            response = await self.llm_factory.chat_completion(
                [{"role": "user", "content": prompt}],
                temperature=0.7
            )
            return response['choices'][0]['message']['content'].strip()
        except Exception as e:
            logger.warning(f"LLM explanation failed: {e}")
            return None

    async def generate_career_path(self, candidate_id: str) -> Dict[str, Any]:
        """
        Generate career path inference and gap analysis.
        World-Class Feature: "Career Path Intelligence".
        
        Infer:
        - Current Role Level
        - Next Logical Role
        - Ultimate Likely Goal
        - Skill Gaps to reach next role
        """
        db = Database.get_db()
        from bson import ObjectId
        candidate = await db.candidates.find_one({"_id": ObjectId(candidate_id)})
        
        if not candidate:
            raise ValueError("Candidate not found")
            
        skills = candidate.get("skills", [])
        resume_text = candidate.get("resume_text", "")[:1000]  # First 1k chars for context
        
        try:
            prompt = f"""Analyze this candidate's profile to suggest a career path.
            
            Skills: {', '.join(skills[:15])}
            Resume Snippet: {resume_text}
            
            Return a JSON object with:
            - "current_level": (e.g., Junior, Mid, Senior)
            - "next_role": (Title of the next logical step)
            - "long_term_goal": (A likely ultimate career goal, e.g., CTO, Principal Architect)
            - "skills_to_acquire": (List of 3-5 skills needed for the Next Role)
            - "reasoning": (Brief explanation)
            """
            
            response = await self.llm_factory.chat_completion(
                [{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.7
            )
            
            import json
            result = json.loads(response['choices'][0]['message']['content'])
            return result
            
        except Exception as e:
            logger.error(f"Career path generation failed: {e}")
            return {
                "error": "Could not generate career path",
                "details": str(e)
            }

    def _detect_cold_start(self, candidate: Dict) -> bool:
        """
        Detect if candidate is a 'cold start' user (new, little data).
        """
        has_skills = len(candidate.get('skills', [])) > 2
        has_resume = len(candidate.get('resume_text', '')) > 100
        has_history = candidate.get('interaction_count', 0) > 5
        
        return not (has_skills and has_resume) and not has_history

    
    async def _calculate_semantic_score(self, candidate: Dict, job: Dict) -> float:
        """
        Calculate semantic similarity between candidate and job.
        Uses pre-computed embeddings when available.
        """
        import asyncio
        
        # Get or compute embeddings
        candidate_embedding = candidate.get('resume_embedding')
        job_embedding = job.get('job_embedding')
        
        if candidate_embedding is None:
            resume_text = candidate.get('resume_text', '')
            if not resume_text:
                return 0.0
            # Run CPU-bound embedding in thread to avoid blocking event loop
            candidate_embedding = await asyncio.to_thread(
                self.embedding_service.encode_resume, resume_text
            )
        
        if job_embedding is None:
            description = job.get('description', '')
            if not description:
                return 0.0
            # Run CPU-bound embedding in thread to avoid blocking event loop
            job_embedding = await asyncio.to_thread(
                self.embedding_service.encode_job_description, description
            )
        
        # Calculate cosine similarity
        similarity = self.embedding_service.cosine_similarity(
            np.array(candidate_embedding),
            np.array(job_embedding)
        )
        
        # Convert to 0-1 range (cosine similarity can be negative)
        return (similarity + 1) / 2
    
    def _generate_explanation(
        self,
        semantic_score: float,
        skill_score: float,
        preference_score: float,
        matched_skills: List[str],
        missing_skills: List[str],
        candidate: Dict,
        job: Dict,
        semantic_weight: float,
        skill_weight: float,
        preference_weight: float
    ) -> str:
        """Generate human-readable explanation of the match."""
        explanations = []
        
        # Overall assessment
        overall = semantic_score * semantic_weight + skill_score * skill_weight + preference_score * preference_weight
        if overall >= 0.8:
            explanations.append("Excellent match!")
        elif overall >= 0.6:
            explanations.append("Strong match.")
        elif overall >= 0.4:
            explanations.append("Good potential match.")
        else:
            explanations.append("Partial match.")
        
        # Skill match details
        if matched_skills:
            top_matched = matched_skills[:5]
            explanations.append(
                f"Matching skills: {', '.join(top_matched)}"
                + (f" (+{len(matched_skills) - 5} more)" if len(matched_skills) > 5 else "")
            )
        
        # Missing skills
        if missing_skills and len(missing_skills) <= 3:
            explanations.append(f"Skills to develop: {', '.join(missing_skills)}")
        elif missing_skills:
            explanations.append(f"Missing {len(missing_skills)} required skills")
        
        # Preference alignment
        if preference_score >= 0.7:
            explanations.append("Aligns well with stated preferences.")
        
        return " ".join(explanations)
    
    async def get_all_recommendations(
        self, 
        top_k_per_candidate: int = 10
    ) -> List[Dict]:
        """
        Get recommendations for all candidates.
        
        Returns:
            List of recommendation responses for all candidates
        """
        db = Database.get_db()
        
        # Get all candidates
        candidates_cursor = db.candidates.find({})
        candidates = await candidates_cursor.to_list(length=None)
        
        all_recommendations = []
        
        for candidate in candidates:
            try:
                recs = await self.recommend_jobs_for_candidate(
                    str(candidate['_id']), 
                    top_k=top_k_per_candidate
                )
                all_recommendations.append(recs)
            except Exception as e:
                logger.error(f"Error getting recommendations for {candidate.get('_id')}: {e}")
        
        return all_recommendations
    
    async def refresh_embeddings(self):
        """
        Refresh all embeddings in the database.
        Call this when model or data changes.
        """
        db = Database.get_db()
        
        # Update candidate embeddings
        candidates_cursor = db.candidates.find({})
        async for candidate in candidates_cursor:
            resume_text = candidate.get('resume_text', '')
            if resume_text:
                embedding = self.embedding_service.encode_resume(resume_text)
                expanded_skills = list(self.skill_expander.expand_skills(
                    candidate.get('skills', []), depth=2
                ))
                
                await db.candidates.update_one(
                    {"_id": candidate["_id"]},
                    {
                        "$set": {
                            "resume_embedding": embedding,
                            "expanded_skills": expanded_skills,
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
        
        # Update job embeddings
        jobs_cursor = db.jobs.find({})
        async for job in jobs_cursor:
            description = job.get('description', '')
            if description:
                embedding = self.embedding_service.encode_job_description(description)
                expanded_skills = list(self.skill_expander.expand_skills(
                    job.get('required_skills', []), depth=1
                ))
                
                await db.jobs.update_one(
                    {"_id": job["_id"]},
                    {
                        "$set": {
                            "job_embedding": embedding,
                            "expanded_skills": expanded_skills,
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
        
        logger.info("✅ All embeddings refreshed")

    async def find_similar_jobs_by_vector(self, candidate_vector: List[float], top_k: int = 10) -> List[Dict]:
        """
        Efficiently find jobs similar to a query vector using batch operations.
        Useful for ad-hoc resume validation where we don't have a full candidate record.
        """
        db = Database.get_db()
        jobs = await db.jobs.find({"job_embedding": {"$ne": None}, "is_active": True}).to_list(length=None)
        
        if not jobs:
            return []

        # Convert to numpy for batch operation
        job_embeddings = np.array([j["job_embedding"] for j in jobs])
        query_vec = np.array(candidate_vector)
        
        # Calculate scores
        scores = self.embedding_service.batch_cosine_similarity(query_vec, job_embeddings)
        
        # Rank
        ranked_indices = np.argsort(scores)[::-1][:top_k]
        
        results = []
        for idx in ranked_indices:
            j = jobs[idx]
            results.append({
                "job_id": str(j["_id"]),
                "title": j.get("title"),
                "company": j.get("company"),
                "score": float(scores[idx]),
                "required_skills": j.get("required_skills", []),
                "description": j.get("description", "")[:200]
            })
            
        return results

    async def batch_recommend_all_candidates(
        self, 
        top_k_per_candidate: int = 10
    ) -> List[Dict]:
        """
        Efficiently compute recommendations for all candidates using batch matrix operations.
        Inspired by Two-Tower architecture's similarity matrix computation.
        
        This is O(n*m) where n=candidates, m=jobs instead of O(n*m*d) for individual computations.
        
        Returns:
            List of recommendation responses for all candidates
        """
        db = Database.get_db()
        
        # Load all candidates and jobs with embeddings
        candidates = await db.candidates.find({"resume_embedding": {"$ne": None}}).to_list(length=None)
        jobs = await db.jobs.find({"job_embedding": {"$ne": None}, "is_active": True}).to_list(length=None)
        
        if not candidates or not jobs:
            logger.warning("No candidates or jobs with embeddings found for batch processing")
            return []
        
        # Extract embeddings as matrices
        candidate_embeddings = np.array([c["resume_embedding"] for c in candidates])
        job_embeddings = np.array([j["job_embedding"] for j in jobs])
        
        # Normalize for cosine similarity
        candidate_norms = np.linalg.norm(candidate_embeddings, axis=1, keepdims=True)
        job_norms = np.linalg.norm(job_embeddings, axis=1, keepdims=True)
        
        candidate_embeddings = candidate_embeddings / (candidate_norms + 1e-8)
        job_embeddings = job_embeddings / (job_norms + 1e-8)
        
        # Compute similarity matrix: [num_candidates, num_jobs]
        similarity_matrix = np.dot(candidate_embeddings, job_embeddings.T)
        
        # Get top-k jobs for each candidate
        all_recommendations = []
        for i, candidate in enumerate(candidates):
            scores = similarity_matrix[i]
            top_indices = np.argsort(scores)[::-1][:top_k_per_candidate]
            
            recommendations = []
            for idx in top_indices:
                job = jobs[idx]
                # Combine semantic score with skill matching
                semantic_score = float(scores[idx])
                skill_result = self.skill_expander.get_comprehensive_match(
                    candidate_skills=candidate.get('skills', []),
                    candidate_preferences=candidate.get('preferences', []),
                    job_title=job.get('title', ''),
                    job_skills=job.get('required_skills', [])
                )
                
                # Quick composite score (lighter than full _calculate_match_score)
                composite_score = (
                    0.45 * (semantic_score + 1) / 2 +  # Normalize to 0-1
                    0.35 * skill_result['skill_score'] +
                    0.20 * skill_result.get('preference_score', 0.5)
                )
                
                recommendations.append({
                    "job_id": str(job["_id"]),
                    "title": job.get("title"),
                    "company": job.get("company"),
                    "semantic_score": round(semantic_score, 4),
                    "skill_score": round(skill_result['skill_score'], 4),
                    "composite_score": round(composite_score, 4),
                    "matched_skills": skill_result['matched_skills'][:5]
                })
            
            all_recommendations.append({
                "candidate_id": str(candidate["_id"]),
                "candidate_name": candidate.get("name", "Unknown"),
                "recommendations": recommendations
            })
        
        logger.info(f"✅ Batch processed {len(candidates)} candidates × {len(jobs)} jobs")
        return all_recommendations


# Factory function
def get_recommendation_engine() -> RecommendationEngine:
    """Get a recommendation engine instance."""
    return RecommendationEngine()

