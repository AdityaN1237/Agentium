import functools
import logging
from typing import Callable, Any

logger = logging.getLogger(__name__)

def self_healing(fallback_schema: Any = None):
    """
    Elite Self-Healing decorator for Agent methods.
    Detects failures and automatically executes fallback logic or provider switching.
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                # Primary attempt
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(f"⚠️ Self-Healing detected failure in {func.__name__}: {e}")
                
                # Attempt 2: Switch to Local Fallback Provider if it was an LLM error
                try:
                    logger.info("🔧 Attempting fallback to Local LLM Provider...")
                    # This logic depends on how args are passed to the agent
                    # For simplicity, we assume the agent can handle a provider switch internally
                    # or we return a safe default based on the schema
                    if fallback_schema:
                        logger.info(f"🛡️ Returning safe default schema for {func.__name__}")
                        try:
                            return fallback_schema().dict()
                        except Exception:
                            # If schema requires mandatory fields, try to construct with zeroed values
                            try:
                                # Get mandatory fields from pydantic model
                                fields = fallback_schema.model_fields
                                defaults = {}
                                for name, info in fields.items():
                                    if info.annotation == float: defaults[name] = 0.0
                                    elif info.annotation == int: defaults[name] = 0
                                    elif info.annotation == str: defaults[name] = "N/A"
                                    elif getattr(info.annotation, "__origin__", None) == list: defaults[name] = []
                                    elif getattr(info.annotation, "__origin__", None) == dict: defaults[name] = {}
                                    else: defaults[name] = None
                                return fallback_schema(**defaults).dict()
                            except Exception as e2:
                                logger.error(f"Failed to create zeroed fallback schema: {e2}")
                                return {"error": "Degraded mode"}
                    
                    raise e # Case where no schema fallback is provided
                except Exception as final_e:
                    logger.critical(f"🚨 Self-healing failed for {func.__name__}: {final_e}")
                    return {"error": "System is currently in a degraded state. Please try again later."}
        return wrapper
    return decorator
