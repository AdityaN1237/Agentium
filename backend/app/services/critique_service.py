from typing import Any, Dict, Optional
from app.ai_engine.prompts import ELITE_CRITIQUE_PROMPT
import json
import logging

logger = logging.getLogger(__name__)

class CritiqueService:
    """Implements Loop 4: Cross-Agent Critique."""

    @staticmethod
    async def critique_decision(reviewer_agent_id: str, subject_prediction: Any, ground_truth: Optional[Any] = None) -> Dict[str, Any]:
        """
        Have one agent review another's prediction.
        """
        from app.services.llm_factory import get_llm
        llm = get_llm()
        
        prompt = ELITE_CRITIQUE_PROMPT.format(
            agent_a_prediction=json.dumps(subject_prediction, indent=2, default=str),
            ground_truth=json.dumps(ground_truth, indent=2, default=str) if ground_truth else "Not available"
        )

        try:
            response = await llm.chat_completion([{"role": "user", "content": prompt}])
            content = response["choices"][0]["message"]["content"]
            critique = json.loads(content)
            
            logger.info(f"⚖️ Critique by {reviewer_agent_id} completed. Recommendation: {critique.get('recommendation')}")
            return critique
        except Exception as e:
            logger.error(f"❌ Critique failed: {e}")
            return {
                "recommendation": "accept",
                "confidence_penalty": 0.0,
                "valid_objections": [f"Critique system error: {str(e)}"],
                "commentary": "Failed to generate critique."
            }

critique_service = CritiqueService()
