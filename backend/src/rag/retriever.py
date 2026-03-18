"""RAG retriever for finding similar resolved tickets within same domain."""

from typing import List, Optional

import numpy as np

from ..database import TicketRepository, TicketSearchResult
from ..agents import EmbeddingAgent, TicketAgent
from ..utils.config import Config
from ..utils.logger import LoggerMixin


class TicketRetriever(LoggerMixin):
    """Retriever for finding similar tickets using vector similarity.
    
    CRITICAL: Only retrieves tickets from the same domain as the query.
    """
    
    def __init__(
        self,
        config: Config,
        repository: Optional[TicketRepository] = None,
        embedding_agent: Optional[EmbeddingAgent] = None,
        ticket_agent: Optional[TicketAgent] = None
    ):
        """Initialize the retriever.
        
        Args:
            config: System configuration
            repository: Database repository (created if None)
            embedding_agent: Embedding agent (created if None)
        """
        self.config = config
        self.repository = repository or TicketRepository(config)
        self.embedding_agent = embedding_agent or EmbeddingAgent(config)
        self.ticket_agent = ticket_agent or TicketAgent(config)
    
    def find_similar(
        self,
        query: str,
        domain: str,  # REQUIRED domain filter
        top_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None,
        filter_resolved: bool = True
    ) -> List[TicketSearchResult]:
        """Find similar tickets within the same domain.
        
        CRITICAL: Only returns tickets from the specified domain.
        
        Args:
            query: Query text (problem description, keywords, etc.)
            domain: Domain to search within (REQUIRED)
            top_k: Number of results to return (uses config default if None)
            similarity_threshold: Minimum similarity (uses config default if None)
            filter_resolved: If True, only search resolved tickets
            
        Returns:
            List of TicketSearchResult objects sorted by similarity
            
        Raises:
            ValueError: If domain is not provided
        """
        if not domain:
            raise ValueError("Domain is required for ticket retrieval")
        
        # Use config defaults if not specified
        if top_k is None:
            top_k = self.config.rag_top_k
        if similarity_threshold is None:
            similarity_threshold = self.config.rag_similarity_threshold
        
        self.logger.info(
            f"Searching for similar tickets in domain '{domain}': "
            f"query='{query[:50]}...', top_k={top_k}"
        )
        results=[]
        try:
            # Step 1: Analyze ticket
            self.logger.debug("Step 1: Analyzing ticket")
            cause_summary, keywords = self.ticket_agent.analyze_cause(query)
            # Step 2: Generate embedding
            self.logger.warning(f"Cause summary: {cause_summary}")
            if cause_summary:
                embedding_text = self.embedding_agent.prepare_text_for_embedding(
                    cause_summary=cause_summary,
                    keywords=keywords,
                    domain=domain
                )
                query_embedding = self.embedding_agent(embedding_text)
                # Generate query embedding
                #query_embedding = self.embedding_agent.generate_embedding(embedding_text)

                # Search database with domain filter
                results = self.repository.search_similar_tickets(
                    query_embedding=query_embedding,
                    domain=domain,  # CRITICAL: Domain filter
                    top_k=top_k,
                    similarity_threshold=similarity_threshold,
                    resolved_only=filter_resolved
                )
            else:
                self.logger.warning("No cause summary available, skipping embedding")
            
        except Exception as e:
            self.logger.error(f"Error processing ticket : {e}")
            
        self.logger.info(f"Found {len(results)} similar tickets in domain '{domain}'")
        return results
    
    def find_similar_by_embedding(
        self,
        query_embedding: np.ndarray,
        domain: str,  # REQUIRED domain filter
        top_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None,
        filter_resolved: bool = True
    ) -> List[TicketSearchResult]:
        """Find similar tickets using a pre-computed embedding.
        
        Args:
            query_embedding: Query embedding vector
            domain: Domain to search within (REQUIRED)
            top_k: Number of results to return
            similarity_threshold: Minimum similarity
            filter_resolved: If True, only search resolved tickets
            
        Returns:
            List of TicketSearchResult objects
            
        Raises:
            ValueError: If domain is not provided
        """
        if not domain:
            raise ValueError("Domain is required for ticket retrieval")
        
        if top_k is None:
            top_k = self.config.rag_top_k
        if similarity_threshold is None:
            similarity_threshold = self.config.rag_similarity_threshold
        
        self.logger.info(f"Searching with pre-computed embedding in domain '{domain}', top_k={top_k}")
        
        results = self.repository.search_similar_tickets(
            query_embedding=query_embedding,
            domain=domain,  # CRITICAL: Domain filter
            top_k=top_k,
            similarity_threshold=similarity_threshold,
            resolved_only=filter_resolved
        )
        
        return results
    
    def retrieve_context(
        self,
        query: str,
        domain: str,  # REQUIRED domain filter
        top_k: Optional[int] = None,
        similarity_threshold: Optional[float] = 0.7,
        include_cause: bool = True,
        include_resolution: bool = True
    ) -> str:
        """Retrieve and format context for RAG within same domain.
        
        Args:
            query: Query text
            domain: Domain to search within (REQUIRED)
            top_k: Number of similar tickets to retrieve
            similarity_threshold: Minimum similarity threshold
            include_cause: Include cause information
            include_resolution: Include resolution information
            
        Returns:
            Formatted context string for LLM
            
        Raises:
            ValueError: If domain is not provided
        """
        if not domain:
            raise ValueError("Domain is required for context retrieval")
        
        results = self.find_similar(query, domain=domain, top_k=top_k, similarity_threshold=similarity_threshold)
        
        if not results:
            return f"No similar resolved tickets found in domain '{domain}'."
        
        context_parts = [f"Similar resolved tickets in domain '{domain}':\n"]
        
        for i, result in enumerate(results, 1):
            ticket = result.ticket
            parts = [f"\n{i}. Ticket {ticket.ticket_number} (Similarity: {result.similarity:.2%})"]
            
            if include_cause and ticket.cause:
                parts.append(f"   Cause: {ticket.cause}")
            
            if include_resolution and ticket.resolution_summary:
                parts.append(f"   Resolution: {ticket.resolution_summary}")
            
            context_parts.append("\n".join(parts))
        
        context = "\n".join(context_parts)
        self.logger.debug(f"Generated context with {len(results)} tickets from domain '{domain}'")
        
        return context


if __name__ == "__main__":
    # Example usage
    from ..utils.config import get_config
    
    config = get_config()
    retriever = TicketRetriever(config)
    
    # Search for similar tickets in Network domain
    query = "DNS server high CPU usage"
    domain = "Network"
    
    results = retriever.find_similar(query, domain=domain, top_k=5)
    
    print(f"Found {len(results)} similar tickets in domain '{domain}':")
    for result in results:
        print(f"\n{result.ticket_number} (similarity: {result.similarity:.2%})")
        print(f"Cause: {result.cause}")
        print(f"Resolution: {result.resolution_summary}")
    
    # Get formatted context
    context = retriever.retrieve_context(query, domain=domain, top_k=3)
    print(f"\n\nFormatted context:\n{context}")
