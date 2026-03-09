"""Unified Ticket Analysis Agent with multiple functionalities."""

import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Tuple, List

# Add project root to path for prompt imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import openai
import ollama
from tenacity import retry, stop_after_attempt, wait_exponential

from ..utils.config import Config
from ..utils.logger import LoggerMixin

# Import prompts
try:
    from prompts.templates import (
        STATUS_ANALYSIS_PROMPT,
        CAUSE_ANALYSIS_PROMPT,
        RESOLUTION_ANALYSIS_PROMPT
    )
except ImportError:
    # Fallback for direct execution
    import os
    prompts_dir = Path(__file__).parent.parent.parent / "prompts"
    sys.path.insert(0, str(prompts_dir.parent))
    from prompts.templates import (
        STATUS_ANALYSIS_PROMPT,
        CAUSE_ANALYSIS_PROMPT,
        RESOLUTION_ANALYSIS_PROMPT
    )


@dataclass
class TicketAnalysis:
    """Complete analysis result for a ticket."""

    # Status determination
    is_resolved: Optional[bool] = None  # None instead of "I don't know"

    # Cause analysis (only if resolved)
    cause_summary: Optional[str] = None
    keywords: Optional[List[str]] = None

    # Resolution analysis (only if resolved)
    resolution_summary: Optional[str] = None
    resolution_steps: Optional[List[str]] = None

    # Error tracking
    error: Optional[str] = None


