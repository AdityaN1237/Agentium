"""
Candidates API Router.
Handles all candidate-related endpoints.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime
from bson import ObjectId

from app.database import Database
from app.models.candidate import (
    CandidateCreate, 
    CandidateListResponse
)
from app.services import get_embedding_service, get_skill_expander

# Constants for single-user mode
DEFAULT_USER_ID = "local_user"

router = APIRouter(prefix="/candidates", tags=["Candidates"])


@router.get("/", response_model=CandidateListResponse)
async def get_candidates(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    skill: Optional[str] = Query(None, description="Filter by skill"),
    search: Optional[str] = Query(None, description="Search by name or email")
):
    """
    Get paginated list of candidates.
    Supports filtering by skill and text search.
    """
    db = Database.get_db()
    
    # Build query filter
    query = {}
    
    if skill:
        # Use expanded skills for matching
        skill_expander = get_skill_expander()
        expanded = skill_expander.expand_skill(skill)
        query["$or"] = [
            {"skills": {"$in": list(expanded)}},
            {"expanded_skills": {"$in": list(expanded)}}
        ]
    
    if search:
        query["$or"] = query.get("$or", []) + [
            {"name": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}},
            {"current_role": {"$regex": search, "$options": "i"}}
        ]
    
    # Single-user mode: See all candidates or just own? 
    # Viewing all is better for a demo/admin dashboard feel.
    pass 
    
    # Get total count
    total = await db.candidates.count_documents(query)
    
    # Get paginated results
    skip = (page - 1) * page_size
    cursor = db.candidates.find(query).skip(skip).limit(page_size).sort("created_at", -1)
    candidates = await cursor.to_list(length=page_size)
    
    # Format response
    formatted_candidates = []
    for c in candidates:
        c["_id"] = str(c["_id"])
        formatted_candidates.append(c)
    
    return CandidateListResponse(
        total=total,
        page=page,
        page_size=page_size,
        candidates=formatted_candidates
    )


@router.get("/{candidate_id}")
async def get_candidate(candidate_id: str):
    """Get a single candidate by ID."""
    db = Database.get_db()
    
    try:
        candidate = await db.candidates.find_one({"_id": ObjectId(candidate_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid candidate ID format")
    
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    candidate["_id"] = str(candidate["_id"])
    
    # Remove embedding from response (too large)
    candidate.pop("resume_embedding", None)
    
    return candidate


@router.post("/", status_code=201)
async def create_candidate(candidate: CandidateCreate):
    """
    Create a new candidate.
    """
    db = Database.get_db()
    
    # Check if email already exists
    existing = await db.candidates.find_one({"email": candidate.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already exists")
    
    # Generate embedding
    embedding_service = get_embedding_service()
    skill_expander = get_skill_expander()
    
    candidate_dict = candidate.model_dump()
    candidate_dict["resume_embedding"] = embedding_service.encode_resume(candidate.resume_text)
    candidate_dict["expanded_skills"] = list(skill_expander.expand_skills(candidate.skills, depth=2))
    candidate_dict["created_at"] = datetime.utcnow()
    candidate_dict["updated_at"] = datetime.utcnow()
    candidate_dict["user_id"] = DEFAULT_USER_ID
    candidate_dict["manager_id"] = DEFAULT_USER_ID

    # Insert
    result = await db.candidates.insert_one(candidate_dict)
    
    return {
        "id": str(result.inserted_id),
        "message": "Candidate created successfully"
    }


@router.put("/{candidate_id}")
async def update_candidate(candidate_id: str, candidate: CandidateCreate):
    """Update an existing candidate."""
    db = Database.get_db()
    
    try:
        existing = await db.candidates.find_one({"_id": ObjectId(candidate_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid candidate ID format")
    
    if not existing:
        raise HTTPException(status_code=404, detail="Candidate not found")

    # Generate new embedding if resume changed
    embedding_service = get_embedding_service()
    skill_expander = get_skill_expander()
    
    update_dict = candidate.model_dump()
    update_dict["resume_embedding"] = embedding_service.encode_resume(candidate.resume_text)
    update_dict["expanded_skills"] = list(skill_expander.expand_skills(candidate.skills, depth=2))
    update_dict["updated_at"] = datetime.utcnow()
    
    await db.candidates.update_one(
        {"_id": ObjectId(candidate_id)},
        {"$set": update_dict}
    )
    
    return {"message": "Candidate updated successfully"}


@router.delete("/{candidate_id}")
async def delete_candidate(candidate_id: str):
    """Delete a candidate."""
    db = Database.get_db()
    
    try:
        result = await db.candidates.delete_one({"_id": ObjectId(candidate_id)})
        if result.deleted_count == 0:
             raise HTTPException(status_code=404, detail="Candidate not found")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid candidate ID format")

    return {"message": "Candidate deleted successfully"}


@router.get("/{candidate_id}/skills/expanded")
async def get_expanded_skills(candidate_id: str):
    """Get a candidate's expanded skills (including related skills)."""
    db = Database.get_db()
    
    try:
        candidate = await db.candidates.find_one({"_id": ObjectId(candidate_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid candidate ID format")
    
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    skill_expander = get_skill_expander()
    
    original_skills = candidate.get("skills", [])
    expanded_skills = list(skill_expander.expand_skills(original_skills, depth=2))
    
    return {
        "candidate_id": candidate_id,
        "original_skills": original_skills,
        "expanded_skills": expanded_skills,
        "total_original": len(original_skills),
        "total_expanded": len(expanded_skills)
    }


@router.get("/stats/summary")
async def get_candidates_stats():
    """Get candidate statistics."""
    db = Database.get_db()
    
    match_stage = {} 

    total = await db.candidates.count_documents(match_stage)
    
    # Get skill distribution
    pipeline = [
        {"$unwind": "$skills"},
        {"$group": {"_id": "$skills", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 20}
    ]
    skill_dist = await db.candidates.aggregate(pipeline).to_list(length=20)
    
    # Get experience distribution
    exp_pipeline = [
        {"$bucket": {
            "groupBy": "$experience_years",
            "boundaries": [0, 2, 5, 8, 12, 100],
            "default": "Other",
            "output": {"count": {"$sum": 1}}
        }}
    ]
    exp_dist = await db.candidates.aggregate(exp_pipeline).to_list(length=10)
    
    return {
        "total_candidates": total,
        "top_skills": skill_dist,
        "experience_distribution": exp_dist
    }
