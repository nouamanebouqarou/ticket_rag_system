"""Prompt templates package."""

from .templates import (
    STATUS_ANALYSIS_PROMPT,
    CAUSE_ANALYSIS_PROMPT,
    RESOLUTION_ANALYSIS_PROMPT,
    RAG_RESOLUTION_PROMPT,
    get_prompt_version,
    validate_prompts
)

__all__ = [
    'STATUS_ANALYSIS_PROMPT',
    'CAUSE_ANALYSIS_PROMPT',
    'RESOLUTION_ANALYSIS_PROMPT',
    'RAG_RESOLUTION_PROMPT',
    'get_prompt_version',
    'validate_prompts'
]

__version__ = get_prompt_version()
