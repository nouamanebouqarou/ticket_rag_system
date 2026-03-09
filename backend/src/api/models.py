"""Pydantic models for API requests and responses."""

from typing import Optional, List
from pydantic import BaseModel


# Request Models
class TicketAnalysisRequest(BaseModel):
    """Request model for ticket analysis."""
    ticket_number: str
    context: str
    domain: Optional[str] = None


class TicketBatchRequest(BaseModel):
    """Request model for batch ticket processing."""
    tickets: List[TicketAnalysisRequest]
    show_progress: bool = False


class SimilarTicketsRequest(BaseModel):
    """Request model for finding similar tickets."""
    query: str
    domain: str
    top_k: int = 5
    similarity_threshold: float = 0.7


class ResolutionRequest(BaseModel):
    """Request model for resolution suggestions."""
    problem_description: str
    domain: str
    top_k: int = 5


# Response Models
class TicketAnalysisResponse(BaseModel):
    """Response model for ticket analysis."""
    ticket_number: str
    domain: Optional[str] = None
    is_resolved: Optional[bool] = None
    cause_summary: Optional[str] = None
    keywords: Optional[List[str]] = None
    resolution_summary: Optional[str] = None
    resolution_steps: Optional[List[str]] = None
    embedding_generated: bool = False
    saved_to_db: bool = False
    error: Optional[str] = None


class TicketBatchResponse(BaseModel):
    """Response model for batch processing."""
    results: List[TicketAnalysisResponse]
    summary: dict


class SimilarTicketResponse(BaseModel):
    """Response model for similar ticket search."""
    ticket_number: str
    similarity: float
    cause: Optional[str] = None
    resolution_summary: Optional[str] = None


class ResolutionResponse(BaseModel):
    """Response model for resolution suggestions."""
    suggestions: str


class StatusResponse(BaseModel):
    """Response model for system status."""
    status: str
    api_type: str
    database_connected: bool
    models: dict


# Special response for OpenAPI docs
class HealthResponse(BaseModel):
    """Health check response."""
    health: str = "ok"


class ErrorDetail(BaseModel):
    """Error detail model."""
    message: str


class ErrorResponse(BaseModel):
    """Error response model."""
    error: ErrorDetail
