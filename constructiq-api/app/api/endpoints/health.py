"""
Health check endpoints
"""

from datetime import datetime
from fastapi import APIRouter, Depends

from app.models.api import HealthResponse, APIInfo
from app.api.deps import get_vector_engine, get_permits_data
from app.services.vector_search import VectorSearchEngine
from app.core.config import settings

router = APIRouter()


@router.get("/healthz", response_model=HealthResponse)
async def health_check(
    vector_engine: VectorSearchEngine = Depends(get_vector_engine)
):
    """
    Health check endpoint
    
    Returns system health status and basic information
    """
    try:
        # Check vector engine status
        stats = await vector_engine.get_stats()
        
        return HealthResponse(
            ok=True,
            timestamp=datetime.now().isoformat(),
            version=settings.app_version,
            status=f"healthy - {stats['total_documents']} documents indexed"
        )
    except Exception as e:
        return HealthResponse(
            ok=False,
            timestamp=datetime.now().isoformat(),
            version=settings.app_version,
            status=f"unhealthy - {str(e)}"
        )


@router.get("/", response_model=APIInfo)
async def root(permits_data = Depends(get_permits_data)):
    """
    Root endpoint with API information
    """
    return APIInfo(
        message=settings.app_name,
        version=settings.app_version,
        endpoints={
            "search": "/search",
            "health": "/healthz", 
            "docs": "/docs",
            "openapi": "/openapi.json"
        },
        description=f"Semantic search for Austin construction permits using PostgreSQL pgvector. Currently indexing {len(permits_data)} permits."
    )
