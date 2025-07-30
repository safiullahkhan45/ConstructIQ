"""
API request and response models
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class SearchFilters(BaseModel):
    """Filters for permit search"""
    permit_type: Optional[str] = Field(
        None, 
        description="Type of permit (e.g., 'Building', 'Electrical')",
        example="Building"
    )
    calendar_year_issued: Optional[int] = Field(
        None, 
        description="Year the permit was issued",
        example=2023
    )
    work_class: Optional[str] = Field(
        None, 
        description="Class of work being performed",
        example="Commercial"
    )
    use_category: Optional[str] = Field(
        None, 
        description="Category of use (e.g., 'Residential', 'Commercial')",
        example="Commercial"
    )
    city: Optional[str] = Field(
        None, 
        description="City where work is being performed",
        example="Austin"
    )
    council_district: Optional[int] = Field(
        None, 
        description="Austin council district number",
        example=9
    )


class SearchRequest(BaseModel):
    """Search request model"""
    query: str = Field(
        ..., 
        description="Natural language search query",
        example="irrigation system"
    )
    filters: Optional[SearchFilters] = Field(
        None, 
        description="Optional filters to apply"
    )
    limit: Optional[int] = Field(
        5, 
        ge=1, 
        le=20, 
        description="Maximum number of results to return"
    )


class PermitSearchResult(BaseModel):
    """Individual search result"""
    permit_id: str
    permit_number: Optional[str] = None
    permit_type: Optional[str] = None
    work_description: Optional[str] = None
    street_address: Optional[str] = None
    city: Optional[str] = None
    contractor_name: Optional[str] = None
    total_valuation: Optional[float] = None
    issue_date: Optional[str] = None
    similarity_score: float = Field(
        ..., 
        description="Cosine similarity score (0-1)",
        ge=0.0,
        le=1.0
    )


class SearchResponse(BaseModel):
    """Search response model"""
    results: List[PermitSearchResult]
    total_found: int
    query: str
    filters_applied: Optional[SearchFilters] = None
    search_time_ms: float


class DataLoadResponse(BaseModel):
    """Response model for data loading operations"""
    success: bool
    message: str
    records_loaded: int
    records_indexed: int
    processing_time_seconds: float
    timestamp: datetime


class HealthResponse(BaseModel):
    """Health check response"""
    ok: bool
    timestamp: str
    version: str = "1.0.0"
    status: str = "healthy"


class APIInfo(BaseModel):
    """API information response"""
    message: str
    version: str
    endpoints: dict
    description: str

