import os
from typing import Dict, Any, List, Optional, Type
from app.services.llm_base import LLMProvider
from app.services.gemini_provider import GeminiProvider


class LocalProvider(LLMProvider):
    """
    Fallback LLM provider for self-healing and offline scenarios.
    """
    async def chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        # Minimal mock response to keep system running during provider downtime
        return {
            "choices": [{
                "message": {
                    "content": "{\"error\": \"LLM provider unavailable. System running in fallback mode.\"}"
                }
            }]
        }


class ProviderFactory:
    """
    Elite Factory for LLM Provider instantiation.
    """
    _providers: Dict[str, Type[LLMProvider]] = {
        "gemini": GeminiProvider,
        "local": LocalProvider
    }

    @classmethod
    def get_provider(cls, name: str = "gemini") -> LLMProvider:
        provider_cls = cls._providers.get(name.lower(), LocalProvider)
        return provider_cls()


def get_llm(name: Optional[str] = None) -> LLMProvider:
    """Zero-hardcoding helper to get primary provider."""
    # Logic to switch based on health (Self-Healing placeholder)
    try:
        provider_name = name or os.getenv("PRIMARY_LLM_PROVIDER", "gemini")
        return ProviderFactory.get_provider(provider_name)
    except Exception:
        return ProviderFactory.get_provider("local")
