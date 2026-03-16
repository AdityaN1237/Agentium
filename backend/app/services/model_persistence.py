"""
Model Persistence Service.
Handles saving and loading trained model data, embeddings, and training artifacts.
"""
import json
import pickle
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
import numpy as np

logger = logging.getLogger(__name__)

# Base directory for model storage
MODELS_DATA_DIR = Path(__file__).parent.parent / "models_data"


class ModelPersistenceService:
    """
    Service for persisting and loading trained model data.
    Supports version management and metadata tracking.
    """
    
    _instance: Optional['ModelPersistenceService'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Create necessary directories for model storage."""
        MODELS_DATA_DIR.mkdir(parents=True, exist_ok=True)
        (MODELS_DATA_DIR / "embeddings").mkdir(exist_ok=True)
        (MODELS_DATA_DIR / "checkpoints").mkdir(exist_ok=True)
        (MODELS_DATA_DIR / "metadata").mkdir(exist_ok=True)
        logger.info(f"📁 Model storage initialized at: {MODELS_DATA_DIR}")
    
    def get_agent_dir(self, agent_id: str) -> Path:
        """Get the storage directory for a specific agent."""
        agent_dir = MODELS_DATA_DIR / agent_id
        agent_dir.mkdir(parents=True, exist_ok=True)
        return agent_dir
    
    def save_embeddings(
        self, 
        agent_id: str, 
        embeddings: np.ndarray, 
        ids: List[str],
        version: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Save embeddings array with associated IDs.
        
        Args:
            agent_id: Agent identifier
            embeddings: NumPy array of embeddings
            ids: List of document/item IDs corresponding to embeddings
            version: Optional version string (defaults to timestamp)
        
        Returns:
            Dict with save metadata
        """
        agent_dir = self.get_agent_dir(agent_id)
        version = version or datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        embeddings_path = agent_dir / f"embeddings_{version}.npy"
        ids_path = agent_dir / f"ids_{version}.json"
        
        np.save(embeddings_path, embeddings)
        with open(ids_path, 'w') as f:
            json.dump(ids, f)
        
        # Update latest pointer
        latest_path = agent_dir / "latest.json"
        with open(latest_path, 'w') as f:
            json.dump({
                "version": version,
                "embeddings_file": f"embeddings_{version}.npy",
                "ids_file": f"ids_{version}.json",
                "saved_at": datetime.utcnow().isoformat(),
                "count": len(ids),
                "embedding_dim": embeddings.shape[1] if len(embeddings.shape) > 1 else 0
            }, f, indent=2)
        
        logger.info(f"💾 Saved {len(ids)} embeddings for agent '{agent_id}' (v{version})")
        
        return {
            "version": version,
            "count": len(ids),
            "path": str(embeddings_path)
        }
    
    def load_embeddings(
        self, 
        agent_id: str, 
        version: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Load embeddings for an agent.
        
        Args:
            agent_id: Agent identifier
            version: Specific version to load (defaults to latest)
        
        Returns:
            Dict with 'embeddings' (np.ndarray) and 'ids' (list), or None
        """
        agent_dir = self.get_agent_dir(agent_id)
        
        if version is None:
            # Load latest
            latest_path = agent_dir / "latest.json"
            if not latest_path.exists():
                return None
            with open(latest_path, 'r') as f:
                latest = json.load(f)
            version = latest["version"]
        
        embeddings_path = agent_dir / f"embeddings_{version}.npy"
        ids_path = agent_dir / f"ids_{version}.json"
        
        if not embeddings_path.exists() or not ids_path.exists():
            return None
        
        embeddings = np.load(embeddings_path)
        with open(ids_path, 'r') as f:
            ids = json.load(f)
        
        logger.info(f"📂 Loaded {len(ids)} embeddings for agent '{agent_id}' (v{version})")
        
        return {
            "embeddings": embeddings,
            "ids": ids,
            "version": version
        }
    
    def save_checkpoint(
        self, 
        agent_id: str, 
        checkpoint_data: Dict[str, Any],
        checkpoint_name: Optional[str] = None
    ) -> str:
        """
        Save a training checkpoint.
        
        Args:
            agent_id: Agent identifier
            checkpoint_data: Dictionary with training state
            checkpoint_name: Optional name (defaults to timestamp)
        
        Returns:
            Checkpoint filename
        """
        agent_dir = self.get_agent_dir(agent_id)
        checkpoints_dir = agent_dir / "checkpoints"
        checkpoints_dir.mkdir(exist_ok=True)
        
        checkpoint_name = checkpoint_name or datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        checkpoint_path = checkpoints_dir / f"{checkpoint_name}.pkl"
        
        with open(checkpoint_path, 'wb') as f:
            pickle.dump(checkpoint_data, f)
        
        logger.info(f"💾 Saved checkpoint '{checkpoint_name}' for agent '{agent_id}'")
        return checkpoint_name
    
    def load_checkpoint(
        self, 
        agent_id: str, 
        checkpoint_name: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Load a training checkpoint.
        
        Args:
            agent_id: Agent identifier
            checkpoint_name: Specific checkpoint to load (defaults to latest)
        
        Returns:
            Checkpoint data dict or None
        """
        agent_dir = self.get_agent_dir(agent_id)
        checkpoints_dir = agent_dir / "checkpoints"
        
        if not checkpoints_dir.exists():
            return None
        
        if checkpoint_name is None:
            # Find latest checkpoint
            checkpoints = list(checkpoints_dir.glob("*.pkl"))
            if not checkpoints:
                return None
            checkpoint_path = max(checkpoints, key=lambda p: p.stat().st_mtime)
        else:
            checkpoint_path = checkpoints_dir / f"{checkpoint_name}.pkl"
        
        if not checkpoint_path.exists():
            return None
        
        with open(checkpoint_path, 'rb') as f:
            data = pickle.load(f)
        
        logger.info(f"📂 Loaded checkpoint from '{checkpoint_path.name}' for agent '{agent_id}'")
        return data
    
    def save_metadata(
        self, 
        agent_id: str, 
        metadata: Dict[str, Any]
    ):
        """Save agent training metadata."""
        agent_dir = self.get_agent_dir(agent_id)
        metadata_path = agent_dir / "metadata.json"
        
        # Merge with existing if present
        existing = {}
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                existing = json.load(f)
        
        existing.update(metadata)
        existing["updated_at"] = datetime.utcnow().isoformat()
        
        with open(metadata_path, 'w') as f:
            json.dump(existing, f, indent=2)
    
    def get_metadata(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent training metadata."""
        agent_dir = self.get_agent_dir(agent_id)
        metadata_path = agent_dir / "metadata.json"
        
        if not metadata_path.exists():
            return None
        
        with open(metadata_path, 'r') as f:
            return json.load(f)
    
    def get_model_status(self, agent_id: str) -> Dict[str, Any]:
        """Get comprehensive model status for an agent."""
        agent_dir = self.get_agent_dir(agent_id)
        
        status = {
            "agent_id": agent_id,
            "has_embeddings": False,
            "has_checkpoints": False,
            "versions": [],
            "latest_version": None,
            "metadata": None
        }
        
        # Check for embeddings
        latest_path = agent_dir / "latest.json"
        if latest_path.exists():
            with open(latest_path, 'r') as f:
                latest = json.load(f)
            status["has_embeddings"] = True
            status["latest_version"] = latest.get("version")
            status["embedding_count"] = latest.get("count", 0)
            status["last_saved"] = latest.get("saved_at")
        
        # List versions
        for f in agent_dir.glob("embeddings_*.npy"):
            version = f.stem.replace("embeddings_", "")
            status["versions"].append(version)
        
        # Check checkpoints
        checkpoints_dir = agent_dir / "checkpoints"
        if checkpoints_dir.exists():
            checkpoints = list(checkpoints_dir.glob("*.pkl"))
            status["has_checkpoints"] = len(checkpoints) > 0
            status["checkpoint_count"] = len(checkpoints)
        
        # Get metadata
        status["metadata"] = self.get_metadata(agent_id)
        
        return status
    
    def list_all_models(self) -> List[Dict[str, Any]]:
        """List all agents with saved model data."""
        models = []
        
        if not MODELS_DATA_DIR.exists():
            return models
        
        for agent_dir in MODELS_DATA_DIR.iterdir():
            if agent_dir.is_dir() and agent_dir.name not in ["embeddings", "checkpoints", "metadata"]:
                status = self.get_model_status(agent_dir.name)
                if status["has_embeddings"] or status["has_checkpoints"]:
                    models.append(status)
        
        return models
    
    def delete_version(self, agent_id: str, version: str) -> bool:
        """Delete a specific version of embeddings."""
        agent_dir = self.get_agent_dir(agent_id)
        embeddings_path = agent_dir / f"embeddings_{version}.npy"
        ids_path = agent_dir / f"ids_{version}.json"
        
        deleted = False
        if embeddings_path.exists():
            embeddings_path.unlink()
            deleted = True
        if ids_path.exists():
            ids_path.unlink()
            deleted = True
        
        if deleted:
            logger.info(f"🗑️ Deleted version '{version}' for agent '{agent_id}'")
        
        return deleted


# Singleton instance
def get_model_persistence() -> ModelPersistenceService:
    """Get the singleton model persistence service instance."""
    return ModelPersistenceService()
