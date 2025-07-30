"""
API dependencies
"""

from typing import Dict, List, Any
from fastapi import HTTPException

from app.services.vector_search import VectorSearchEngine
from app.core.config import settings
from app.core.logging import logger

# Global variables for dependency injection
vector_engine: VectorSearchEngine = None
permits_data: List[Dict[str, Any]] = []


async def get_vector_engine() -> VectorSearchEngine:
    """Get the vector search engine instance"""
    global vector_engine
    if vector_engine is None:
        raise HTTPException(
            status_code=503, 
            detail="Vector search engine not initialized"
        )
    return vector_engine


async def get_permits_data() -> List[Dict[str, Any]]:
    """Get the permits data"""
    global permits_data
    return permits_data


def set_vector_engine(engine: VectorSearchEngine):
    """Set the vector search engine instance"""
    global vector_engine
    vector_engine = engine


def set_permits_data(data: List[Dict[str, Any]]):
    """Set the permits data"""
    global permits_data
    permits_data = data


def add_permits_data(data: List[Dict[str, Any]]):
    """Add to permits data"""
    global permits_data
    permits_data.extend(data)