"""
Skill Expander Service.
Expands skills using the knowledge graph to find all related skills.
This is the key to matching Java → Spring Boot, React → Redux, etc.
"""
from typing import List, Set, Dict, Optional
from functools import lru_cache
from datetime import datetime
import logging

from app.services.embedding_service import get_embedding_service
from app.services.gemini_provider import gemini_provider

logger = logging.getLogger(__name__)


class SkillExpander:
    """
    Expands skills using a combination of:
    1. Pre-built skill taxonomy (knowledge graph)
    2. Semantic similarity using embeddings
    
    This ensures that a candidate with "Java" preference will match
    jobs requiring "Spring Boot", "Hibernate", etc.
    """
    
    _instance: Optional['SkillExpander'] = None
    _taxonomy: Optional[Dict] = None
    
    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the skill expander."""
        if self._taxonomy is None:
            self._taxonomy = {}
    
    async def load_taxonomy(self):
        """Load the skill taxonomy (In-memory/Local)."""
        # Removed DB load. For now, we can rely on dynamic expansion or a local JSON if needed.
        self._taxonomy = {} 
        logger.info("✅ Skill Expander initialized (Memory/Dynamic mode)")

    async def save_skill_info(self, skill: str, info: Dict):
        """Persist skill information (In-memory only)."""
        normalized = self.normalize_skill(skill)
        info['name'] = normalized
        info['updated_at'] = datetime.utcnow()
        self._taxonomy[normalized] = info

    
    def expand_skill(
        self, 
        skill: str, 
        include_related: bool = True,
        include_children: bool = True,
        include_alternatives: bool = True,
        depth: int = 1
    ) -> Set[str]:
        """
        Expand a single skill to include all related skills.
        
        Args:
            skill: The skill to expand
            include_related: Include semantically related skills
            include_children: Include child/specialized skills
            include_alternatives: Include alternative names
            depth: How many levels deep to expand
            
        Returns:
            Set of all related skill names
        """
        expanded = {self.normalize_skill(skill)}
        
        skill_info = self.get_skill_info(skill)
        if skill_info is None:
            return expanded
        
        # Add related skills
        if include_related:
            expanded.update([
                self.normalize_skill(s) 
                for s in skill_info.get('related_skills', [])
            ])
        
        # Add child skills
        if include_children:
            expanded.update([
                self.normalize_skill(s) 
                for s in skill_info.get('child_skills', [])
            ])
        
        # Add alternative names
        if include_alternatives:
            expanded.update([
                self.normalize_skill(s) 
                for s in skill_info.get('alternative_names', [])
            ])
        
        # Recursive expansion for deeper relationships
        if depth > 1:
            current_expanded = list(expanded)
            for s in current_expanded:
                if s != self.normalize_skill(skill):
                    deeper = self.expand_skill(
                        s, 
                        include_related=include_related,
                        include_children=include_children,
                        include_alternatives=include_alternatives,
                        depth=depth - 1
                    )
                    expanded.update(deeper)
        
        return expanded
    
    async def expand_skills_dynamic(self, skills: List[str]) -> Set[str]:
        """
        Use Gemini to dynamically expand skills based on current market trends and technology stacks.
        High-performance alternative to static taxonomy.
        """
        if not gemini_provider.api_key:
            return self.expand_skills(skills)

        prompt = f"""
        Given the following list of technical skills: {', '.join(skills)}
        
        Identify:
        1. Related technologies commonly used together (e.g., React -> Redux, Next.js)
        2. Underlying languages or frameworks (e.g., Spring Boot -> Java)
        3. Modern alternatives or supersets
        
        Return ONLY a comma-separated list of 10-15 highly relevant skills.
        """
        
        messages = [
            {"role": "system", "content": "You are a technical knowledge graph assistant."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = await gemini_provider.chat_completion(messages=messages, temperature=0.0)
            content = response['choices'][0]['message']['content']
            dynamic_skills = {self.normalize_skill(s.strip()) for s in content.split(',')}
            
            # Combine with static taxonomy for robustness
            static_skills = self.expand_skills(skills)
            return dynamic_skills.union(static_skills)
        except Exception as e:
            logger.error(f"Dynamic skill expansion failed: {e}")
            return self.expand_skills(skills)

    def expand_skills(
        self, 
        skills: List[str], 
        depth: int = 1
    ) -> Set[str]:
        """
        Expand a list of skills.
        
        Args:
            skills: List of skills to expand
            depth: Expansion depth
            
        Returns:
            Set of all expanded skills
        """
        all_expanded = set()
        
        for skill in skills:
            expanded = self.expand_skill(skill, depth=depth)
            all_expanded.update(expanded)
        
        return all_expanded
    
    def get_skill_match_score(
        self, 
        candidate_skills: List[str], 
        job_skills: List[str]
    ) -> tuple:
        """
        Calculate skill match score with expansion.
        
        Args:
            candidate_skills: Candidate's skills
            job_skills: Job's required skills
            
        Returns:
            Tuple of (score, matched_skills, missing_skills)
        """
        # Expand candidate skills
        expanded_candidate = self.expand_skills(candidate_skills, depth=2)
        
        # Normalize job skills
        normalized_job = {self.normalize_skill(s) for s in job_skills}
        
        # Find matches
        matched = expanded_candidate & normalized_job
        missing = normalized_job - expanded_candidate
        
        # Calculate score
        if not normalized_job:
            score = 0.0
        else:
            score = len(matched) / len(normalized_job)
        
        return score, list(matched), list(missing)
    
    def get_preference_match_score(
        self, 
        preferences: List[str], 
        job_title: str,
        job_skills: List[str]
    ) -> float:
        """
        Calculate how well a job matches candidate preferences.
        
        Args:
            preferences: Candidate's job preferences
            job_title: Job title
            job_skills: Job's required skills
            
        Returns:
            Preference match score (0-1)
        """
        if not preferences:
            return 0.5  # Neutral if no preferences
        
        # Expand preferences
        expanded_prefs = self.expand_skills(preferences, depth=2)
        
        # Check job title match
        title_words = set(job_title.lower().split())
        title_match = bool(expanded_prefs & title_words)
        
        # Check skill overlap
        job_skills_normalized = {self.normalize_skill(s) for s in job_skills}
        skill_overlap = len(expanded_prefs & job_skills_normalized)
        
        # Calculate score
        base_score = 0.3 if title_match else 0.0
        skill_bonus = min(skill_overlap * 0.1, 0.7)
        
        return min(base_score + skill_bonus, 1.0)
    
    def semantic_skill_match(
        self, 
        candidate_skills: List[str], 
        job_skills: List[str],
        threshold: float = 0.5
    ) -> tuple:
        """
        Use semantic embeddings to find skill matches.
        This catches cases where taxonomy doesn't have the relationship.
        
        Args:
            candidate_skills: Candidate's skills
            job_skills: Job's required skills
            threshold: Minimum similarity for a match
            
        Returns:
            Tuple of (score, semantic_matches)
        """
        if not candidate_skills or not job_skills:
            return 0.0, []
        
        embedding_service = get_embedding_service()
        
        # Get embeddings
        candidate_embeddings = embedding_service.encode_skills(candidate_skills)
        job_embeddings = embedding_service.encode_skills(job_skills)
        
        semantic_matches = []
        matched_job_indices = set()
        
        for i, cand_emb in enumerate(candidate_embeddings):
            for j, job_emb in enumerate(job_embeddings):
                if j in matched_job_indices:
                    continue
                    
                similarity = embedding_service.cosine_similarity(cand_emb, job_emb)
                
                if similarity >= threshold:
                    semantic_matches.append({
                        'candidate_skill': candidate_skills[i],
                        'job_skill': job_skills[j],
                        'similarity': float(similarity)
                    })
                    matched_job_indices.add(j)
        
        score = len(matched_job_indices) / len(job_skills) if job_skills else 0.0
        
        return score, semantic_matches
    
    def get_comprehensive_match(
        self, 
        candidate_skills: List[str],
        candidate_preferences: List[str],
        job_title: str,
        job_skills: List[str]
    ) -> Dict:
        """
        Get comprehensive skill matching using both taxonomy and semantics.
        
        Returns:
            Dictionary with all match details
        """
        # Taxonomy-based matching
        taxonomy_score, matched, missing = self.get_skill_match_score(
            candidate_skills, job_skills
        )
        
        # Semantic matching for remaining skills
        semantic_score, semantic_matches = self.semantic_skill_match(
            candidate_skills, 
            list(missing),  # Only check missing skills
            threshold=0.6
        )
        
        # Preference matching
        preference_score = self.get_preference_match_score(
            candidate_preferences, job_title, job_skills
        )
        
        # Add semantic matches to matched skills
        for sm in semantic_matches:
            matched.append(sm['job_skill'])
            missing.remove(sm['job_skill'])
        
        # Combined score
        final_score = max(taxonomy_score, taxonomy_score * 0.7 + semantic_score * 0.3)
        
        return {
            'skill_score': final_score,
            'preference_score': preference_score,
            'matched_skills': matched,
            'missing_skills': missing,
            'semantic_matches': semantic_matches,
            'expanded_candidate_skills': list(self.expand_skills(candidate_skills))
        }
    
    def get_all_categories(self) -> List[str]:
        """Get all skill categories from taxonomy."""
        categories = set()
        for skill_info in self._taxonomy.values():
            categories.add(skill_info.get('category', 'General'))
        return sorted(list(categories))
    
    def get_skills_by_category(self, category: str) -> List[str]:
        """Get all skills in a category."""
        skills = []
        for skill_name, skill_info in self._taxonomy.items():
            if skill_info.get('category', '').lower() == category.lower():
                skills.append(skill_name)
        return sorted(skills)


@lru_cache()
def get_skill_expander() -> SkillExpander:
    """Get the singleton skill expander instance."""
    return SkillExpander()
