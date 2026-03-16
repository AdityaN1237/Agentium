from fastapi import APIRouter, UploadFile, File, HTTPException, Body
from typing import Dict, Any
from datetime import datetime
from pathlib import Path

from app.database import Database
from app.models.resume import ResumeInDB, ResumeUploadResponse
from app.services import get_skill_expander, get_embedding_service
from app.services.training_manager import training_manager
from app.services.file_processing import extract_text_from_file

router = APIRouter(prefix="/resumes", tags=["Resumes"])

DEFAULT_USER_ID = "local_user"

def _extract_structured_info(text: str) -> Dict[str, Any]:
    """
    Extract structured information from resume text using semantic matching.
    Uses embeddings to find skills that match the taxonomy.
    """
    skill_expander = get_skill_expander()
    embedding_service = get_embedding_service()
    
    # 1. Get Taxonomy
    taxonomy_skills = []
    try:
        taxonomy_skills = list(skill_expander._taxonomy.keys()) if getattr(skill_expander, "_taxonomy", None) else []
    except Exception:
        taxonomy_skills = []
        
    if not text or not taxonomy_skills:
        return {"extracted_skills": [], "current_role": None, "experience_years": 0}

    # 2. Semantic Skill Extraction
    extracted_skills = []
    try:
        # Generate embedding for the resume text
        # chunking if necessary (using first 5000 chars significantly speeds this up for matching)
        text_chunk = text[:5000]
        resume_emb = embedding_service.encode_single(text_chunk)
        
        # Batch compare against skills (optimize by caching skill embeddings in production)
        # For now, we sample or use a pre-computed list if available
        # Real-world optimization: Pre-compute skill embeddings on startup
        
        # Heuristic: Check for exact matches first (fast)
        normalized_text = text.lower()
        exact_matches = [s for s in taxonomy_skills if s.lower() in normalized_text]
        extracted_skills.extend(exact_matches)
        
        # Semantic Match for implicit skills
        # We only run semantics on skills NOT found exactly to save compute
        candidates = [s for s in taxonomy_skills if s not in exact_matches]
        if candidates and resume_emb:
            # Limit to top 200 most likely skills based on simple keyword overlap first? 
            # Or just do batch cos sim on all (might be slow if > 10k skills)
            # For this demo, we'll take a random sample or first 500 to show capability
            sample_candidates = candidates[:500] 
            
            cand_embs = embedding_service.encode_skills(sample_candidates)
            import numpy as np
            scores = embedding_service.batch_cosine_similarity(np.array(resume_emb), np.array(cand_embs))
            
            # Threshold 0.45 for semantic relevance
            for idx, score in enumerate(scores):
                if score > 0.45:
                    extracted_skills.append(sample_candidates[idx])
                    
    except Exception as e:
        print(f"Error in skill extraction: {e}")

    # 3. Role Extraction (Simple Semantic Match)
    current_role = None
    try:
        role_candidates = skill_expander.get_skills_by_category("Role") or ["Software Engineer", "Data Scientist", "Product Manager"]
        if role_candidates:
            role_embs = embedding_service.encode_skills(role_candidates)
            # Use beginning of resume for role
            header_emb = embedding_service.encode_single(text[:300]) 
            import numpy as np
            role_scores = embedding_service.batch_cosine_similarity(np.array(header_emb), np.array(role_embs))
            best_idx = int(np.argmax(role_scores))
            if role_scores[best_idx] > 0.4:
                current_role = role_candidates[best_idx]
    except Exception:
        pass

    # 4. Experience Extraction (Regex for now, hard to do purely semantically without LLM)
    experience_years = 0
    import re
    years_pattern = r"(\d+)\+?\s*years? of experience"
    match = re.search(years_pattern, text, re.IGNORECASE)
    if match:
        try:
            experience_years = int(match.group(1))
        except:
            pass

    # 5. Preferences Extraction (Infer from role and skills)
    preferences = []
    if current_role:
        preferences.append(current_role)
        # Add related roles based on skills
        if "python" in [s.lower() for s in extracted_skills]:
            if "data" in text.lower() or "machine learning" in [s.lower() for s in extracted_skills]:
                preferences.extend(["Data Scientist", "ML Engineer"])
            else:
                preferences.extend(["Backend Developer", "Full Stack Developer"])
        if "react" in [s.lower() for s in extracted_skills] or "javascript" in [s.lower() for s in extracted_skills]:
            preferences.extend(["Frontend Developer", "Full Stack Developer"])
        if "java" in [s.lower() for s in extracted_skills]:
            preferences.extend(["Backend Developer", "Full Stack Developer"])
    preferences = list(set(preferences))  # Remove duplicates

    return {
        "extracted_skills": list(set(extracted_skills)),
        "current_role": current_role,
        "experience_years": experience_years,
        "preferences": preferences
    }


