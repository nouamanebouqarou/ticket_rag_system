# Ticket RAG System - React Frontend

A modern React-based frontend for the Ticket RAG System API.

## Features

- **Dashboard**: View system statistics and available domains
- **Analyze Ticket**: Submit tickets for AI-powered analysis
- **Search Similar**: Find similar resolved tickets using semantic search
- **Suggest Resolution**: Get AI-generated resolution suggestions

## Prerequisites

- Node.js 16+
- npm or yarn
- Backend API running on `http://localhost:8000`

## Installation

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install
```

## Configuration

Create a `.env` file in the frontend directory:

```env
REACT_APP_API_URL=http://localhost:8000
```

## Running

```bash
# Start development server
npm start
```

The app will be available at `http://localhost:3000`.

## Building for Production

```bash
# Create production build
npm run build
```

The build output will be in the `build/` directory.

## Project Structure

```
frontend/
├── public/
│   └── index.html
├── src/
│   ├── components/
│   │   ├── Dashboard.js        # Statistics dashboard
│   │   ├── TicketAnalyzer.js   # Ticket analysis form
│   │   ├── TicketSearch.js     # Similar ticket search
│   │   └── ResolutionSuggester.js  # Resolution suggestions
│   ├── services/
│   │   └── api.js              # API client
│   ├── App.js                  # Main application component
│   ├── App.css                 # Styles
│   └── index.js                # Entry point
├── package.json
└── README.md
```

## API Endpoints Used

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/status` | GET | System status |
| `/stats` | GET | Database statistics |
| `/domains` | GET | List all domains |
| `/analyze` | POST | Analyze a ticket |
| `/search` | POST | Search similar tickets |
| `/suggest-resolution` | POST | Get resolution suggestions |

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
Edit `src/App.css` to customize the appearance. The app uses CSS variables for easy theming:

```css
:root {
  --primary: #6366f1;
  --secondary: #0ea5e9;
  --success: #10b981;
  --warning: #f59e0b;
  --danger: #ef4444;
  --bg-dark: #1a1a2e;
  --bg-card: #16213e;
  --bg-input: #0f172a;
  --text-primary: #f1f5f9;
  --text-secondary: #94a3b8;
  --border: #334155;
}
```

### API Configuration
Update `src/services/api.js` to change the API base URL or add authentication headers.

## Troubleshooting

### CORS Issues
If you see CORS errors, ensure the backend has CORS enabled for `http://localhost:3000`.

### Connection Refused
Make sure the backend API is running on port 8000:
```bash
cd ..
source venv/bin/activate
uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

### Empty Domains List
If the domains dropdown is empty, make sure you've analyzed some tickets first.