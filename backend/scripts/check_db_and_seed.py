import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def check_db():
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client['ai_recruiter']
    candidates = await db.candidates.count_documents({})
    jobs = await db.jobs.count_documents({})
    print(f"Candidates count: {candidates}")
    print(f"Jobs count: {jobs}")
    
    # No dummy data insertion - system requires real uploaded data
    if candidates == 0:
        print("No candidates found. Please upload resumes to populate the database.")

    if jobs == 0:
        print("No jobs found. Please add job postings to the system.")

if __name__ == "__main__":
    asyncio.run(check_db())
