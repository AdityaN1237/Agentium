from datetime import datetime
from pathlib import Path
from app.models.config import AgentConfig
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class ConfigService:
    """
    Service to manage dynamic configurations for AI agents.
    It provides a caching layer on top of the database to reduce lookups.
    """
    _configs: Dict[str, AgentConfig] = {}
    _defaults: Dict[str, Dict[str, Any]] = {
        "rag_qa": {
            "chunk_size": 512,
            "overlap": 64,
            "top_k": 3,
            "retrieval_strategy": "hybrid",
            "similarity_threshold": 0.3
        },
        "resume_screening": {
            "top_k": 10,
            "skill_match_weight": 0.5,
            "semantic_score_weight": 0.5,
            "ner_model": "spacy/en_core_web_sm" # Placeholder
        }
    }

    CONFIG_FILE = Path(__file__).resolve().parent.parent / "data" / "agent_configs.json"

    @classmethod
    async def load_all_configs(cls):
        """
        Load all agent configurations from local JSON file.
        Seeds default configurations if they don't exist.
        """
        import json
        logger.info("🔄 Loading all agent configurations from disk...")
        
        # Ensure file exists
        if not cls.CONFIG_FILE.exists():
            cls.CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(cls.CONFIG_FILE, 'w') as f:
                json.dump({}, f)
        
        try:
            with open(cls.CONFIG_FILE, 'r') as f:
                 stored_configs = json.load(f)
        except Exception as e:
             logger.error(f"Failed to read config file: {e}")
             stored_configs = {}

        # Merge with defaults
        for agent_id, default_params in cls._defaults.items():
            if agent_id not in stored_configs:
                logger.info(f"🌱 No config found for '{agent_id}'. Seeding with defaults.")
                new_config = AgentConfig(agent_id=agent_id, parameters=default_params)
                stored_configs[agent_id] = new_config.model_dump(by_alias=True)
                cls._configs[agent_id] = new_config
            else:
                # Load existing
                cls._configs[agent_id] = AgentConfig(**stored_configs[agent_id])
        
        # Save back to ensure defaults are persisted
        cls._save_configs_to_disk(stored_configs)
        logger.info(f"✅ Loaded {len(cls._configs)} configurations.")

    @classmethod
    def _save_configs_to_disk(cls, data: Dict):
        import json
        try:
            with open(cls.CONFIG_FILE, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save configs to disk: {e}")

    @classmethod
    def get_config(cls, agent_id: str) -> Dict[str, Any]:
        """
        Get the configuration for a specific agent from the cache.
        Falls back to defaults if not in cache.
        """
        config = cls._configs.get(agent_id)
        if not config:
            # Check defaults directly if not in cache (e.g. new agent)
            return cls._defaults.get(agent_id, {})
        return config.parameters

    @classmethod
    async def update_config(cls, agent_id: str, new_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update the configuration for an agent and persist to disk.
        """
        # Get current config and merge with new params
        current_config = cls.get_config(agent_id)
        updated_params = {**current_config, **new_params}
        
        # Update Cache
        if agent_id in cls._configs:
            cls._configs[agent_id].parameters = updated_params
            cls._configs[agent_id].updated_at = datetime.utcnow()
            cls._configs[agent_id].version += 1
        else:
            cls._configs[agent_id] = AgentConfig(
                agent_id=agent_id, 
                parameters=updated_params,
                version=1
            )
            
        # Serialize for disk
        all_configs_dict = {
            k: v.model_dump(by_alias=True) 
            for k, v in cls._configs.items()
        }
        
        cls._save_configs_to_disk(all_configs_dict)
        logger.info(f"✅ Updated and refreshed config for '{agent_id}'.")
        return cls._configs[agent_id].parameters

# Instantiate the service to be used across the application
config_service = ConfigService()