class TicketAgent(LoggerMixin):
    """Unified agent for ticket analysis.

    This agent handles:
    1. Status determination (is ticket resolved?)
    2. Cause analysis (what went wrong?)
    3. Resolution extraction (how was it fixed?)

    Analysis only proceeds if status is "Yes" (resolved).
    Supports OpenAI, Ollama, and VertexAI APIs.
    """

    def __init__(self, config: Config):
        """Initialize the ticket analysis agent.

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

        self.max_tokens = config.agent_max_tokens
        self.temperature = config.agent_temperature
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def _call_llm(self, prompt: str, max_tokens: Optional[int] = None) -> str:
        """Call LLM with retry logic.

        Args:
            prompt: Formatted prompt
            max_tokens: Token limit override

        Returns:
            LLM response text
        """
        if self.api_type == "openai":
            response = openai.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens or self.max_tokens,
                temperature=self.temperature
            )
            return response.choices[0].message.content.strip()
        elif self.api_type == "ollama":
            response = self.ollama_client.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                options={
                    "num_predict": max_tokens or self.max_tokens,
                    "temperature": self.temperature
                },
                think=False,
                stream=False,
            )
            return response["message"]["content"].strip()
        else:
            # VertexAI
            response = self.vertexai_client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={
                    "max_output_tokens": max_tokens or self.max_tokens,
                    "temperature": self.temperature
                }
            )
            return response.text.strip()
    
    def determine_status(self, context: str) -> Optional[bool]:
        """Determine if ticket is resolved.
        
        Args:
            context: Ticket description/CRA
            
        Returns:
            True if resolved, False if not resolved, None if uncertain
        """
        self.logger.debug("Determining ticket resolution status")
        
        try:
            prompt = STATUS_ANALYSIS_PROMPT.format(context=context)
            result = self._call_llm(prompt, max_tokens=10)  # Short response
            
            # Parse response
            result_clean = result.strip().lower()
            
            if result_clean == "yes":
                self.logger.info("Status: RESOLVED")
                return True
            elif result_clean == "no":
                self.logger.info("Status: NOT RESOLVED")
                return False
            else:
                # Handle "none", "null", or anything else as uncertain
                self.logger.info("Status: UNCERTAIN")
                return None
                
        except Exception as e:
            self.logger.error(f"Error determining status: {e}")
            return None
    
    def analyze_cause(self, context: str) -> Tuple[Optional[str], Optional[List[str]]]:
        """Extract root cause and keywords.
        
        Args:
            context: Ticket description
            
        Returns:
            Tuple of (cause_summary, keywords) or (None, None) on error
        """
        self.logger.debug("Analyzing ticket cause")
        
        try:
            prompt = CAUSE_ANALYSIS_PROMPT.format(context=context)
            result = self._call_llm(prompt)
            
            # Parse structured output
            cause_summary = None
            keywords = []
            
            for line in result.split('\n'):
                line = line.strip()
                if not line or line.startswith('```'):
                    continue
                
                if line.startswith('CAUSE:'):
                    cause_summary = line.replace('CAUSE:', '').strip()
                elif line.startswith('KEYWORDS:'):
                    keywords_text = line.replace('KEYWORDS:', '').strip()
                    keywords = [k.strip() for k in keywords_text.split(',') if k.strip()]
            
            # Validation
            if not cause_summary:
                self.logger.warning("Could not extract cause summary from response")
                # Fallback: use first non-empty line
                for line in result.split('\n'):
                    if line.strip() and not line.startswith('```'):
                        cause_summary = line.strip()
                        break
            
            if not keywords:
                self.logger.warning("Could not extract keywords from response")
                keywords = ["unspecified"]
            
            self.logger.info(f"Cause analysis complete: {len(keywords)} keywords extracted")
            return cause_summary, keywords
            
        except Exception as e:
            self.logger.error(f"Error analyzing cause: {e}")
            return None, None
    
    def analyze_resolution(self, context: str) -> Tuple[Optional[str], Optional[List[str]]]:
        """Extract resolution summary and steps.
        
        Args:
            context: Ticket description
            
        Returns:
            Tuple of (resolution_summary, resolution_steps) or (None, None) if no resolution
        """
        self.logger.debug("Analyzing ticket resolution")
        
        try:
            prompt = RESOLUTION_ANALYSIS_PROMPT.format(context=context)
            result = self._call_llm(prompt)
            
            # Check for no resolution
            if "NO_RESOLUTION" in result:
                self.logger.info("No resolution found in ticket")
                return None, None
            
            # Parse structured output
            resolution_summary = None
            resolution_steps = []
            
            in_steps_section = False
            
            for line in result.split('\n'):
                line = line.strip()
                if not line or line.startswith('```'):
                    continue
                
                if line.startswith('RESOLUTION:'):
                    resolution_summary = line.replace('RESOLUTION:', '').strip()
                elif line.startswith('STEPS:'):
                    in_steps_section = True
                elif in_steps_section:
                    # Extract numbered steps
                    # Remove step numbers and common prefixes
                    step = line.lstrip('0123456789.-) ').strip()
                    if step:
                        resolution_steps.append(step)
            
            # Validation
            if not resolution_summary:
                self.logger.warning("Could not extract resolution summary")
                return None, None
            
            self.logger.info(f"Resolution analysis complete: {len(resolution_steps)} steps extracted")
            return resolution_summary, resolution_steps
            
        except Exception as e:
            self.logger.error(f"Error analyzing resolution: {e}")
            return None, None
    
    def analyze(self, context: str) -> TicketAnalysis:
        """Perform complete ticket analysis.
        
        Workflow:
        1. Determine status
        2. If resolved (True), extract cause and resolution
        3. If not resolved (False) or uncertain (None), stop here
        
        Args:
            context: Ticket description/CRA
            
        Returns:
            TicketAnalysis with all extracted information
        """
        self.logger.info("Starting complete ticket analysis")
        
        analysis = TicketAnalysis()
        
        try:
            # Step 1: Determine status
            is_resolved = self.determine_status(context)
            analysis.is_resolved = is_resolved
            
            # Only proceed with analysis if ticket is resolved (True)
            if is_resolved is True:
                self.logger.info("Ticket is resolved, proceeding with cause and resolution analysis")
                
                # Step 2: Analyze cause
                cause_summary, keywords = self.analyze_cause(context)
                analysis.cause_summary = cause_summary
                analysis.keywords = keywords
                
                # Step 3: Analyze resolution
                resolution_summary, resolution_steps = self.analyze_resolution(context)
                analysis.resolution_summary = resolution_summary
                analysis.resolution_steps = resolution_steps
                
            else:
                self.logger.info("Ticket is not resolved or uncertain, skipping cause/resolution analysis")
            
        except Exception as e:
            self.logger.error(f"Error during ticket analysis: {e}")
            analysis.error = str(e)
        
        return analysis
    
    def __call__(self, context: str) -> TicketAnalysis:
        """Make agent callable.
        
        Args:
            context: Ticket context
            
        Returns:
            Complete ticket analysis
        """
        return self.analyze(context)


if __name__ == "__main__":
    # Example usage
    from ..utils.config import get_config
    
    config = get_config()
    agent = TicketAgent(config)
    
    # Test with resolved ticket
    resolved_context = """
    alarme cleared 2025-11-06 23:48:25
    DNS server CPU usage exceeded 60% threshold due to memory leak.
    Restarted DNS service and applied patch version 2.1.5.
    CPU usage returned to normal levels (<30%).
    Monitoring for 24h before final closure.
    """
    
    print("Testing with resolved ticket:")
    analysis = agent(resolved_context)
    print(f"Resolved: {analysis.is_resolved}")
    print(f"Cause: {analysis.cause_summary}")
    print(f"Keywords: {analysis.keywords}")
    print(f"Resolution: {analysis.resolution_summary}")
    print(f"Steps: {analysis.resolution_steps}")
    
    # Test with unresolved ticket
    unresolved_context = """
    Faille de sécurité CVE-2025-40778 et 40780
    Domaine du problème: Disparu avant intervention
    Origine du problème: Disparu avant intervention
    """
    
    print("\n\nTesting with unresolved ticket:")
    analysis = agent(unresolved_context)
    print(f"Resolved: {analysis.is_resolved}")
    print(f"Cause: {analysis.cause_summary}")  # Should be None
