"""
Agent Verification Script.
Tests all agents by running their training pipelines and verifying predictions.
"""
import asyncio
import sys
from datetime import datetime
from typing import Dict, Any, List

# Add parent directory to path for imports
sys.path.insert(0, '/Users/aditya/Downloads/Antigravity/backend')

from app.database import Database
from app.agents.registry import AgentRegistry


async def verify_agent(agent, test_input: Dict[str, Any]) -> Dict[str, Any]:
    """Verify a single agent's prediction capability."""
    agent_id = agent.metadata.id
    result = {
        "agent_id": agent_id,
        "name": agent.metadata.name,
        "status": "UNKNOWN",
        "metrics": None,
        "prediction_test": None,
        "error": None
    }
    
    try:
        # Set to READY state for testing
        agent.metadata.state = "READY"
        
        # Run evaluate to get metrics
        print(f"  📊 Evaluating {agent_id}...")
        metrics = await agent.evaluate()
        result["metrics"] = {
            "accuracy": getattr(metrics, 'accuracy', None),
            "precision": getattr(metrics, 'precision', None),
            "recall": getattr(metrics, 'recall', None),
            "latency_ms": getattr(metrics, 'latency_ms', None),
            "sample_size": getattr(metrics, 'sample_size', None)
        }
        
        # Run prediction test
        print(f"  🔮 Testing prediction for {agent_id}...")
        prediction = await agent.predict(test_input)
        
        if isinstance(prediction, dict):
            if prediction.get("status") == "SUCCESS":
                result["prediction_test"] = "PASS"
                result["status"] = "READY"
            elif prediction.get("status") == "FAILED":
                result["prediction_test"] = "FAIL"
                result["status"] = "DEGRADED"
                result["error"] = prediction.get("errors", ["Unknown error"])
            else:
                result["prediction_test"] = "PASS"
                result["status"] = "READY"
        else:
            result["prediction_test"] = "PASS"
            result["status"] = "READY"
            
    except Exception as e:
        result["status"] = "ERROR"
        result["error"] = str(e)
        result["prediction_test"] = "ERROR"
        
    return result


async def train_agent(agent) -> Dict[str, Any]:
    """Train a single agent."""
    agent_id = agent.metadata.id
    result = {
        "agent_id": agent_id,
        "name": agent.metadata.name,
        "status": "UNKNOWN",
        "error": None,
        "duration_seconds": 0
    }
    
    try:
        print(f"  🔄 Training {agent_id}...")
        start_time = datetime.utcnow()
        
        # Execute training pipeline
        await agent.execute_pipeline({})
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        result["status"] = agent.metadata.state
        result["duration_seconds"] = round(duration, 2)
        
        if agent.metadata.metrics:
            result["accuracy"] = getattr(agent.metadata.metrics, 'accuracy', None)
            
    except Exception as e:
        result["status"] = "FAILED"
        result["error"] = str(e)
        
    return result


