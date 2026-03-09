"""Configuration management using environment variables only."""

import os
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    """Application configuration loaded from environment variables."""

    # API Selection: "openai", "ollama", or "vertexai"
    api_type: str = Field(default="openai", env="API_TYPE")

    # OpenAI Configuration (Azure OpenAI)
    openai_api_type: str = Field(default="azure", env="OPENAI_API_TYPE")
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    openai_endpoint: str = Field(..., env="OPENAI_ENDPOINT")
    openai_api_version: str = Field(default="2023-05-15", env="OPENAI_API_VERSION")
    openai_model: str = Field(default="gpt-4", env="OPENAI_MODEL")
    openai_embedding_model: str = Field(
        default="text-embedding-ada-002",
        env="OPENAI_EMBEDDING_MODEL"
    )
    openai_embedding_vec_len: int = Field(default=1536, env="OPENAI_EMBEDDING_VEC_LEN")

    # Ollama Configuration (On-Premises APIs)
    ollama_endpoint: str = Field(default="http://localhost:11434", env="OLLAMA_ENDPOINT")
    ollama_model: str = Field(default="kimi-k2.5:cloud", env="OLLAMA_MODEL")
    ollama_embedding_model: str = Field(default="qwen3-embedding:4b", env="OLLAMA_EMBEDDING_MODEL")
    ollama_embedding_vec_len: int = Field(default=768, env="OLLAMA_EMBEDDING_VEC_LEN")

    # VertexAI Configuration
    vertexai_project_id: str = Field(default="", env="VERTEXAI_PROJECT_ID")
    vertexai_region: str = Field(default="us-central1", env="VERTEXAI_REGION")
    vertexai_model: str = Field(default="gemini-1.5-flash", env="VERTEXAI_MODEL")
    vertexai_embedding_model: str = Field(default="text-embedding-004", env="VERTEXAI_EMBEDDING_MODEL")
    vertexai_embedding_vec_len: int = Field(default=768, env="VERTEXAI_EMBEDDING_VEC_LEN")
    
    # Database Configuration
    db_host: str = Field(default="localhost", env="DB_HOST")
    db_port: int = Field(default=5432, env="DB_PORT")
    db_name: str = Field(default="vectordb", env="DB_NAME")
    db_user: str = Field(..., env="DB_USER")
    db_password: str = Field(..., env="DB_PASSWORD")
    
    # RAG Configuration
    rag_top_k: int = Field(default=5, env="RAG_TOP_K")
    rag_similarity_threshold: float = Field(default=0.7, env="RAG_SIMILARITY_THRESHOLD")
    
    # Agent Configuration
    agent_max_tokens: int = Field(default=2000, env="AGENT_MAX_TOKENS")
    agent_temperature: float = Field(default=0.0, env="AGENT_TEMPERATURE")
    agent_max_retries: int = Field(default=3, env="AGENT_MAX_RETRIES")
    
    # Application Configuration
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    batch_size: int = Field(default=100, env="BATCH_SIZE")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    @property
    def database_url(self) -> str:
        """Generate PostgreSQL connection string."""
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    @property
    def embedding_vec_len(self) -> int:
        """Get embedding vector length based on selected API."""
        if self.api_type == "ollama":
            return self.ollama_embedding_vec_len
        if self.api_type == "vertexai":
            return self.vertexai_embedding_vec_len
        return self.openai_embedding_vec_len

    def __repr__(self) -> str:
        """Safe representation without sensitive data."""
        if self.api_type == "openai":
            model = self.openai_model
        elif self.api_type == "ollama":
            model = self.ollama_model
        else:
            model = self.vertexai_model
        return (
            f"Config(api_type={self.api_type}, "
            f"model={model}, "
            f"db_host={self.db_host}, "
            f"log_level={self.log_level})"
        )


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get or create global configuration instance.
    
    Returns:
        Config instance loaded from environment
    """
    global _config
    if _config is None:
        _config = Config()
    return _config


def reload_config() -> Config:
    """Reload configuration from environment.
    
    Returns:
        Fresh Config instance
    """
    global _config
    _config = Config()
    return _config


if __name__ == "__main__":
    # Test configuration loading
    try:
        config = get_config()
        print("✅ Configuration loaded successfully")
        print(f"\nConfiguration:")
        print(f"  API Type: {config.api_type}")
        if config.api_type == "openai":
            print(f"  OpenAI Model: {config.openai_model}")
            print(f"  OpenAI Embedding Model: {config.openai_embedding_model}")
        elif config.api_type == "ollama":
            print(f"  Ollama Model: {config.ollama_model}")
            print(f"  Ollama Embedding Model: {config.ollama_embedding_model}")
        else:
            print(f"  VertexAI Model: {config.vertexai_model}")
            print(f"  VertexAI Embedding Model: {config.vertexai_embedding_model}")
        print(f"  Embedding Vec Length: {config.embedding_vec_len}")
        print(f"  Database: {config.db_host}:{config.db_port}/{config.db_name}")
        print(f"  RAG Top-K: {config.rag_top_k}")
        print(f"  Similarity Threshold: {config.rag_similarity_threshold}")
        print(f"  Log Level: {config.log_level}")
    except Exception as e:
        print(f"❌ Configuration failed: {e}")
        print("\nMake sure .env file exists with required variables:")
        print("  API_TYPE (openai, ollama, or vertexai)")
        print("  OPENAI_API_KEY (if using openai)")
        print("  OPENAI_ENDPOINT (if using openai)")
        print("  OLLAMA_ENDPOINT (if using ollama)")
        print("  VERTEXAI_PROJECT_ID (if using vertexai)")
        print("  DB_USER")
        print("  DB_PASSWORD")
