from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from app.services.config_service import config_service
from app.models.config import AgentConfigUpdate

router = APIRouter(prefix="/configs", tags=["Configurations"])

@router.get("/", response_model=Dict[str, Dict[str, Any]])
async def get_all_configurations():
    """
    Retrieve the configurations for all agents.
    """
    all_configs = {}
    for agent_id in config_service._defaults.keys():
        all_configs[agent_id] = config_service.get_config(agent_id)
    return all_configs

@router.get("/{agent_id}", response_model=Dict[str, Any])
async def get_agent_configuration(agent_id: str):
    """
    Retrieve the configuration for a specific agent.
    """
    config = config_service.get_config(agent_id)
    if not config:
        raise HTTPException(status_code=404, detail=f"Configuration for agent '{agent_id}' not found.")
    return config

@router.put("/{agent_id}", response_model=Dict[str, Any])
async def update_agent_configuration(agent_id: str, update: AgentConfigUpdate):
    """
    Update the configuration for a specific agent.
    This allows for real-time changes to agent parameters.
    """
    if agent_id not in config_service._defaults:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' is not a valid agent.")

    try:
        updated_config = await config_service.update_config(agent_id, update.parameters)
        return updated_config
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update configuration: {str(e)}")
