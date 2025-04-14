#!/usr/bin/env python3
"""
Script to process a CSV file containing claim data.
"""
import os
import sys
from sqlmodel import Session

from app.database import engine, create_db_and_tables
from app.services.claim_processor import ClaimProcessor


def main():
    """Main function to process a CSV file"""
    # Check if a CSV file path is provided
    if len(sys.argv) < 2:
        print("Usage: python process_csv.py <csv_file_path>")
        sys.exit(1)

    csv_file_path = sys.argv[1]

    # Check if the file exists
    if not os.path.exists(csv_file_path):
        print(f"Error: File '{csv_file_path}' not found.")
        sys.exit(1)

    # Create database tables
    create_db_and_tables()

    # Create claim processor
    claim_processor = ClaimProcessor()

    # Process claims
    with Session(engine) as session:
        try:
            processed_claims = claim_processor.process_claims_csv(csv_file_path, session)
            print(f"Successfully processed {len(processed_claims)} claims.")

            # Get top providers
            top_providers = claim_processor.get_top_providers_by_net_fee(session)
            print("\nTop providers by net fee:")
            for i, provider in enumerate(top_providers, 1):
                print(f"{i}. Provider NPI: {provider['provider_npi']}, Net Fee: {provider['total_net_fee']}")

        except Exception as e:
            print(f"Error processing claims: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
