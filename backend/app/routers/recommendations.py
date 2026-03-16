"""
Recommendations API Router.
Core endpoint for AI-powered job recommendations.
"""
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime
from bson import ObjectId

from app.database import Database
from app.services import get_recommendation_engine, get_skill_expander

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.get("/{candidate_id}")
async def get_recommendations_for_candidate(
    candidate_id: str,
    top_k: int = Query(10, ge=1, le=50, description="Number of recommendations")
):
    """
    Get personalized job recommendations for a candidate.
    
    Uses hybrid AI approach:
    - Semantic similarity (40%): Resume vs job description matching
    - Skill matching (35%): Including related skills from knowledge graph
    - Preference alignment (25%): Based on stated job preferences
    
    Example: A candidate with "Java" preference will receive Spring Boot,
    Microservices, and Java Backend roles.
    """
    try:
        engine = get_recommendation_engine()
        recommendations = await engine.recommend_jobs_for_candidate(candidate_id, top_k=top_k)
        return recommendations
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating recommendations: {str(e)}")


@router.get("/")
async def get_all_recommendations(
    top_k_per_candidate: int = Query(10, ge=1, le=20, description="Recommendations per candidate")
):
    """
    Get job recommendations for all candidates.
    Returns a list of recommendation responses for each candidate.
    """
    try:
        engine = get_recommendation_engine()
        all_recommendations = await engine.get_all_recommendations(top_k_per_candidate)
        
        return {
            "total_candidates": len(all_recommendations),
            "generated_at": datetime.utcnow(),
            "recommendations": all_recommendations
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating recommendations: {str(e)}")


@router.get("/{candidate_id}/explain/{job_id}")
async def explain_match(candidate_id: str, job_id: str):
    """
    Get detailed explanation of why a job matches a candidate.
    Useful for understanding the recommendation logic.
    """
    db = Database.get_db()
    
    # Get candidate
    try:
        candidate = await db.candidates.find_one({"_id": ObjectId(candidate_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid candidate ID format")
    
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    # Get job
    try:
        job = await db.jobs.find_one({"_id": ObjectId(job_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid job ID format")
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Get skill expander for detailed analysis
    skill_expander = get_skill_expander()
    
    # Expand candidate skills
    candidate_skills = candidate.get("skills", [])
    expanded_candidate_skills = list(skill_expander.expand_skills(candidate_skills, depth=2))
    
    # Get job skills
    job_skills = job.get("required_skills", [])
    
    # Calculate matches
    matched_direct = set(s.lower() for s in candidate_skills) & set(s.lower() for s in job_skills)
    matched_via_expansion = set(s.lower() for s in expanded_candidate_skills) & set(s.lower() for s in job_skills)
    matched_by_expansion = matched_via_expansion - matched_direct
    
    # Missing skills
    all_matched = matched_via_expansion
    missing = set(s.lower() for s in job_skills) - all_matched
    
    # Get recommendations to find the actual score
    engine = get_recommendation_engine()
    recommendations = await engine.recommend_jobs_for_candidate(candidate_id, top_k=100)
    
    job_recommendation = None
    for rec in recommendations.get("recommendations", []):
        if rec["job"]["_id"] == job_id:
            job_recommendation = rec
            break
    
    return {
        "candidate": {
            "id": candidate_id,
            "name": candidate.get("name"),
            "skills": candidate_skills,
            "preferences": candidate.get("preferences", []),
            "expanded_skills_count": len(expanded_candidate_skills)
        },
        "job": {
            "id": job_id,
            "title": job.get("title"),
            "company": job.get("company"),
            "required_skills": job_skills
        },
        "match_analysis": {
            "directly_matched_skills": list(matched_direct),
            "matched_via_skill_expansion": list(matched_by_expansion),
            "missing_skills": list(missing),
            "skill_coverage": f"{len(all_matched)}/{len(job_skills)} ({100*len(all_matched)/len(job_skills) if job_skills else 0:.1f}%)"
        },
        "scores": job_recommendation if job_recommendation else {
            "note": "This job was not in the top recommendations for this candidate"
        },
        "skill_expansion_examples": {
            skill: list(skill_expander.expand_skill(skill))[:5]
            for skill in candidate_skills[:3]
        }
    }


@router.post("/refresh-embeddings")
async def refresh_all_embeddings():
    """
    Refresh all embeddings in the database.
    Call this when you update the model or want to regenerate embeddings.
    """
    try:
        engine = get_recommendation_engine()
        await engine.refresh_embeddings()
        return {"message": "All embeddings refreshed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error refreshing embeddings: {str(e)}")


@router.get("/skills/expand/{skill_name}")
async def expand_skill(
    skill_name: str,
    depth: int = Query(1, ge=1, le=3, description="Expansion depth")
):
    """
    Expand a skill to see all related skills.
    Useful for understanding how skill matching works.
    
    Example: "Java" expands to include "Spring Boot", "Hibernate", etc.
    """
    skill_expander = get_skill_expander()
    
    expanded = list(skill_expander.expand_skill(skill_name, depth=depth))
    skill_info = skill_expander.get_skill_info(skill_name)
    
    return {
        "original_skill": skill_name,
        "expanded_skills": expanded,
        "total_expanded": len(expanded),
        "depth": depth,
        "skill_info": skill_info,
        "example_usage": f"A candidate with '{skill_name}' will match jobs requiring: {', '.join(expanded[:10])}"
    }


@router.get("/skills/categories")
async def get_skill_categories():
    """Get all skill categories from the knowledge graph."""
    skill_expander = get_skill_expander()
    categories = skill_expander.get_all_categories()
    
    result = {}
    for category in categories:
        skills = skill_expander.get_skills_by_category(category)
        if skills:
            result[category] = skills
    
    return {
        "total_categories": len(categories),
        "categories": result
    }


@router.get("/analyze/candidate/{candidate_id}")
async def analyze_candidate_for_recommendations(candidate_id: str):
    """
    Analyze a candidate's profile for recommendation potential.
    Shows how their skills and preferences translate to job matches.
    """
    db = Database.get_db()
    
    try:
        candidate = await db.candidates.find_one({"_id": ObjectId(candidate_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid candidate ID format")
    
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    skill_expander = get_skill_expander()
    
    skills = candidate.get("skills", [])
    preferences = candidate.get("preferences", [])
    
    # Expand skills and preferences
    expanded_skills = list(skill_expander.expand_skills(skills, depth=2))
    expanded_preferences = list(skill_expander.expand_skills(preferences, depth=2))
    
    # Get matching categories
    skill_categories = set()
    for skill in skills:
        info = skill_expander.get_skill_info(skill)
        if info:
            skill_categories.add(info.get("category", "General"))
    
    # Get recommendations
    engine = get_recommendation_engine()
    recommendations = await engine.recommend_jobs_for_candidate(candidate_id, top_k=5)
    top_matches = recommendations.get("recommendations", [])
    
    return {
        "candidate": {
            "id": candidate_id,
            "name": candidate.get("name"),
            "experience_years": candidate.get("experience_years"),
            "current_role": candidate.get("current_role")
        },
        "skills_analysis": {
            "original_skills": skills,
            "expanded_skill_count": len(expanded_skills),
            "skill_categories": list(skill_categories),
            "sample_expansions": {
                skill: list(skill_expander.expand_skill(skill))[:5]
                for skill in skills[:3]
            }
        },
        "preferences_analysis": {
            "stated_preferences": preferences,
            "expanded_preferences": expanded_preferences[:20]
        },
        "top_job_matches": [
            {
                "job_title": m["job"]["title"],
                "company": m["job"]["company"],
                "match_score": f"{m['match_score']*100:.1f}%",
                "matched_skills": m["matched_skills"][:5]
            }
            for m in top_matches
        ],
        "recommendation_summary": (
            f"Based on {len(skills)} skills that expand to {len(expanded_skills)} related skills, "
            f"this candidate matches best with {top_matches[0]['job']['title'] if top_matches else 'N/A'} roles."
        )
    }

from pydantic import BaseModel, Field

class RecommendationFeedback(BaseModel):
    """User feedback for a specific job recommendation."""
    candidate_id: str
    job_id: str
    feedback_type: str = Field(..., description="relevant, not_relevant, applied, viewed")
    comments: str = Field(None, description="Optional user comments")
    rating: int = Field(None, ge=1, le=5, description="1-5 star rating")


@router.post("/feedback")
async def submit_feedback(feedback: RecommendationFeedback):
    """
    Submit user feedback for a recommendation.
    Used for Continuous Learning and model improvement.
    """
    db = Database.get_db()
    
    feedback_doc = feedback.dict()
    feedback_doc["created_at"] = datetime.utcnow()
    
    try:
        await db.feedback.insert_one(feedback_doc)
        
        # If feedback is negative, we might want to trigger a re-training flag or log it
        if feedback.feedback_type == "not_relevant" or (feedback.rating and feedback.rating <= 2):
            # Log for analysis
            pass
            
        return {"message": "Feedback received", "id": str(feedback_doc.get("_id"))}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving feedback: {str(e)}")
