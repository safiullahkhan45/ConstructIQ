#!/usr/bin/env python3
"""
Database initialization script for ConstructIQ API
Sets up database schema and pgvector extension only
Data loading is handled by /admin/load-data endpoint
"""

import asyncio
import asyncpg
import os
from pathlib import Path

async def init_database():
    """Initialize the database with required schema and extensions"""
    
    # Get database URL from environment
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL environment variable not found")
        print("Make sure you're running this in Railway environment or set DATABASE_URL locally")
        return False
    
    # Convert DATABASE_URL format if needed (remove +asyncpg)
    if "+asyncpg" in database_url:
        database_url = database_url.replace("+asyncpg", "")
    
    try:
        # Connect to database
        print("🔌 Connecting to database...")
        conn = await asyncpg.connect(database_url)
        
        # Read SQL setup file
        sql_file = Path(__file__).parent.parent / "setup_database.sql"
        if not sql_file.exists():
            print(f"❌ SQL file not found: {sql_file}")
            return False
        
        print("📄 Reading setup_database.sql...")
        sql_content = sql_file.read_text()
        
        # Execute SQL setup
        print("🚀 Setting up database schema...")
        await conn.execute(sql_content)
        
        # Verify setup
        print("✅ Verifying database setup...")
        
        # Check if vector extension is installed
        vector_check = await conn.fetchval(
            "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')"
        )
        
        if vector_check:
            print("✅ Vector extension is installed")
        else:
            print("❌ Vector extension is not installed")
            return False
        
        # Check if permits table exists
        table_check = await conn.fetchval(
            "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'permits')"
        )
        
        if table_check:
            print("✅ Permits table created successfully")
        else:
            print("❌ Permits table was not created")
            return False
        
        # Check table statistics
        count = await conn.fetchval("SELECT COUNT(*) FROM permits")
        print(f"📊 Permits table ready with {count} records")
        
        await conn.close()
        print("🎉 Database initialization completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

async def test_connection():
    """Test database connection and basic operations"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        return False
    
    if "+asyncpg" in database_url:
        database_url = database_url.replace("+asyncpg", "")
    
    try:
        conn = await asyncpg.connect(database_url)
        
        # Test basic query
        result = await conn.fetchval("SELECT 1")
        print(f"✅ Database connection test: {result}")
        
        # Test vector operations
        await conn.execute("SELECT '[1,2,3]'::vector")
        print("✅ Vector extension test passed")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database connection test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 ConstructIQ Database Initialization")
    print("=" * 50)
    
    # Test connection first
    print("1. Testing database connection...")
    if not asyncio.run(test_connection()):
        exit(1)
    
    # Initialize database
    print("\n2. Initializing database schema...")
    if not asyncio.run(init_database()):
        exit(1)
    
    print("\n🎉 Database setup completed!")
    print("\nNext steps:")
    print("1. Start your API")
    print("2. Use POST /admin/load-data to load permit data")
    print("3. Test search: POST /search")
    print("4. View docs: /docs")