"""Database package for the Ticket RAG System."""

from .models import Base, Ticket, TicketSearchResult, EMBEDDING_DIMENSION
from .repository import TicketRepository, set_embedding_dimension

__all__ = [
    'Base',
    'Ticket',
    'TicketSearchResult',
    'TicketRepository',
    'set_embedding_dimension',
    'EMBEDDING_DIMENSION',
]