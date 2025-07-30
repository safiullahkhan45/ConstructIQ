"""
Local development runner for Austin Permits API
"""

import os
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

if __name__ == "__main__":
    import uvicorn
    from app.core.config import settings
    
    print(f"Starting {settings.app_name} v{settings.app_version}")
    print(f"Server will be available at: http://{settings.host}:{settings.port}")
    print(f"API Documentation: http://{settings.host}:{settings.port}/docs")
    print(f"Health Check: http://{settings.host}:{settings.port}/healthz")
    print("\nMake sure you have set your OPENAI_API_KEY in the .env file!")
    print("-" * 60)
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level=settings.log_level.lower()
    )