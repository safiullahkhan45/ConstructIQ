-- Setup script for PostgreSQL database with pgvector extension
-- Run this script to set up your database for the Austin Permits API

-- Install pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create permit_vectors table
CREATE TABLE IF NOT EXISTS permit_vectors (
    id SERIAL PRIMARY KEY,
    permit_id VARCHAR UNIQUE NOT NULL,
    permit_number VARCHAR,
    permit_type VARCHAR,
    work_class VARCHAR,
    use_category VARCHAR,
    city VARCHAR,
    council_district INTEGER,
    calendar_year_issued INTEGER,
    total_valuation FLOAT,
    embedding_text TEXT NOT NULL,
    embedding vector(1536), -- OpenAI text-embedding-3-small dimension
    permit_data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_permit_vectors_permit_id ON permit_vectors(permit_id);
CREATE INDEX IF NOT EXISTS idx_permit_vectors_permit_type ON permit_vectors(permit_type);
CREATE INDEX IF NOT EXISTS idx_permit_vectors_work_class ON permit_vectors(work_class);
CREATE INDEX IF NOT EXISTS idx_permit_vectors_use_category ON permit_vectors(use_category);
CREATE INDEX IF NOT EXISTS idx_permit_vectors_city ON permit_vectors(city);
CREATE INDEX IF NOT EXISTS idx_permit_vectors_council_district ON permit_vectors(council_district);
CREATE INDEX IF NOT EXISTS idx_permit_vectors_calendar_year ON permit_vectors(calendar_year_issued);

-- Create vector index for similarity search
CREATE INDEX IF NOT EXISTS idx_permit_vectors_embedding ON permit_vectors 
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Verify setup
SELECT 'pgvector extension installed successfully' as status 
WHERE EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector');

SELECT 'permit_vectors table created successfully' as status 
WHERE EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'permit_vectors');