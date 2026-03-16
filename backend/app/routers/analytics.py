from fastapi import APIRouter
from app.database import Database
from collections import Counter
import logging

router = APIRouter(prefix="/analytics", tags=["Analytics"])
logger = logging.getLogger(__name__)

@router.get("/")
async def get_analytics():
    """
    Get aggregated analytics for the dashboard.
    """
    db = Database.get_db()
    
    # 1. Skill Distribution (from Candidates)
    candidates = await db.candidates.find({}).to_list(length=None)
    all_skills = []
    for c in candidates:
        if isinstance(c.get('skills'), list):
            all_skills.extend(c['skills'])
        elif isinstance(c.get('skills'), str):
             all_skills.extend([s.strip() for s in c['skills'].split(',')])
             
    skill_counts = Counter(all_skills).most_common(5)
    skill_composition = [
        {"name": skill, "value": count, "fill": f"hsl({210 + i * 20}, 80%, 60%)"}
        for i, (skill, count) in enumerate(skill_counts)
    ]
    
    # 2. Market Demand (from Jobs)
    jobs = await db.jobs.find({}).to_list(length=None)
    job_skills = []
    for j in jobs:
        if isinstance(j.get('required_skills'), list):
            job_skills.extend(j['required_skills'])
            
    job_skill_counts = Counter(job_skills).most_common(7)
    market_drift = [
        {"subject": skill, "A": count, "B": max(0, count - 2), "fullMark": max(count * 1.5, 10)}
        for skill, count in job_skill_counts
    ]
    if not market_drift: # Fallback if empty to prevent chart crash
        market_drift = [{"subject": "N/A", "A": 0, "B": 0, "fullMark": 100}]

    # 3. Inference Quality (Backed by DB; seed if empty)
    history = await db.training_history.find({}).sort("month_index", 1).to_list(length=None)
    if not history:
        seed = [
            {"month": "Jan", "month_index": 1, "accuracy": 0.65, "latency": 45},
            {"month": "Feb", "month_index": 2, "accuracy": 0.72, "latency": 40},
            {"month": "Mar", "month_index": 3, "accuracy": 0.85, "latency": 35},
            {"month": "Apr", "month_index": 4, "accuracy": 0.92, "latency": 28},
            {"month": "May", "month_index": 5, "accuracy": 0.96, "latency": 25},
            {"month": "Jun", "month_index": 6, "accuracy": 0.98, "latency": 22},
        ]
        await db.training_history.insert_many(seed)
        history = seed
    inference_quality = [
        {"month": h["month"], "accuracy": int((h.get("accuracy", 0) or 0) * 100), "latency": h.get("latency", 0)}
        for h in history
    ]

    return {
        "skill_composition": skill_composition,
        "market_drift": market_drift,
        "inference_quality": inference_quality
    }
