"""
Enhanced logging configuration with detailed query analytics
"""

import logging
import sys
import json
from pathlib import Path
from typing import Any, Dict, List
from datetime import datetime

from app.core.config import settings


def setup_logging() -> logging.Logger:
    """Setup application logging configuration"""
    
    # Create logs directory if it doesn't exist
    log_file_path = Path(settings.log_file)
    log_file_path.parent.mkdir(exist_ok=True)
    
    # Configure logging format
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format=log_format,
        handlers=[
            logging.FileHandler(settings.log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Get logger for our application
    logger = logging.getLogger("austin_permits_api")
    
    return logger


def log_search_query(
    logger: logging.Logger,
    query: str,
    filters: Dict[str, Any],
    results_count: int,
    search_time_ms: float,
    result_ids: List[str] = None,
    similarity_scores: List[float] = None,
    user_info: Dict[str, Any] = None
):
    """
    Enhanced search query logging with detailed analytics
    
    Args:
        logger: Logger instance
        query: Search query text
        filters: Applied filters dictionary
        results_count: Number of results returned
        search_time_ms: Search execution time
        result_ids: List of result permit IDs
        similarity_scores: List of similarity scores for results
        user_info: Optional user information (IP, user agent, etc.)
    """
    
    # Calculate analytics
    avg_similarity = sum(similarity_scores) / len(similarity_scores) if similarity_scores else 0
    max_similarity = max(similarity_scores) if similarity_scores else 0
    min_similarity = min(similarity_scores) if similarity_scores else 0
    
    # Build comprehensive log entry
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "query": query,
        "query_length": len(query),
        "filters": filters,
        "filter_count": len(filters) if filters else 0,
        "results_count": results_count,
        "search_time_ms": round(search_time_ms, 2),
        "performance_category": _categorize_performance(search_time_ms),
        "result_ids": result_ids[:10] if result_ids else [],  # Limit to first 10
        "similarity_analytics": {
            "avg_score": round(avg_similarity, 4),
            "max_score": round(max_similarity, 4),
            "min_score": round(min_similarity, 4),
            "score_range": round(max_similarity - min_similarity, 4) if similarity_scores else 0
        },
        "query_quality": _assess_query_quality(avg_similarity, results_count),
        "user_info": user_info or {}
    }
    
    # Log with structured format for easy parsing
    logger.info(f"SEARCH_QUERY: {json.dumps(log_entry, indent=None)}")
    
    # Also log a human-readable summary
    logger.info(
        f"Search: '{query}' | "
        f"Results: {results_count} | "
        f"Time: {search_time_ms:.0f}ms | "
        f"Avg Score: {avg_similarity:.3f} | "
        f"Quality: {log_entry['query_quality']}"
    )


def _categorize_performance(search_time_ms: float) -> str:
    """Categorize search performance"""
    if search_time_ms < 100:
        return "excellent"
    elif search_time_ms < 500:
        return "good"
    elif search_time_ms < 1000:
        return "fair"
    else:
        return "slow"


def _assess_query_quality(avg_similarity: float, results_count: int) -> str:
    """Assess the quality of search results"""
    if avg_similarity > 0.7:
        return "excellent"
    elif avg_similarity > 0.5:
        return "good"
    elif avg_similarity > 0.3:
        return "fair"
    else:
        return "poor"


def log_search_analytics_summary(logger: logging.Logger):
    """Log periodic analytics summary (could be called by a scheduled task)"""
    
    # This would typically read from stored logs or database
    # For now, just log a placeholder
    logger.info("ANALYTICS_SUMMARY: Search analytics summary would go here")


# Initialize logger
logger = setup_logging()