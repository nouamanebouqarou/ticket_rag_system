# Ticket RAG System v3.0 - Complete Documentation

## Table of Contents

1. [Overview](#1-overview)
2. [Architecture](#2-architecture)
3. [Installation](#3-installation)
4. [Configuration](#4-configuration)
5. [Core Components](#5-core-components)
6. [Database Layer](#6-database-layer)
7. [RAG System](#7-rag-system)
8. [API Reference](#8-api-reference)
9. [Prompt Engineering](#9-prompt-engineering)
10. [Usage Examples](#10-usage-examples)
11. [Deployment](#11-deployment)
12. [Troubleshooting](#12-troubleshooting)

---

## 1. Overview

### 1.1 Introduction

The Ticket RAG System is a production-ready Retrieval-Augmented Generation (RAG) system designed for IT support ticket analysis. It leverages Large Language Models (LLMs) and vector embeddings to:

- **Analyze Tickets**: Determine resolution status, extract root causes, and document resolution steps
- **Generate Embeddings**: Create semantic vector representations for similarity search
- **Retrieve Similar Tickets**: Find historically similar resolved tickets using domain-filtered vector search
- **Suggest Resolutions**: Provide actionable resolution suggestions based on past solutions

### 1.2 Key Features

| Feature | Description |
|---------|-------------|
| Multi-LLM Support | OpenAI (Azure), Ollama, and VertexAI backends |
| Conditional Processing | Analysis and embeddings only for resolved tickets (cost optimization) |
| Domain Filtering | RAG retrieval scoped to the same domain for relevance |
| REST API | FastAPI endpoints for all operations |
| Vector Search | PostgreSQL + pgvector for similarity search |
| Docker Ready | Containerized deployment with Docker Compose |
| Batch Processing | Process multiple tickets from CSV files |

### 1.3 System Requirements

- **Python**: 3.11+
- **PostgreSQL**: 14+ with pgvector extension
- **Memory**: 4GB+ RAM recommended
- **Storage**: Depends on ticket volume (embeddings storage)

---

## 2. Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              INPUT LAYER                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │  CSV File    │  │  REST API    │  │  Python SDK  │  │   CLI        │    │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘    │
└─────────┼──────────────────┼──────────────────┼──────────────────┼─────────┘
          │                  │                  │                  │
          └──────────────────┴──────────────────┴──────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PIPELINE LAYER                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                       TicketPipeline                                  │   │
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐              │   │
│  │  │  Status     │───▶│  Analysis   │───▶│  Embedding  │              │   │
│  │  │  Detection  │    │  (if res.)  │    │  (if res.)  │              │   │
│  │  └─────────────┘    └─────────────┘    └─────────────┘              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
          ┌─────────────────────────────┼─────────────────────────────┐
          │                             │                             │
          ▼                             ▼                             ▼
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│    TicketAgent      │    │   EmbeddingAgent    │    │    ResolutionGen    │
│  ┌───────────────┐  │    │  ┌───────────────┐  │    │  ┌───────────────┐  │
│  │ Status Det.   │  │    │  │ Text Prepare  │  │    │  │ Context Retr. │  │
│  │ Cause Analy.  │  │    │  │ Embed Gen.    │  │    │  │ LLM Generate  │  │
│  │ Resol. Extract│  │    │  │ Batch Support │  │    │  │               │  │
│  └───────────────┘  │    │  └───────────────┘  │    │  └───────────────┘  │
│         │           │    │         │           │    │         │           │
│         ▼           │    │         ▼           │    │         ▼           │
│  ┌───────────────┐  │    │  ┌───────────────┐  │    │  ┌───────────────┐  │
│  │    LLM API    │  │    │  │  Embedding API│  │    │  │  Retriever +  │  │
│  │ (OpenAI/      │  │    │  │ (OpenAI/      │  │    │  │    LLM API    │  │
│  │  Ollama/      │  │    │  │  Ollama/      │  │    │  │               │  │
│  │  VertexAI)    │  │    │  │  VertexAI)    │  │    │  │               │  │
│  └───────────────┘  │    │  └───────────────┘  │    │  └───────────────┘  │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATA LAYER                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    PostgreSQL + pgvector                              │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │   │
│  │  │ tickets      │  │ embeddings   │  │ indexes      │               │   │
│  │  │ (metadata)   │  │ (vector)     │  │ (HNSW)       │               │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Processing Flow

```
                    ┌─────────────────────┐
                    │   Input Ticket      │
                    │  (number, context,  │
                    │      domain)        │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   TicketAgent       │
                    │  determine_status() │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
        ┌──────────┐    ┌──────────┐    ┌──────────┐
        │ is_resolved     │ is_resolved     │ is_resolved
        │  = True  │    │  = False │    │  = None  │
        └────┬─────┘    └────┬─────┘    └────┬─────┘
             │               │               │
             ▼               ▼               ▼
    ┌─────────────────┐ ┌───────────┐ ┌───────────┐
    │ analyze_cause() │ │   Store   │ │   Store   │
    │ analyze_resol() │ │  status   │ │  status   │
    │                 │ │   only    │ │   only    │
    └────────┬────────┘ └───────────┘ └───────────┘
             │
             ▼
    ┌─────────────────┐
    │ EmbeddingAgent  │
    │ generate_embed()│
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │   Store Full    │
    │   Ticket +      │
    │   Embedding     │
    └─────────────────┘
```

### 2.3 RAG Retrieval Flow

```
┌─────────────────────┐
│  Query Problem      │
│  + Domain           │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ EmbeddingAgent      │
│ generate_embedding  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PostgreSQL + pgvector                         │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ SELECT * FROM tickets                                        ││
│  │ WHERE domain = :domain                                       ││
│  │   AND is_resolved = true                                     ││
│  │   AND cause_embedding IS NOT NULL                            ││
│  │ ORDER BY cause_embedding <=> :query_embedding                ││
│  │ LIMIT :top_k                                                 ││
│  └─────────────────────────────────────────────────────────────┘│
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Similar Tickets   │
                    │   (Same Domain)     │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ ResolutionGenerator │
                    │   (LLM + Context)   │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Resolution          │
                    │ Suggestions         │
                    └─────────────────────┘
```

---

## 3. Installation

### 3.1 Prerequisites

- Python 3.11+
- PostgreSQL 14+ with pgvector extension
- Docker and Docker Compose (optional, for containerized deployment)

### 3.2 Local Installation

```bash
# Clone the repository
git clone <repository-url>
cd ticket_rag_system

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp env-2.example .env

# Edit configuration
nano .env
```

### 3.3 Database Setup

```bash
# Ensure PostgreSQL is running with pgvector extension
# Create database
createdb vectordb

# Run setup script
python scripts/setup_db.py

# To reset database (WARNING: deletes all data)
python scripts/setup_db.py --drop
```

### 3.4 Docker Installation

```bash
# Copy environment file
cp env-2.example .env

# Edit configuration for Docker
nano .env

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f ticket-rag-api

# Stop services
docker-compose down
```

---

## 4. Configuration

### 4.1 Environment Variables

Create a `.env` file in the project root:

```bash
# =============================================================================
# API SELECTION
# =============================================================================
# Options: "openai", "ollama", "vertexai"
API_TYPE=openai

# =============================================================================
# OPENAI CONFIGURATION (Azure OpenAI)
# =============================================================================
OPENAI_API_TYPE=azure
OPENAI_API_KEY=your-azure-openai-api-key-here
OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
OPENAI_API_VERSION=2023-05-15
OPENAI_MODEL=gpt-4
OPENAI_EMBEDDING_MODEL=text-embedding-ada-002
OPENAI_EMBEDDING_VEC_LEN=1536

# =============================================================================
# OLLAMA CONFIGURATION (On-Premises)
# =============================================================================
OLLAMA_ENDPOINT=http://localhost:11434
OLLAMA_MODEL=llama3.1
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
OLLAMA_EMBEDDING_VEC_LEN=768

# =============================================================================
# VERTEXAI CONFIGURATION (Google Cloud)
# =============================================================================
VERTEXAI_PROJECT_ID=your-gcp-project-id
VERTEXAI_REGION=us-central1
VERTEXAI_MODEL=gemini-1.5-flash
VERTEXAI_EMBEDDING_MODEL=text-embedding-004
VERTEXAI_EMBEDDING_VEC_LEN=768

# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================
DB_HOST=localhost
DB_PORT=5432
DB_NAME=vectordb
DB_USER=postgres
DB_PASSWORD=your-postgres-password

# =============================================================================
# RAG CONFIGURATION
# =============================================================================
RAG_TOP_K=5                           # Number of similar tickets to retrieve
RAG_SIMILARITY_THRESHOLD=0.7          # Minimum similarity score (0-1)

# =============================================================================
# AGENT CONFIGURATION
# =============================================================================
AGENT_MAX_TOKENS=2000                 # Max tokens for LLM responses
AGENT_TEMPERATURE=0.0                 # LLM temperature (0.0 for deterministic)
AGENT_MAX_RETRIES=3                   # Max retries for API calls

# =============================================================================
# APPLICATION CONFIGURATION
# =============================================================================
LOG_LEVEL=INFO                        # DEBUG, INFO, WARNING, ERROR
BATCH_SIZE=100                        # Default batch size for processing
```

### 4.2 Configuration Class

The `Config` class in `src/utils/config.py` manages all settings:

```python
from src.utils.config import get_config, reload_config

# Get configuration (loaded once, cached)
config = get_config()

# Access settings
print(f"API Type: {config.api_type}")
print(f"Database URL: {config.database_url}")
print(f"Embedding Dimension: {config.embedding_vec_len}")

# Reload from environment
config = reload_config()
```

### 4.3 API Provider Selection

| Provider | API_TYPE | Models | Embedding Dimension |
|----------|----------|--------|---------------------|
| Azure OpenAI | `openai` | GPT-4, GPT-3.5 | 1536 |
| Ollama | `ollama` | Llama, Mistral, etc. | 768 (varies) |
| VertexAI | `vertexai` | Gemini | 768 |

---

## 5. Core Components

### 5.1 TicketPipeline

The main orchestration class that coordinates all operations.

**Location**: `src/pipeline.py`

```python
from src.pipeline import TicketPipeline

# Initialize
pipeline = TicketPipeline()

# Process single ticket
result = pipeline.process_ticket(
    ticket_number="TI001",
    context="DNS server CPU high. Restarted service and patched. CPU normal.",
    domain="Network"
)

# Access results
print(f"Resolved: {result.is_resolved}")      # True/False/None
print(f"Cause: {result.cause_summary}")        # Only if resolved=True
print(f"Resolution: {result.resolution_summary}")
print(f"Embedding Generated: {result.embedding_generated}")

# Batch processing
import pandas as pd
df = pd.DataFrame([
    {"ticket_number": "TI001", "context": "...", "domain": "Network"},
    {"ticket_number": "TI002", "context": "...", "domain": "Security"},
])
results = pipeline.process_batch(df, show_progress=True)

# Find similar tickets
similar = pipeline.get_similar_tickets(
    query="DNS high CPU usage",
    domain="Network",
    top_k=5
)

# Get resolution suggestions
suggestions = pipeline.suggest_resolution(
    problem_description="Server responding slowly",
    domain="Infrastructure",
    top_k=5
)
```

### 5.2 TicketAgent

Handles ticket analysis using LLM.

**Location**: `src/agents/ticket_agent.py`

```python
from src.agents import TicketAgent
from src.utils.config import get_config

config = get_config()
agent = TicketAgent(config)

# Analyze ticket
analysis = agent.analyze(context)

# Check results
if analysis.is_resolved is True:
    print(f"Cause: {analysis.cause_summary}")
    print(f"Keywords: {analysis.keywords}")
    print(f"Resolution: {analysis.resolution_summary}")
    print(f"Steps: {analysis.resolution_steps}")
elif analysis.is_resolved is False:
    print("Ticket is not resolved")
else:
    print("Status uncertain")
```

**Methods**:

| Method | Description | Returns |
|--------|-------------|---------|
| `determine_status(context)` | Check if ticket is resolved | `True/False/None` |
| `analyze_cause(context)` | Extract root cause and keywords | `(cause, keywords)` |
| `analyze_resolution(context)` | Extract resolution details | `(summary, steps)` |
| `analyze(context)` | Full analysis pipeline | `TicketAnalysis` |

### 5.3 EmbeddingAgent

Generates vector embeddings for semantic search.

**Location**: `src/agents/embedding_agent.py`

```python
from src.agents import EmbeddingAgent, CachedEmbeddingAgent
from src.utils.config import get_config

config = get_config()
agent = EmbeddingAgent(config)

# Generate embedding for text
embedding = agent.generate_embedding("DNS server CPU issue")
print(f"Shape: {embedding.shape}")  # (768,) or (1536,)

# Prepare text for embedding
text = agent.prepare_text_for_embedding(
    cause_summary="DNS server memory leak causing CPU spike",
    keywords=["DNS", "CPU", "memory leak"],
    domain="Network"
)

# Batch embeddings
embeddings = agent.generate_batch_embeddings([
    "DNS issue",
    "Network timeout",
    "Server crash"
])

# Use cached version for performance
cached_agent = CachedEmbeddingAgent(config)
```

---

## 6. Database Layer

### 6.1 Schema

```sql
CREATE TABLE tickets (
    id SERIAL PRIMARY KEY,
    ticket_number VARCHAR(50) UNIQUE NOT NULL,
    cra TEXT,                                    -- Activity report context
    domain VARCHAR(100),                         -- Problem domain
    is_resolved BOOLEAN,                         -- Resolution status
    cause TEXT,                                  -- Root cause analysis
    resolution_summary TEXT,                     -- Resolution summary
    cause_embedding vector(1536),                -- Vector embedding
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_ticket_number ON tickets(ticket_number);
CREATE INDEX idx_is_resolved ON tickets(is_resolved);
CREATE INDEX idx_domain_resolved ON tickets(domain, is_resolved);
CREATE INDEX idx_cause_embedding ON tickets
    USING hnsw (cause_embedding vector_cosine_ops);
```

### 6.2 TicketRepository

Database operations class.

**Location**: `src/database/repository.py`

```python
from src.database import TicketRepository
from src.utils.config import get_config

config = get_config()
repo = TicketRepository(config)

# Create tables
repo.create_tables()

# Create ticket
ticket = repo.create_ticket(
    ticket_number="TI001",
    cra="DNS server CPU issue...",
    domain="Network",
    is_resolved=True,
    cause="Memory leak in DNS service",
    resolution_summary="Restarted and patched",
    cause_embedding=embedding
)

# Get ticket by number
ticket = repo.get_ticket_by_number("TI001")

# Update ticket
repo.update_ticket(
    ticket_number="TI001",
    is_resolved=True,
    cause="Updated cause info"
)

# Search similar tickets (requires domain)
results = repo.search_similar_tickets(
    query_embedding=embedding,
    domain="Network",
    top_k=5,
    similarity_threshold=0.7
)

# Get statistics
total = repo.count_tickets()
resolved = repo.count_tickets(resolved_only=True)
domains = repo.get_all_domains()
```

### 6.3 TicketSearchResult

Search result wrapper class.

```python
@dataclass
class TicketSearchResult:
    ticket: Ticket
    similarity: float
    distance: float

    # Properties
    ticket_number: str
    cause: str
    resolution_summary: str

    # Methods
    def to_dict() -> dict
```

---

## 7. RAG System

### 7.1 TicketRetriever

Handles vector similarity search with domain filtering.

**Location**: `src/rag/retriever.py`

```python
from src.rag import TicketRetriever
from src.utils.config import get_config

config = get_config()
retriever = TicketRetriever(config)

# Find similar tickets (domain is REQUIRED)
results = retriever.find_similar(
    query="DNS server high CPU usage",
    domain="Network",
    top_k=5,
    similarity_threshold=0.7
)

# Get formatted context for LLM
context = retriever.retrieve_context(
    query="Server performance issue",
    domain="Infrastructure",
    top_k=3,
    include_cause=True,
    include_resolution=True
)
```

### 7.2 ResolutionGenerator

Generates resolution suggestions using RAG.

**Location**: `src/rag/generator.py`

```python
from src.rag import ResolutionGenerator
from src.utils.config import get_config

config = get_config()
generator = ResolutionGenerator(config)

# Generate resolution suggestions
suggestions = generator.generate_resolution(
    problem_description="DNS server responding slowly with high CPU",
    domain="Network",
    top_k=5
)

print(suggestions)
```

---

## 8. API Reference

### 8.1 Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Root health check |
| GET | `/health` | Health check |
| GET | `/status` | System status and configuration |
| POST | `/analyze` | Analyze single ticket |
| POST | `/analyze/batch` | Batch analyze tickets |
| GET | `/tickets/{ticket_number}` | Get ticket by number |
| POST | `/search` | Find similar tickets |
| POST | `/suggest-resolution` | Get resolution suggestions |
| GET | `/domains` | List all domains |
| GET | `/stats` | Database statistics |

### 8.2 Request/Response Models

#### POST /analyze

**Request**:
```json
{
    "ticket_number": "TI001",
    "context": "DNS server CPU exceeded 60% threshold...",
    "domain": "Network"
}
```

**Response**:
```json
{
    "ticket_number": "TI001",
    "domain": "Network",
    "is_resolved": true,
    "cause_summary": "DNS server memory leak causing CPU spike",
    "keywords": ["DNS", "CPU", "memory leak", "performance"],
    "resolution_summary": "Restarted DNS service and applied patch v2.1.5",
    "resolution_steps": [
        "Restart DNS service",
        "Apply patch version 2.1.5",
        "Verify CPU usage returned to normal",
        "Monitor for 24 hours"
    ],
    "embedding_generated": true,
    "saved_to_db": true,
    "error": null
}
```

#### POST /analyze/batch

**Request**:
```json
{
    "tickets": [
        {"ticket_number": "TI001", "context": "...", "domain": "Network"},
        {"ticket_number": "TI002", "context": "...", "domain": "Security"}
    ],
    "show_progress": false
}
```

**Response**:
```json
{
    "results": [...],
    "summary": {
        "total": 2,
        "resolved": 1,
        "unresolved": 1,
        "uncertain": 0
    }
}
```

#### POST /search

**Request**:
```json
{
    "query": "DNS server high CPU usage",
    "domain": "Network",
    "top_k": 5,
    "similarity_threshold": 0.7
}
```

**Response**:
```json
[
    {
        "ticket_number": "TI001",
        "similarity": 0.92,
        "cause": "DNS memory leak causing CPU spike",
        "resolution_summary": "Restarted and patched DNS service"
    }
]
```

#### POST /suggest-resolution

**Request**:
```json
{
    "problem_description": "DNS server responding slowly with high CPU",
    "domain": "Network",
    "top_k": 5
}
```

**Response**:
```json
{
    "suggestions": "SUGGESTION 1: Restart DNS Service\nConfidence: High\n..."
}
```

#### GET /status

**Response**:
```json
{
    "status": "healthy",
    "api_type": "openai",
    "database_connected": true,
    "models": {
        "llm": "gpt-4",
        "embedding": "text-embedding-ada-002"
    }
}
```

#### GET /stats

**Response**:
```json
{
    "total_tickets": 1000,
    "resolved_tickets": 650,
    "unresolved_tickets": 350,
    "domains": ["Network", "Security", "Infrastructure", "Application"]
}
```

### 8.3 Running the API

```bash
# Development
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --workers 4

# Docker
docker-compose up -d
```

### 8.4 API Documentation

Access interactive API documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## 9. Prompt Engineering

### 9.1 Prompt Templates

All prompts are centralized in `prompts/templates.py` for easy maintenance and A/B testing.

#### STATUS_ANALYSIS_PROMPT

Determines if a ticket is resolved.

```
Returns: "Yes" (resolved) | "No" (not resolved) | None (uncertain)
```

Key criteria:
- **Resolved**: Explicit resolution actions taken
- **Not Resolved**: Issue disappeared without intervention, still ongoing
- **Uncertain**: Insufficient or contradictory information

#### CAUSE_ANALYSIS_PROMPT

Extracts root cause and keywords.

Output format:
```
CAUSE: <concise root cause summary>
KEYWORDS: <keyword1>, <keyword2>, <keyword3>
```

#### RESOLUTION_ANALYSIS_PROMPT

Documents resolution steps.

Output format:
```
RESOLUTION: <concise resolution summary>
STEPS:
1. <first action>
2. <second action>
...
```

#### RAG_RESOLUTION_PROMPT

Generates resolution suggestions based on similar tickets.

### 9.2 Customizing Prompts

```python
# Edit prompts/templates.py
# Changes are immediately effective (no code changes needed)

STATUS_ANALYSIS_PROMPT = """
Your custom prompt here...
{context}
"""

# Version tracking
def get_prompt_version():
    return "2.1.0"  # Increment when prompts change
```

### 9.3 Prompt Validation

```python
from prompts.templates import validate_prompts, get_prompt_version

# Validate on import (automatic)
validate_prompts()

# Get current version
version = get_prompt_version()
```

---

## 10. Usage Examples

### 10.1 Basic Usage

```python
from src.pipeline import TicketPipeline

# Initialize pipeline
pipeline = TicketPipeline()

# Process a resolved ticket
result = pipeline.process_ticket(
    ticket_number="TI0000001",
    context="""
        alarme cleared 2025-11-06 23:48:25
        DNS server CPU usage exceeded 60% threshold due to memory leak.
        Restarted DNS service and applied patch version 2.1.5.
        CPU usage returned to normal levels (<30%).
        Monitoring for 24h before final closure.
    """,
    domain="Network"
)

print(f"Is Resolved: {result.is_resolved}")  # True
print(f"Cause: {result.cause_summary}")
print(f"Keywords: {result.keywords}")
print(f"Resolution: {result.resolution_summary}")
```

### 10.2 Processing Unresolved Tickets

```python
# Process an unresolved ticket
result = pipeline.process_ticket(
    ticket_number="TI0000002",
    context="""
        Security vulnerability CVE-2025-40778
        Disparu avant intervention
        Domaine du problème: Disparu avant intervention
    """,
    domain="Security"
)

print(f"Is Resolved: {result.is_resolved}")  # False
print(f"Cause: {result.cause_summary}")      # None (skipped analysis)
print(f"Embedding: {result.embedding_generated}")  # False
```

### 10.3 Batch Processing from CSV

```bash
# Create input CSV (tickets.csv)
ticket_number,context,domain
TI001,"DNS CPU high issue...","Network"
TI002,"Security alert...","Security"

# Run batch processing
python scripts/process_tickets.py tickets.csv --output results.csv

# With options
python scripts/process_tickets.py tickets.csv \
    --output results.csv \
    --ticket-col ticket_number \
    --context-col context \
    --domain-col domain \
    --log-level DEBUG
```

### 10.4 Finding Similar Tickets

```python
# Find similar resolved tickets
similar = pipeline.get_similar_tickets(
    query="DNS server experiencing high CPU usage",
    domain="Network",  # REQUIRED
    top_k=5
)

for result in similar:
    print(f"Ticket: {result['ticket_number']}")
    print(f"Similarity: {result['similarity']:.2%}")
    print(f"Cause: {result['cause']}")
    print(f"Resolution: {result['resolution_summary']}")
    print()
```

### 10.5 Resolution Suggestions

```python
# Get resolution suggestions
suggestions = pipeline.suggest_resolution(
    problem_description="""
        DNS server on 10.131.17.197 is experiencing high CPU usage (>60%).
        This has been ongoing for several hours.
    """,
    domain="Network",
    top_k=5
)

print(suggestions)
```

### 10.6 Using the API

```python
import requests

BASE_URL = "http://localhost:8000"

# Analyze ticket
response = requests.post(f"{BASE_URL}/analyze", json={
    "ticket_number": "TI001",
    "context": "DNS server CPU issue...",
    "domain": "Network"
})
result = response.json()

# Search similar tickets
response = requests.post(f"{BASE_URL}/search", json={
    "query": "DNS high CPU",
    "domain": "Network",
    "top_k": 5
})
similar = response.json()

# Get resolution suggestions
response = requests.post(f"{BASE_URL}/suggest-resolution", json={
    "problem_description": "Server slow",
    "domain": "Infrastructure"
})
suggestions = response.json()
```

---

## 11. Deployment

### 11.1 Docker Deployment

```yaml
# docker-compose.yml
services:
  pgvector:
    image: ankane/pgvector:v0.5.1
    ports:
      - "5432:5432"
    environment:
      POSTGRES_DB: vectordb
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"

  ticket-rag-api:
    build: .
    ports:
      - "8000:8080"
    environment:
      - API_TYPE=ollama
      - OLLAMA_ENDPOINT=http://ollama:11434
      - DB_HOST=pgvector
      - DB_PORT=5432
      - DB_NAME=vectordb
      - DB_USER=postgres
      - DB_PASSWORD=password
    depends_on:
      - pgvector
      - ollama
```

```bash
# Build and start
docker-compose up -d

# Check logs
docker-compose logs -f ticket-rag-api

# Scale API
docker-compose up -d --scale ticket-rag-api=3
```

### 11.2 Production Considerations

1. **Database**:
   - Use connection pooling
   - Configure appropriate HNSW index parameters
   - Regular backups
   - Monitor query performance

2. **API**:
   - Use multiple workers: `uvicorn app:app --workers 4`
   - Enable CORS appropriately
   - Add rate limiting
   - Use HTTPS

3. **LLM Provider**:
   - Monitor API costs
   - Implement caching for repeated queries
   - Consider fallback providers

4. **Monitoring**:
   - Log aggregation
   - Performance metrics
   - Error tracking

### 11.3 Environment Variables for Production

```bash
# Production .env
API_TYPE=openai
OPENAI_API_KEY=${OPENAI_API_KEY}
OPENAI_ENDPOINT=${OPENAI_ENDPOINT}
DB_HOST=postgres.production.internal
DB_PORT=5432
DB_NAME=ticket_rag
DB_USER=${DB_USER}
DB_PASSWORD=${DB_PASSWORD}
LOG_LEVEL=WARNING
AGENT_MAX_TOKENS=2000
AGENT_TEMPERATURE=0.0
RAG_TOP_K=5
RAG_SIMILARITY_THRESHOLD=0.7
```

---

## 12. Troubleshooting

### 12.1 Common Issues

#### Database Connection Errors

```
Error: could not connect to server: Connection refused
```

**Solution**:
- Verify PostgreSQL is running
- Check connection parameters in `.env`
- Ensure pgvector extension is installed:
  ```sql
  CREATE EXTENSION IF NOT EXISTS vector;
  ```

#### API Key Errors

```
Error: Invalid API key
```

**Solution**:
- Verify `OPENAI_API_KEY` is set correctly
- Check API endpoint URL
- Ensure key has required permissions

#### Vector Dimension Mismatch

```
Error: embedding dimension mismatch
```

**Solution**:
- Ensure `*_EMBEDDING_VEC_LEN` matches your embedding model
- OpenAI: 1536
- Ollama: varies (check model documentation)
- VertexAI: 768

#### Domain Required Error

```
ValueError: Domain is required for ticket retrieval
```

**Solution**:
- Always provide `domain` parameter for retrieval operations
- Domain filtering is mandatory for relevance

### 12.2 Debugging

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run with verbose output
python scripts/process_tickets.py tickets.csv --log-level DEBUG

# Check API health
curl http://localhost:8000/status
```

### 12.3 Performance Tuning

1. **Embedding Cache**: Use `CachedEmbeddingAgent` for repeated queries
2. **Batch Processing**: Use batch embedding generation
3. **Database Indexes**: Ensure HNSW index is created
4. **Connection Pooling**: Configure pool size in repository

---

## Appendix A: File Structure

```
ticket_rag_system/
├── prompts/
│   ├── __init__.py
│   └── templates.py              # Prompt templates
├── src/
│   ├── __init__.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── ticket_agent.py       # Ticket analysis agent
│   │   └── embedding_agent.py    # Embedding generation
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py               # FastAPI application
│   │   └── models.py             # Pydantic models
│   ├── database/
│   │   ├── __init__.py
│   │   ├── models.py             # SQLAlchemy models
│   │   └── repository.py         # Database operations
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── retriever.py          # Vector search
│   │   └── generator.py          # Resolution generation
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── config.py             # Configuration management
│   │   └── logger.py             # Logging utilities
│   └── pipeline.py               # Main orchestration
├── scripts/
│   ├── setup_db.py               # Database initialization
│   └── process_tickets.py        # Batch processing script
├── tests/
│   └── test_agents.py            # Unit tests
├── notebooks/                    # Jupyter notebooks
├── docker_data/                  # Docker volumes
├── .env                          # Environment variables
├── .env.example                  # Environment template
├── docker-compose.yml            # Docker composition
├── Dockerfile                    # Container definition
├── requirements.txt              # Python dependencies
├── README.md                     # Quick start guide
└── DOCUMENTATION.md              # This file
```

---

## Appendix B: Dependencies

```
# requirements.txt

# Core dependencies
ollama>=0.6.1
openai>=1.0.0
google-genai>=0.3.0
python-dotenv>=1.0.0
pandas>=2.0.0
numpy>=1.24.0

# Database
psycopg2-binary>=2.9.0
sqlalchemy>=2.0.0
pgvector>=0.2.0

# Configuration
pydantic>=2.0.0
pydantic-settings>=2.0.0

# Utilities
tenacity>=8.2.0
python-json-logger>=2.0.0
tqdm>=4.66.0

# Web Framework
fastapi>=0.115.0
uvicorn>=0.32.0
python-multipart>=0.0.19

# Testing
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-mock>=3.11.0

# Development
black>=23.0.0
flake8>=6.1.0
isort>=5.12.0
jupyter>=1.0.0
```

---

## Appendix C: Error Codes

| Code | Description | Solution |
|------|-------------|----------|
| `E001` | Database connection failed | Check DB credentials and status |
| `E002` | API key invalid | Verify API key configuration |
| `E003` | Embedding generation failed | Check embedding model availability |
| `E004` | Domain required | Provide domain parameter |
| `E005` | Ticket not found | Verify ticket number exists |
| `E006` | Vector dimension mismatch | Check embedding dimension config |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 3.0 | 2025-02 | VertexAI support, FastAPI endpoints |
| 2.1 | 2025-01 | Dual API support (OpenAI & Ollama) |
| 2.0 | 2024-12 | Unified agent, conditional processing, domain filtering |
| 1.0 | 2024-11 | Initial release |

---

**Documentation maintained by the Ticket RAG System team.**