from fastapi import APIRouter, HTTPException, UploadFile, File, Body, WebSocket, WebSocketDisconnect, BackgroundTasks, Form
from typing import List, Dict, Any, Optional
from app.agents.registry import registry
from app.services.training_manager import training_manager
from app.database import Database
from app.models.agent import AgentCreate, AgentUpdate, AgentResponse
import logging
import asyncio
import json
import csv
import io
import zipfile
import os
import tempfile
from pathlib import Path
from datetime import datetime
from app.services.extraction.extractor import DocumentExtractor
from app.services.skill_expander import get_skill_expander
import shutil
import re

router = APIRouter(prefix="/agents", tags=["Agents"])
documents_router = APIRouter(prefix="/documents", tags=["Documents"])
router.include_router(documents_router)
logger = logging.getLogger(__name__)

# --- CRUD Operations ---

@router.get("/types", response_model=List[str])
async def get_agent_types():
    """Get the list of available agent classes discovered by the registry."""
    try:
        return registry.get_types()
    except Exception as e:
        logger.error(f"Failed to fetch agent types: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while fetching agent types")

@router.get("/", response_model=List[Dict[str, Any]])
async def list_agents():
    """List all available AI agents from the active registry."""
    return registry.list_agents()

@router.post("/", response_model=AgentResponse)
async def create_agent(agent: AgentCreate):
    """Create a new agent configuration and activate it."""
    db = Database.get_db()
    
    # Check ID conflict in DB
    if await db.agents.find_one({"id": agent.id}):
         raise HTTPException(status_code=400, detail=f"Agent ID '{agent.id}' already exists.")
         
    new_agent_dict = agent.dict()
    new_agent_dict["created_at"] = datetime.utcnow()
    new_agent_dict["updated_at"] = datetime.utcnow()
    
    await db.agents.insert_one(new_agent_dict)
    
    # Instantiate in Registry
    try:
        registry.instantiate_from_db(new_agent_dict)
    except Exception as e:
        logger.error(f"Failed to activate new agent: {e}")
        
    return new_agent_dict

@router.get("/{agent_id}")
async def get_agent_info(agent_id: str):
    """Get metadata for a specific agent (Registry)."""
    try:
        agent = registry.get_agent(agent_id)
        return agent.get_info().dict()
    except ValueError:
        raise HTTPException(status_code=404, detail="Agent not found in active registry")

@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(agent_id: str, update_data: AgentUpdate):
    """Update an agent and synchronize instance."""
    db = Database.get_db()
    stored_agent = await db.agents.find_one({"id": agent_id})
    if not stored_agent:
        raise HTTPException(status_code=404, detail="Agent not found in database")
        
    # Filter None values
    update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
    update_dict["updated_at"] = datetime.utcnow()
    
    await db.agents.update_one({"id": agent_id}, {"$set": update_dict})
    
    # Re-sync Registry
    updated_record = await db.agents.find_one({"id": agent_id})
    try:
        # Re-instantiate (replaces old one in registry dict)
        registry.instantiate_from_db(updated_record)
    except Exception as e:
        logger.error(f"Failed to sync agent update to registry: {e}")
        
    if "_id" in updated_record: del updated_record["_id"]
    return updated_record

