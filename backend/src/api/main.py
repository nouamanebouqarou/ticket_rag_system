"""FastAPI application for Ticket RAG System."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

from src.utils.config import get_config
from src.agents import TicketAgent, EmbeddingAgent
from src.database import TicketRepository
from src.rag import TicketRetriever, ResolutionGenerator
from src.pipeline import TicketPipeline

from .models import (
    TicketAnalysisRequest,
    TicketBatchRequest,
    SimilarTicketsRequest,
    ResolutionRequest,
    TicketAnalysisResponse,
    TicketBatchResponse,
    SimilarTicketResponse,
    ResolutionResponse,
    StatusResponse,
    HealthResponse,
)

app = FastAPI(
    title="Ticket RAG API",
    description="API for IT support ticket analysis using RAG",
    version="3.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_pipeline() -> TicketPipeline:
    """Get or create pipeline instance."""
    config = get_config()
    return TicketPipeline(config)


@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint."""
    return {"health": "ok"}


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    return {"health": "ok"}


@app.get("/status", response_model=StatusResponse)
async def status():
    """Get system status and configuration."""
    config = get_config()

    try:
        pipeline = get_pipeline()
        db_connected = True
    except Exception:
        db_connected = False

    return {
        "status": "healthy" if db_connected else "database_unavailable",
        "api_type": config.api_type,
        "database_connected": db_connected,
        "models": {
            "llm": config.openai_model if config.api_type == "openai" else (
                config.ollama_model if config.api_type == "ollama" else config.vertexai_model
            ),
            "embedding": config.openai_embedding_model if config.api_type == "openai" else (
                config.ollama_embedding_model if config.api_type == "ollama" else config.vertexai_embedding_model
            )
        }
    }


@app.post("/analyze", response_model=TicketAnalysisResponse)
async def analyze_ticket(request: TicketAnalysisRequest):
    """Analyze a single ticket."""
    try:
        pipeline = get_pipeline()
        result = pipeline.process_ticket(
            ticket_number=request.ticket_number,
            context=request.context,
            domain=request.domain,
            save_to_db=True
        )
        return TicketAnalysisResponse(**result.to_dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze/batch", response_model=TicketBatchResponse)
async def analyze_tickets_batch(request: TicketBatchRequest):
    """Analyze multiple tickets in batch."""
    try:
        pipeline = get_pipeline()
        results = pipeline.process_batch(
            tickets_df=pipeline.__class__.__dict__.get('__annotations__', {}).get('tickets_df'),
            show_progress=request.show_progress
        )

        # Convert to DataFrame
        import pandas as pd
        df_data = []
        for t in request.tickets:
            df_data.append({
                'ticket_number': t.ticket_number,
                'context': t.context,
                'domain': t.domain
            })
        df = pd.DataFrame(df_data)

        results = pipeline.process_batch(
            tickets_df=df,
            show_progress=request.show_progress
        )

        return TicketBatchResponse(
            results=[TicketAnalysisResponse(**r.to_dict()) for r in results],
            summary={
                "total": len(results),
                "resolved": sum(1 for r in results if r.is_resolved is True),
                "unresolved": sum(1 for r in results if r.is_resolved is False),
                "uncertain": sum(1 for r in results if r.is_resolved is None),
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tickets/{ticket_number}", response_model=TicketAnalysisResponse)
async def get_ticket(ticket_number: str):
    """Get a ticket by its number."""
    try:
        pipeline = get_pipeline()
        ticket = pipeline.repository.get_ticket_by_number(ticket_number)
        if ticket is None:
            raise HTTPException(status_code=404, detail="Ticket not found")
        return TicketAnalysisResponse(
            ticket_number=ticket.ticket_number,
            domain=ticket.domain,
            is_resolved=ticket.is_resolved,
            cause_summary=ticket.cause,
            resolution_summary=ticket.resolution_summary,
            saved_to_db=True
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search", response_model=list[SimilarTicketResponse])
async def search_similar_tickets(request: SimilarTicketsRequest):
    """Search for similar tickets within the same domain."""
    try:
        pipeline = get_pipeline()
        results = pipeline.get_similar_tickets(
            query=request.query,
            domain=request.domain,
            top_k=request.top_k,
            similarity_threshold=request.similarity_threshold
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/suggest-resolution", response_model=ResolutionResponse)
async def suggest_resolution(request: ResolutionRequest):
    """Generate resolution suggestions for a problem."""
    try:
        pipeline = get_pipeline()
        suggestions = pipeline.suggest_resolution(
            problem_description=request.problem_description,
            domain=request.domain,
            top_k=request.top_k
        )
        return ResolutionResponse(suggestions=suggestions)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/domains", response_model=list[str])
async def get_domains():
    """Get all domains in the database."""
    try:
        pipeline = get_pipeline()
        return pipeline.repository.get_all_domains()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats", response_model=dict)
async def get_stats():
    """Get database statistics."""
    try:
        pipeline = get_pipeline()
        total = pipeline.repository.count_tickets()
        resolved = pipeline.repository.count_tickets(resolved_only=True)
        domains = pipeline.repository.get_all_domains()
        return {
            "total_tickets": total,
            "resolved_tickets": resolved,
            "unresolved_tickets": total - resolved,
            "domains": domains
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
