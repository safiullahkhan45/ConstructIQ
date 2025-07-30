# Austin Construction Permits Semantic Search API

A FastAPI backend that normalizes Austin construction permit data, creates vector embeddings using OpenAI, and provides semantic search capabilities with PostgreSQL pgvector.

## 🏗️ Project Structure

```
austin-permits-api/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app and startup
│   ├── api/
│   │   ├── __init__.py
│   │   ├── endpoints/
│   │   │   ├── __init__.py
│   │   │   ├── search.py       # Search endpoints
│   │   │   ├── health.py       # Health check endpoints
│   │   │   └── admin.py        # Admin endpoints
│   │   └── deps.py             # Dependencies
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py           # Configuration settings
│   │   └── logging.py          # Logging configuration
│   ├── models/
│   │   ├── __init__.py
│   │   ├── permit.py           # Permit data models
│   │   └── api.py              # API request/response models
│   └── services/
│       ├── __init__.py
│       ├── normalizer.py       # Data normalization pipeline
│       ├── vector_search.py    # Vector search engine
│       └── database.py         # PostgreSQL database service
├── requirements.txt
├── .env.example
├── setup_database.sql          # Database setup script
├── README.md
└── run_local.py                # Local development runner
```

## ✨ Features

- 🔍 **Semantic Search**: Natural language queries using OpenAI embeddings
- 🎯 **Advanced Filtering**: Filter by permit type, year, work class, location, etc.
- 📊 **Data Normalization**: Clean, structured schema from messy permit data
- 🚀 **High Performance**: FastAPI with async PostgreSQL and pgvector
- 📝 **Query Logging**: Comprehensive logging for analytics
- 📚 **Auto Documentation**: Interactive OpenAPI/Swagger docs
- 🗄️ **Production Ready**: PostgreSQL with proper indexing and performance optimization

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 14+ with pgvector extension
- OpenAI API key

### 1. Setup PostgreSQL Database

#### Install PostgreSQL and pgvector
```bash
# Install PostgreSQL (Ubuntu/Debian)
sudo apt update
sudo apt install postgresql postgresql-contrib

# Install pgvector extension
git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install

# Create database and user
sudo -u postgres psql
CREATE DATABASE austin_permits;
CREATE USER austin_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE austin_permits TO austin_user;
\q

# Setup database tables
psql -U austin_user -d austin_permits -f setup_database.sql
```

### 2. Setup Application Environment

```bash
# Clone the repository
git clone https://github.com/safiullahkhan45/ConstructIQ
cd constructiq-api

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env and configure your settings
OPENAI_API_KEY=your-openai-api-key-here
DATABASE_URL=postgresql+asyncpg://austin_user:your_password@localhost:5432/austin_permits
```

### 4. Load Permit Data

```bash
python load_permits.py
```

### 5. Run Locally

```bash
# Run the development server
python run_local.py

# Or use uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 6. Access the API

- **API Base**: http://localhost:8000
- **Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/healthz
- **Admin**: http://localhost:8000/admin/load-data

## 📡 API Endpoints

### `POST /search`
Semantic search with optional filters

**Request:**
```json
{
  "query": "electrical permit",
  "filters": {
    "permit_type": "Building",
    "calendar_year_issued": 2025,
    "use_category": "Commercial"
  },
  "limit": 5
}
```

**Response:**
```json
{
  "results": [
    {
      "permit_id": "2023BP-001234",
      "permit_number": "BP-2023-001234",
      "permit_type": "Building",
      "work_description": "Commercial office remodel...",
      "street_address": "123 E 6th St",
      "city": "Austin",
      "contractor_name": "Austin Commercial Builders LLC",
      "total_valuation": 250000.0,
      "issue_date": "2023-03-15",
      "similarity_score": 0.89
    }
  ],
  "total_found": 1,
  "query": "commercial remodel downtown",
  "filters_applied": {...},
  "search_time_ms": 45.2
}
```

### `GET /healthz`
Health check endpoint

### `POST /admin/load-data`
Load and index permit data (admin endpoint)

### `GET /docs`
Interactive API documentation

## 🎯 Architecture

### Data Pipeline
1. **Normalization**: Raw Austin permit data → Clean structured schema
2. **Embedding**: Relevant fields → OpenAI text-embedding-3-small vectors (1536 dimensions)
3. **Indexing**: Vector storage in PostgreSQL with pgvector and metadata indexes
4. **Search**: Vector similarity search with SQL-based metadata filtering

### Database Schema

```sql
permit_vectors (
    id SERIAL PRIMARY KEY,
    permit_id VARCHAR UNIQUE,
    permit_type VARCHAR,        -- Indexed for filtering
    work_class VARCHAR,         -- Indexed for filtering  
    use_category VARCHAR,       -- Indexed for filtering
    city VARCHAR,              -- Indexed for filtering
    council_district INTEGER,   -- Indexed for filtering
    calendar_year_issued INTEGER, -- Indexed for filtering
    total_valuation FLOAT,
    embedding_text TEXT,
    embedding vector(1536),     -- pgvector column with cosine similarity index
    permit_data JSONB,          -- Full normalized permit data
    created_at TIMESTAMP
)
```

### Performance Features

- **Vector Index**: IVFFlat index for fast similarity search
- **Metadata Indexes**: B-tree indexes on filter columns
- **Async Database**: Non-blocking PostgreSQL operations
- **Connection Pooling**: SQLAlchemy async session management

## 🧪 Testing the API

### Sample Queries

Try these queries in the `/docs` interface:

1. **Commercial Projects**:
   ```json
   {"query": "commercial remodel downtown", "limit": 3}
   ```

2. **Residential Work**:
   ```json
   {"query": "home addition bedroom", "filters": {"use_category": "Residential"}}
   ```

3. **Electrical Work**:
   ```json
   {"query": "electrical restaurant kitchen", "filters": {"permit_type": "Electrical"}}
   ```

4. **High Value Projects**:
   ```json
   {"query": "expensive construction", "limit": 5}
   ```

5. **Year-based Filter**:
   ```json
   {"query": "building permit", "filters": {"calendar_year_issued": 2023}}
   ```

### cURL Examples

```bash
# Health check
curl http://localhost:8000/healthz

