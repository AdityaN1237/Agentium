from typing import Dict, List, Optional

class TrieNode:
    def __init__(self):
        self.children: Dict[str, TrieNode] = {}
        self.is_end_of_word: bool = False
        self.skill_metadata: Optional[Dict] = None

class SkillTrie:
    """
    Elite Trie data structure for O(L) skill search and autocomplete.
    L = Length of the search prefix.
    """
    def __init__(self):
        self.root = TrieNode()

    def insert(self, skill: str, metadata: Optional[Dict] = None):
        node = self.root
        for char in skill.lower():
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_end_of_word = True
        node.skill_metadata = metadata

    def search(self, prefix: str) -> List[str]:
        node = self.root
        for char in prefix.lower():
            if char not in node.children:
                return []
            node = node.children[char]
        
        results = []
        self._dfs(node, prefix, results)
        return results

    def _dfs(self, node: TrieNode, prefix: str, results: List[str]):
        if node.is_end_of_word:
            results.append(prefix)
        
        for char, child_node in node.children.items():
            self._dfs(child_node, prefix + char, results)

_skill_trie = None

def get_skill_trie() -> SkillTrie:
    global _skill_trie
    if _skill_trie is None:
        _skill_trie = SkillTrie()
    return _skill_trie
