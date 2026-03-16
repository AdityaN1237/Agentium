from typing import Dict, List, Set

class SkillNode:
    def __init__(self, name: str):
        self.name = name
        self.neighbors: Set['SkillNode'] = set() # Transitive dependencies / relationships

class SkillGraph:
    """
    Elite Graph-based Skill Expansion (DAG).
    Allows for complex relationship traversal and depth-aware weighting.
    """
    def __init__(self):
        self.nodes: Dict[str, SkillNode] = {}

    def add_skill(self, skill: str):
        skill = skill.lower()
        if skill not in self.nodes:
            self.nodes[skill] = SkillNode(skill)
        return self.nodes[skill]

    def add_relationship(self, skill_a: str, skill_b: str):
        node_a = self.add_skill(skill_a)
        node_b = self.add_skill(skill_b)
        node_a.neighbors.add(node_b)

    def expand(self, skills: List[str], depth: int = 1) -> Set[str]:
        expanded = set(s.lower() for s in skills)
        to_visit = list(expanded)
        
        for _ in range(depth):
            next_visit = []
            for skill in to_visit:
                if skill in self.nodes:
                    for neighbor in self.nodes[skill].neighbors:
                        if neighbor.name not in expanded:
                            expanded.add(neighbor.name)
                            next_visit.append(neighbor.name)
            to_visit = next_visit
            if not to_visit: break
            
        return expanded

_skill_graph = None

def get_skill_graph() -> SkillGraph:
    global _skill_graph
    if _skill_graph is None:
        _skill_graph = SkillGraph()
        # Seed with basic tech stack relationships
        _skill_graph.add_relationship("python", "fastapi")
        _skill_graph.add_relationship("python", "django")
        _skill_graph.add_relationship("javascript", "react")
        _skill_graph.add_relationship("javascript", "node.js")
        _skill_graph.add_relationship("java", "spring boot")
        _skill_graph.add_relationship("react", "redux")
        _skill_graph.add_relationship("node.js", "express")
    return _skill_graph
