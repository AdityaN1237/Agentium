import asyncio
import sys
import os
from datetime import datetime

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.agents.rag_qa.agent import RAGQAAgent
from app.schemas.agent_io import AgentMetadata

# Golden Dataset (Questions that SHOULD have answers if docs are indexed)
# We assume the user has indexed some basic 'Antigravity' or 'Python' docs. 
# Since we don't know the exact docs, we'll use generic technical questions likely to be in a sample set,
# OR we rely on the agent to answer gracefully.
# Ideally, this should match the user's uploaded data.
# For now, we will test the *capabilities* (Reasoning, Latency) rather than strict fact-checking on unknown docs.

EVAL_QUESTIONS = [
    {"q": "What is the purpose of this system?", "expected": "unknown"}, 
    {"q": "How do I fix a connection timeout?", "expected": "timeout"},
    {"q": "Explain the architecture of the RAG agent.", "expected": "architecture"},
    {"q": "sfjkshdfjkshdf", "expected": "I don't have enough information"}, # Garbage test
    {"q": "Write a python script to connect to MongoDB", "expected": "pymongo"}
]

async def evaluate():
    print("🚀 Starting RAG Agent Evaluation...")
    agent = RAGQAAgent()
    
    # Ensure loaded
    if not agent._chunks:
         print("⚠️ No chunks indexed. Evaluation will be limited to 'Empty' responses.")
    
    results = []
    
    for item in EVAL_QUESTIONS:
        q = item["q"]
        print(f"\nrunning: {q}")
        
        start = datetime.utcnow()
        response = await agent.predict({"query": q, "top_k": 5})
        duration = (datetime.utcnow() - start).total_seconds()
        
        data = response.get("data", {})
        answer = data.get("answer", "")
        confidence = data.get("confidence", 0)
        
        is_correct = False
        # Simple keyword heuristic for correctness
        if item["expected"] in answer.lower() or (item["expected"] == "unknown" and confidence > 0.5):
            is_correct = True
        elif "don't have enough information" in answer and item["q"] == "sfjkshdfjkshdf":
            is_correct = True
            
        results.append({
            "query": q,
            "correct": is_correct,
            "confidence": confidence,
            "latency": duration,
            "answer_snippet": answer[:100] + "..."
        })
        
        print(f"   -> Confidence: {confidence}")
        print(f"   -> Correct: {is_correct}")
        print(f"   -> Latency: {duration:.2f}s")
        if "<thinking>" in answer:
             print("   -> 🧠 Thinking Trace Detected")

    # Summary
    avg_conf = sum(r["confidence"] for r in results) / len(results)
    avg_lat = sum(r["latency"] for r in results) / len(results)
    accuracy = sum(1 for r in results if r["correct"]) / len(results)
    
    print("\n" + "="*30)
    print("📊 EVALUATION REPORT")
    print("="*30)
    print(f"Files Indexed: {len(agent._documents)}")
    print(f"Avg Confidence: {avg_conf:.2f}")
    print(f"Avg Latency:    {avg_lat:.2f}s")
    print(f"Accuracy (Est): {accuracy*100:.0f}%")
    print("="*30)
    
    if accuracy > 0.8:
        print("✅ PASSED: System meets 'Intelligent' criteria.")
    else:
        print("⚠️ WARNING: Accuracy is below expected threshold (Requires relevant docs).")

if __name__ == "__main__":
    asyncio.run(evaluate())
