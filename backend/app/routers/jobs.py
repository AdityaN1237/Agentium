"""
Jobs API Router.
Handles all job posting-related endpoints.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime
from bson import ObjectId

from app.database import Database
from app.models.job import (
    JobCreate, 
    JobListResponse
)
from app.services import get_embedding_service, get_skill_expander

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.get("/", response_model=JobListResponse)
async def get_jobs(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    skill: Optional[str] = Query(None, description="Filter by required skill"),
    company: Optional[str] = Query(None, description="Filter by company"),
    location: Optional[str] = Query(None, description="Filter by location"),
    search: Optional[str] = Query(None, description="Search by title"),
    active_only: bool = Query(True, description="Show only active jobs")
):
    """
    Get paginated list of jobs.
    Supports filtering by skill, company, location, and text search.
    """
    db = Database.get_db()
    
    # Build query filter
    query = {}
    
    if active_only:
        query["is_active"] = True
    
    if skill:
        # Use skill expansion for flexible matching
        skill_expander = get_skill_expander()
        expanded = skill_expander.expand_skill(skill)
        query["$or"] = [
            {"required_skills": {"$in": list(expanded)}},
            {"expanded_skills": {"$in": list(expanded)}}
        ]
    
    if company:
        query["company"] = {"$regex": company, "$options": "i"}
    
    if location:
        query["location"] = {"$regex": location, "$options": "i"}
    
    if search:
        if "$or" in query:
            query["$and"] = [
                {"$or": query.pop("$or")},
                {"$or": [
                    {"title": {"$regex": search, "$options": "i"}},
                    {"description": {"$regex": search, "$options": "i"}}
                ]}
            ]
        else:
            query["$or"] = [
                {"title": {"$regex": search, "$options": "i"}},
                {"description": {"$regex": search, "$options": "i"}}
            ]
    
    # Get total count
    total = await db.jobs.count_documents(query)
    
    # Get paginated results
    skip = (page - 1) * page_size
    cursor = db.jobs.find(query).skip(skip).limit(page_size).sort("created_at", -1)
    jobs = await cursor.to_list(length=page_size)
    
    # Format response
    formatted_jobs = []
    for j in jobs:
        j["_id"] = str(j["_id"])
        # Remove embedding from response
        j.pop("job_embedding", None)
        formatted_jobs.append(j)
    
    return JobListResponse(
        total=total,
        page=page,
        page_size=page_size,
        jobs=formatted_jobs
    )


@router.get("/{job_id}")
async def get_job(job_id: str):
    """Get a single job by ID."""
    db = Database.get_db()
    
    try:
        job = await db.jobs.find_one({"_id": ObjectId(job_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid job ID format")
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job["_id"] = str(job["_id"])
    job.pop("job_embedding", None)
    
    return job


@router.post("/", status_code=201)
async def create_job(job: JobCreate):
    """
    Create a new job posting.
    Automatically generates embeddings and expands required skills.
    """
    db = Database.get_db()
    
    # Generate embedding
    embedding_service = get_embedding_service()
    skill_expander = get_skill_expander()
    
    job_dict = job.model_dump()
    job_dict["job_embedding"] = embedding_service.encode_job_description(job.description)
    job_dict["expanded_skills"] = list(skill_expander.expand_skills(job.required_skills, depth=1))
    job_dict["is_active"] = True
    job_dict["created_at"] = datetime.utcnow()
    job_dict["updated_at"] = datetime.utcnow()
    
    # Insert
    result = await db.jobs.insert_one(job_dict)
    
    return {
        "id": str(result.inserted_id),
        "message": "Job created successfully"
    }


@router.put("/{job_id}")
async def update_job(job_id: str, job: JobCreate):
    """Update an existing job."""
    db = Database.get_db()
    
    try:
        existing = await db.jobs.find_one({"_id": ObjectId(job_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid job ID format")
    
    if not existing:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Generate new embedding
    embedding_service = get_embedding_service()
    skill_expander = get_skill_expander()
    
    update_dict = job.model_dump()
    update_dict["job_embedding"] = embedding_service.encode_job_description(job.description)
    update_dict["expanded_skills"] = list(skill_expander.expand_skills(job.required_skills, depth=1))
    update_dict["updated_at"] = datetime.utcnow()
    
    await db.jobs.update_one(
        {"_id": ObjectId(job_id)},
        {"$set": update_dict}
    )
    
    return {"message": "Job updated successfully"}


@router.delete("/{job_id}")
async def delete_job(job_id: str):
    """Delete a job posting."""
    db = Database.get_db()
    
    try:
        result = await db.jobs.delete_one({"_id": ObjectId(job_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid job ID format")
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {"message": "Job deleted successfully"}


@router.patch("/{job_id}/deactivate")
async def deactivate_job(job_id: str):
    """Deactivate a job posting."""
    db = Database.get_db()
    
    try:
        result = await db.jobs.update_one(
            {"_id": ObjectId(job_id)},
            {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
        )
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid job ID format")
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {"message": "Job deactivated successfully"}


@router.patch("/{job_id}/activate")
async def activate_job(job_id: str):
    """Activate a job posting."""
    db = Database.get_db()
    
    try:
        result = await db.jobs.update_one(
            {"_id": ObjectId(job_id)},
            {"$set": {"is_active": True, "updated_at": datetime.utcnow()}}
        )
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid job ID format")
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {"message": "Job activated successfully"}


@router.get("/{job_id}/skills/expanded")
async def get_job_expanded_skills(job_id: str):
    """Get a job's expanded skills (including related skills)."""
    db = Database.get_db()
    
    try:
        job = await db.jobs.find_one({"_id": ObjectId(job_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid job ID format")
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    skill_expander = get_skill_expander()
    
    original_skills = job.get("required_skills", [])
    expanded_skills = list(skill_expander.expand_skills(original_skills, depth=2))
    
    return {
        "job_id": job_id,
        "job_title": job.get("title"),
        "original_skills": original_skills,
        "expanded_skills": expanded_skills,
        "total_original": len(original_skills),
        "total_expanded": len(expanded_skills)
    }


@router.get("/stats/summary")
async def get_jobs_stats():
    """Get job statistics."""
    db = Database.get_db()
    
    total = await db.jobs.count_documents({})
    active = await db.jobs.count_documents({"is_active": True})
    
    # Get skill distribution
    pipeline = [
        {"$unwind": "$required_skills"},
        {"$group": {"_id": "$required_skills", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 20}
    ]
    skill_dist = await db.jobs.aggregate(pipeline).to_list(length=20)
    
    # Get company distribution
    company_pipeline = [
        {"$group": {"_id": "$company", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    company_dist = await db.jobs.aggregate(company_pipeline).to_list(length=10)
    
    # Get location distribution
    location_pipeline = [
        {"$group": {"_id": "$location", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    location_dist = await db.jobs.aggregate(location_pipeline).to_list(length=10)
    
    return {
        "total_jobs": total,
        "active_jobs": active,
        "top_skills": skill_dist,
        "top_companies": company_dist,
        "top_locations": location_dist
    }
