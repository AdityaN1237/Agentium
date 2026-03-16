"""
Two-Tower Model Training Service.
Provides API for training and inference with the Two-Tower recommendation model.
All training artifacts are persisted to the backend directory.
"""

import os
import json
import pickle
from pathlib import Path
from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)

# Base paths for training artifacts
BASE_DIR = Path(__file__).parent.parent.parent.parent  # backend/
MODELS_DIR = BASE_DIR / "models"
TRAINING_DATA_DIR = BASE_DIR / "training_data"
EMBEDDINGS_DIR = BASE_DIR / "embeddings"


class TwoTowerService:
    """
    Service for Two-Tower model training and inference.
    Persists all training artifacts to backend directories.
    """
    
    _instance: Optional['TwoTowerService'] = None
    _model = None
    _encoders = None
    _config = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the Two-Tower service."""
        # Ensure directories exist
        MODELS_DIR.mkdir(exist_ok=True)
        TRAINING_DATA_DIR.mkdir(exist_ok=True)
        EMBEDDINGS_DIR.mkdir(exist_ok=True)
        
        self._load_if_exists()
    
    def _load_if_exists(self):
        """Load existing model and encoders if available."""
        model_path = MODELS_DIR / "two_tower" / "best_model.pth"
        encoders_path = MODELS_DIR / "two_tower" / "encoders.pkl"
        config_path = MODELS_DIR / "two_tower" / "model_config.json"
        
        if model_path.exists() and encoders_path.exists():
            try:
                import torch
                from app.ml.two_tower import TwoTowerModel, load_model_config
                
                # Load config
                if config_path.exists():
                    self._config = load_model_config(str(config_path))
                
                # Load encoders
                with open(encoders_path, 'rb') as f:
                    self._encoders = pickle.load(f)
                
                # Load model
                self._model = TwoTowerModel(**self._config)
                checkpoint = torch.load(model_path, map_location='cpu')
                self._model.load_state_dict(checkpoint['model_state_dict'])
                self._model.eval()
                
                logger.info("✅ Loaded Two-Tower model from persisted artifacts")
            except Exception as e:
                logger.warning(f"Could not load Two-Tower model: {e}")
    
    @property
    def is_trained(self) -> bool:
        """Check if model is trained and loaded."""
        return self._model is not None
    
    def get_model_info(self) -> Dict:
        """Get information about the current model state."""
        return {
            "is_trained": self.is_trained,
            "model_dir": str(MODELS_DIR / "two_tower"),
            "training_data_dir": str(TRAINING_DATA_DIR),
            "has_encoders": self._encoders is not None,
            "config": self._config
        }
    
    async def train(
        self,
        data_path: Optional[str] = None,
        num_epochs: int = 100,
        batch_size: int = 512
    ) -> Dict:
        """
        Train the Two-Tower model.
        
        Args:
            data_path: Path to training data (CSV with user_id, job_id, domain, label)
            num_epochs: Number of training epochs
            batch_size: Batch size for training
            
        Returns:
            Training metrics and model info
        """
        import torch
        from app.ml.two_tower.train_two_tower_model import (
            prepare_data, TwoTowerTrainer
        )
        from app.ml.two_tower import TwoTowerModel, create_model_config
        
        # Use default training data if not specified
        if data_path is None:
            data_path = TRAINING_DATA_DIR / "data"
        else:
            data_path = Path(data_path)
        
        # Prepare output directory
        output_dir = MODELS_DIR / "two_tower"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Set device
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        logger.info(f"Training on device: {device}")
        
        # Prepare data
        train_loader, val_loader, encoders = prepare_data(data_path)
        
        # Create model config
        config = create_model_config(
            user_vocab_size=len(encoders['user_encoder'].classes_),
            job_vocab_size=len(encoders['job_encoder'].classes_),
            domain_vocab_size=len(encoders['domain_encoder'].classes_)
        )
        
        # Create model
        model = TwoTowerModel(**config)
        
        # Save config and encoders
        with open(output_dir / 'model_config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        with open(output_dir / 'encoders.pkl', 'wb') as f:
            pickle.dump(encoders, f)
        
        # Train
        trainer = TwoTowerTrainer(model, train_loader, val_loader, device, output_dir)
        metrics = trainer.train(num_epochs=num_epochs)
        
        # Update instance state
        self._model = model
        self._encoders = encoders
        self._config = config
        
        logger.info("✅ Two-Tower model training completed")
        
        return {
            "status": "success",
            "model_path": str(output_dir / "best_model.pth"),
            "final_train_auc": metrics['train_auc'][-1] if metrics['train_auc'] else None,
            "final_val_auc": metrics['val_auc'][-1] if metrics['val_auc'] else None,
            "epochs_trained": len(metrics['train_loss'])
        }
    
    def predict(
        self,
        user_id: str,
        job_ids: List[str],
        user_domain: str = "Technology"
    ) -> List[Dict]:
        """
        Get job recommendations for a user.
        
        Args:
            user_id: User identifier
            job_ids: List of job identifiers to score
            user_domain: User's primary domain
            
        Returns:
            List of jobs with scores
        """
        if not self.is_trained:
            raise ValueError("Model not trained. Call train() first.")
        
        import torch
        
        self._model.eval()
        
        # Encode inputs
        user_encoded = self._encoders['user_encoder'].transform([user_id])[0]
        jobs_encoded = self._encoders['job_encoder'].transform(job_ids)
        domain_encoded = self._encoders['domain_encoder'].transform([user_domain])[0]
        
        # Create tensors
        user_tensor = torch.tensor([user_encoded] * len(job_ids), dtype=torch.long)
        user_domain_tensor = torch.tensor([domain_encoded] * len(job_ids), dtype=torch.long)
        job_tensor = torch.tensor(jobs_encoded, dtype=torch.long)
        job_domain_tensor = torch.tensor([domain_encoded] * len(job_ids), dtype=torch.long)
        
        # Get predictions
        with torch.no_grad():
            outputs = self._model(
                user_ids=user_tensor,
                user_domains=user_domain_tensor,
                job_ids=job_tensor,
                job_domains=job_domain_tensor
            )
        
        predictions = outputs['predictions'].numpy()
        similarities = outputs['cosine_similarity'].numpy()
        
        results = []
        for i, job_id in enumerate(job_ids):
            results.append({
                "job_id": job_id,
                "match_score": float(predictions[i]),
                "similarity": float(similarities[i])
            })
        
        return sorted(results, key=lambda x: x['match_score'], reverse=True)


# Singleton instance
def get_two_tower_service() -> TwoTowerService:
    """Get the Two-Tower service singleton."""
    return TwoTowerService()
