#!/usr/bin/env python3
"""Script to process tickets in batch from a CSV file."""

import argparse
import sys
from pathlib import Path

import pandas as pd

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipeline import TicketPipeline
from src.utils.config import get_config
from src.utils.logger import setup_logger


def main():
    """Process tickets from CSV file."""
    parser = argparse.ArgumentParser(
        description="Process tickets in batch"
    )
    parser.add_argument(
        'input_file',
        type=str,
        help='Path to input CSV file with tickets'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Path to output CSV file with results (optional)'
    )
    parser.add_argument(
        '--ticket-col',
        type=str,
        default='ticket_number',
        help='Column name for ticket numbers (default: ticket_number)'
    )
    parser.add_argument(
        '--context-col',
        type=str,
        default='context',
        help='Column name for ticket context/CRA (default: context)'
    )
    parser.add_argument(
        '--domain-col',
        type=str,
        default='domain',
        help='Column name for domain (default: domain)'
    )
    parser.add_argument(
        '--no-save-db',
        action='store_true',
        help='Do not save results to database'
    )
    parser.add_argument(
        '--no-progress',
        action='store_true',
        help='Do not show progress bar'
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
    logger = setup_logger('process_tickets', level=args.log_level)
    
    try:
        # Load configuration from environment
        logger.info("Loading configuration from environment variables")
        config = get_config()
        
        # Load input CSV
        logger.info(f"Loading tickets from {args.input_file}")
        df = pd.read_csv(args.input_file)
        logger.info(f"Loaded {len(df)} tickets")
        
        # Validate columns
        required_cols = [args.ticket_col, args.context_col]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            logger.error(f"Missing required columns: {missing_cols}")
            logger.error(f"Available columns: {df.columns.tolist()}")
            sys.exit(1)
        
        # Check for domain column
        if args.domain_col not in df.columns:
            logger.warning(f"Domain column '{args.domain_col}' not found - retrieval features will be limited")
        
        # Initialize pipeline
        logger.info("Initializing processing pipeline")
        pipeline = TicketPipeline(config)
        
        # Process tickets
        results = pipeline.process_batch(
            tickets_df=df,
            ticket_number_col=args.ticket_col,
            context_col=args.context_col,
            domain_col=args.domain_col if args.domain_col in df.columns else None,
            save_to_db=not args.no_save_db,
            show_progress=not args.no_progress
        )
        
        # Create results DataFrame
        results_df = pd.DataFrame([r.to_dict() for r in results])
        
        # Save output if requested
        if args.output:
            logger.info(f"Saving results to {args.output}")
            results_df.to_csv(args.output, index=False)
        
        # Print summary
        total = len(results)
        successful = sum(1 for r in results if not r.error)
        resolved = sum(1 for r in results if r.is_resolved is True)
        unresolved = sum(1 for r in results if r.is_resolved is False)
        uncertain = sum(1 for r in results if r.is_resolved is None)
        errors = total - successful
        
        logger.info("=" * 60)
        logger.info("PROCESSING SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total tickets:          {total}")
        logger.info(f"Successfully processed: {successful}")
        logger.info(f"Errors:                 {errors}")
        logger.info(f"Resolved tickets:       {resolved}")
        logger.info(f"Unresolved tickets:     {unresolved}")
        logger.info(f"Uncertain status:       {uncertain}")
        logger.info("=" * 60)
        
        if errors > 0:
            logger.warning(f"\n{errors} tickets had errors:")
            for r in results:
                if r.error:
                    logger.warning(f"  - {r.ticket_number}: {r.error}")
        
    except FileNotFoundError:
        logger.error(f"Input file not found: {args.input_file}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error processing tickets: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
