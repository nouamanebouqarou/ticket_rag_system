"""Ticket RAG System v2.0 - Production-ready RAG for IT support tickets."""

__version__ = "2.0.0"
__author__ = "Ticket RAG Team"

from .pipeline import TicketPipeline, TicketProcessingResult
from .utils.config import Config, get_config

__all__ = [
    'TicketPipeline',
    'TicketProcessingResult',
    'Config',
    'get_config',
]
