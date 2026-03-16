from typing import Dict, List, Type, Any
from app.agents.base import BaseAgent, AgentMetadata
import json
import logging
import os
import importlib
import inspect

logger = logging.getLogger(__name__)

class AgentRegistry:
    """
    Central registry to manage and access active agents.
    Supports dynamic auto-discovery of agent types from the agents directory.
    """
    _agents: Dict[str, BaseAgent] = {}
    _types: Dict[str, Type[BaseAgent]] = {}

    @classmethod
    async def initialize(cls, db):
        """
        Auto-discover agent types and instantiate existing agents from the database.
        """
        logger.info("🔍 Auto-discovering agent types...")
        cls._discover_types()
        logger.info(f"📁 Discovered {len(cls._types)} agent types: {list(cls._types.keys())}")
        
        # Check if we need to seed the database
        count = await db.agents.count_documents({})
        if count == 0:
            logger.info("🌱 Seeding database with default neural nodes...")
            try:
                # Find path to json
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                json_path = os.path.join(base_dir, "data", "default_agents.json")
                
                if os.path.exists(json_path):
                    with open(json_path, 'r') as f:
                        default_agents = json.load(f)
                    await db.agents.insert_many(default_agents)
                    logger.info(f"✅ Seeded {len(default_agents)} nodes")
                else:
                    logger.warning(f"⚠️ Seed file not found at {json_path}")
            except Exception as e:
                logger.error(f"❌ Failed to seed database: {e}")

        logger.info("🔌 Loading active agents from database...")
        agent_records = await db.agents.find({}).to_list(length=100)
        logger.info(f"📑 Found {len(agent_records)} records in DB")
        
        for record in agent_records:
            agent_id = record.get('id')
            try:
                logger.debug(f"⚙️ Instantiating '{agent_id}' of type '{record.get('type')}'...")
                cls.instantiate_from_db(record)
                logger.info(f"✅ Activated agent: {agent_id}")
            except Exception as e:
                logger.error(f"❌ Failed to instantiate agent {agent_id}: {str(e)}")
        
        logger.info(f"💡 {len(cls._agents)} neural nodes active")

    @classmethod
    def _discover_types(cls):
        """
        Scans the app.agents directory for subpackages containing agent classes.
        """
        # Get the directory of this file
        agents_dir = os.path.dirname(os.path.abspath(__file__))
        
        for item in os.listdir(agents_dir):
            item_path = os.path.join(agents_dir, item)
            
            # Check if it's a directory and has an agent.py
            if os.path.isdir(item_path) and os.path.exists(os.path.join(item_path, "agent.py")):
                try:
                    # Construct module path
                    module_name = f"app.agents.{item}.agent"
                    module = importlib.import_module(module_name)
                    
                    # Find classes that inherit from BaseAgent and are not BaseAgent itself
                    for name, obj in inspect.getmembers(module):
                        if (inspect.isclass(obj) and 
                            issubclass(obj, BaseAgent) and 
                            obj is not BaseAgent):
                            
                            # Use folder name as the unique type name
                            type_name = item
                            cls.register_type(type_name, obj)
                except Exception as e:
                    logger.error(f"⚠️ Failed to import agent from {item}: {e}")

    @classmethod
    def register_type(cls, type_name: str, agent_class: Type[BaseAgent]):
        """Register an agent class by its type name."""
        cls._types[type_name] = agent_class
        logger.info(f"🧬 Agent Type Registered: {type_name} -> {agent_class.__name__}")

    @classmethod
    def get_types(cls) -> List[str]:
        """Return list of available agent types."""
        return list(cls._types.keys())

    @classmethod
    def register(cls, agent_instance: BaseAgent):
        """Register a specific agent instance."""
        cls._agents[agent_instance.metadata.id] = agent_instance
        logger.info(f"✅ Agent instance active: {agent_instance.metadata.name} ({agent_instance.metadata.id})")

    @classmethod
    def get_agent(cls, agent_id: str) -> BaseAgent:
        """Get agent instance by ID."""
        agent = cls._agents.get(agent_id)
        if not agent:
            raise ValueError(f"Agent '{agent_id}' not found in registry.")
        return agent

    @classmethod
    def list_agents(cls) -> List[Dict[str, Any]]:
        """List all registered agent instances with enterprise metadata."""
        return [
            {
                "id": agent.metadata.id,
                "name": agent.metadata.name,
                "description": agent.metadata.description,
                "state": agent.metadata.state,
                "status": agent.metadata.status, # Legacy support
                "type": getattr(agent.metadata, "type", "generic"),
                "version": agent.metadata.version,
                "accuracy": agent.metadata.accuracy,
                "metrics": agent.metadata.metrics,
                "last_trained": agent.metadata.last_trained,
                "trained_at": agent.metadata.trained_at
            }
            for agent in cls._agents.values()
        ]

    @classmethod
    def instantiate_from_db(cls, agent_data: Dict[str, Any]) -> BaseAgent:
        """Create an agent instance based on DB metadata."""
        agent_type = agent_data.get("type", "generic")
        agent_id = agent_data.get("id")
        
        if agent_type not in cls._types:
            # Fallback to generic if type not found
            if "generic" in cls._types: agent_type = "generic"

        agent_class = cls._types[agent_type]
        
        # Convert DB dict to AgentMetadata
        metadata = AgentMetadata(
            id=agent_data["id"],
            name=agent_data["name"],
            description=agent_data["description"],
            version=agent_data.get("version", "1.0.0"),
            type=agent_type,
            state=agent_data.get("state", "IDLE"),
            status=agent_data.get("status", "inactive"),
            last_trained=agent_data.get("last_trained"),
            accuracy=agent_data.get("accuracy"),
            metrics=agent_data.get("metrics", {}),
            trained_at=agent_data.get("trained_at")
        )
        
        instance = agent_class(metadata=metadata)
        cls.register(instance)
        return instance

    @classmethod
    def remove_agent(cls, agent_id: str):
        """Remove an agent instance from the registry."""
        if agent_id in cls._agents:
            del cls._agents[agent_id]
            logger.info(f"🗑️ Agent instance removed: {agent_id}")

    @classmethod
    def clear(cls):
        """Clear all active instances."""
        cls._agents = {}

# Global registry instance
registry = AgentRegistry()
