"""RAG generator for creating responses with retrieved context."""

import sys
from pathlib import Path
from typing import Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import openai
import ollama
from tenacity import retry, stop_after_attempt, wait_exponential

from .retriever import TicketRetriever
from ..utils.config import Config
from ..utils.logger import LoggerMixin

# Import prompt
try:
    from prompts.templates import RAG_RESOLUTION_PROMPT
except ImportError:
    prompts_dir = Path(__file__).parent.parent.parent / "prompts"
    sys.path.insert(0, str(prompts_dir.parent))
    from prompts.templates import RAG_RESOLUTION_PROMPT


class ResolutionGenerator(LoggerMixin):
    """Generator for creating resolution suggestions using RAG.

    Supports OpenAI, Ollama, and VertexAI APIs.
    """

    def __init__(
        self,
        config: Config,
        retriever: Optional[TicketRetriever] = None
    ):
        """Initialize the generator.

        Args:
            config: System configuration
            retriever: Ticket retriever (created if None)
        """
        self.config = config
        self.api_type = config.api_type
        self.retriever = retriever or TicketRetriever(config)

        if self.api_type == "openai":
            # Configure OpenAI
            openai.api_type = config.openai_api_type
            openai.api_key = config.openai_api_key
            openai.azure_endpoint = config.openai_endpoint
            openai.api_version = config.openai_api_version
            self.model = config.openai_model
        elif self.api_type == "ollama":
            # Configure Ollama
            self.ollama_client = ollama.Client(host=config.ollama_endpoint)
            self.model = config.ollama_model
        else:
            # Configure VertexAI
            from google import genai
            self.vertexai_client = genai.Client(
                project=config.vertexai_project_id,
                location=config.vertexai_region
            )
            self.model = config.vertexai_model

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def generate_resolution(
        self,
        problem_description: str,
        domain: str,  # REQUIRED domain
        top_k: int = 5,
        max_tokens: int = 2000
    ) -> str:
        """Generate resolution suggestions for a problem.

        Args:
            problem_description: Description of the current problem
            domain: Problem domain (REQUIRED for retrieval)
            top_k: Number of similar tickets to retrieve
            max_tokens: Maximum tokens in response

        Returns:
            Generated resolution suggestions

        Raises:
            ValueError: If domain is not provided
        """
        if not domain:
            raise ValueError("Domain is required for resolution generation")

        self.logger.info(
            f"Generating resolution for domain '{domain}': {problem_description[:100]}..."
        )

        # Retrieve similar tickets from same domain
        context = self.retriever.retrieve_context(
            query=problem_description,
            domain=domain,
            top_k=top_k,
            include_cause=True,
            include_resolution=True
        )

        # Generate prompt
        prompt = RAG_RESOLUTION_PROMPT.format(
            similar_tickets_context=context,
            current_problem=problem_description
        )

        # Call LLM
        try:
            if self.api_type == "openai":
                response = openai.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=0.3
                )
                resolution = response.choices[0].message.content.strip()
            elif self.api_type == "ollama":
                self.logger.info(f"Calling Ollama model: {self.model}")
                try:
                    # Try with options first
                    response = self.ollama_client.chat(
                        model=self.model,
                        messages=[{"role": "user", "content": prompt}],
                        options={
                            "num_predict": max_tokens,
                            "temperature": 0.3
                        },                                                                                                                                                                  
                        think=False,                                                                                                                                                        
                        stream=False 
                    )
                except Exception as e:
                    self.logger.warning(f"Ollama chat with options failed: {e}, trying without options")
                    # Fallback to simple call without options
                    response = self.ollama_client.chat(
                        model=self.model,
                        messages=[{"role": "user", "content": prompt}]
                    )
                resolution = response["message"]["content"].strip()
            else:
                # VertexAI
                response = self.vertexai_client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config={
                        "max_output_tokens": max_tokens,
                        "temperature": 0.3
                    }
                )
                resolution = response.text.strip()

            self.logger.info("Resolution generated successfully")
            return resolution

        except Exception as e:
            self.logger.error(f"Error generating resolution: {e}")
            raise


if __name__ == "__main__":
    # Example usage
    from ..utils.config import get_config

    config = get_config()
    generator = ResolutionGenerator(config)

    # Generate resolution
    problem = """
    DNS server on 10.131.17.197 is experiencing high CPU usage (>60%).
    This has been ongoing for several hours and affecting service performance.
    """
    domain = "Network"

    resolution = generator.generate_resolution(problem, domain=domain, top_k=3)
    print("Generated Resolution:")
    print(resolution)