# Filtered search
curl --location 'http://localhost:8000/search' \
--header 'Content-Type: application/json' \
--data '{"query": "Irrigation System", "filters": {"permit_type": "Plumbing Permit", "calendar_year_issued": 2025}}'
```

## 📊 Sample Data

The API includes 5 sample Austin permits:

1. **Commercial Office Remodel** ($250K) - Downtown tech company
2. **Residential Addition** ($85K) - Home bedroom suite addition  
3. **Restaurant Electrical** ($15K) - Kitchen equipment wiring
4. **HVAC Replacement** ($12K) - Residential heat pump system
5. **New Restaurant** ($450K) - Full commercial kitchen and dining

## 🔧 Processing Real Data

To process actual Austin permit data:

1. **Download Austin permit data** from: https://data.austintexas.gov/Building-and-Development/Issued-Construction-Permits/3syk-w9eu/

2. **Process the data**:
```python
from app.services.normalizer import AustinPermitsNormalizer

normalizer = AustinPermitsNormalizer()
normalized_permits = normalizer.normalize_dataset("austin_permits.csv", limit=10)
```

3. **Index the data**:
```python
from app.services.vector_search import VectorSearchEngine

vector_engine = VectorSearchEngine(openai_api_key)
await vector_engine.index_permits(normalized_permits)
```

## 🚀 Deployment

### Environment Variables for Production

```bash
OPENAI_API_KEY=your-production-openai-key
DATABASE_URL=postgresql+asyncpg://user:password@your-db-host:5432/austin_permits
DATABASE_ECHO=false
DEBUG=false
LOG_LEVEL=info
```

### Performance Tuning

For production scale:

1. **Database Optimization**:
   - Adjust `work_mem` for vector operations
   - Tune `shared_buffers` for caching
   - Monitor query performance with `EXPLAIN ANALYZE`

2. **Vector Index Tuning**:
   ```sql
   -- Rebuild index with optimal list count based on data size
   DROP INDEX idx_permit_vectors_embedding;
   CREATE INDEX idx_permit_vectors_embedding ON permit_vectors 
   USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
   ```

3. **Connection Pooling**:
   - Configure SQLAlchemy pool settings
   - Use pgbouncer for connection management

## 🔍 Query Logging

All searches are logged with:
- Timestamp
- Query text and filters applied
- Results count and permit IDs returned
- Response time in milliseconds
- Similarity scores

Logs are written to both console and `query_logs.log` file.

## ⚡ Performance Characteristics

- **Search latency**: ~30-80ms per query (including embedding generation)
- **Indexing speed**: ~1-2 records/second (due to OpenAI API rate limits)
- **Memory usage**: ~200MB base + ~6KB per indexed record
- **Concurrent requests**: 100+ with proper database connection pooling

## 🛠️ Technical Decisions

### PostgreSQL + pgvector
- **Production-ready**: ACID compliance, mature ecosystem
- **Vector support**: Native vector operations with indexing
- **Scalability**: Handles large datasets efficiently
- **Filtering**: SQL-based metadata filtering alongside vector search

### OpenAI text-embedding-3-small
- **Quality**: High-quality embeddings for construction domain
- **Performance**: Fast generation, reasonable cost
- **Dimensions**: 1536-dimensional vectors for good granularity

### FastAPI Architecture
- **Auto-documentation**: Interactive API docs with Swagger
- **Async support**: Non-blocking I/O for better performance
- **Type safety**: Pydantic models for request/response validation
- **Modern Python**: Leverages latest async/await patterns

---

# 📝 Normalizatio Pipeline Decisions

## 1. **Normalized Schema**

### **Location Object**
Standardized location information for each permit, including geographic and administrative details.

- **street_address**: The street address of the permit location (string).
- **city**: The city where the permit is located (default: "Austin") (string).
- **state**: The state where the permit is located (default: "TX") (string).
- **zip_code**: The ZIP code of the location (string).
- **latitude**: Latitude coordinate of the location (float).
- **longitude**: Longitude coordinate of the location (float).
- **council_district**: Austin city council district number (integer).

### **Contractor Object**
Contractor-related information, including company name, license details, and contact information.

- **name**: Name of the contractor (string).
- **license_number**: Contractor's professional license number (string).
- **phone**: Contractor's phone number in the format `XXX-XXX-XXXX` (string).
- **address**: Address of the contractor (string).
- **company_type**: Type of contracting company (string).

### **Applicant Object**
Information about the permit applicant.

- **name**: Name of the applicant (string).
- **company**: Name of the applicant's company (string).
- **phone**: Applicant's phone number (string).
- **email**: Applicant's email address (string).
- **address**: Applicant's address (string).

### **Valuation Object**
Valuation and financial information about the construction project.

- **total_valuation**: Total project valuation (float, USD).
- **permit_fee**: Permit fee paid (float, USD).
- **currency**: Currency code (default: "USD") (string).

### **WorkDetails Object**
Describes the work related to the permit, including the type of work and specifications.

- **permit_type**: Type of the permit (e.g., Building, Electrical, Mechanical) (string).
- **work_class**: Work class or category (string).
- **description**: Description of the work being performed (string).
- **use_category**: Category of use (string).


### **PermitDates Object**
Standardized date information for the permit.

- **issue_date**: Date when the permit was issued (ISO format, string).
- **expiration_date**: Date when the permit expires (ISO format, string).
- **application_date**: Date when the permit was applied for (ISO format, string).

### **NormalizedPermit Object**
This is the main object that holds the normalized information for each permit.

- **permit_id**: Unique identifier for the permit (string).
- **permit_number**: Permit number (string, optional).
- **status**: Status of the permit (string, optional).
- **location**: Standardized location object.
- **contractor**: Standardized contractor object.
- **applicant**: Standardized applicant object.
- **valuation**: Standardized valuation object.
- **work_details**: Standardized work details object (newly added).
- **dates**: Standardized date object.
- **metadata**: Metadata related to the normalization process, such as the timestamp and data quality score (dictionary).

---

## 2. **Logic Decisions**

### **Normalization Logic**
- **Grouping Fields**: Related fields such as location, contractor, and applicant information are grouped into respective sub-objects, making it easier to query.
- **Renaming Fields**: Ambiguous or inconsistent field names (e.g., `original_address1` → `street_address`) are mapped to standardized field names to ensure consistency.
- **Date Formatting**: All dates are converted to **ISO format** (`YYYY-MM-DD`), which is a standard date format.
- **Data Type Standardization**: Currency values are normalized to `float`, and phone numbers are standardized to the `XXX-XXX-XXXX` format.

### **Handling Missing or Null Data**
- **Default Values**: Default values like `"Austin"` for city and `"TX"` for state are used when missing. This ensures no critical information is left blank.
- **Skip Invalid or Empty Fields**: If a field is `None`, `NaN`, or empty, it is skipped, avoiding incorrect or incomplete data in the final output.
- **Handling Missing ZIP Codes**: ZIP codes are fetched from an external API (OpenStreetMap Nominatim API) if missing.

### **Data Integrity**
- **Duplicate Handling**: Redundant or conflicting fields (e.g., `permit_class` vs. `permit_class_mapped`) are prioritized based on their relevance or completeness.
- **External Data Sources**: Missing ZIP codes are fetched using an external service (OpenStreetMap Nominatim API).

---

## 3. **Assumptions + Tradeoffs**

### **Assumptions**
- **Geographic Location**: The default city is assumed to be Austin, the state is assumed to be TX, and the country is assumed to be US for most records.
- **Uniformity of Permit Types**: The pipeline assumes that permit types will be from a predefined list (Building, Electrical, Mechanical, etc.), with possible expansion in the future.
- **Date Formats**: It is assumed that input data may contain several different date formats, but only the first valid format is considered for normalization.

### **Tradeoffs**
- **External API Dependency**: The reliance on the OpenStreetMap Nominatim API introduces a potential failure point if the service is slow or unavailable. This introduces a tradeoff between automation and external dependency.
- **Handling Null or Missing Fields**: By skipping empty or null fields, the script avoids introducing incorrect data but may result in incomplete records. This tradeoff is essential to maintain data integrity but could affect completeness.
- **Default Values**: The use of default values for `city` and `state` is a tradeoff between convenience and accuracy, assuming that most records are for Austin. This might lead to inaccuracies if records for other cities are included.

---

**Author**: Built by Safiullah Khan Sherzad  
**Purpose**: ConstructIQ Technical Assessment - Backend/AI Challenge  
**Database**: PostgreSQL with pgvector extension for production-ready vector search
