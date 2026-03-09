"""Database repository for ticket operations with domain filtering."""

from typing import List, Optional

import numpy as np
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.exc import IntegrityError, StatementError

from .models import Base, Ticket, TicketSearchResult
from ..utils.config import Config
from ..utils.logger import LoggerMixin
from . import models


def set_embedding_dimension(vec_len: int) -> None:
    """Set the embedding dimension for the database models.

    Args:
        vec_len: Vector dimension (768 for Ollama, 1536 for OpenAI)
    """
    models.EMBEDDING_DIMENSION = vec_len


class TicketRepository(LoggerMixin):
    """Repository for ticket database operations."""

    def __init__(self, config: Config):
        """Initialize repository with database configuration.

        Args:
            config: Application configuration
        """
        self.config = config
        # Set embedding dimension based on selected API type
        set_embedding_dimension(config.embedding_vec_len)
        self.logger.info(f"Embedding vector dimension = {models.EMBEDDING_DIMENSION}")
        self.engine = create_engine(
            config.database_url,
            echo=False,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20
        )
        self.SessionLocal = sessionmaker(bind=self.engine)

    def create_tables(self) -> None:
        """Create all database tables and enable pgvector extension."""
        with self.engine.begin() as conn:
            # Enable pgvector extension
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            self.logger.info("pgvector extension enabled")

        # Create tables
        Base.metadata.create_all(self.engine)
        self.logger.info("Database tables created successfully")

    def drop_tables(self) -> None:
        """Drop all database tables (use with caution!)."""
        Base.metadata.drop_all(self.engine)
        self.logger.warning("All database tables dropped")

    def get_session(self) -> Session:
        """Get a new database session.

        Returns:
            SQLAlchemy session
        """
        return self.SessionLocal()

    def create_ticket(
        self,
        ticket_number: str,
        cra: Optional[str] = None,
        domain: Optional[str] = None,
        is_resolved: Optional[bool] = None,
        cause: Optional[str] = None,
        resolution_summary: Optional[str] = None,
        cause_embedding: Optional[np.ndarray] = None,
    ) -> Ticket:
        """Create a new ticket in the database.

        Args:
            ticket_number: Unique ticket identifier
            cra: Activity report context
            domain: Problem domain
            is_resolved: Resolution status (None for uncertain)
            cause: Root cause analysis
            resolution_summary: Resolution summary
            cause_embedding: Vector embedding of the cause

        Returns:
            Created ticket instance

        Raises:
            IntegrityError: If ticket_number already exists
        """
        session = self.get_session()
        try:
            ticket = Ticket(
                ticket_number=ticket_number,
                cra=cra,
                domain=domain,
                is_resolved=is_resolved,
                cause=cause,
                resolution_summary=resolution_summary,
                cause_embedding=cause_embedding.tolist() if cause_embedding is not None else None,
            )
            session.add(ticket)
            session.commit()
            session.refresh(ticket)
            self.logger.info(f"Created ticket: {ticket_number}")
            return ticket
        except IntegrityError as e:
            session.rollback()
            self.logger.error(f"Failed to create ticket {ticket_number}: {e}")
            raise
        finally:
            session.close()

    def get_ticket_by_number(self, ticket_number: str) -> Optional[Ticket]:
        """Retrieve a ticket by its number.

        Args:
            ticket_number: Ticket identifier

        Returns:
            Ticket instance or None if not found
        """
        session = self.get_session()
        try:
            ticket = session.query(Ticket).filter(
                Ticket.ticket_number == ticket_number
            ).first()
            return ticket
        finally:
            session.close()

    def update_ticket(
        self,
        ticket_number: str,
        **kwargs
    ) -> Optional[Ticket]:
        """Update a ticket's attributes.

        Args:
            ticket_number: Ticket identifier
            **kwargs: Fields to update

        Returns:
            Updated ticket instance or None if not found
        """
        session = self.get_session()
        try:
            ticket = session.query(Ticket).filter(
                Ticket.ticket_number == ticket_number
            ).first()

            if ticket:
                for key, value in kwargs.items():
                    if hasattr(ticket, key):
                        # Handle numpy arrays for embeddings
                        if key == 'cause_embedding' and isinstance(value, np.ndarray):
                            value = value.tolist()
                        setattr(ticket, key, value)

                session.commit()
                session.refresh(ticket)
                self.logger.info(f"Updated ticket: {ticket_number}")
                return ticket
            else:
                self.logger.warning(f"Ticket not found: {ticket_number}")
                return None
        finally:
            session.close()

    def search_similar_tickets(
        self,
        query_embedding: np.ndarray,
        domain: str,
        top_k: int = 5,
        similarity_threshold: float = 0.0,
        resolved_only: bool = True
    ) -> List[TicketSearchResult]:
        """Search for similar tickets using vector similarity within the same domain.

        Args:
            query_embedding: Query vector embedding
            domain: Domain to filter by (REQUIRED)
            top_k: Number of results to return
            similarity_threshold: Minimum similarity score (0-1)
            resolved_only: If True, only search resolved tickets

        Returns:
            List of TicketSearchResult instances sorted by similarity

        Raises:
            ValueError: If domain is not provided
            RuntimeError: If database query fails
        """
        if not domain:
            raise ValueError("Domain is required for ticket search")

        session = self.get_session()
        try:
            # Convert numpy array to list for PostgreSQL
            query_vector = query_embedding.tolist()

            self.logger.debug(f"Searching in domain '{domain}' with vector dim {len(query_vector)}")

            # Build the query with domain filter
            query = session.query(
                Ticket,
                (1 - Ticket.cause_embedding.cosine_distance(query_vector)).label('similarity')
            ).filter(
                Ticket.cause_embedding.isnot(None),
                Ticket.domain == domain
            )

            if resolved_only:
                query = query.filter(Ticket.is_resolved == True)

            # Filter by similarity threshold
            query = query.filter(
                (1 - Ticket.cause_embedding.cosine_distance(query_vector)) >= similarity_threshold
            )

            # Order by similarity and limit
            results = query.order_by(
                Ticket.cause_embedding.cosine_distance(query_vector)
            ).limit(top_k).all()

            # Convert to TicketSearchResult objects
            search_results = [
                TicketSearchResult(
                    ticket=ticket,
                    similarity=similarity,
                    distance=1 - similarity
                )
                for ticket, similarity in results
            ]

            self.logger.info(f"Found {len(search_results)} similar tickets in domain '{domain}'")
            return search_results

        except StatementError as e:
            self.logger.error(f"Database statement error: {e}")
            error_msg = str(e)
            if "dimension" in error_msg.lower() or "vector" in error_msg.lower():
                raise RuntimeError(
                    f"Vector dimension mismatch. Query has {len(query_vector)} dimensions. "
                    f"Original error: {e}"
                ) from e
            raise RuntimeError(f"Database query failed: {e}") from e
        except Exception as e:
            self.logger.error(f"Error searching similar tickets: {e}")
            raise RuntimeError(f"Failed to search similar tickets: {e}") from e
        finally:
            session.close()

    def delete_ticket(self, ticket_number: str) -> bool:
        """Delete a ticket by its number.

        Args:
            ticket_number: Ticket identifier

        Returns:
            True if deleted, False if not found
        """
        session = self.get_session()
        try:
            ticket = session.query(Ticket).filter(
                Ticket.ticket_number == ticket_number
            ).first()

            if ticket:
                session.delete(ticket)
                session.commit()
                self.logger.info(f"Deleted ticket: {ticket_number}")
                return True
            else:
                self.logger.warning(f"Ticket not found for deletion: {ticket_number}")
                return False
        finally:
            session.close()

    def count_tickets(
        self,
        resolved_only: bool = False,
        domain: Optional[str] = None
    ) -> int:
        """Count total number of tickets.

        Args:
            resolved_only: If True, only count resolved tickets
            domain: Optional domain filter

        Returns:
            Number of tickets
        """
        session = self.get_session()
        try:
            query = session.query(Ticket)

            if resolved_only:
                query = query.filter(Ticket.is_resolved == True)

            if domain:
                query = query.filter(Ticket.domain == domain)

            return query.count()
        finally:
            session.close()

    def get_all_domains(self) -> List[str]:
        """Get list of all unique domains in the database.

        Returns:
            List of domain names
        """
        session = self.get_session()
        try:
            domains = session.query(Ticket.domain).distinct().all()
            return [d[0] for d in domains if d[0] is not None]
        finally:
            session.close()