@router.post("/upload", response_model=ResumeUploadResponse)
async def upload_resume(file: UploadFile = File(...)):
    db = Database.get_db()
    # Aligning with the registry ID for the Resume Screening Agent
    agent_id = "resume_screening"
    session = training_manager.start_session(agent_id)
    session.add_log(f"🚀 Starting real-time analysis for resume: {file.filename}", "INFO")

    user_id = DEFAULT_USER_ID

    try:
        contents = await file.read()
        if not contents:
            session.add_log("❌ Uploaded file is empty.", "ERROR")
            session.is_active = False
            raise HTTPException(status_code=400, detail="Uploaded file is empty")

        uploads_dir = Path(__file__).parent.parent / "data" / "uploads" / user_id
        uploads_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{file.filename}"
        file_path = uploads_dir / filename
        try:
            with open(file_path, "wb") as f:
                f.write(contents)
            session.add_log(f"✅ File stored securely at {filename}", "INFO")
        except Exception:
            session.add_log("❌ Failed to store file.", "ERROR")
            raise HTTPException(status_code=500, detail="Failed to store uploaded file")

        resume_text = extract_text_from_file(contents, file.content_type or "", file.filename)
        session.add_log(f"📄 Text extraction complete. Length: {len(resume_text)} chars.", "INFO")

        # Validate extracted text
        if not resume_text or len(resume_text.strip()) < 50:
            session.add_log("❌ No meaningful text extracted from file. Please upload a valid resume document.", "ERROR")
            session.is_active = False
            raise HTTPException(status_code=400, detail="No meaningful text could be extracted from the uploaded file. Please ensure the file contains readable text content.")

        structured = _extract_structured_info(resume_text)

        resume_record = ResumeInDB(
            user_id=user_id,
            filename=file.filename,
            content_type=file.content_type or "application/octet-stream",
            file_path=str(file_path),
            resume_text=resume_text,
            extracted_skills=structured["extracted_skills"],
            current_role=structured["current_role"],
            experience_years=structured["experience_years"],
        ).model_dump(by_alias=True)

        session.add_log(f"🧠 Skills extracted: {', '.join(structured['extracted_skills'][:5])}...", "INFO")
        result = await db.resumes.insert_one(resume_record)

        embedding_service = get_embedding_service()
        skill_expander = get_skill_expander()
        session.add_log("🔢 Generating embeddings and expanding skills...", "INFO")

        candidate_dict = {
            "name": "Local User",
            "email": "local@antigravity.dev",
            "current_role": structured["current_role"],
            "experience_years": structured["experience_years"],
            "skills": structured["extracted_skills"],
            "preferences": structured.get("preferences", []),
            "resume_text": resume_text,
            "resume_embedding": embedding_service.encode_resume(resume_text) if resume_text else None,
            "expanded_skills": list(skill_expander.expand_skills(structured["extracted_skills"], depth=2)) if structured["extracted_skills"] else [],
            "user_id": user_id,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        existing_candidate = await db.candidates.find_one({"user_id": user_id})
        candidate_id = None
        if existing_candidate:
            await db.candidates.update_one({"_id": existing_candidate["_id"]}, {"$set": candidate_dict})
            candidate_id = str(existing_candidate["_id"])
            session.add_log("🔄 Existing candidate profile updated with new data.", "SUCCESS")
        else:
            cand_res = await db.candidates.insert_one(candidate_dict)
            candidate_id = str(cand_res.inserted_id)
            session.add_log("✨ New candidate profile created.", "SUCCESS")

        session.is_active = False
        return ResumeUploadResponse(
            resume_id=str(result.inserted_id),
            candidate_id=candidate_id,
            message="Resume uploaded and profile updated"
        )
    except Exception as e:
        session.add_log(f"❌ Error processing resume: {str(e)}", "ERROR")
        session.is_active = False
        raise e

@router.post("/retrain")
async def retrain_resume():
    db = Database.get_db()
    agent_id = "resume_screening"
    session = training_manager.start_session(agent_id)
    session.add_log("🚀 Starting manual retraining for candidate profile...", "INFO")

    user_id = DEFAULT_USER_ID

    from app.services import get_embedding_service, get_skill_expander
    emb = get_embedding_service()
    exp = get_skill_expander()
    cand = await db.candidates.find_one({"user_id": user_id})
    if not cand:
        session.add_log("❌ Candidate profile not found.", "ERROR")
        session.is_active = False
        raise HTTPException(status_code=404, detail="Candidate profile not found")
    skills = cand.get("skills", [])
    resume_text = cand.get("resume_text", "")
    
    session.add_log("🔄 Refreshing embeddings and skill expansion...", "INFO")
    expanded = list(exp.expand_skills(skills, depth=2)) if skills else []
    resume_embedding = emb.encode_resume(resume_text) if resume_text else None
    await db.candidates.update_one({"_id": cand["_id"]}, {"$set": {
        "expanded_skills": expanded,
        "resume_embedding": resume_embedding,
        "updated_at": datetime.utcnow()
    }})
    
    session.add_log("✅ Candidate embeddings refreshed.", "SUCCESS")
    session.is_active = False
    return {"status": "updated", "message": "Candidate embeddings refreshed"}


@router.get("/me")
async def my_resume():
    db = Database.get_db()
    user_id = DEFAULT_USER_ID
    resume = await db.resumes.find_one({"user_id": user_id}, sort=[("created_at", -1)])
    if not resume:
        return {"message": "No resume uploaded yet"}
    resume["_id"] = str(resume["_id"])
    return resume


@router.get("/")
async def list_resumes(page: int = 1, page_size: int = 20):
    db = Database.get_db()
    # Show all resumes in single-user mode
    query = {}
    total = await db.resumes.count_documents(query)
    skip = (page - 1) * page_size
    cursor = db.resumes.find(query).skip(skip).limit(page_size).sort("created_at", -1)
    items = await cursor.to_list(length=page_size)
    for r in items:
        r["_id"] = str(r["_id"])
    return {"total": total, "page": page, "page_size": page_size, "resumes": items}

@router.get("/recommend/{user_id}")
async def recommend_for_user(user_id: str, top_k: int = 10):
    db = Database.get_db()
    # Allow any recommendation request
    cand = await db.candidates.find_one({"user_id": user_id})
    if not cand:
        # Fallback to demo user if requested
        if user_id == DEFAULT_USER_ID:
            # Maybe create one? For now just 404
             raise HTTPException(status_code=404, detail="Candidate not found")
        raise HTTPException(status_code=404, detail="Candidate not found")

    from app.services.recommendation_engine import RecommendationEngine
    engine = RecommendationEngine()
    
    return await engine.recommend_jobs_for_candidate(str(cand["_id"]), top_k=top_k)


@router.post("/batch")
async def batch_process_resumes(
    directory: str = Body(..., embed=True)
):
    """
    Trigger batch processing of resumes from a server-side directory.
    """
    from app.services.batch_processing import get_batch_service
    service = get_batch_service()
    
    result = await service.scan_and_process(directory, user_id=DEFAULT_USER_ID)
    return result
