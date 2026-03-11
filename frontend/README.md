# Ticket RAG System - Streamlit Frontend

A modern Streamlit-based frontend for the Ticket RAG System API.

## Features

- **Dashboard**: View system statistics and available domains
- **Analyze Ticket**: Submit tickets for AI-powered analysis
- **Search Similar**: Find similar resolved tickets using semantic search
- **Suggest Resolution**: Get AI-generated resolution suggestions

## Prerequisites

- Python 3.11+
- pip
- Backend API running on `http://localhost:8080`

## Installation

```bash
# Navigate to frontend directory
cd frontend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Configuration

Set the API URL environment variable (optional, defaults to `http://localhost:8080`):

```bash
export API_URL=http://localhost:8000
```

Or when running with Docker, set in your `.env` file:

```env
API_URL=http://ticket-rag-api:8080
```

## Running

```bash
# Start Streamlit server
streamlit run app.py
```

The app will be available at `http://localhost:8501`.

## Running with Docker

```bash
# Build and run with docker-compose
docker-compose up --build ticket-rag-frontend
```

The app will be available at `http://localhost:${FRONTEND_PORT}` (default: 3000).

## Project Structure

```
frontend/
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker image configuration
├── .dockerignore         # Docker ignore rules
└── README.md
```

## API Endpoints Used

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/status` | GET | System status |
| `/api/stats` | GET | Database statistics |
| `/api/domains` | GET | List all domains |
| `/api/analyze` | POST | Analyze a ticket |
| `/api/search` | POST | Search similar tickets |
| `/api/suggest-resolution` | POST | Get resolution suggestions |

## Screenshots

### Dashboard
Shows total tickets, resolved/unresolved counts, and available domains.

### Analyze Ticket
Submit a ticket for analysis. The system will:
1. Determine if the ticket is resolved
2. Extract root cause and keywords
3. Document resolution steps
4. Generate embeddings for semantic search

### Search Similar
Find similar resolved tickets by describing the problem. Results are filtered by domain.

### Suggest Resolution
Get AI-powered resolution suggestions based on historically similar tickets.

## Customization

### Styling
The app uses custom CSS embedded in `app.py`. Modify the CSS in the `st.markdown()` block to change the appearance:

```python
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
    }
    /* Add your custom styles here */
</style>
""", unsafe_allow_html=True)
```

Streamlit theming can also be configured via `~/.streamlit/config.toml`:

```toml
[theme]
primaryColor = "#6366f1"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
```

### API Configuration
Update the `API_BASE_URL` variable at the top of `app.py` to change the API endpoint:

```python
API_BASE_URL = os.getenv('API_URL', 'http://localhost:8000')
```

## Troubleshooting

### Connection Refused
Make sure the backend API is running on port 8000:
```bash
cd ..
uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

### Empty Domains List
If the domains dropdown is empty, make sure you've analyzed some tickets first.

### Streamlit Not Found
If you get "command not found: streamlit", make sure you've installed the requirements:
```bash
pip install -r requirements.txt
```

Or run via Python module:
```bash
python -m streamlit run app.py
```

### Port Already in Use
If port 8501 is already in use, specify a different port:
```bash
streamlit run app.py --server.port 8502
```