async def main():
    """Main verification routine."""
    print("=" * 60)
    print("🧪 AI AGENT VERIFICATION SUITE")
    print("=" * 60)
    print(f"Started at: {datetime.utcnow().isoformat()}")
    print()
    
    # Connect to database
    print("📡 Connecting to database...")
    await Database.connect()
    db = Database.get_db()
    
    # Check database status
    print("\n📊 Database Status:")
    candidates_count = await db.candidates.count_documents({})
    jobs_count = await db.jobs.count_documents({})
    skills_count = await db.skills.count_documents({})
    documents_count = await db.documents.count_documents({})
    
    print(f"  - Candidates: {candidates_count}")
    print(f"  - Jobs: {jobs_count}")
    print(f"  - Skills: {skills_count}")
    print(f"  - Documents: {documents_count}")
    
    if candidates_count == 0 or jobs_count == 0:
        print("\n⚠️  Database is empty! Run seed_database.py first.")
        print("   python scripts/seed_database.py")
        await Database.disconnect()
        return
    
    # Initialize agents
    print("\n🔌 Initializing agents...")
    await AgentRegistry.initialize(db)
    
    agents = AgentRegistry.list_agents()
    print(f"  Found {len(agents)} registered agents")
    
    # Test inputs for each agent type
    test_inputs = {
        "resume_screening": {
            "job_description": "We are looking for a Senior Python Developer with 5+ years of experience in FastAPI, PostgreSQL, and AWS. The ideal candidate has strong problem-solving skills and experience with microservices architecture."
        },
        "skill_job_matching": {
            "resume_text": "Experienced Python developer with 6 years of experience in backend development. Proficient in FastAPI, Django, PostgreSQL, and Docker. Led development of payment processing systems."
        },
        "jd_to_skill": {
            "job_description": "Looking for a Full Stack Developer with React, Node.js, and TypeScript experience. Must have 3+ years of experience with modern web development and API design."
        },
        "candidate_fit": {
            "candidate_skills": ["Python", "FastAPI", "PostgreSQL", "Docker"],
            "job_requirements": "Senior Backend Engineer position requiring 5+ years of Python experience, expertise in FastAPI or Django, and strong database skills with PostgreSQL.",
            "candidate_experience": "6 years of backend development experience"
        },
        "skill_gap": {
            "candidate_skills": ["Python", "SQL"],
            "job_requirements": "We need a Full Stack Developer proficient in Python, React, Node.js, and AWS. Experience with Docker and CI/CD pipelines is required."
        },
        "market_trend": {
            "skill": "Python",
            "location": "USA"
        },
        "rag_qa": {
            "query": "How many days of annual leave do employees get?"
        }
    }
    
    # Phase 1: Train all agents
    print("\n" + "=" * 60)
    print("📚 PHASE 1: TRAINING AGENTS")
    print("=" * 60)
    
    training_results = []
    for agent_info in agents:
        agent_id = agent_info["id"]
        try:
            agent = AgentRegistry.get_agent(agent_id)
            result = await train_agent(agent)
            training_results.append(result)
            status_icon = "✅" if result["status"] == "READY" else "❌"
            print(f"  {status_icon} {agent_id}: {result['status']} ({result['duration_seconds']}s)")
        except Exception as e:
            print(f"  ❌ {agent_id}: ERROR - {str(e)}")
            training_results.append({
                "agent_id": agent_id,
                "status": "ERROR",
                "error": str(e)
            })
    
    # Phase 2: Verify all agents
    print("\n" + "=" * 60)
    print("🔍 PHASE 2: VERIFYING PREDICTIONS")
    print("=" * 60)
    
    verification_results = []
    for agent_info in agents:
        agent_id = agent_info["id"]
        try:
            agent = AgentRegistry.get_agent(agent_id)
            test_input = test_inputs.get(agent_id, {})
            
            if not test_input:
                print(f"  ⚠️  {agent_id}: No test input defined, skipping")
                continue
                
            result = await verify_agent(agent, test_input)
            verification_results.append(result)
            
            status_icon = "✅" if result["prediction_test"] == "PASS" else "❌"
            accuracy = result["metrics"].get("accuracy", "N/A") if result["metrics"] else "N/A"
            print(f"  {status_icon} {agent_id}: {result['status']} (Accuracy: {accuracy})")
            
        except Exception as e:
            print(f"  ❌ {agent_id}: ERROR - {str(e)}")
            verification_results.append({
                "agent_id": agent_id,
                "status": "ERROR",
                "error": str(e)
            })
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 VERIFICATION SUMMARY")
    print("=" * 60)
    
    total = len(verification_results)
    passed = sum(1 for r in verification_results if r.get("prediction_test") == "PASS")
    failed = sum(1 for r in verification_results if r.get("prediction_test") == "FAIL")
    errors = sum(1 for r in verification_results if r.get("prediction_test") == "ERROR")
    
    print(f"\n  Total Agents: {total}")
    print(f"  ✅ Passed: {passed}")
    print(f"  ❌ Failed: {failed}")
    print(f"  ⚠️  Errors: {errors}")
    
    # Show detailed results
    print("\n📊 Detailed Metrics:")
    for result in verification_results:
        print(f"\n  {result['name']} ({result['agent_id']}):")
        print(f"    Status: {result['status']}")
        if result["metrics"]:
            print(f"    Accuracy: {result['metrics'].get('accuracy', 'N/A')}")
            print(f"    Latency: {result['metrics'].get('latency_ms', 'N/A')}ms")
        if result.get("error"):
            print(f"    Error: {result['error']}")
    
    print("\n" + "=" * 60)
    print(f"✅ Verification complete at {datetime.utcnow().isoformat()}")
    print("=" * 60)
    
    await Database.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
