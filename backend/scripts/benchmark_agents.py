import asyncio
import time
from app.agents.registry import registry
from app.database import Database

async def benchmark_agents():
    await Database.connect()
    db = Database.get_db()
    
    # Initialize registry
    await registry.initialize(db)
    print("Starting Agent Benchmarking...")
    
    # Mock LLM for benchmarking to avoid external latency and API keys
    from unittest.mock import AsyncMock
    import app.services.llm_factory as llm_factory
    mock_provider = AsyncMock()
    
    async def side_effect(messages, **kwargs):
        content = messages[-1]["content"].lower()
        if "score" in content and "feedback" in content:
            return {
                "choices": [{
                    "message": {
                        "content": '{"score": 0.95, "feedback": "Excellent reasoning detected."}'
                    }
                }]
            }
        elif "fit" in content or "candidate" in content:
            return {
                "choices": [{
                    "message": {
                        "content": '{"overall_fit_score": 0.85, "technical_readiness": 0.9, "cultural_alignment": 0.8, "retention_probability": 0.95, "reasoning": {"steps": ["step1"], "conclusion": "Good"}}'
                    }
                }]
            }
        elif "answer" in content or "question" in content or "query" in content:
            return {
                "choices": [{
                    "message": {
                        "content": '{"answer": "The vacation policy allows 25 days.", "confidence_score": 0.98}'
                    }
                }]
            }
        return {
            "choices": [{
                "message": {
                    "content": '{"result": "success", "score": 0.9}'
                }
            }]
        }
    
    mock_provider.chat_completion.side_effect = side_effect
    llm_factory.get_llm = lambda name=None: mock_provider

    # Ensure some data exists
    candidate = await db.candidates.find_one({})
    candidate_id = str(candidate["_id"]) if candidate else "000000000000000000000000"
    if not candidate:
        res = await db.candidates.insert_one({
            "user_id": "bench_user",
            "name": "Bench Candidate",
            "resume_text": "Sample resume text for benchmarking purposes.",
            "resume_embedding": [0.1] * 384,
            "skills": ["Python"]
        })
        candidate_id = str(res.inserted_id)

    # Ensure some chunks exist for RAG
    if await db.doc_chunks.count_documents({}) == 0:
        await db.doc_chunks.insert_one({
            "doc_id": "bench_doc",
            "text": "The vacation policy allows 25 days.",
            "embedding": [0.1] * 384,
            "chunk_index": 0
        })

    agents_to_test = [
        "skill_job_matching",
        "resume_screening",
        "candidate_fit",
        "rag_qa"
    ]
    
    results = {}
    
    for agent_id in agents_to_test:
        print(f"\nBenchmarking Agent: {agent_id}")
        agent = registry.get_agent(agent_id)
        
        # 1. Pipeline Execution Time
        start_time = time.time()
        # We trigger training which starts execute_pipeline in background
        # For benchmarking, we'll wait for it to complete by checking state
        await agent.train()
        
        timeout = 60 # seconds
        elapsed = 0
        while agent.metadata.state != "READY" and elapsed < timeout:
            await asyncio.sleep(1)
            elapsed += 1
            print(f"  ... Waiting for pipeline ( {elapsed}s )", end="\r")
        
        pipeline_time = time.time() - start_time
        if agent.metadata.state == "READY":
            print(f"\n  Pipeline completed in {pipeline_time:.2f}s")
        else:
            print(f"\n  Pipeline timed out or failed. Current state: {agent.metadata.state}")
            continue

        # 2. Inference Latency
        print("  Measuring Inference Latency...")
        test_inputs = {
            "skill_job_matching": {"candidate_id": candidate_id, "top_k": 5},
            "resume_screening": {"job_description": "Looking for a Python Developer with FastAPI experience and 5+ years of background in scalable cloud systems.", "top_k": 5},
            "candidate_fit": {
                "candidate_skills": ["Python", "Docker"], 
                "job_requirements": "Looking for an engineer with Python and Docker knowledge. Must have at least 5 years of professional experience.",
                "candidate_experience": "6 years of Python development."
            },
            "rag_qa": {"query": "What is the vacation policy?"}
        }
        
        input_data = test_inputs.get(agent_id, {})
        latencies = []
        for _ in range(5):
            inf_start = time.time()
            await agent.predict(input_data)
            latencies.append((time.time() - inf_start) * 1000)
        
        avg_latency = sum(latencies) / len(latencies)
        print(f"  Avg Inference Latency: {avg_latency:.2f}ms")
        
        results[agent_id] = {
            "pipeline_time_s": round(pipeline_time, 2),
            "avg_latency_ms": round(avg_latency, 2),
            "accuracy": agent.metadata.metrics.accuracy if agent.metadata.metrics else 0.0
        }

    print("\n" + "="*40)
    print("      FINAL BENCHMARK RESULTS")
    print("="*40)
    for agent_id, data in results.items():
        print(f"Agent: {agent_id:20} | Pipeline: {data['pipeline_time_s']:6}s | Latency: {data['avg_latency_ms']:8}ms | Acc: {data['accuracy']:.2f}")

if __name__ == "__main__":
    asyncio.run(benchmark_agents())
