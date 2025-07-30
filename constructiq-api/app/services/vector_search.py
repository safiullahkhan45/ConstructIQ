"""
Vector search service using PostgreSQL pgvector and OpenAI embeddings
"""

from typing import Dict, List, Any, Optional

import openai

from app.models.api import SearchFilters
from app.services.database import get_database_service
from app.core.config import settings
from app.core.logging import logger


class VectorSearchEngine:
    """Vector search engine using PostgreSQL pgvector and OpenAI embeddings"""

    def __init__(self, openai_api_key: str):
        self.openai_client = openai.OpenAI(api_key=openai_api_key)
        self.db_service = get_database_service()

    async def initialize(self):
        """Initialize the database"""
        await self.db_service.initialize_database()

    def create_embedding_text(self, permit: Dict[str, Any]) -> str:
        """Create text for embedding from permit data"""
        text_parts = []
        
        # Add permit type and work details
        if permit.get("work_details"):
            work = permit["work_details"]
            if work.get("permit_type"):
                text_parts.append(f"Permit Type: {work['permit_type']}")
            if work.get("work_class"):
                text_parts.append(f"Work Class: {work['work_class']}")
            if work.get("description"):
                text_parts.append(f"Description: {work['description']}")
            if work.get("use_category"):
                text_parts.append(f"Use Category: {work['use_category']}")

        # Add location info
        if permit.get("location"):
            location = permit["location"]
            if location.get("street_address"):
                text_parts.append(f"Address: {location['street_address']}")
            if location.get("city"):
                text_parts.append(f"City: {location['city']}")

        # Add contractor info
        if permit.get("contractor") and permit["contractor"].get("name"):
            text_parts.append(f"Contractor: {permit['contractor']['name']}")

        # Add valuation if significant
        if permit.get("valuation") and permit["valuation"].get("total_valuation"):
            val = permit["valuation"]["total_valuation"]
            if val and val > 0:
                text_parts.append(f"Valuation: ${val:,.2f}")

        return " | ".join(text_parts)

    async def get_embedding(self, text: str) -> List[float]:
        """Get embedding from OpenAI"""
        try:
            response = self.openai_client.embeddings.create(
                model=settings.openai_model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error getting embedding: {e}")
            raise

    async def index_permits(self, permits: List[Dict[str, Any]]):
        """Index permits into vector database"""
        logger.info(f"Indexing {len(permits)} permits...")
        
        for permit in permits:
            try:
                # Create embedding text
                embedding_text = self.create_embedding_text(permit)
                
                # Get embedding
                embedding = await self.get_embedding(embedding_text)
                
                # Insert into database
                await self.db_service.insert_permit_vector(
                    permit_id=permit["permit_id"],
                    permit_data=permit,
                    embedding_text=embedding_text,
                    embedding=embedding
                )

            except Exception as e:
                logger.error(f"Error processing permit {permit.get('permit_id', 'unknown')}: {e}")

        logger.info(f"Successfully indexed {len(permits)} permits")

    async def search(self, query: str, filters: Optional[SearchFilters] = None, limit: int = 5) -> List[Dict[str, Any]]:
        """Search permits using vector similarity"""
        # Get query embedding
        query_embedding = await self.get_embedding(query)
        
        # Convert filters to dict
        filter_dict = {}
        if filters:
            if filters.permit_type:
                filter_dict["permit_type"] = filters.permit_type
            if filters.calendar_year_issued:
                filter_dict["calendar_year_issued"] = filters.calendar_year_issued
            if filters.work_class:
                filter_dict["work_class"] = filters.work_class
            if filters.use_category:
                filter_dict["use_category"] = filters.use_category
            if filters.city:
                filter_dict["city"] = filters.city
            if filters.council_district:
                filter_dict["council_district"] = filters.council_district

        # Search in database
        results = await self.db_service.search_similar_permits(
            query_embedding=query_embedding,
            filters=filter_dict if filter_dict else None,
            limit=limit
        )
        
        return results

    async def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the indexed collection"""
        return await self.db_service.get_stats()

    async def close(self):
        """Close database connections"""
        await self.db_service.close()
