import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field
import logging
import json
from pathlib import Path
from collections import deque

logger = logging.getLogger(__name__)

# Persistence Path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "backend" / "data"  # Fix path resolution
if not DATA_DIR.exists():
    DATA_DIR = BASE_DIR.parent / "backend" / "data"

# Fallback to absolute if relative fails
if not DATA_DIR.exists():
    DATA_DIR = Path("/Users/aditya/Downloads/Antigravity/backend/data")

TRAINING_RUNS_DIR = DATA_DIR / "training_runs"
TRAINING_RUNS_DIR.mkdir(parents=True, exist_ok=True)

@dataclass
class TrainingArtifact:
    """Represents a training artifact (embeddings, checkpoints, etc.)."""
    artifact_type: str
    path: str
    version: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TrainingRun:
    """Complete record of a training run for reproducibility."""
    run_id: str
    agent_id: str
    agent_type: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str = "running"
    config: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    artifacts: List[TrainingArtifact] = field(default_factory=list)
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "status": self.status,
            "config": self.config,
            "metrics": self.metrics,
            "artifacts": [
                {
                    "artifact_type": a.artifact_type,
                    "path": a.path,
                    "version": a.version,
                    "created_at": a.created_at.isoformat(),
                    "metadata": a.metadata
                }
                for a in self.artifacts
            ],
            "error": self.error
        }

class TrainingSession:
    """Active training session with real-time logging."""
    
    def __init__(self, agent_id: str, agent_type: str = "generic"):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.logs: deque = deque(maxlen=200)
        self.is_active = True
        self.should_stop = False
        self.start_time = datetime.utcnow()
        self.subscribers: List[asyncio.Queue] = []
        
        self.run_id = f"{agent_id}_{self.start_time.strftime('%Y%m%d_%H%M%S')}"
        self.training_run = TrainingRun(
            run_id=self.run_id,
            agent_id=agent_id,
            agent_type=agent_type,
            started_at=self.start_time
        )
        self.step_metrics: Dict[str, Any] = {}

    def add_log(self, message: str, level: str = "INFO"):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "message": message,
            "level": level,
            "run_id": self.run_id
        }
        self.logs.append(log_entry)
        
        for queue in self.subscribers:
            try:
                queue.put_nowait(log_entry)
            except asyncio.QueueFull:
                pass

    def record_step_metric(self, step: str, metric_name: str, value: Any):
        if step not in self.step_metrics:
            self.step_metrics[step] = {}
        self.step_metrics[step][metric_name] = value
        self.training_run.metrics[step] = self.step_metrics[step]

    def add_artifact(self, artifact_type: str, path: str, version: str, metadata: Dict[str, Any] = None):
        artifact = TrainingArtifact(
            artifact_type=artifact_type,
            path=path,
            version=version,
            metadata=metadata or {}
        )
        self.training_run.artifacts.append(artifact)
        self.add_log(f"📦 Artifact registered: {artifact_type}", "DEBUG")

    def complete(self, metrics: Dict[str, Any] = None):
        self.is_active = False
        self.training_run.completed_at = datetime.utcnow()
        self.training_run.status = "completed"
        if metrics:
            self.training_run.metrics.update(metrics)

    def fail(self, error: str):
        self.is_active = False
        self.training_run.completed_at = datetime.utcnow()
        self.training_run.status = "failed"
        self.training_run.error = error

    def stop(self):
        self.should_stop = True
        self.is_active = False
        self.training_run.completed_at = datetime.utcnow()
        self.training_run.status = "stopped"
        self.add_log("🛑 Training stopped by user.", "WARNING")


class TrainingManager:
    """
    Central manager for training sessions with file-based persistence.
    """
    _instance: Optional['TrainingManager'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TrainingManager, cls).__new__(cls)
            cls._instance.sessions: Dict[str, TrainingSession] = {}
            cls._instance.completed_runs: Dict[str, TrainingRun] = {}
        return cls._instance

    def start_session(self, agent_id: str, agent_type: str = "generic", config: Dict[str, Any] = None) -> TrainingSession:
        session = self.sessions.get(agent_id)
        if session and session.is_active:
            logger.info(f"Joining existing active training session for agent '{agent_id}'.")
            return session

        logger.info(f"Starting new training session for agent '{agent_id}'.")
        new_session = TrainingSession(agent_id, agent_type)
        if config:
            new_session.training_run.config = config
        self.sessions[agent_id] = new_session
        return new_session

    def get_session(self, agent_id: str) -> Optional[TrainingSession]:
        return self.sessions.get(agent_id)

    def stop_session(self, agent_id: str):
        session = self.get_session(agent_id)
        if session:
            session.stop()
            # We assume asyncio.create_task wrapper will handle persistence call after
            # or manual call needed if running synchronously.
            # Ideally async method but sticking to sync interface match for now,
            # persistence happens in BaseAgent.execute_pipeline

    def complete_session(self, agent_id: str, metrics: Dict[str, Any] = None):
        session = self.get_session(agent_id)
        if session:
            session.complete(metrics)

    def fail_session(self, agent_id: str, error: str):
        session = self.get_session(agent_id)
        if session:
            session.fail(error)

    async def persist_run(self, session: TrainingSession):
        """Persist training run to local JSON file."""
        try:
            run_data = session.training_run.to_dict()
            run_data["logs"] = list(session.logs)
            
            file_path = TRAINING_RUNS_DIR / f"{session.run_id}.json"
            with open(file_path, 'w') as f:
                json.dump(run_data, f, indent=2, default=str)
                
            logger.info(f"💾 Persisted training run to {file_path}")
            
            # Clean up active session from memory
            if session.agent_id in self.sessions and not session.is_active:
                del self.sessions[session.agent_id]
                
        except Exception as e:
            logger.error(f"Failed to persist training run: {e}")

    async def load_run(self, run_id: str) -> Optional[TrainingRun]:
        """Load a training run from disk."""
        file_path = TRAINING_RUNS_DIR / f"{run_id}.json"
        if not file_path.exists():
            return None
            
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                
            return TrainingRun(
                run_id=data["run_id"],
                agent_id=data["agent_id"],
                agent_type=data.get("agent_type", "generic"),
                started_at=datetime.fromisoformat(data["started_at"]),
                completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
                status=data.get("status", "unknown"),
                config=data.get("config", {}),
                metrics=data.get("metrics", {}),
                error=data.get("error")
            )
        except Exception as e:
            logger.error(f"Failed to load run {run_id}: {e}")
            return None

    async def list_runs(self, agent_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """List recent training runs for an agent."""
        runs = []
        try:
            for file_path in sorted(TRAINING_RUNS_DIR.glob(f"{agent_id}_*.json"), reverse=True):
                with open(file_path, 'r') as f:
                    runs.append(json.load(f))
                if len(runs) >= limit:
                    break
        except Exception as e:
            logger.error(f"Failed to list runs: {e}")
            
        return runs

    async def subscribe(self, agent_id: str) -> Optional[asyncio.Queue]:
        session = self.get_session(agent_id)
        if not session:
            # Check if recently completed
            return None
            
        queue = asyncio.Queue(maxsize=100)
        session.subscribers.append(queue)
        for log in session.logs:
            queue.put_nowait(log)
            
        return queue

    def unsubscribe(self, agent_id: str, queue: asyncio.Queue):
        session = self.get_session(agent_id)
        if session and queue in session.subscribers:
            session.subscribers.remove(queue)

training_manager = TrainingManager()
