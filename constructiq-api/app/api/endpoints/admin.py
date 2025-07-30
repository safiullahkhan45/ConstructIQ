"""
Admin endpoints for data management
"""

from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime

from app.core.logging import logger
from app.api.deps import get_vector_engine
from app.services.vector_search import VectorSearchEngine
from app.models.api import DataLoadResponse
    
from app.main import load_and_process_permit_data

router = APIRouter(prefix="/admin")


@router.post("/load-data", response_model=DataLoadResponse)
async def load_permit_data(
    vector_engine: VectorSearchEngine = Depends(get_vector_engine)
):
    """
    Load and process permit data on-demand
    """
    
    start_time = datetime.now()
    
    try:
        logger.info("Starting on-demand permit data loading...")

        # Load and process the data
        normalized_permits = await load_and_process_permit_data(vector_engine)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"Successfully loaded {len(normalized_permits)} permits in {processing_time:.2f} seconds")
        
        return DataLoadResponse(
            success=True,
            message=f"Successfully loaded and indexed {len(normalized_permits)} permits",
            records_loaded=len(normalized_permits),
            records_indexed=len(normalized_permits),
            processing_time_seconds=processing_time,
            timestamp=datetime.now()
        )
        
    except FileNotFoundError as e:
        logger.error(f"Data loading failed: {e}")
        raise HTTPException(
            status_code=404,
            detail="Permit data file not found. Please ensure permit_data.json exists in the expected location."
        )
        
    except Exception as e:
        logger.error(f"Error loading permit data: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load permit data: {str(e)}"
        )
