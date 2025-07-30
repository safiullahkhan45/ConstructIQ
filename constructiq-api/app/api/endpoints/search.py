"""
Search endpoints
"""

from datetime import datetime
from typing import List
from fastapi import APIRouter, HTTPException, Depends, Request

from app.models.api import SearchRequest, SearchResponse, PermitSearchResult
from app.api.deps import get_vector_engine, get_permits_data
from app.services.vector_search import VectorSearchEngine
from app.core.logging import logger, log_search_query

router = APIRouter()


@router.post("/search", response_model=SearchResponse)
async def search_permits(
    request: SearchRequest,
    http_request: Request,
    vector_engine: VectorSearchEngine = Depends(get_vector_engine),
    permits_data: List = Depends(get_permits_data)
):
    """
    Search construction permits using semantic similarity
    """
    start_time = datetime.now()
    
    try:
        # Validate query
        if not request.query.strip():
            raise HTTPException(
                status_code=400,
                detail="Query cannot be empty"
            )
        
        # Perform vector search
        search_results = await vector_engine.search(
            query=request.query,
            filters=request.filters,
            limit=request.limit
        )
        
        # Convert results to response format
        results = []
        similarity_scores = []
        
        for result in search_results:
            permit_data = result["permit_data"]
            
            # Handle both nested and flat data structures
            work_description = (
                permit_data.get("work_details", {}).get("description") or
                permit_data.get("work_description") or
                permit_data.get("description")
            )
            
            street_address = (
                permit_data.get("location", {}).get("street_address") or
                permit_data.get("street_address")
            )
            
            contractor_name = (
                permit_data.get("contractor", {}).get("name") or
                permit_data.get("contractor_name")
            )
            
            issue_date = (
                permit_data.get("dates", {}).get("issue_date") or
                permit_data.get("issue_date")
            )
            
            similarity_score = round(result["similarity_score"], 4)
            similarity_scores.append(similarity_score)
            
            search_result = PermitSearchResult(
                permit_id=result["permit_id"],
                permit_number=result["permit_number"],
                permit_type=result["permit_type"],
                work_description=work_description,
                street_address=street_address,
                city=result["city"],
                contractor_name=contractor_name,
                total_valuation=result["total_valuation"],
                issue_date=issue_date,
                similarity_score=similarity_score
            )
            results.append(search_result)
        
        # Calculate search time
        search_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Extract user information for logging
        user_info = {
            "ip_address": getattr(http_request.client, "host", None) if http_request.client else None,
            "user_agent": http_request.headers.get("user-agent"),
            "referer": http_request.headers.get("referer")
        }
        
        # Enhanced logging with analytics
        result_ids = [r.permit_id for r in results]
        log_search_query(
            logger=logger,
            query=request.query,
            filters=request.filters.dict() if request.filters else {},
            results_count=len(results),
            search_time_ms=search_time,
            result_ids=result_ids,
            similarity_scores=similarity_scores,
            user_info=user_info
        )
        
        return SearchResponse(
            results=results,
            total_found=len(results),
            query=request.query,
            filters_applied=request.filters,
            search_time_ms=round(search_time, 2)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")