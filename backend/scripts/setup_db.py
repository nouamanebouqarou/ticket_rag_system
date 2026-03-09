#!/usr/bin/env python3
"""Script to set up the database for the Ticket RAG System."""

import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import TicketRepository
from src.utils.config import get_config
from src.utils.logger import setup_logger


def main():
    """Set up database tables and extensions."""
    parser = argparse.ArgumentParser(
        description="Set up database for Ticket RAG System"
    )
    parser.add_argument(
        '--drop',
        action='store_true',
        help='Drop existing tables before creating (CAUTION: This will delete all data!)'
    )
    parser.add_argument(
        '--log-level',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level'
    )
    
    args = parser.parse_args()
    
    # Set up logger
    logger = setup_logger('setup_db', level=args.log_level)
    
    try:
        # Load configuration from environment
        logger.info("Loading configuration from environment variables")
        config = get_config()
        
        # Initialize repository
        logger.info(f"Connecting to database: {config.db_host}/{config.db_name}")
        repository = TicketRepository(config)
        
        # Drop tables if requested
        if args.drop:
            logger.warning("Dropping existing tables...")
            confirm = input("Are you sure you want to drop all tables? This will delete all data! (yes/no): ")
            if confirm.lower() == 'yes':
                repository.drop_tables()
                logger.info("Tables dropped successfully")
            else:
                logger.info("Drop operation cancelled")
                return
        
        # Create tables
        logger.info("Creating database tables and enabling pgvector extension...")
        repository.create_tables()
        
        # Verify
        count = repository.count_tickets()
        logger.info(f"Database setup complete! Current ticket count: {count}")
        logger.info(f"Connection string: {config.database_url}")
        
    except Exception as e:
        logger.error(f"Error setting up database: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
