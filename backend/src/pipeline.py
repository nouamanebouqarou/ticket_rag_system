"""Main pipeline for processing tickets through the system.

Key Changes:
- Single unified TicketAgent for status + analysis
- Embedding and detailed analysis ONLY for resolved tickets
- Returns None instead of "I don't know"
- Domain-based filtering in retrieval
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List

import pandas as pd
from tqdm import tqdm

from .agents import TicketAgent, EmbeddingAgent, TicketAnalysis
from .database import TicketRepository
from .rag import TicketRetriever, ResolutionGenerator
from .utils.config import Config, get_config
from .utils.logger import LoggerMixin


@dataclass
class TicketProcessingResult:
    """Result of processing a single ticket."""
    ticket_number: str
    domain: Optional[str] = None
    
    # Status (always determined)
    is_resolved: Optional[bool] = None  # True/False/None (instead of "Yes"/"No"/"I don't know")
    
    # Analysis (only if resolved=True)
    cause_summary: Optional[str] = None
    keywords: Optional[List[str]] = None
    resolution_summary: Optional[str] = None
    resolution_steps: Optional[List[str]] = None
    embedding_generated: bool = False
    
    # Metadata
    saved_to_db: bool = False
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'ticket_number': self.ticket_number,
            'domain': self.domain,
            'is_resolved': self.is_resolved,
            'cause_summary': self.cause_summary,
            'keywords': self.keywords,
            'resolution_summary': self.resolution_summary,
            'resolution_steps': self.resolution_steps,
            'embedding_generated': self.embedding_generated,
            'saved_to_db': self.saved_to_db,
            'error': self.error
        }


class TicketPipeline(LoggerMixin):
    """End-to-end pipeline for ticket processing.
    
    Workflow:
    1. Determine resolution status (TicketAgent)
    2. IF status is True (resolved):
       a. Analyze cause and resolution (TicketAgent)
       b. Generate embeddings (EmbeddingAgent)
       c. Store in database
    3. IF status is False or None:
       a. Store minimal info (status only)
       b. Skip analysis and embeddings
    """
    
    def __init__(
        self,
        config: Optional[Config] = None,
        ticket_agent: Optional[TicketAgent] = None,
        embedding_agent: Optional[EmbeddingAgent] = None,
        repository: Optional[TicketRepository] = None
    ):
        """Initialize the pipeline.
        
        Args:
            config: System configuration (loads from env if None)
            ticket_agent: Unified ticket analysis agent
            embedding_agent: Embedding generation agent
            repository: Database repository
        """
        self.config = config or get_config()
        
        # Initialize agents
        self.ticket_agent = ticket_agent or TicketAgent(self.config)
        self.embedding_agent = embedding_agent or EmbeddingAgent(self.config)
        
        # Initialize database
        self.repository = repository or TicketRepository(self.config)
        
        self.logger.info("Ticket pipeline initialized")
    
    def process_ticket(
        self,
        ticket_number: str,
        context: str,
        domain: Optional[str] = None,
        save_to_db: bool = True
    ) -> TicketProcessingResult:
        """Process a single ticket through the pipeline.
        
        New Workflow:
        1. Always determine status
        2. Only analyze & embed if status is True (resolved)
        
        Args:
            ticket_number: Unique ticket identifier
            context: Ticket description/CRA
            domain: Problem domain (REQUIRED for proper retrieval)
            save_to_db: Whether to save results to database
            
        Returns:
            TicketProcessingResult with analysis (if resolved)
        """
        self.logger.info(f"Processing ticket: {ticket_number}")
        
        result = TicketProcessingResult(
            ticket_number=ticket_number,
            domain=domain
        )
        
        try:
            # Step 1: Analyze ticket (includes status determination)
            self.logger.debug("Step 1: Analyzing ticket")
            analysis = self.ticket_agent.analyze(context)
            
            # Set status
            result.is_resolved = analysis.is_resolved
            
            # Step 2: ONLY if resolved, proceed with full analysis and embedding
            if analysis.is_resolved is True:
                self.logger.info("Ticket is RESOLVED - proceeding with full analysis")
                
                # Set analysis results
                result.cause_summary = analysis.cause_summary
                result.keywords = analysis.keywords
                result.resolution_summary = analysis.resolution_summary
                result.resolution_steps = analysis.resolution_steps
                
                # Step 3: Generate embedding (only for resolved tickets)
                if result.cause_summary:
                    self.logger.debug("Step 2: Generating embedding for resolved ticket")
                    embedding_text = self.embedding_agent.prepare_text_for_embedding(
                        cause_summary=result.cause_summary,
                        keywords=result.keywords,
                        domain=domain
                    )
                    embedding = self.embedding_agent(embedding_text)
                    result.embedding_generated = True
                else:
                    self.logger.warning("No cause summary available, skipping embedding")
                    embedding = None
                
                # Save to database with full analysis
                if save_to_db:
                    self.logger.debug("Step 3: Saving resolved ticket to database")
                    self._save_ticket(
                        ticket_number=ticket_number,
                        context=context,
                        domain=domain,
                        is_resolved=True,
                        cause=result.cause_summary,
                        resolution_summary=result.resolution_summary,
                        embedding=embedding
                    )
                    result.saved_to_db = True
            
            else:
                # Ticket is NOT resolved or UNCERTAIN
                status_text = "NOT RESOLVED" if analysis.is_resolved is False else "UNCERTAIN"
                self.logger.info(f"Ticket is {status_text} - skipping analysis and embedding")
                
                # Save minimal info to database
                if save_to_db:
                    self.logger.debug("Saving unresolved/uncertain ticket to database")
                    self._save_ticket(
                        ticket_number=ticket_number,
                        context=context,
                        domain=domain,
                        is_resolved=analysis.is_resolved,
                        cause=None,
                        resolution_summary=None,
                        embedding=None
                    )
                    result.saved_to_db = True
            
            self.logger.info(f"Successfully processed ticket: {ticket_number}")
            
        except Exception as e:
            self.logger.error(f"Error processing ticket {ticket_number}: {e}")
            result.error = str(e)
        
        return result
    
    def _save_ticket(
        self,
        ticket_number: str,
        context: str,
        domain: Optional[str],
        is_resolved: Optional[bool],
        cause: Optional[str],
        resolution_summary: Optional[str],
        embedding: Optional[Any]
    ) -> None:
        """Save or update ticket in database.
        
        Args:
            ticket_number: Ticket ID
            context: Ticket context
            domain: Domain
            is_resolved: Resolution status
            cause: Cause summary
            resolution_summary: Resolution
            embedding: Embedding vector
        """
        # Check if ticket exists
        existing = self.repository.get_ticket_by_number(ticket_number)
        
        if existing:
            # Update existing ticket
            self.repository.update_ticket(
                ticket_number=ticket_number,
                cra=context,
                domain=domain,
                is_resolved=is_resolved,
                cause=cause,
                resolution_summary=resolution_summary,
                cause_embedding=embedding
            )
        else:
            # Create new ticket
            self.repository.create_ticket(
                ticket_number=ticket_number,
                cra=context,
                domain=domain,
                is_resolved=is_resolved,
                cause=cause,
                resolution_summary=resolution_summary,
                cause_embedding=embedding
            )
    
    def process_batch(
        self,
        tickets_df: pd.DataFrame,
        ticket_number_col: str = 'ticket_number',
        context_col: str = 'context',
        domain_col: str = 'domain',
        save_to_db: bool = True,
        show_progress: bool = True
    ) -> List[TicketProcessingResult]:
        """Process multiple tickets in batch.
        
        Args:
            tickets_df: DataFrame with ticket information
            ticket_number_col: Column name for ticket numbers
            context_col: Column name for context/CRA
            domain_col: Column name for domain
            save_to_db: Whether to save results to database
            show_progress: Show progress bar
            
        Returns:
            List of TicketProcessingResult objects
        """
        self.logger.info(f"Processing batch of {len(tickets_df)} tickets")
        
        results = []
        
        # Create progress bar
        iterator = tqdm(tickets_df.iterrows(), total=len(tickets_df)) if show_progress else tickets_df.iterrows()
        
        for idx, row in iterator:
            ticket_number = row[ticket_number_col]
            context = row[context_col]
            domain = row.get(domain_col) if domain_col in row else None
            
            result = self.process_ticket(
                ticket_number=ticket_number,
                context=context,
                domain=domain,
                save_to_db=save_to_db
            )
            
            results.append(result)
            
            # Update progress bar description
            if show_progress:
                status = "✓" if result.is_resolved is True else ("✗" if result.is_resolved is False else "?")
                iterator.set_description(f"{status} {ticket_number}")
        
        # Summary
        successful = sum(1 for r in results if not r.error)
        resolved = sum(1 for r in results if r.is_resolved is True)
        unresolved = sum(1 for r in results if r.is_resolved is False)
        uncertain = sum(1 for r in results if r.is_resolved is None)
        
        self.logger.info(
            f"Batch processing complete: {successful}/{len(results)} successful, "
            f"{resolved} resolved, {unresolved} unresolved, {uncertain} uncertain"
        )
        
        return results
    
    def get_similar_tickets(
        self,
        query: str,
        domain: str,  # REQUIRED
        top_k: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Find similar tickets within same domain using RAG retrieval.
        
        Args:
            query: Query description
            domain: Domain to search within (REQUIRED)
            top_k: Number of results
            similarity_threshold: Minimum similarity
            
        Returns:
            List of similar ticket dictionaries
            
        Raises:
            ValueError: If domain is not provided
        """
        if not domain:
            raise ValueError("Domain is required for ticket retrieval")
        
        retriever = TicketRetriever(self.config, repository=self.repository)
        
        results = retriever.find_similar(
            query=query,
            domain=domain,
            top_k=top_k,
            similarity_threshold=similarity_threshold
        )
        
        return [r.to_dict() for r in results]
    
    def suggest_resolution(
        self,
        problem_description: str,
        domain: str,  # REQUIRED
        top_k: int = 5
    ) -> str:
        """Generate resolution suggestions for a problem.
        
        Args:
            problem_description: Description of the problem
            domain: Problem domain (REQUIRED)
            top_k: Number of similar tickets to use
            
        Returns:
            Resolution suggestions
            
        Raises:
            ValueError: If domain is not provided
        """
        if not domain:
            raise ValueError("Domain is required for resolution generation")
        
        generator = ResolutionGenerator(
            self.config,
            retriever=TicketRetriever(self.config, repository=self.repository)
        )
        
        return generator.generate_resolution(
            problem_description,
            domain=domain,
            top_k=top_k
        )


if __name__ == "__main__":
    # Example usage
    pipeline = TicketPipeline()
    
    # Example 1: Resolved ticket
    resolved_ticket = {
        'ticket_number': 'TI0000001',
        'context': """
            DNS server CPU usage exceeded 60% threshold.
            Restarted DNS service and applied patch v2.1.5.
            CPU returned to normal (<30%). Monitoring 24h.
        """,
        'domain': 'Network'
    }
    
    result = pipeline.process_ticket(**resolved_ticket)
    print(f"Ticket: {result.ticket_number}")
    print(f"Resolved: {result.is_resolved}")
    print(f"Cause: {result.cause_summary}")
    print(f"Embedding Generated: {result.embedding_generated}")
    
    # Example 2: Unresolved ticket
    unresolved_ticket = {
        'ticket_number': 'TI0000002',
        'context': """
            Security vulnerability CVE-2025-40778
            Disparu avant intervention
        """,
        'domain': 'Security'
    }
    
    result = pipeline.process_ticket(**unresolved_ticket)
    print(f"\nTicket: {result.ticket_number}")
    print(f"Resolved: {result.is_resolved}")
    print(f"Cause: {result.cause_summary}")  # Should be None
