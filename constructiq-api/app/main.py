"""
FastAPI application main module with on-demand data loading
"""

from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import logger
from app.services.vector_search import VectorSearchEngine
from app.services.normalizer import AustinPermitsNormalizer
from app.api.deps import set_vector_engine, set_permits_data
from app.api.endpoints import search, health


def load_permits_from_json(file_path: str):
    """Load permit data from JSON file"""
    try:
        file_path = Path(file_path)
        
        if not file_path.exists():
            return []
        
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Handle both single objects and arrays
        if isinstance(data, list):
            permits = data
        else:
            permits = [data]
        
        logger.info(f"Loaded {len(permits)} permits from {file_path}")
        return permits
        
    except Exception as e:
        logger.error(f"Error loading permits from {file_path}: {e}")
        return []


async def load_and_process_permit_data(vector_engine: VectorSearchEngine):
    """Load raw permit data from JSON and normalize it"""
    
    # Try to load permit data from JSON file in multiple locations
    json_file_paths = [
        "data/permit_data.json",
        "app/data/permit_data.json", 
        "permit_data.json",
        "./permit_data.json"
    ]
    
    raw_permits = []
    for file_path in json_file_paths:
        raw_permits = load_permits_from_json(file_path)
        if raw_permits:
            logger.info(f"Found permit data file: {file_path}")
            break
    
    if not raw_permits:
        raise FileNotFoundError("No permit data file found in any of the expected locations")
    
    logger.info(f"Processing {len(raw_permits)} raw permit records...")
    
    # Initialize normalizer
    normalizer = AustinPermitsNormalizer()
    
    # Normalize all permits
    normalized_permits = []
    for i, raw_permit in enumerate(raw_permits):
        try:
            normalized_permit = normalizer.normalize_record(raw_permit)
            if normalized_permit:
                from dataclasses import asdict
                normalized_permits.append(asdict(normalized_permit))
            
            # Log progress for large datasets
            if (i + 1) % 10 == 0:
                logger.info(f"Normalized {i + 1}/{len(raw_permits)} permits")
                
        except Exception as e:
            logger.error(f"Error normalizing permit {raw_permit.get('permit_number', 'unknown')}: {e}")
            continue
    
    logger.info(f"Successfully normalized {len(normalized_permits)}/{len(raw_permits)} permits")
    
    # Set normalized permits data for API access
    set_permits_data(normalized_permits)
    
    # Index permits in vector database
    if normalized_permits:
        await vector_engine.index_permits(normalized_permits)
        logger.info(f"Indexed {len(normalized_permits)} permits in vector database")
    else:
        logger.warning("No permits to index - database will be empty")
    
    # Log normalization statistics
    stats = normalizer.stats
    logger.info(f"Normalization stats - Total: {stats['total_records']}, "
               f"Normalized: {stats['normalized_records']}, "
               f"Errors: {stats['errors']}, Warnings: {stats['warnings']}")
    
    return normalized_permits


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management - Initialize only core services"""
    
    # Startup
    logger.info(f"Starting up {settings.app_name} v{settings.app_version}")
    
    # Validate OpenAI API key
    if not settings.openai_api_key:
        logger.error("OpenAI API key not found. Please set OPENAI_API_KEY environment variable.")
        raise ValueError("OpenAI API key is required")
    
    # Initialize vector search engine (but don't load data yet)
    try:
        vector_engine = VectorSearchEngine(settings.openai_api_key)
        await vector_engine.initialize()
        set_vector_engine(vector_engine)
        logger.info("Vector search engine initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize vector search engine: {e}")
        raise
    
    # Initialize with empty permits data
    set_permits_data([])
    logger.info("Application started with empty permit database")
    logger.info("Use POST /admin/load-data endpoint to load permit data on-demand")
    
    yield
    
    # Shutdown
    logger.info(f"Shutting down {settings.app_name}")
    try:
        await vector_engine.close()
    except Exception as e:
        logger.warning(f"Error during shutdown: {e}")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Semantic search API for Austin construction permits using PostgreSQL pgvector and OpenAI embeddings",
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(search.router, tags=["search"])
app.include_router(health.router, tags=["health"])

# Import and include admin router
from app.api.endpoints import admin
app.include_router(admin.router, tags=["admin"])

# Additional middleware for logging
@app.middleware("http")
async def log_requests(request, call_next):
    """Log all HTTP requests"""
    start_time = datetime.now()
    
    response = await call_next(request)
    
    process_time = (datetime.now() - start_time).total_seconds() * 1000
    logger.info(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.2f}ms")
    
    return response


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level
    )