@router.delete("/{agent_id}")
async def delete_agent(agent_id: str):
    """Delete an agent from DB and Registry."""
    db = Database.get_db()
    
    # Delete from DB
    result = await db.agents.delete_one({"id": agent_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Agent not found")
        
    # Remove from Registry
    registry.remove_agent(agent_id)
    
    return {"message": "Agent deleted and decommissioned successfully"}


# --- Specific Agent Actions (Keep Existing) ---
# NOTE: These will currently only work for Registry agents unless we implement dynamic loading.

@router.get("/{agent_id}/metrics")
async def get_agent_metrics(agent_id: str):
    """Get live metrics for a specific agent."""
    try:
        agent = registry.get_agent(agent_id)
        return await agent.get_metrics()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to fetch metrics for {agent_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while fetching metrics")

@router.post("/{agent_id}/predict")
async def agent_predict(agent_id: str, payload: Dict[str, Any] = Body(...)):
    """Unified predict endpoint for all agents."""
    try:
        agent = registry.get_agent(agent_id)
        result = await agent.predict(payload or {})
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Inference failed for {agent_id}: {e}")
        raise HTTPException(status_code=500, detail="Agent inference failed")

@router.post("/{agent_id}/predict/file")
async def agent_predict_file(agent_id: str, file: UploadFile = File(...), config: str = Form("{}")):
    """File-based prediction helper for agents that accept ad-hoc documents (e.g., resume screening, job matching)."""
    try:
        try:
             config_dict = json.loads(config)
        except json.JSONDecodeError:
             raise HTTPException(status_code=400, detail="Invalid JSON in 'config' form field")

        agent = registry.get_agent(agent_id)
        
        # Create temp file for extraction
        fd, temp_path = tempfile.mkstemp(suffix=Path(file.filename).suffix)
        try:
            contents = await file.read()
            if not contents:
                raise HTTPException(status_code=400, detail="Uploaded file is empty")
                
            with os.fdopen(fd, 'wb') as tmp:
                tmp.write(contents)
            
            # Use Local Extractor
            extractor = DocumentExtractor(include_images=True, ocr_enabled=True)
            result = await extractor.extract(temp_path)
            
            if not result['success']:
                 logger.warning(f"Extraction failed for {file.filename}: {result.get('error')}")
                 raise HTTPException(status_code=400, detail=f"Extraction failed: {result.get('error')}")
            
            text = result.get("content", "")
            if isinstance(text, dict): text = json.dumps(text)
            
            if not text.strip():
                logger.warning(f"Text extraction result was empty for {file.filename}")
                raise HTTPException(status_code=400, detail="Unable to extract text from document (empty result)")
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
        # Standardize payload
        payload = {"resume_text": text, **(config_dict or {})}
        result = await agent.predict(payload)
        return result
    except ValueError as e:
        logger.warning(f"Validation error in predict/file: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"File-based inference failed for {agent_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"File-based agent inference failed: {str(e)}")

@router.get("/{agent_id}/protocol")
async def get_agent_protocol(agent_id: str):
    """Return standardized IO protocol and configuration for the agent."""
    try:
        agent = registry.get_agent(agent_id)
        from app.services.config_service import config_service
        cfg = config_service.get_config(agent_id)
        info = agent.get_info().dict()
        return {
            "agent": {
                "id": info["id"],
                "name": info["name"],
                "type": info.get("type"),
                "version": info.get("version"),
                "status": info.get("status")
            },
            "protocol": {
                "predict_input_examples": [
                    {"candidate_id": "mongodb_object_id", "top_k": 10},
                    {"resume_text": "raw resume text...", "top_k": 10}
                ],
                "file_predict_supported": True,
                "dataset_upload_supported": True
            },
            "config": cfg
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to fetch protocol for {agent_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while fetching protocol")

@router.websocket("/{agent_id}/training/ws")
async def training_ws(websocket: WebSocket, agent_id: str):
    """Live training log stream via WebSocket."""
    await websocket.accept()
    queue = None
    try:
        # Retry loop to wait for a session to start
        for _ in range(10):  # Wait up to 5 seconds
            queue = await training_manager.subscribe(agent_id)
            if queue:
                break
            await asyncio.sleep(0.5)

        if not queue:
            # Send a clear message if no session is active/found
            try:
                await websocket.send_json({
                    "timestamp": datetime.utcnow().isoformat(),
                    "message": "[SYSTEM] No active training session found. Waiting for trigger...",
                    "level": "SYSTEM"
                })
            except Exception:
                # Client already disconnected, ignore
                pass
            # Keep connection open but idle, or close. keeping open allows frontend to potentially receive later?
            # actually training_manager.subscribe only gets CURRENT session. 
            # If a new one starts, we need to re-subscribe.
            # For now, let's close to force frontend retry or handle gracefully.
            return

        while True:
            log = await queue.get()
            try:
                await websocket.send_json(log)
            except Exception:
                # Client disconnected during send, exit gracefully
                break
    except WebSocketDisconnect:
        pass
    except Exception as e:
        # Only log unexpected errors, not client disconnections
        error_msg = str(e).lower()
        if "disconnect" not in error_msg and "closed" not in error_msg and "going away" not in error_msg:
            logger.error(f"WebSocket error for agent {agent_id}: {e}", exc_info=True)
    finally:
        try:
            if queue:
                training_manager.unsubscribe(agent_id, queue)
        except Exception:
            pass

async def process_zip_background(file_path: str, agent_id: str):
    """Background task to process large ZIP files using Toronto Extraction Engine."""
    # Start a formal session so logs appear in UI
    session = training_manager.start_session(agent_id, "ingestion", {"source": "zip_upload"})
    session.add_log(f"📦 Starting ZIP processing: {file_path}", "INFO")
    
    db = Database.get_db()
    extractor = DocumentExtractor(include_images=True, ocr_enabled=True)
    
    # Create a temporary directory for extraction
    temp_extract_dir = tempfile.mkdtemp()
    
    try:
        agent = registry.get_agent(agent_id)
        info = agent.get_info().dict()
        agent_type = info.get("type")
        
        session.add_log(f"Agent Type identified: {agent_type}", "DEBUG")
        
        data = []
        file_count = 0
        
        # 1. Extract ZIP contents to temp dir
        session.add_log("Unzipping archive...", "INFO")
        try:
            with zipfile.ZipFile(file_path, 'r') as zf:
                zf.extractall(temp_extract_dir)
                file_names = [os.path.join(path, name) 
                             for path, subdirs, files in os.walk(temp_extract_dir) 
                             for name in files 
                             if not name.startswith('.') and not '__MACOSX' in path]
        except Exception as e:
             session.add_log(f"Failed to unzip file: {e}", "ERROR")
             training_manager.fail_session(agent_id, f"Unzip failed: {e}")
             return

        total_files = len(file_names)
        session.add_log(f"Found {total_files} files in archive.", "INFO")
        
        # 2. Process Files in Parallel
        # Sempahore for concurrency
        semaphore = asyncio.Semaphore(4) # Limit concurrent heavy extractions
        
        async def process_file(full_path: str):
            async with semaphore:
                try:
                    filename = os.path.basename(full_path)
                    
                    # Use DocumentExtractor (Async)
                    result = await extractor.extract(full_path)
                    
                    if not result['success']:
                        session.add_log(f"⚠️ Failed to process {filename}: {result.get('error')}", "WARNING")
                        return None
                        
                    text = result.get('content')
                    
                    # If dict check (ImageProcessor might return dict if we had Gemini, but now it returns text for Tesseract)
                    # Actually Tesseract returns text string.
                    if isinstance(text, dict):
                         text = json.dumps(text)
                    
                    if not text or not text.strip():
                        return None
                        
                    if agent_type == "rag_qa":
                        return {"text": text, "title": filename, "source": "zip_upload"}
                    else:
                        # Logic for Resume vs Job
                        t = text.lower()
                        job_terms = ["job description", "responsibilities", "requirements", "qualifications", "we are looking"]
                        cand_terms = ["experience", "education", "projects", "skills", "certifications", "profile"]
                        is_job = sum(1 for term in job_terms if term in t) >= sum(1 for term in cand_terms if term in t)
                        
                        if is_job:
                            return {"title": filename, "required_skills": [], "description": text}
                        else:
                            uid = f"zip_{filename}_{datetime.utcnow().timestamp()}"
                            return {
                                "name": filename.rsplit('.', 1)[0].replace('_', ' ').replace('-', ' ').title(),
                                "skills": [],
                                "resume_text": text,
                                "user_id": uid,
                                "email": f"no-email-{uid}@placeholder.com"
                            }
                except Exception as e:
                    logger.warning(f"Error processing {full_path}: {e}")
                    return None

        # Process in batches
        batch_size = 10
        for i in range(0, total_files, batch_size):
            batch = file_names[i:i + batch_size]
            tasks = [process_file(f) for f in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for res in results:
                file_count += 1
                if isinstance(res, dict): # Valid data
                    data.append(res)
            
            # Progress log
            session.add_log(f"Processing... {min(i + batch_size, total_files)}/{total_files} files processed. ({len(data)} valid)", "INFO")

        if data:
            session.add_log(f"📤 Uploading {len(data)} records to Agent...", "INFO")
            await agent.upload_dataset(data)
            session.add_log("✅ Dataset ingestion complete.", "SUCCESS")
        else:
            session.add_log("⚠️ No valid data extracted from archive.", "WARNING")

        training_manager.complete_session(agent_id, {"processed_files": total_files, "valid_records": len(data)})

    except Exception as e:
        session.add_log(f"❌ ZIP Processing Failed: {e}", "ERROR")
        training_manager.fail_session(agent_id, str(e))
    finally:
        # Cleanup
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except: pass
        if os.path.exists(temp_extract_dir):
            try:
                shutil.rmtree(temp_extract_dir)
            except: pass
        
        logger.info(f"Cleanup complete for session {session.run_id}")
        await training_manager.persist_run(session)

@router.post("/{agent_id}/upload")
async def upload_dataset(agent_id: str, background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Upload a dataset for a specific agent."""
    try:
        agent = registry.get_agent(agent_id)
        
        contents = await file.read()
        filename = file.filename.lower()
        file_size_mb = len(contents) / (1024 * 1024)
        logger.info(f"Received upload for {agent_id}: Filename={file.filename}, Content-Type={file.content_type}, Size={file_size_mb:.2f} MB")

        if not contents:
             raise HTTPException(status_code=400, detail=f"Uploaded file '{file.filename}' is empty.")

        # Size limit for uploads (500MB)
        if file_size_mb > 500:
            raise HTTPException(status_code=413, detail=f"File too large: {file_size_mb:.2f} MB. Maximum allowed: 500 MB.")

        data = []
        
        def _extract_skills_from_text(text: str) -> List[str]:
            try:
                skill_expander = get_skill_expander()
                taxonomy = list(getattr(skill_expander, "_taxonomy", {}).keys()) if getattr(skill_expander, "_taxonomy", None) else []
            except Exception:
                taxonomy = []
            if not taxonomy or not text:
                return []
            lower = text.lower()
            skills = [s for s in taxonomy if s in lower]
            return list(set(skills))
        
        def _detect_is_job(text: str) -> bool:
            t = text.lower()
            job_terms = ["job description", "responsibilities", "requirements", "qualifications", "we are looking", "position", "role", "job title"]
            cand_terms = ["summary", "experience", "education", "projects", "skills", "certifications", "profile", "resume"]
            score_job = sum(1 for term in job_terms if term in t)
            score_cand = sum(1 for term in cand_terms if term in t)
            return score_job >= score_cand
        
        def _extract_title(text: str) -> str:
            lines = [l.strip() for l in text.splitlines() if l.strip()]
            for l in lines[:20]:
                m = re.match(r"(job title|title)\s*[:\-]\s*(.+)", l, re.IGNORECASE)
                if m:
                    return m.group(2)[:200]
            for l in lines[:5]:
                if len(l.split()) <= 12 and l == l.upper():
                    return l[:200]
            return (lines[0] if lines else "")[:200]
        
        def _extract_name_from_filename(name: str) -> str:
            base = name.rsplit('.', 1)[0]
            return re.sub(r"[_\-]+", " ", base).title()
        
        def _map_text_to_schema(text: str, name: str) -> Dict[str, Any]:
            if _detect_is_job(text):
                title = _extract_title(text) or _extract_name_from_filename(name)
                skills = _extract_skills_from_text(text)
                return {"title": title, "required_skills": skills or [], "description": text, "is_active": True}
            else:
                skills = _extract_skills_from_text(text)
                
                # Attempt to extract real name from Resume text (First line heuristic)
                candidate_name = _extract_name_from_filename(name)
                first_line = text.strip().splitlines()[0].strip()
                # If first line is short and title-like, use it instead of filename (which might be a hash/ID)
                if first_line and len(first_line) < 50 and len(first_line.split()) < 6:
                     # Remove common stopwords often found at top
                     if "resume" not in first_line.lower() and "curriculum" not in first_line.lower():
                         candidate_name = first_line.title()

                uid = f"upload_{name}_{datetime.utcnow().timestamp()}"
                return {
                    "name": candidate_name,
                    "skills": skills or [],
                    "resume_text": text,
                    "filename": name,
                    "user_id": uid,
                    "email": f"no-email-{uid}@placeholder.com"
                }
        
        if filename.endswith('.zip') or file.content_type == 'application/zip':
            # Create Temp File
            fd, temp_path = tempfile.mkstemp(suffix=".zip")
            with os.fdopen(fd, 'wb') as tmp:
                tmp.write(contents)
            
            # Offload to Background
            background_tasks.add_task(process_zip_background, temp_path, agent_id)
            
            return {
                "status": "processing", 
                "message": "Large ZIP accepted. Processing started in background to prevent timeout. Check logs for progress.",
                "file_size_mb": round(len(contents) / (1024*1024), 2)
            }
        elif filename.endswith('.csv') or file.content_type == 'text/csv':
            try:
                # Decode bytes to string
                text_content = contents.decode('utf-8')
                # Parse CSV
                csv_reader = csv.DictReader(io.StringIO(text_content))
                data = list(csv_reader)
            except Exception as e:
                logger.error(f"CSV Parse Error: {e}")
                raise HTTPException(status_code=400, detail=f"Invalid CSV in '{file.filename}'. Error: {str(e)}")
        
        # Handle ZIP Archives (Bulk Upload)
        elif filename.endswith('.zip') or file.content_type == 'application/zip':
            def process_zip_sync(zip_bytes: bytes) -> List[Dict[str, Any]]:
                """CPU-bound ZIP processing to be run in thread."""
                extracted_data = []
                try:
                    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
                        for zfilename in z.namelist():
                            if zfilename.startswith("__MACOSX") or zfilename.startswith("."):
                                continue
                            
                            with z.open(zfilename) as zf:
                                
                                # Nested JSON
                                if zfilename.endswith(".json"):
                                    try:
                                        z_bytes_content = zf.read()
                                        json_data = json.loads(z_bytes_content)
                                        if isinstance(json_data, list):
                                            extracted_data.extend(json_data)
                                        elif isinstance(json_data, dict):
                                            extracted_data.append(json_data)
                                    except: pass
                                    
                                # Nested CSV
                                elif zfilename.endswith(".csv"):
                                    try:
                                        z_bytes_content = zf.read()
                                        csv_text = z_bytes_content.decode('utf-8')
                                        extracted_data.extend(list(csv.DictReader(io.StringIO(csv_text))))
                                    except: pass
                                    
                                # Nested Documents (PDF/DOCX/TXT) -> Treat as Resume/Candidate
                                elif zfilename.lower().endswith(('.pdf', '.docx', '.txt')):
                                    try:
                                        z_bytes_content = zf.read()
                                        # extract_text_from_file is synchronous, safe here
                                        ext_text = extract_text_from_file(z_bytes_content, "", zfilename)
                                        if ext_text.strip():
                                            # Use the schema mapper to detect Job vs Candidate and extract Name/Skills
                                            record = _map_text_to_schema(ext_text, zfilename)
                                            record["source"] = f"zip/{zfilename}"
                                            extracted_data.append(record)
                                    except: pass
                except Exception as e:
                    logger.error(f"Error inside ZIP processing thread: {e}")
                    raise e
                return extracted_data

            try:
                # Offload the ENTIRE zip processing to a thread
                data = await asyncio.to_thread(process_zip_sync, contents)
                
                if not data:
                     raise HTTPException(status_code=400, detail="ZIP archive contained no valid files (JSON, CSV, PDF, DOCX).")
                     
            except zipfile.BadZipFile:
                 raise HTTPException(status_code=400, detail="Invalid ZIP file.")
            except Exception as e:
                logger.error(f"ZIP Processing Error: {e}")
                raise HTTPException(status_code=400, detail=f"Failed to process ZIP: {str(e)}")

        # Handle Single PDF/DOCX/TXT
        elif filename.endswith('.pdf') or filename.endswith('.docx') or filename.endswith('.txt'):
            try:
                # Create temp file
                fd, temp_path = tempfile.mkstemp(suffix=Path(filename).suffix)
                try:
                    with os.fdopen(fd, 'wb') as tmp:
                        tmp.write(contents)
                        
                    extractor = DocumentExtractor(include_images=True, ocr_enabled=True)
                    result = await extractor.extract(temp_path)
                    
                    if not result['success']:
                         raise HTTPException(status_code=400, detail=f"Extraction failed: {result.get('error')}")
                         
                    text = result.get('content', "")
                    if isinstance(text, dict): text = json.dumps(text)
                finally:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                
                if not text or not text.strip():
                     raise HTTPException(status_code=400, detail=f"Could not extract text from '{filename}'. File might be empty or scanned image.")
                
                if agent.metadata.type == "rag_qa":
                    data = [{"text": text, "title": filename, "source": "upload"}]
                else:
                    # Treat single doc as resume for skill matching
                    data = [{
                        "name": Path(filename).stem,
                        "resume_text": text,
                        "skills": [],
                        "source": "upload"
                    }]
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Text Extraction Error: {e}")
                raise HTTPException(status_code=400, detail=f"Failed to process document '{filename}': {str(e)}")

        # JSON Parsing (Default Fallback)
        else:
            try:
                data = json.loads(contents)
            except json.JSONDecodeError as e:
                logger.error(f"JSON Parse Error: {e}")
                preview = contents[:50].decode('utf-8', errors='ignore') if contents else ""
                raise HTTPException(status_code=400, detail=f"Invalid or Unsupported File Format '{file.filename}'. Expected JSON or CSV. Parser error: {str(e)}. Preview: {preview}")
            
        if not isinstance(data, list):
            # If it's a dict, maybe wrap it or check for a key like "candidates"
            if isinstance(data, dict):
                if "candidates" in data:
                    data = data["candidates"]
                elif "jobs" in data:
                    data = data["jobs"]
                else:
                    data = [data] # Treat as single record
            else:
                 raise HTTPException(status_code=400, detail=f"Dataset must be a list of records. Received type: {type(data).__name__}")

        return await agent.upload_dataset(data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@documents_router.post("/upload")
async def upload_document(file: UploadFile = File(...), config: Dict[str, Any] = Body({})):
    db = Database.get_db()
    agent = registry.get_agent("rag_qa")
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")
    
    # Create temp file
    fd, temp_path = tempfile.mkstemp(suffix=Path(file.filename).suffix)
    try:
        with os.fdopen(fd, 'wb') as tmp:
            tmp.write(contents)
            
        extractor = DocumentExtractor(include_images=True, ocr_enabled=True)
        result = await extractor.extract(temp_path)
        
        if not result['success']:
             raise HTTPException(status_code=400, detail=f"Extraction failed: {result.get('error')}")
             
        text = result.get('content', "")
        if isinstance(text, dict): text = json.dumps(text)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
    if not text.strip():
        raise HTTPException(status_code=400, detail="Unable to extract text from document")
    doc = {
        "text": text,
        "title": file.filename,
        "tags": [],
        "source": "upload",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    existing = await db.documents.find_one({"title": file.filename})
    if existing:
        await db.documents.update_one({"_id": existing["_id"]}, {"$set": doc})
        doc["_id"] = existing["_id"]
    else:
        res = await db.documents.insert_one(doc)
        doc["_id"] = res.inserted_id
    result = await agent.incremental_index(doc, config or {})
    return {"status": "accepted", "message": "Document ingested; incremental indexing started", "agent_response": result, "doc_id": str(doc["_id"])}

@documents_router.post("/retrain")
async def retrain_document(body: Dict[str, Any] = Body(...)):
    db = Database.get_db()
    agent = registry.get_agent("rag_qa")
    doc_id = body.get("doc_id")
    if not doc_id:
        raise HTTPException(status_code=400, detail="doc_id is required")
    try:
        from bson import ObjectId
        oid = ObjectId(doc_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid doc_id")
    doc = await db.documents.find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    result = await agent.incremental_index(doc, body.get("config") or {})
    return {"status": "accepted", "message": "Incremental retraining started", "agent_response": result}

@documents_router.post("/ask")
async def ask_question(body: Dict[str, Any] = Body(...)):
    agent = registry.get_agent("rag_qa")
    return await agent.predict(body or {})

 


@router.get("/{agent_id}/metrics")
async def get_agent_metrics(agent_id: str):
    """Get live metrics for a specific agent."""
    try:
        agent = registry.get_agent(agent_id)
        info = agent.get_info()
        return info.metrics or {}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to fetch metrics for {agent_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while fetching metrics")

@router.post("/{agent_id}/train")
async def train_agent(agent_id: str, config: Dict[str, Any] = Body({})):
    """Trigger the Enterprise Training Pipeline."""
    try:
        agent = registry.get_agent(agent_id)
        return await agent.train(config)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{agent_id}/stop")
async def stop_training(agent_id: str):
    """Stop the currently running training sequence."""
    try:
        agent = registry.get_agent(agent_id)
        return await agent.stop_training()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
