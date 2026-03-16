"""
AI-Powered Job Recommendation System
Main FastAPI Application Entry Point

This system uses advanced AI techniques for job matching:
- Sentence Transformers for semantic embeddings
- Skill Knowledge Graph for technology relationships
- Hybrid multi-factor scoring system
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import sys
import time

from app.config import settings
from app.database import Database
from app.routers import (
    candidates_router,
    jobs_router,
    recommendations_router,
    agents_router
)
from app.routers.analytics import router as analytics_router
from app.routers.resumes import router as resumes_router
from app.routers.configs import router as configs_router
from app.routers.inference_chat import router as chat_router
from app.services.config_service import config_service

# Simple in-memory cache for stats
_stats_cache = {}
_STATS_CACHE_TTL = 30  # 30 seconds TTL

def _get_cached_stats():
    """Get cached stats if still valid, otherwise return None."""
    now = time.time()
    if 'data' in _stats_cache and 'timestamp' in _stats_cache:
        if now - _stats_cache['timestamp'] < _STATS_CACHE_TTL:
            return _stats_cache['data']
    return None

def _set_cached_stats(data):
    """Cache the stats data with current timestamp."""
    _stats_cache['data'] = data
    _stats_cache['timestamp'] = time.time()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    Manages database connections and model loading.
    """
    # Startup
    logger.info("Starting AI Job Recommendation System...")
    
    # Connect to MongoDB
    await Database.connect()
    db = Database.get_db()

    # Load all agent configurations into memory
    await config_service.load_all_configs()

    # Load persistent skill taxonomy
    from app.services.skill_expander import get_skill_expander
    await get_skill_expander().load_taxonomy()

    # Dynamic Agent Initialization
    from app.agents.registry import registry
    await registry.initialize(db)
    
    yield
    
    # Shutdown
    logger.info("🔌 Shutting down...")
    await Database.disconnect()
    logger.info("👋 Goodbye!")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
# AI-Powered Job Recommendation System

## Overview
This system provides intelligent job recommendations for candidates using advanced AI techniques:

### Features
- **Semantic Matching**: Uses Sentence Transformers to understand the meaning of resumes and job descriptions
- **Skill Knowledge Graph**: Automatically expands skills (e.g., "Java" → "Spring Boot", "Hibernate")
- **Hybrid Scoring**: Combines semantic similarity, skill matching, and preference alignment

### How it Works
1. **Resume Embedding**: Each resume is converted to a 384-dimensional vector
2. **Job Embedding**: Each job description gets its own vector
3. **Skill Expansion**: Skills are expanded using a knowledge graph (Java includes Spring Boot, etc.)
4. **Multi-factor Scoring**:
   - 40% Semantic Similarity (resume vs job description)
   - 35% Skill Match (including expanded skills)
   - 25% Preference Alignment

### Example
A candidate with preference "Java" will match:
- ✅ Senior Java Backend Developer
- ✅ Spring Boot Engineer  
- ✅ Java Microservices Developer
- ✅ Full Stack Java Developer
""",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(candidates_router)
app.include_router(jobs_router)
app.include_router(recommendations_router)
app.include_router(agents_router)
app.include_router(analytics_router)
app.include_router(resumes_router)
app.include_router(configs_router)
app.include_router(chat_router)

# Global Exception Handler Middleware

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"❌ Global Exception Blocked: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "A critical system error occurred. Our engineers have been notified.",
            "detail": str(exc) if settings.DEBUG else "Hidden in production"
        }
    )


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - API health check."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "healthy",
        "message": "Welcome to the AI-Powered Job Recommendation System!",
        "docs": "/docs",
        "endpoints": {
            "candidates": "/candidates",
            "jobs": "/jobs",
            "recommendations": "/recommendations"
        }
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check endpoint."""
    db_status = "healthy"
    
    try:
        db = Database.get_db()
        await db.candidates.count_documents({})
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "components": {
            "database": db_status,
            "api": "healthy"
        }
    }


@app.get("/stats", tags=["Health"])
async def get_system_stats():
    """Get system statistics with caching to reduce database load."""
    # Check cache first
    cached_stats = _get_cached_stats()
    if cached_stats is not None:
        return cached_stats

    # Cache miss - fetch fresh data
    from app.services.training_manager import training_manager
    from app.agents.registry import registry

    db = Database.get_db()

    candidates_count = await db.candidates.count_documents({})
    jobs_count = await db.jobs.count_documents({})
    active_jobs = await db.jobs.count_documents({"is_active": True})

    # Real-time System Metrics
    active_training_sessions = sum(1 for s in training_manager.sessions.values() if s.is_active)
    active_agents = len(registry.list_agents())
    total_vectors = candidates_count + jobs_count # Proxy for total embeddings

    # Try to count recommendations if collection exists
    try:
        global_queries = await db.recommendations.count_documents({})
    except:
        global_queries = 0

    stats_data = {
        "candidates": candidates_count,
        "jobs": {
            "total": jobs_count,
            "active": active_jobs
        },
        "system": {
             "active_agents": active_agents,
             "training_active": active_training_sessions,
             "total_vectors": total_vectors,
             "global_queries": global_queries,
             "health_score": 100.0
        },
        "ai_config": {
            "embedding_model": settings.EMBEDDING_MODEL,
            "embedding_dimension": settings.EMBEDDING_DIMENSION,
            "weights": {
                "semantic": settings.SEMANTIC_WEIGHT,
                "skill_match": settings.SKILL_MATCH_WEIGHT,
                "preference": settings.PREFERENCE_WEIGHT
            }
        }
    }

    # Cache the result
    _set_cached_stats(stats_data)

    return stats_data


@app.get("/models/status", tags=["Models"])
async def get_models_status():
    """Get status of all saved model artifacts."""
    from app.services.model_persistence import get_model_persistence
    
    persistence = get_model_persistence()
    models = persistence.list_all_models()
    
    return {
        "models": models,
        "total_models": len(models),
        "storage_path": str(persistence.get_agent_dir("").parent)
    }


@app.get("/models/{agent_id}/status", tags=["Models"])
async def get_agent_model_status(agent_id: str):
    """Get model status for a specific agent."""
    from app.services.model_persistence import get_model_persistence
    
    persistence = get_model_persistence()
    status = persistence.get_model_status(agent_id)
    
    return status
