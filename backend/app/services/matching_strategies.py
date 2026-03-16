from abc import ABC, abstractmethod
from typing import Dict

class MatchingStrategy(ABC):
    """
    Elite Strategy pattern for dynamic matching algorithms.
    """
    @abstractmethod
    def calculate_score(self, candidate: Dict, job: Dict, **kwargs) -> Dict:
        pass

class AdaptiveMatchingStrategy(MatchingStrategy):
    """
    Dynamic strategy that uses weights from the agent's Policy Memory.
    """
    def calculate_score(self, candidate: Dict, job: Dict, **kwargs) -> Dict:
        # Pull weights from policy if provided, else use defaults
        policy_weights = kwargs.get('policy_weights', {})
        semantic_w = policy_weights.get('semantic', 0.40)
        skill_w = policy_weights.get('skill', 0.35)
        pref_w = policy_weights.get('preference', 0.25)

        # Placeholder for actual scoring logic which will be integrated
        # into recommendation_engine.py using this strategy.
        return {
            "match_score": 0.0,
            "breakdown": {
                "semantic": 0.0,
                "skill": 0.0,
                "preference": 0.0
            },
            "weights_used": {
                "semantic": semantic_w,
                "skill": skill_w,
                "preference": pref_w
            }
        }

class SemanticSkillStrategy(MatchingStrategy):
    """
    Standard Hybrid Strategy combining Vector Similarity and Skill expansion.
    """
    def calculate_score(self, candidate: Dict, job: Dict, **kwargs) -> Dict:
        return {"match_score": 0.0}
