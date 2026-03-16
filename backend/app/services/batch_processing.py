"""
Batch Processing Service.
Handles batch processing of resumes from directories.
"""
import asyncio
import logging
from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime

from app.database import Database
from app.services.file_processing import extract_text_from_file
from app.services.training_manager import training_manager

logger = logging.getLogger(__name__)

# Default directory for uploads if not specified
DEFAULT_BATCH_DIR = Path(__file__).parent.parent.parent / "data" / "resumes"

class BatchProcessingService:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @staticmethod
    def _is_valid_file(filename: str) -> bool:
        return filename.lower().endswith(('.pdf', '.docx', '.txt'))

    async def scan_and_process(
            self, 
            directory: str, 
            agent_id: str = "batch_processor",
            user_id: str = "system"
    ) -> Dict[str, Any]:
        """
        Scans a directory for resumes and processes them in batch.
        Extracts text, skills, and creates candidate profiles.
        """
        scan_path = Path(directory)
        if not scan_path.exists():
            return {"status": "error", "message": f"Directory not found: {directory}"}
        
        # Start a training session for progress tracking
        session = training_manager.start_session(agent_id)
        session.add_log(f"📂 Scanning directory: {directory}", "INFO")
        
        files = [f for f in scan_path.iterdir() if f.is_file() and self._is_valid_file(f.name)]
        total = len(files)
        
        if total == 0:
            session.add_log("⚠️ No valid documents found in directory.", "WARNING")
            session.is_active = False
            return {"status": "warning", "message": "No files found"}

        session.add_log(f"🚀 Found {total} documents. Starting batch processing...", "INFO")
        
        # Run processing in background
        asyncio.create_task(self._process_batch(session, files, user_id))
        
        return {
            "status": "started", 
            "message": f"Batch processing started for {total} files",
            "agent_id": agent_id,
            "total_files": total
        }

    async def _process_batch(self, session, files: List[Path], user_id: str):
        processed = 0
        failed = 0
        
        db = Database.get_db()
        # Import here to avoid circular dependencies
        from app.services.embedding_service import get_embedding_service
        from app.services.skill_expander import get_skill_expander
        
        emb_service = get_embedding_service()
        skill_expander = get_skill_expander()
        
        for file_path in files:
            if session.should_stop:
                session.add_log("🛑 Batch processing stopped by user.", "WARNING")
                break
                
            try:
                # 1. Read File
                with open(file_path, "rb") as f:
                    content = f.read()
                
                # 2. Extract Text
                filename = file_path.name
                content_type = "application/pdf" if filename.endswith(".pdf") else "application/octet-stream"
                text = await asyncio.to_thread(extract_text_from_file, content, content_type, filename)
                
                if not text or len(text) < 50:
                    session.add_log(f"⚠️ Skipped {filename}: Insufficient text content", "WARNING")
                    failed += 1
                    continue

                # 3. Extract information (Simulated NLP extraction for now, will enhance later)
                # In a real scenario, this would call an LLM or specific extractor
                
                # 4. Generate Embedding for quick skill match
                resume_emb = await asyncio.to_thread(emb_service.encode_resume, text)
                
                # 5. Create Candidate Profile
                # Use filename as name alias for now
                name_guess = filename.rsplit('.', 1)[0].replace('_', ' ').replace('-', ' ').title()

                # Generate a unique placeholder email to avoid unique index violation
                unique_suffix = f"{datetime.utcnow().timestamp()}"
                placeholder_email = f"batch_{filename}_{unique_suffix}@placeholder.local"

                candidate_data = {
                    "user_id": f"batch_{filename}_{unique_suffix}",
                    "name": name_guess,
                    "email": placeholder_email,
                    "resume_text": text,
                    "resume_embedding": resume_emb,
                    "source": "batch_upload",
                    "file_path": str(file_path),
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                    # Placeholder skills until we run the full extractor
                    "skills": [], 
                    "processed_by": user_id
                }
                
                # Upsert by filename or some unique identifier
                # Ideally we check content hash, but filename + size proxy is okay for demo
                await db.candidates.update_one(
                    {"file_path": str(file_path)},
                    {"$set": candidate_data},
                    upsert=True
                )
                
                processed += 1
                if processed % 5 == 0:
                    session.add_log(f"✅ Processed {processed}/{len(files)}: {filename}", "DEBUG")
                    
            except Exception as e:
                session.add_log(f"❌ Failed to process {file_path.name}: {e}", "ERROR")
                failed += 1

        # Final Summary
        session.add_log(f"🏁 Batch complete. Processed: {processed}, Failed: {failed}", "SUCCESS")
        
        # Trigger re-indexing of skill/attributes if needed
        # We could auto-trigger the resume_screening agent here
        pass

# Singleton
_batch_service = BatchProcessingService()
def get_batch_service():
    return _batch_service
