"""Embedding Agent for vector generation."""

from typing import List, Optional

import numpy as np
import openai
import ollama
from tenacity import retry, stop_after_attempt, wait_exponential

from ..utils.config import Config
from ..utils.logger import LoggerMixin


class EmbeddingAgent(LoggerMixin):
    """Agent that generates vector embeddings for semantic search.

    This agent is kept separate from the TicketAgent because:
    1. Embeddings are only needed for resolved tickets
    2. Uses different API endpoint (embeddings vs completions)
    3. Can be cached independently
    4. May use different models/configurations

    Supports OpenAI, Ollama, and VertexAI APIs.
    """

    def __init__(self, config: Config):
        """Initialize the embedding agent.

        Args:
            config: Application configuration
        """
        self.config = config
        self.api_type = config.api_type

        if self.api_type == "openai":
            # Configure OpenAI client
            openai.api_type = config.openai_api_type
            openai.api_key = config.openai_api_key
            openai.azure_endpoint = config.openai_endpoint
            openai.api_version = config.openai_api_version
            self.embedding_model = config.openai_embedding_model
        elif self.api_type == "ollama":
            # Configure Ollama
            self.ollama_client = ollama.Client(host=config.ollama_endpoint)
            self.embedding_model = config.ollama_embedding_model
        else:
            # Configure VertexAI
            from google import genai
            self.vertexai_client = genai.Client(
                project=config.vertexai_project_id,
                location=config.vertexai_region
            )
            self.embedding_model = config.vertexai_embedding_model
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding vector for text.

        Args:
            text: Text to embed

        Returns:
            Numpy array of shape (vec_len,) containing the embedding

        Raises:
            ValueError: If text is empty
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty for embedding generation")

        self.logger.debug(f"Generating embedding for text: {text[:100]}...")

        try:
            if self.api_type == "openai":
                response = openai.embeddings.create(
                    model=self.embedding_model,
                    input=text
                )
                embedding = np.array(response.data[0].embedding, dtype=np.float32)
            elif self.api_type == "ollama":
                response = self.ollama_client.embeddings(
                    model=self.embedding_model,
                    prompt=text
                )
                embedding = np.array(response["embedding"], dtype=np.float32)
            else:
                # VertexAI
                response = self.vertexai_client.models.get_embeddings(
                    model=self.embedding_model,
                    texts=[text]
                )
                embedding = np.array(response[0].embeddings[0], dtype=np.float32)

            #self.logger.info(f"Generated embedding:  {embedding}")
            self.logger.info(f"Generated embedding of shape {embedding.shape}")
            return embedding

        except Exception as e:
            self.logger.error(f"Error generating embedding: {e}")
            raise
    
    def prepare_text_for_embedding(
        self,
        cause_summary: str,
        keywords: Optional[List[str]] = None,
        domain: Optional[str] = None
    ) -> str:
        """Prepare text for embedding by combining relevant information.
        
        Args:
            cause_summary: Root cause description
            keywords: List of extracted keywords
            domain: Problem domain/category
            
        Returns:
            Combined text optimized for semantic search
        """
        parts = [cause_summary]
        
        if keywords:
            keywords_str = ", ".join(keywords)
            parts.append(f"Keywords: {keywords_str}")
        
        if domain:
            parts.append(f"Domain: {domain}")
        
        combined_text = " | ".join(parts)
        self.logger.debug(f"Prepared text for embedding: {combined_text[:150]}...")
        
        return combined_text
    
    def generate_batch_embeddings(self, texts: List[str]) -> List[np.ndarray]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding arrays
        """
        if not texts:
            return []

        self.logger.info(f"Generating embeddings for {len(texts)} texts")

        try:
            if self.api_type == "openai":
                response = openai.embeddings.create(
                    model=self.embedding_model,
                    input=texts
                )
                embeddings = [
                    np.array(item.embedding, dtype=np.float32)
                    for item in response.data
                ]
            elif self.api_type == "ollama":
                response = self.ollama_client.embeddings(
                    model=self.embedding_model,
                    prompt=texts
                )
                embeddings = [
                    np.array(item, dtype=np.float32)
                    for item in response["embeddings"]
                ]
            else:
                # VertexAI
                response = self.vertexai_client.models.get_embeddings(
                    model=self.embedding_model,
                    texts=texts
                )
                embeddings = [
                    np.array(e.embeddings[0], dtype=np.float32)
                    for e in response
                ]

            #self.logger.info(f"Generated embedding:  {embeddings}")
            self.logger.info(f"Generated {len(embeddings)} embeddings")
            return embeddings

        except Exception as e:
            self.logger.error(f"Error generating batch embeddings: {e}")
            raise
    
    def __call__(self, text: str) -> np.ndarray:
        """Make agent callable.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        return self.generate_embedding(text)


class CachedEmbeddingAgent(EmbeddingAgent):
    """Embedding agent with caching for improved performance."""
    
    def __init__(self, config: Config):
        """Initialize cached embedding agent.
        
        Args:
            config: Application configuration
        """
        super().__init__(config)
        self._cache: dict[str, np.ndarray] = {}
    
    def generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding with caching.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector (from cache if available)
        """
        # Check cache
        if text in self._cache:
            self.logger.debug("Returning cached embedding")
            return self._cache[text]
        
        # Generate new embedding
        embedding = super().generate_embedding(text)
        
        # Store in cache
        self._cache[text] = embedding
        self.logger.debug(f"Cached embedding (cache size: {len(self._cache)})")
        
        return embedding
    
    def clear_cache(self) -> None:
        """Clear the embedding cache."""
        cache_size = len(self._cache)
        self._cache.clear()
        self.logger.info(f"Cleared embedding cache ({cache_size} entries)")
    
    @property
    def cache_size(self) -> int:
        """Get current cache size."""
        return len(self._cache)


if __name__ == "__main__":
    # Example usage
    from ..utils.config import get_config
    
    config = get_config()
    agent = EmbeddingAgent(config)
    
    # Prepare text
    text = agent.prepare_text_for_embedding(
        cause_summary="DNS server CPU usage exceeded threshold due to memory leak",
        keywords=["DNS", "CPU", "memory leak", "performance"],
        domain="Network"
    )
    
    print(f"Text for embedding: {text}")
    
    # Generate embedding
    embedding = agent(text)
    print(f"\nEmbedding shape: {embedding.shape}")
    print(f"Embedding sample (first 5): {embedding[:5]}")
    
    # Test caching
    print("\n--- Testing Cache ---")
    cached_agent = CachedEmbeddingAgent(config)
    
    # First call
    emb1 = cached_agent(text)
    print(f"Cache size after first call: {cached_agent.cache_size}")
    
    # Second call (should use cache)
    emb2 = cached_agent(text)
    print(f"Cache hit: {np.array_equal(emb1, emb2)}")
    print(f"Cache size: {cached_agent.cache_size}")
