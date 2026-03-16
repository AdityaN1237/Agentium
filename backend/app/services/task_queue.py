"""
Background Task Queue for Non-Blocking Training.
Uses ThreadPoolExecutor to handle CPU-bound embedding operations without blocking the event loop.
"""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, Callable, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class BackgroundTask:
    """Represents a background training task."""
    task_id: str
    agent_id: str
    status: TaskStatus = TaskStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    progress: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "status": self.status.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "progress": self.progress,
            "error": self.error
        }


class BackgroundTaskQueue:
    """
    Non-blocking task queue with thread pool for CPU-bound work.
    
    The key insight is that Python's asyncio.create_task() does NOT help with
    CPU-bound operations because of the GIL. We need ThreadPoolExecutor to
    actually run CPU-bound work (like embedding generation) in a separate thread.
    
    Usage:
        queue = get_task_queue()
        task = await queue.submit_training("skill_job_matching", agent.execute_pipeline)
        status = queue.get_task_status(task.task_id)
    """
    
    _instance: Optional['BackgroundTaskQueue'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, max_workers: int = 2):
        if self._initialized:
            return
            
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="train_worker")
        self._tasks: Dict[str, BackgroundTask] = {}
        self._futures: Dict[str, asyncio.Future] = {}
        self._initialized = True
        logger.info(f"🚀 BackgroundTaskQueue initialized with {max_workers} workers")
    
    async def submit_training(
        self, 
        agent_id: str, 
        train_func: Callable,
        *args,
        **kwargs
    ) -> BackgroundTask:
        """
        Submit a training function to run in the background.
        
        Args:
            agent_id: ID of the agent being trained
            train_func: The async training function to execute
            *args, **kwargs: Arguments to pass to the training function
        
        Returns:
            BackgroundTask object for tracking progress
        """
        task_id = f"{agent_id}_{datetime.utcnow().timestamp()}"
        
        # Check if agent already has an active training task
        for task in self._tasks.values():
            if task.agent_id == agent_id and task.status in [TaskStatus.PENDING, TaskStatus.RUNNING]:
                logger.warning(f"Agent {agent_id} already has active training task")
                return task
        
        task = BackgroundTask(
            task_id=task_id,
            agent_id=agent_id,
            status=TaskStatus.PENDING,
            started_at=datetime.utcnow()
        )
        self._tasks[task_id] = task
        
        # Create wrapper to run async function in thread pool
        async def run_training():
            task.status = TaskStatus.RUNNING
            logger.info(f"🏃 Starting training for {agent_id} (task: {task_id})")
            try:
                # For async functions, we need to run them in the current event loop
                # but offload CPU-bound parts using asyncio.to_thread internally
                if asyncio.iscoroutinefunction(train_func):
                    result = await train_func(*args, **kwargs)
                else:
                    # For sync functions, run in thread pool
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(self._executor, train_func, *args)
                
                task.result = result
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.utcnow()
                task.progress = 1.0
                logger.info(f"✅ Training completed for {agent_id} (task: {task_id})")
                
            except Exception as e:
                task.status = TaskStatus.FAILED
                task.error = str(e)
                task.completed_at = datetime.utcnow()
                logger.error(f"❌ Training failed for {agent_id}: {e}")
        
        # Schedule the training on the event loop
        asyncio.create_task(run_training())
        
        return task
    
    def get_task_status(self, task_id: str) -> Optional[BackgroundTask]:
        """Get the current status of a training task."""
        return self._tasks.get(task_id)
    
    def get_agent_task(self, agent_id: str) -> Optional[BackgroundTask]:
        """Get the most recent task for an agent."""
        agent_tasks = [t for t in self._tasks.values() if t.agent_id == agent_id]
        if not agent_tasks:
            return None
        return max(agent_tasks, key=lambda t: t.started_at or datetime.min)
    
    def cancel_task(self, task_id: str) -> bool:
        """Attempt to cancel a pending/running task."""
        task = self._tasks.get(task_id)
        if not task:
            return False
        
        if task.status == TaskStatus.PENDING:
            task.status = TaskStatus.CANCELLED
            task.completed_at = datetime.utcnow()
            logger.info(f"🛑 Task {task_id} cancelled")
            return True
        
        if task.status == TaskStatus.RUNNING:
            # Mark as cancelled - actual training will check this flag
            task.status = TaskStatus.CANCELLED
            logger.info(f"🛑 Task {task_id} marked for cancellation")
            return True
        
        return False
    
    def list_tasks(self, agent_id: Optional[str] = None, limit: int = 10) -> list:
        """List recent tasks, optionally filtered by agent."""
        tasks = list(self._tasks.values())
        
        if agent_id:
            tasks = [t for t in tasks if t.agent_id == agent_id]
        
        # Sort by started_at descending
        tasks.sort(key=lambda t: t.started_at or datetime.min, reverse=True)
        
        return [t.to_dict() for t in tasks[:limit]]
    
    def is_agent_training(self, agent_id: str) -> bool:
        """Check if an agent currently has an active training task."""
        for task in self._tasks.values():
            if task.agent_id == agent_id and task.status in [TaskStatus.PENDING, TaskStatus.RUNNING]:
                return True
        return False
    
    def cleanup_old_tasks(self, max_age_hours: int = 24):
        """Remove tasks older than max_age_hours."""
        cutoff = datetime.utcnow().timestamp() - (max_age_hours * 3600)
        to_remove = []
        
        for task_id, task in self._tasks.items():
            if task.completed_at and task.completed_at.timestamp() < cutoff:
                to_remove.append(task_id)
        
        for task_id in to_remove:
            del self._tasks[task_id]
        
        if to_remove:
            logger.info(f"🧹 Cleaned up {len(to_remove)} old tasks")


# Singleton accessor
_task_queue: Optional[BackgroundTaskQueue] = None

def get_task_queue() -> BackgroundTaskQueue:
    """Get the singleton task queue instance."""
    global _task_queue
    if _task_queue is None:
        _task_queue = BackgroundTaskQueue()
    return _task_queue
