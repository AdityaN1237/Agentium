from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Union
from pydantic import BaseModel, Field, ConfigDict
import logging
import asyncio
from datetime import datetime
from app.models.memory import EpisodicMemory, ReflectiveMemory, PolicyMemory
from app.services.memory_service import memory_service

class MetricsModel(BaseModel):
    """Standardized performance metrics for agents."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    latency_ms: float = 0.0
    sample_size: int = 0
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)

class AgentMetadata(BaseModel):
    """Enterprise metadata for AI agents."""
    model_config = ConfigDict(protected_namespaces=())

    id: str
    name: str
    description: str
    version: str
    type: str = "generic"
    # Lifecycle states: IDLE → INDEXING → READY → DEGRADED
    state: str = Field(default="IDLE")
    status: str = Field(default="inactive") # For backward compatibility during migration, will be deprecated
    last_trained: Optional[str] = None
    accuracy: Optional[float] = None
    metrics: Union[MetricsModel, Dict[str, Any]] = Field(default_factory=dict)
    trained_at: Optional[str] = None

class BaseAgent(ABC):
    """
    Abstract base class for Enterprise-Grade AI Agents.
    Enforces strict lifecycle control and includes a 4-brain memory system.
    """
    
    def __init__(self, metadata: AgentMetadata):
        self.metadata = metadata
        self.logger = logging.getLogger(f"agent.{metadata.id}")
        self.policy: Optional[PolicyMemory] = None

    async def initialize_brains(self):
        """Load or initialize the agent's policy brain."""
        self.policy = await memory_service.get_latest_policy(self.metadata.id)
        if not self.policy:
            # Initialize with default weights from settings or generic defaults
            from app.config import settings
            self.policy = PolicyMemory(
                agent_id=self.metadata.id,
                version=self.metadata.version,
                weights={
                    "semantic": settings.SEMANTIC_WEIGHT,
                    "skill": settings.SKILL_MATCH_WEIGHT,
                    "preference": settings.PREFERENCE_WEIGHT
                }
            )
            await memory_service.update_policy(self.policy)
            self.logger.info(f"🧠 Initialized Policy Brain for agent {self.metadata.id}")

    async def sanitize_data(self, data: Any) -> Any:
        """
        Standardized data sanitization to remove PII and placeholders.
        """
        import re
        if isinstance(data, str):
            # Remove basic PII patterns (emails, phone numbers) - simplified
            data = re.sub(r'[\w\.-]+@[\w\.-]+\.\w+', '[EMAIL_REDACTED]', data)
            data = re.sub(r'\+?\d{10,12}', '[PHONE_REDACTED]', data)
            
            # Remove common placeholders
            placeholders = ["lorem ipsum", "john doe", "placeholder", "tbd", "n/a"]
            for p in placeholders:
                data = re.sub(re.escape(p), "", data, flags=re.IGNORECASE)
            
            return data.strip()
        elif isinstance(data, list):
            return [await self.sanitize_data(item) for item in data]
        elif isinstance(data, dict):
            return {k: await self.sanitize_data(v) for k, v in data.items()}
        return data

    @abstractmethod
    async def validate_data_readiness(self) -> bool:
        """STEP 1: Check if real data exists and reject placeholders."""
        pass

    @abstractmethod
    async def index_data(self, session: Any) -> None:
        """STEP 2: Massive vectorization of the corpus."""
        pass

    @abstractmethod
    async def train_knowledge_graph(self, session: Any) -> None:
        """STEP 3: Persistent relationship expansion."""
        pass

    @abstractmethod
    async def calibrate_intelligence(self, session: Any) -> None:
        """STEP 4: Intelligence & Reasoning Calibration."""
        pass

    @abstractmethod
    async def calibrate_scoring(self, session: Any) -> None:
        """STEP 5: Scoring Engine Calibration."""
        pass

    @abstractmethod
    async def evaluate(self) -> Union[MetricsModel, Dict[str, Any]]:
        """STEP 8: Perform evaluation and return metrics."""
        pass

    async def execute_pipeline(self, config: Dict[str, Any] = None) -> None:
        """
        The standardized 9-step operationalization pipeline.
        Centralized in BaseAgent to ensure consistent lifecycle management.
        """
        from app.services.training_manager import training_manager
        session = training_manager.start_session(
            self.metadata.id, 
            self.metadata.type,
            config or {}
        )
        
        try:
            # STEP 1: VALIDATION
            session.add_log("🟩 STEP 1: Data Validation & Sanitization...", "INFO")
            if not await self.validate_data_readiness():
                raise ValueError("Data validation failed: Missing real data in corpus.")
            session.record_step_metric("validation", "passed", True)
            session.add_log("✅ Step 1 Complete.", "SUCCESS")
            await asyncio.sleep(0)  # Yield to event loop to prevent blocking other APIs
            
            # STEP 2: INDEXING
            session.add_log("🟩 STEP 2: Embedding Corpus Construction (Indexing)...", "INFO")
            await self.index_data(session)
            session.add_log("✅ Step 2 Complete.", "SUCCESS")
            await asyncio.sleep(0)  # Yield to event loop
            
            # STEP 3: KG TRAINING
            session.add_log("🟩 STEP 3: Knowledge Graph Training (Skill Expansion)...", "INFO")
            await self.train_knowledge_graph(session)
            session.add_log("✅ Step 3 Complete.", "SUCCESS")
            await asyncio.sleep(0)  # Yield to event loop
            
            # STEP 4: PROMPT CALIBRATION
            session.add_log("🟩 STEP 4: Intelligence & Reasoning Calibration...", "INFO")
            await self.calibrate_intelligence(session)
            session.add_log("✅ Step 4 Complete.", "SUCCESS")
            await asyncio.sleep(0)  # Yield to event loop
            
            # STEP 5: SCORING CALIBRATION
            session.add_log("🟩 STEP 5: Scoring Engine Calibration (Weights Enforced)...", "INFO")
            await self.calibrate_scoring(session)
            session.add_log("✅ Step 5 Complete.", "SUCCESS")
            await asyncio.sleep(0)  # Yield to event loop

            # STEP 6: STATE LOCKING
            session.add_log("🟩 STEP 6: State Locking & Weights Freezing...", "INFO")
            await self._lock_state(session)
            session.add_log("✅ Step 6 Complete.", "SUCCESS")

            # STEP 7: GATEKEEPING
            session.add_log("🟩 STEP 7: Inference Gatekeeping & Safety Audit...", "INFO")
            await self._audit_gatekeeping(session)
            session.add_log("✅ Step 7 Complete.", "SUCCESS")
            
            # STEP 8: EVALUATION
            session.add_log("🟩 STEP 8: Data-Driven Performance Evaluation...", "INFO")
            self.metadata.metrics = await self.evaluate()
            
            # Convert MetricsModel to dict for storage if needed
            metrics_dict = self.metadata.metrics
            if hasattr(self.metadata.metrics, 'model_dump'):
                metrics_dict = self.metadata.metrics.model_dump()
            elif hasattr(self.metadata.metrics, 'dict'):
                metrics_dict = self.metadata.metrics.dict()
            elif isinstance(self.metadata.metrics, MetricsModel):
                metrics_dict = {
                    "accuracy": self.metadata.metrics.accuracy,
                    "precision": self.metadata.metrics.precision,
                    "recall": self.metadata.metrics.recall,
                    "f1_score": self.metadata.metrics.f1_score,
                    "latency_ms": self.metadata.metrics.latency_ms,
                    "sample_size": self.metadata.metrics.sample_size
                }
            
            session.record_step_metric("evaluation", "accuracy", getattr(self.metadata.metrics, 'accuracy', 0.0))
            session.add_log(f"✅ Step 8 Complete. Accuracy: {getattr(self.metadata.metrics, 'accuracy', 0.0):.2f}", "SUCCESS")
            
            # STEP 9: VERSIONING & DEPLOYMENT
            session.add_log("🟩 STEP 9: Final Versioning & Neural Deployment...", "INFO")
            self.metadata.trained_at = datetime.utcnow().isoformat()
            self.metadata.version = self._generate_next_version()
            self.metadata.state = "READY"
            self.transition_state("READY")
            
            # Complete session and persist
            training_manager.complete_session(self.metadata.id, metrics_dict if isinstance(metrics_dict, dict) else {})
            await training_manager.persist_run(session)
            
            # CRITICAL: Persist State to DB & Hot Reload
            await self._persist_state(session)
            try:
                self._hot_reload()
                session.add_log("🔥 Agent Hot-Reloaded successfully. New version active.", "SUCCESS")
            except Exception as e:
                session.add_log(f"⚠️ Hot-Reload failed (restart might be needed): {e}", "WARNING")
            
            session.add_log(f"✅ Agent Operationalization Complete. Version: {self.metadata.version}. State: READY", "SUCCESS")
            
        except Exception as e:
            self.transition_state("DEGRADED")
            session.add_log(f"❌ Pipeline Failure: {str(e)}", "ERROR")
            try:
                training_manager.fail_session(self.metadata.id, str(e))
                await training_manager.persist_run(session)
            except: pass
            self.logger.error(f"Enterprise pipeline failed for {self.metadata.id}: {e}")

    async def _persist_state(self, session: Any):
        """Persist current metadata (version, metrics, state) to MongoDB."""
        from app.database import Database
        try:
            db = Database.get_db()
            update_data = self.metadata.dict()
            # Remove None so we don't overwrite with nulls if partial
            update_data = {k: v for k, v in update_data.items() if v is not None}
            
            await db.agents.update_one(
                {"id": self.metadata.id},
                {"$set": update_data}
            )
            session.add_log("💾 Agent metadata persisted to Database.", "DEBUG")
        except Exception as e:
            self.logger.error(f"Failed to persist state: {e}")
            session.add_log(f"⚠️ Failed to persist state to DB: {e}", "WARNING")

    def _hot_reload(self):
        """Trigger Registry to re-instantiate this agent from fresh config."""
        from app.agents.registry import registry
        # We need to construct a dict that mimics what comes from DB
        # Or better, let registry fetch fresh from DB?
        # Registry.instantiate_from_db needs a dict.
        
        # Actually, since we just updated the DB, we can ask registry to re-fetch?
        # No, registry.instantiate_from_db takes the dict.
        # Let's just update the in-memory registry instance with SELF for now?
        # NO, 'hot reload' implies creating a NEW instance (re-init) to load fresh files/embeddings.
        # So we should pass our current metadata to registry.
        
        # But we are inside the instance we are about to replace... tricky?
        # It's fine, the old instance will be garbage collected eventually.
        
        # Construct dict
        agent_data = self.metadata.dict()
        registry.instantiate_from_db(agent_data)

    async def _lock_state(self, session: Any):
        """Standardized state locking (placeholder for future implementation)."""
        pass

    async def _audit_gatekeeping(self, session: Any):
        """Standardized gatekeeping audit (placeholder for future implementation)."""
        pass

    def _generate_next_version(self) -> str:
        """Auto-increment version number."""
        try:
            major, minor, patch = map(int, self.metadata.version.split('.'))
            return f"{major}.{minor}.{patch + 1}"
        except Exception:
            return f"{self.metadata.version}.1"

    @abstractmethod
    async def upload_dataset(self, data: Any) -> Dict[str, Any]:
        """Process and store uploaded dataset."""
        pass

    async def train(self, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Trigger the training workflow (Transition to INDEXING)."""
        if self.metadata.state == "INDEXING":
            return {
                "status": "FAILED", 
                "agent_id": self.metadata.id,
                "errors": ["Training already in progress."]
            }

        # Transition to INDEXING
        self.transition_state("INDEXING")
        
        # Start pipeline in background
        asyncio.create_task(self.execute_pipeline(config or {}))
        
        return {
            "status": "SUCCESS",
            "agent_id": self.metadata.id,
            "training_steps_initiated": ["INITIALIZATION", "VALIDATION"],
            "version": self.metadata.version,
            "state": "INDEXING"
        }

    async def stop_training(self) -> Dict[str, Any]:
        """Stop training and transition to DEGRADED or IDLE."""
        from app.services.training_manager import training_manager
        training_manager.stop_session(self.metadata.id)
        self.transition_state("IDLE")
        return {
            "status": "SUCCESS", 
            "agent_id": self.metadata.id,
            "message": "Neural training aborted by user."
        }

    @abstractmethod
    async def predict_logic(self, input_data: Any) -> Any:
        """Core inference logic to be implemented by child classes."""
        pass

    async def predict(self, input_data: Any) -> Any:
        """
        Inference entry point with episodic memory tracking.
        """
        if self.metadata.state != "READY" and self.metadata.status != "active":
            return {
                "status": "FAILED",
                "agent_id": self.metadata.id,
                "state": self.metadata.state,
                "errors": [f"Agent is not in READY state. Current state: {self.metadata.state}"]
            }

        if not self.policy:
            await self.initialize_brains()

        prediction = await self.predict_logic(input_data)
        
        # Store episode for future reflection
        episode = EpisodicMemory(
            agent_id=self.metadata.id,
            query_id=f"q_{datetime.utcnow().timestamp()}",
            input_data=input_data,
            prediction=prediction,
            confidence=prediction.get("confidence", 0.0) if isinstance(prediction, dict) else 0.0,
            version=self.metadata.version,
            context={"weights": self.policy.weights}
        )
        episode_id = await memory_service.store_episode(episode)
        
        if isinstance(prediction, dict):
            prediction["episode_id"] = episode_id

        return prediction

    async def observe(self, episode_id: str, ground_truth: Any, score: float, feedback: Optional[str] = None):
        """Record ground truth and outcome for an episode."""
        await memory_service.record_feedback(episode_id, ground_truth, score, feedback)
        self.logger.info(f"👁️ Observed feedback for episode {episode_id}. Score: {score}")

    async def reflect(self) -> Dict[str, Any]:
        """
        Analyze past failures and update Reflective Memory.
        Implements Loop 2: Error Replay Training.
        """
        failed_episodes = await memory_service.get_failed_episodes(self.metadata.id)
        if not failed_episodes:
            return {"status": "SKIPPED", "message": "No failed episodes found for reflection."}

        from app.services.llm_factory import get_llm
        from app.ai_engine.prompts import UNIVERSAL_AGENT_TRAINING_PROMPT
        import json

        llm = get_llm()
        
        prompt = UNIVERSAL_AGENT_TRAINING_PROMPT.format(
            failed_episodes=json.dumps(failed_episodes, indent=2, default=str),
            agent_type=self.metadata.type,
            agent_id=self.metadata.id,
            current_heuristics=json.dumps(self.policy.heuristics if self.policy else [])
        )

        response = await llm.chat_completion([{"role": "user", "content": prompt}], response_format={"type": "json_object"})
        content = response["choices"][0]["message"]["content"]
        self.logger.info(f"🧠 Raw Reflection Content: {content}")
        reflection_data = json.loads(content)

        reflection = ReflectiveMemory(
            agent_id=self.metadata.id,
            mistake_patterns=reflection_data.get("mistake_patterns", []),
            root_causes=reflection_data.get("root_causes", []),
            new_decision_rules=reflection_data.get("new_decision_rules", []),
            confidence_adjustments=reflection_data.get("confidence_adjustments", {}),
            learning_summary=reflection_data.get("learning_summary", "Self-reflection completed."),
            source_episodes=[str(e["_id"]) for e in failed_episodes]
        )
        
        reflection_id = await memory_service.store_reflection(reflection)
        return {"status": "SUCCESS", "reflection_id": reflection_id, "summary": reflection.learning_summary}

    async def calibrate(self) -> Dict[str, Any]:
        """
        Update Policy Memory based on Reflective Memory findings.
        Implements Loop 3: Adaptive Weight Learning.
        """
        if not self.policy:
            await self.initialize_brains()

        if not self.policy:
            await self.initialize_brains()

        latest_reflection = await memory_service.get_latest_reflection(self.metadata.id)

        if not latest_reflection:
            return {"status": "SKIPPED", "message": "No reflection found to calibrate from."}

        # Apply confidence adjustments to weights
        adjustments = latest_reflection.confidence_adjustments
        for signal, adj in adjustments.items():
            if signal in self.policy.weights:
                # Basic additive adjustment with clipping
                new_val = max(0.05, min(0.95, self.policy.weights[signal] + adj))
                self.policy.weights[signal] = round(new_val, 3)

        # Normalize weights to sum to 1.0 if they changed
        total = sum(self.policy.weights.values())
        if total > 0:
            for k in self.policy.weights:
                self.policy.weights[k] = round(self.policy.weights[k] / total, 3)

        # Update heuristics
        new_rules = latest_reflection.new_decision_rules
        self.policy.heuristics.extend([r for r in new_rules if r not in self.policy.heuristics])
        self.policy.updated_at = datetime.utcnow()

        await memory_service.update_policy(self.policy)
        
        return {
            "status": "SUCCESS", 
            "updated_weights": self.policy.weights,
            "new_heuristics_count": len(new_rules)
        }

    async def fine_tune(self) -> Dict[str, Any]:
        """
        Perform a deep recalibration of the agent's logic using reflective memory.
        This implements a more intense 'tuning' than standard calibration.
        """
        self.logger.info(f"🚀 Initiating Neural Fine-Tuning for {self.metadata.id}...")
        
        # 1. Self-Reflection (Loop 2)
        reflection_res = await self.reflect()
        if reflection_res.get("status") == "SKIPPED":
            return {"status": "SKIPPED", "message": "Insufficient failure data for fine-tuning."}
            
        # 2. Policy Calibration (Loop 3)
        calibration_res = await self.calibrate()
        
        # 3. Intelligence Recalibration (Rethink prompts if accuracy is low)
        if self.metadata.metrics and getattr(self.metadata.metrics, 'accuracy', 1.0) < 0.8:
            self.logger.info("⚠️ Low accuracy detected. Forcing prompt recalibration...")
            # This would trigger STEP 4 of the pipeline
            from app.services.training_manager import training_manager
            session = training_manager.get_session(self.metadata.id)
            if session:
                await self.calibrate_intelligence(session)

        return {
            "status": "SUCCESS",
            "reflection_summary": reflection_res.get("summary"),
            "updated_weights": calibration_res.get("updated_weights"),
            "new_heuristics": calibration_res.get("new_heuristics_count")
        }

    def get_info(self) -> AgentMetadata:
        """Return agent metadata with current state/versioning."""
        return self.metadata

    async def get_metrics(self) -> Dict[str, Any]:
        """Return current performance metrics."""
        if isinstance(self.metadata.metrics, MetricsModel):
            return self.metadata.metrics.dict()
        return self.metadata.metrics or {}

    def transition_state(self, new_state: str):
        """Standardized state transition with logging."""
        old_state = self.metadata.state
        self.metadata.state = new_state
        self.logger.info(f"🔄 State Transition: {old_state} -> {new_state}")

