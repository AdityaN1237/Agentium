import asyncio
import sys
import os

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import Database
from app.agents.base import BaseAgent, AgentMetadata
from typing import Any, Dict

class MockAgent(BaseAgent):
    async def validate_data_readiness(self) -> bool: return True
    async def upload_dataset(self, data: Any) -> Dict[str, Any]: return {}
    async def train(self, config: Dict[str, Any] = None) -> Dict[str, Any]: return {}
    async def stop_training(self) -> Dict[str, Any]: return {}
    async def evaluate(self) -> Dict[str, Any]: return {"accuracy": 0.8}
    async def predict_logic(self, input_data: Any) -> Any:
        return {"result": "mock_prediction", "confidence": 0.85}

async def verify_agent_learning():
    await Database.connect()
    
    metadata = AgentMetadata(
        id="mock_agent",
        name="Mock Learning Agent",
        description="Verification Agent",
        version="1.0.0",
        state="READY"
    )
    agent = MockAgent(metadata)
    
    # 1. Prediction with Episodic Memory
    print("\n--- Phase 1: Prediction & Episode Storage ---")
    prediction = await agent.predict({"job": "Software Engineer"})
    episode_id = prediction.get("episode_id")
    print(f"Prediction result: {prediction}")
    print(f"Stored Episode ID: {episode_id}")
    
    # 2. Observe Feedback
    print("\n--- Phase 2: Observation & Feedback ---")
    await agent.observe(episode_id, ground_truth={"status": "rejected"}, score=0.2, feedback="Misled by semantic match")
    print("Feedback recorded.")
    
    # 3. Reflection
    print("\n--- Phase 3: Reflection ---")
    reflection = await agent.reflect()
    print(f"Reflection Result: {reflection}")
    
    # 4. Calibration
    print("\n--- Phase 4: Calibration ---")
    calibration = await agent.calibrate()
    print(f"Calibration Result: {calibration}")
    print(f"Updated weights after calibration: {agent.policy.weights}")

    await Database.disconnect()

if __name__ == "__main__":
    asyncio.run(verify_agent_learning())
