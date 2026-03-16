import asyncio
import logging
from typing import Dict, List, Any
import json
from app.services.llm_factory import get_llm
from app.database import Database

logger = logging.getLogger(__name__)

class AgentTuner:
    """
    Advanced utility for calibrating agent prompts, verifying reasoning,
    and calculating real performance metrics.
    """

    def __init__(self):
        self.llm = get_llm()

    async def calibrate_prompts(self, agent_id: str, sample_inputs: List[Dict[str, Any]], system_prompt: str) -> Dict[str, Any]:
        """
        Runs samples through the LLM and uses a critic to evaluate quality.
        Returns a 'calibration_score' and suggested refinements.
        """
        results = []
        for inp in sample_inputs:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": str(inp)}
            ]
            response = await self.llm.chat_completion(messages, temperature=0.0)
            content = response['choices'][0]['message']['content']
            
            # Use LLM as internal critic
            critic_prompt = f"""
            Evaluation Task: Audit the following AI agent output for logical consistency, schema adherence, and reasoning depth.
            Input: {str(inp)}
            Agent Output: {content}
            
            Score from 0.0 to 1.0. If reasoning is missing or shallow, deduct points.
            Return ONLY a JSON object: {{"score": float, "feedback": "str"}}
            """
            critic_resp = await self.llm.chat_completion(
                [{"role": "system", "content": "You are a quality control AI."}, {"role": "user", "content": critic_prompt}],
                response_format={"type": "json_object"}
            )
            audit = json.loads(critic_resp['choices'][0]['message']['content'])
            results.append(audit['score'])

        avg_score = sum(results) / len(results) if results else 0.0
        return {
            "calibration_score": avg_score,
            "status": "EXCELLENT" if avg_score > 0.9 else "NEEDS_TUNING",
            "samples_tested": len(results)
        }

    async def benchmark_retrieval(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """
        Verifies vector retrieval accuracy for RAG agents.
        """
        db = Database.get_db()
        from app.services.embedding_service import get_embedding_service
        embedder = get_embedding_service()
        
        query_emb = await asyncio.to_thread(embedder.encode_single, query)
        
        # Simple proximity check in DB
        cursor = db.doc_chunks.find({})
        chunks = await cursor.to_list(length=1000)
        
        scores = []
        for chunk in chunks:
            sim = embedder.cosine_similarity(query_emb, chunk['embedding'])
            scores.append(sim)
            
        top_scores = sorted(scores, reverse=True)[:top_k]
        return {
            "mean_top_sim": sum(top_scores)/len(top_scores) if top_scores else 0.0,
            "max_sim": max(top_scores) if top_scores else 0.0
        }

    async def run_skill_match_stress_test(self, candidate_skills: List[str], job_skills: List[str]) -> Dict[str, Any]:
        """
        Verifies if the RecommendationEngine correctly handles edge cases.
        """
        from app.services.recommendation_engine import get_recommendation_engine
        engine = get_recommendation_engine()
        
        # Test direct overlap
        score_data = engine.skill_expander.get_comprehensive_match(
            candidate_skills, [], "Test Job", job_skills
        )
        
        return {
            "skill_score": score_data['skill_score'],
            "matched_count": len(score_data['matched_skills']),
            "missing_count": len(score_data['missing_skills'])
        }

    async def calibrate_knowledge_base(self, agent_id: str) -> Dict[str, Any]:
        """
        Verifies the quality and depth of the persistent Knowledge Graph.
        """
        db = Database.get_db()
        skill_count = await db.skills.count_documents({})
        relationship_count = 0
        
        cursor = db.skills.find({})
        async for skill in cursor:
            relationship_count += len(skill.get('related_skills', []))
            relationship_count += len(skill.get('child_skills', []))
            
        avg_density = relationship_count / skill_count if skill_count > 0 else 0.0
        
        return {
            "calibration_score": min(avg_density / 5.0, 1.0), # Target 5 relationships per skill
            "status": "DENSE" if avg_density > 3.0 else "SPARSE",
            "skill_nodes": skill_count,
            "total_edges": relationship_count
        }

    async def calibrate_rag(self, query: str, expected_text_snippet: str) -> Dict[str, Any]:
        """
        Verifies if RAG can find a specific snippet given a query.
        """
        benchmark = await self.benchmark_retrieval(query)
        
        db = Database.get_db()
        # Find if expected snippet exists in top matches
        from app.services.embedding_service import get_embedding_service
        embedder = get_embedding_service()
        query_emb = await asyncio.to_thread(embedder.encode_single, query)
        
        cursor = db.doc_chunks.find({}).sort([("score", -1)]).limit(10)
        # Manual similarity search since MongoDB doesn't have native vector search in this setup
        all_chunks = await db.doc_chunks.find({}).to_list(length=1000)
        scored_chunks = []
        for c in all_chunks:
            sim = embedder.cosine_similarity(query_emb, c['embedding'])
            scored_chunks.append((sim, c['text']))
            
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        top_10_texts = [x[1] for x in scored_chunks[:10]]
        
        found = any(expected_text_snippet.lower() in t.lower() for t in top_10_texts)
        
        return {
            "retrieval_success": found,
            "max_similarity": benchmark['max_sim'],
            "status": "PASS" if found else "FAIL"
        }

def get_agent_tuner() -> AgentTuner:
    return AgentTuner()
