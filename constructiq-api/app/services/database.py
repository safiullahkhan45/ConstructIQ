"""
Database service for PostgreSQL with pgvector
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import text, String, Float, Integer, DateTime, JSON
from pgvector.sqlalchemy import Vector
from datetime import datetime
import numpy as np

from app.core.config import settings
from app.core.logging import logger


class Base(DeclarativeBase):
    """Base class for database models"""
    pass


class PermitVector(Base):
    """Database model for permit vectors"""
    __tablename__ = "permit_vectors"

    id: Mapped[int] = mapped_column(primary_key=True)
    permit_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    permit_number: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    permit_type: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    work_class: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    use_category: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    city: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    council_district: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    calendar_year_issued: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    total_valuation: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    embedding_text: Mapped[str] = mapped_column(String)
    embedding: Mapped[List[float]] = mapped_column(Vector(1536))  # OpenAI embedding dimension
    permit_data: Mapped[Dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<PermitVector(permit_id='{self.permit_id}', permit_type='{self.permit_type}')>"


def clean_data_for_db(data: Any) -> Any:
    """Clean data for database insertion, handling numpy types and NaN values"""
    if isinstance(data, np.integer):
        return int(data)
    elif isinstance(data, np.floating):
        if np.isnan(data):
            return None
        return float(data)
    elif isinstance(data, np.ndarray):
        return data.tolist()
    elif isinstance(data, dict):
        return {key: clean_data_for_db(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [clean_data_for_db(item) for item in data]
    else:
        return data


class DatabaseService:
    """Database service for PostgreSQL operations"""

    def __init__(self, database_url: str = settings.database_url):
        self.engine = create_async_engine(
            database_url,
            echo=settings.database_echo,
            pool_pre_ping=True,
            pool_recycle=3600
        )
        self.async_session = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

    async def initialize_database(self):
        """Initialize database and create tables"""
        try:
            async with self.engine.begin() as conn:
                # Install pgvector extension
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                
                # Create tables
                await conn.run_sync(Base.metadata.create_all)
                
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    async def insert_permit_vector(
        self, 
        permit_id: str,
        permit_data: Dict[str, Any],
        embedding_text: str,
        embedding: List[float]
    ):
        """Insert a permit vector into the database"""
        try:
            # Clean all data to handle numpy types and NaN values
            permit_data_clean = clean_data_for_db(permit_data)
            
            # Extract metadata for filtering
            work_details = permit_data_clean.get("work_details", {})
            location = permit_data_clean.get("location", {})
            dates = permit_data_clean.get("dates", {})
            
            # Extract year from issue date
            calendar_year = None
            if dates.get("issue_date"):
                try:
                    issue_date = datetime.fromisoformat(dates["issue_date"])
                    calendar_year = issue_date.year
                except:
                    pass

            # Clean individual fields
            council_district = location.get("council_district")
            if council_district is not None:
                if isinstance(council_district, (np.integer, np.floating)):
                    if np.isnan(council_district):
                        council_district = None
                    else:
                        council_district = int(council_district)

            total_valuation = permit_data_clean.get("valuation", {}).get("total_valuation")
            if total_valuation is not None and np.isnan(total_valuation):
                total_valuation = None

            permit_vector = PermitVector(
                permit_id=permit_id,
                permit_number=permit_data_clean.get("permit_number"),
                permit_type=work_details.get("permit_type"),
                work_class=work_details.get("work_class"),  
                use_category=work_details.get("use_category"),
                city=location.get("city"),
                council_district=council_district,
                calendar_year_issued=calendar_year,
                total_valuation=total_valuation,
                embedding_text=embedding_text,
                embedding=embedding,
                permit_data=permit_data_clean
            )

            async with self.async_session() as session:
                session.add(permit_vector)
                await session.commit()
                
        except Exception as e:
            logger.error(f"Error inserting permit vector {permit_id}: {e}")
            raise

    async def search_similar_permits(
        self,
        query_embedding: List[float],
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Search for similar permits using vector similarity"""
        try:
            # Convert embedding to proper vector format for PostgreSQL
            embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
            
            # Build the base query - get ALL results and let similarity scoring work
            query_parts = [
                "SELECT permit_id, permit_number, permit_type, work_class, use_category,",
                "city, council_district, calendar_year_issued, total_valuation,",
                "embedding_text, permit_data,",
                f"1 - (embedding <=> '{embedding_str}'::vector) as similarity_score,",
                f"embedding <-> '{embedding_str}'::vector as l2_distance,", 
                f"embedding <#> '{embedding_str}'::vector as inner_product",
                "FROM permit_vectors"
            ]
            
            # Add filters
            where_conditions = []
            params = {}
            
            if filters:
                if filters.get("permit_type"):
                    where_conditions.append("permit_type = :permit_type")
                    params["permit_type"] = filters["permit_type"]
                
                if filters.get("calendar_year_issued"):
                    where_conditions.append("calendar_year_issued = :calendar_year_issued")
                    params["calendar_year_issued"] = filters["calendar_year_issued"]
                
                if filters.get("work_class"):
                    where_conditions.append("work_class = :work_class")
                    params["work_class"] = filters["work_class"]
                
                if filters.get("use_category"):
                    where_conditions.append("use_category = :use_category")
                    params["use_category"] = filters["use_category"]
                
                if filters.get("city"):
                    where_conditions.append("city = :city")
                    params["city"] = filters["city"]
                
                if filters.get("council_district"):
                    where_conditions.append("council_district = :council_district")
                    params["council_district"] = filters["council_district"]
            
            if where_conditions:
                query_parts.append("WHERE " + " AND ".join(where_conditions))
            
            # Order by cosine similarity (best match first) and get all results above a threshold
            query_parts.extend([
                f"ORDER BY embedding <=> '{embedding_str}'::vector",
                f"LIMIT {limit}"
            ])
            
            query_sql = " ".join(query_parts)
            
            logger.info(f"Executing vector search query with embedding length: {len(query_embedding)}")
            
            async with self.async_session() as session:
                result = await session.execute(text(query_sql), params)
                rows = result.fetchall()
                
                logger.info(f"Vector search returned {len(rows)} results")
                
                # Log the first few results for debugging
                for i, row in enumerate(rows[:3]):
                    logger.info(f"Result {i+1}: permit_id={row[0]}, similarity={row[11]:.4f}, l2_distance={row[12]:.4f}, text='{row[9][:100]}...'")
                
                return [
                    {
                        "permit_id": row[0],
                        "permit_number": row[1],
                        "permit_type": row[2],
                        "work_class": row[3],
                        "use_category": row[4],
                        "city": row[5],
                        "council_district": row[6],
                        "calendar_year_issued": row[7],
                        "total_valuation": row[8],
                        "embedding_text": row[9],
                        "permit_data": row[10],
                        "similarity_score": float(row[11])
                    }
                    for row in rows
                ]
                
        except Exception as e:
            logger.error(f"Error searching permits: {e}")
            raise

    async def get_permit_by_id(self, permit_id: str) -> Optional[Dict[str, Any]]:
        """Get a permit by ID"""
        try:
            async with self.async_session() as session:
                result = await session.execute(
                    text("SELECT permit_data FROM permit_vectors WHERE permit_id = :permit_id"),
                    {"permit_id": permit_id}
                )
                row = result.fetchone()
                return row[0] if row else None
        except Exception as e:
            logger.error(f"Error getting permit {permit_id}: {e}")
            return None

    async def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            async with self.async_session() as session:
                result = await session.execute(text("SELECT COUNT(*) FROM permit_vectors"))
                count = result.scalar()
                
                return {
                    "total_documents": count,
                    "status": "ready"
                }
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {
                "total_documents": 0,
                "status": "error",
                "error": str(e)
            }

    async def close(self):
        """Close database connections"""
        await self.engine.dispose()



# Global database service instance
database_service: Optional[DatabaseService] = None


def get_database_service() -> DatabaseService:
    """Get the database service instance"""
    global database_service
    if database_service is None:
        database_service = DatabaseService()
    return database_service