"""Database models for the Ticket RAG System."""

from datetime import datetime
from typing import Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func


# Module-level variable for embedding dimension (set at runtime from config)
EMBEDDING_DIMENSION = 1536

Base = declarative_base()


class Ticket(Base):
    """Ticket model for storing support ticket information."""

    __tablename__ = 'tickets'

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Ticket identification
    ticket_number = Column(String(50), unique=True, nullable=False, index=True)

    # Ticket content
    cra = Column(Text, nullable=True, comment="Compte-Rendu d'Activité (Activity Report)")
    domain = Column(String(100), nullable=True, comment="Problem domain/category")

    # Analysis results
    is_resolved = Column(Boolean, nullable=True, index=True, comment="Resolution status")
    cause = Column(Text, nullable=True, comment="Root cause analysis")
    resolution_summary = Column(Text, nullable=True, comment="Resolution summary")

    # Vector embedding - dimension is set at table creation time
    # For queries, dimension must match the embedding model output
    cause_embedding = Column(
        Vector(EMBEDDING_DIMENSION),
        nullable=True,
        comment="Vector embedding of the cause"
    )

    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=func.now())
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        server_default=func.now(),
        server_onupdate=func.now()
    )

    # Indexes
    __table_args__ = (
        Index('idx_ticket_number', 'ticket_number'),
        Index('idx_is_resolved', 'is_resolved'),
    )

    def __repr__(self) -> str:
        return f"<Ticket(id={self.id}, ticket_number='{self.ticket_number}', is_resolved={self.is_resolved})>"

    def to_dict(self) -> dict:
        """Convert ticket to dictionary.

        Returns:
            Dictionary representation of the ticket
        """
        return {
            'id': self.id,
            'ticket_number': self.ticket_number,
            'cra': self.cra,
            'domain': self.domain,
            'is_resolved': self.is_resolved,
            'cause': self.cause,
            'resolution_summary': self.resolution_summary,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class TicketSearchResult:
    """Data class for ticket search results with similarity scores."""

    def __init__(
        self,
        ticket: Ticket,
        similarity: float,
        distance: Optional[float] = None
    ):
        self.ticket = ticket
        self.similarity = similarity
        self.distance = distance

    @property
    def ticket_number(self) -> str:
        return self.ticket.ticket_number

    @property
    def cause(self) -> Optional[str]:
        return self.ticket.cause

    @property
    def resolution_summary(self) -> Optional[str]:
        return self.ticket.resolution_summary
    
    @property
    def is_resolved(self) -> bool:
        return self.ticket.is_resolved
    
    @property
    def domain(self) -> str:
        return self.ticket.domain

    def __repr__(self) -> str:
        return f"<TicketSearchResult(ticket_number='{self.ticket_number}', similarity={self.similarity:.4f})>"

    def to_dict(self) -> dict:
        """Convert search result to dictionary.

        Returns:
            Dictionary representation of the search result
        """
        result = self.ticket.to_dict()
        result['similarity'] = self.similarity
        if self.distance is not None:
            result['distance'] = self.distance
        return result