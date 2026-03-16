import asyncio
import random
from datetime import datetime
from app.database import Database

async def generate_test_data():
    await Database.connect()
    db = Database.get_db()
    
    # 1. Generate Candidates
    candidates = []
    skills_pool = ["Python", "FastAPI", "React", "Node.js", "Docker", "AWS", "MongoDB", "TypeScript", "Go", "Rust"]
    
    for i in range(20):
        skills = random.sample(skills_pool, k=random.randint(2, 5))
        candidates.append({
            "user_id": f"test_user_{i}",
            "name": f"Candidate {i}",
            "email": f"candidate_{i}@example.com",
            "skills": skills,
            "resume_text": f"Experienced developer with skills in {', '.join(skills)}. Worked on various projects including {random.choice(['E-commerce', 'Fintech', 'AI Platform', 'Blockchain'])}.",
            "updated_at": datetime.utcnow()
        })
    
    await db.candidates.delete_many({"user_id": {"$regex": "^test_user_"}})
    await db.candidates.insert_many(candidates)
    print(f"Generated {len(candidates)} test candidates.")

    # 2. Generate Jobs
    jobs = []
    for i in range(10):
        req_skills = random.sample(skills_pool, k=random.randint(3, 6))
        jobs.append({
            "title": f"Job {i}: {random.choice(['Backend', 'Frontend', 'Fullstack', 'DevOps'])} Engineer",
            "description": f"We are looking for a talented engineer proficient in {', '.join(req_skills)}. The ideal candidate has 5+ years of experience.",
            "required_skills": req_skills,
            "updated_at": datetime.utcnow()
        })
    
    await db.jobs.delete_many({"title": {"$regex": "^Job "}})
    await db.jobs.insert_many(jobs)
    print(f"Generated {len(jobs)} test jobs.")

    # 3. Generate Documents (for RAG)
    documents = []
    for i in range(5):
        documents.append({
            "title": f"Internal Policy {i}",
            "text": f"This document outlines the {random.choice(['vacation', 'security', 'remote work', 'hiring'])} policy of Antigravity. All employees must follow these guidelines.",
            "source": "HR Portal",
            "created_at": datetime.utcnow()
        })
    
    await db.documents.delete_many({"title": {"$regex": "^Internal Policy"}})
    await db.documents.insert_many(documents)
    print(f"Generated {len(documents)} test documents.")

if __name__ == "__main__":
    asyncio.run(generate_test_data())
