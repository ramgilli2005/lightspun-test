import uuid
import csv
import json
from decimal import Decimal
from datetime import datetime
from typing import Dict, List, Any
from sqlmodel import Session, select
from app.models import Claim, ClaimCreate


class ClaimProcessor:
    """Service for processing claims"""

    @staticmethod
    def generate_claim_id() -> str:
        """Generate a unique claim ID"""
        return f"CLM-{uuid.uuid4().hex[:8].upper()}"

    @staticmethod
    def calculate_net_fee(
        provider_fees: Decimal,
        member_coinsurance: Decimal,
        member_copay: Decimal,
        allowed_fees: Decimal
    ) -> Decimal:
        """
        Calculate the net fee based on the formula:
        net_fee = provider_fees + member_coinsurance + member_copay - allowed_fees
        """
        return provider_fees + member_coinsurance + member_copay - allowed_fees

    @staticmethod
    def parse_decimal(value: str) -> Decimal:
        """Parse a string to a Decimal, handling currency format"""
        if isinstance(value, str):
            # Remove currency symbol and whitespace
            value = value.replace("$", "").replace(" ", "")
        return Decimal(value)

    @staticmethod
    def parse_date(date_str: str) -> datetime.date:
        """Parse a date string to a datetime.date object"""
        return datetime.strptime(date_str.split(" ")[0], "%m/%d/%y").date()

    def process_claim_data(self, claim_data: Dict[str, Any], session: Session) -> Claim:
        """Process a single claim and store it in the database"""
        # Normalize keys to handle inconsistent capitalization
        normalized_data = {}
        for key, value in claim_data.items():
            normalized_key = key.lower().strip()
            normalized_data[normalized_key] = value

        # Parse decimal values
        provider_fees = self.parse_decimal(normalized_data.get("provider fees", "0.00"))
        allowed_fees = self.parse_decimal(normalized_data.get("allowed fees", "0.00"))
        member_coinsurance = self.parse_decimal(normalized_data.get("member coinsurance", "0.00"))
        member_copay = self.parse_decimal(normalized_data.get("member copay", "0.00"))

        # Parse date
        service_date = self.parse_date(normalized_data.get("service date", "1/1/00 0:00"))

        # Calculate net fee
        net_fee = self.calculate_net_fee(
            provider_fees, member_coinsurance, member_copay, allowed_fees
        )

        # Create claim object
        claim_create = ClaimCreate(
            service_date=service_date,
            submitted_procedure=normalized_data.get("submitted procedure", "D0000"),
            quadrant=normalized_data.get("quadrant", None),
            plan_group=normalized_data.get("plan/group #", "GRP-1000"),
            subscriber=normalized_data.get("subscriber#", "0000000000"),
            provider_npi=normalized_data.get("provider npi", "1234567890"),
            provider_fees=provider_fees,
            allowed_fees=allowed_fees,
            member_coinsurance=member_coinsurance,
            member_copay=member_copay,
        )

        # Create database record
        claim = Claim.from_orm(claim_create)
        claim.claim_id = self.generate_claim_id()
        claim.net_fee = net_fee

        # Save to database
        session.add(claim)
        session.commit()
        session.refresh(claim)

        return claim

    def process_claims_json(self, claims_json: str, session: Session) -> List[Claim]:
        """Process multiple claims from a JSON string"""
        claims_data = json.loads(claims_json)
        processed_claims = []

        for claim_data in claims_data:
            processed_claim = self.process_claim_data(claim_data, session)
            processed_claims.append(processed_claim)

        return processed_claims

    def process_claims_csv(self, csv_file_path: str, session: Session) -> List[Claim]:
        """Process claims from a CSV file"""
        processed_claims = []

        # Read the file content
        with open(csv_file_path, mode='r', encoding='utf-8') as file:
            lines = file.readlines()

        if not lines:
            return processed_claims

        # Parse header
        header_line = lines[0].strip()
        # Replace quotes and split by comma
        header_parts = [part.strip('"') for part in header_line.split(',')]

        # Process each data line
        for line_idx in range(1, len(lines)):
            line = lines[line_idx].strip()
            if not line:
                continue

            # Parse data line
            data_parts = []
            current_part = ""
            in_quotes = False

            for char in line:
                if char == '"':
                    in_quotes = not in_quotes
                elif char == ',' and not in_quotes:
                    data_parts.append(current_part.strip())
                    current_part = ""
                else:
                    current_part += char

            # Add the last part
            if current_part:
                data_parts.append(current_part.strip())

            # Create a dictionary from header and data
            row = {}
            for i, header in enumerate(header_parts):
                if i < len(data_parts):
                    row[header] = data_parts[i]
                else:
                    row[header] = ""

            # Process the claim
            try:
                processed_claim = self.process_claim_data(row, session)
                processed_claims.append(processed_claim)
            except Exception as e:
                print(f"Error processing claim at line {line_idx + 1}: {e}")
                continue

        return processed_claims

    def get_top_providers_by_net_fee(self, session: Session, limit: int = 10) -> List[Dict[str, Any]]:
        """Get the top providers by net fee"""
        # Query to get the sum of net fees grouped by provider_npi
        from sqlalchemy import func
        
        query = (
            select(
                Claim.provider_npi,
                func.sum(Claim.net_fee).label("total_net_fee")
            )
            .group_by(Claim.provider_npi)
            .order_by(func.sum(Claim.net_fee).desc())
            .limit(limit)
        )

        result = session.exec(query).all()
        
        # Format the result
        top_providers = [
            {
                "provider_npi": provider_npi,
                "total_net_fee": total_net_fee
            }
            for provider_npi, total_net_fee in result
        ]

        return top_providers


# Pseudo code for communication with payments service
"""
Communication between claim_process and payments services:

1. Message Queue Based Communication:
   - After processing a claim and calculating the net fee, claim_process publishes a message to a queue
   - The payments service subscribes to this queue and processes the payment based on the net fee

2. Handling Failures:
   - Use a state machine to track claim processing failures. 
   - The failure can be at Patient level or provider level. Ensure adequate handling is done at Patient and Provider level before processing payment.
   - Use a transactional outbox pattern to ensure message delivery
   - Store outgoing messages in a database table as part of the claim processing transaction
   - A separate process reads from this table and publishes messages to the queue
   - If the payments service fails to process a payment, it can publish a failure message to another queue
   - The claim_process service can subscribe to this queue and handle the failure (e.g., mark the claim as failed)

3. Handling Concurrent Processing:
   - Use message deduplication to prevent duplicate processing
   - Include a unique claim ID in each message
   - The payments service can check if a payment has already been processed for a given claim ID
   - Use distributed locks to prevent concurrent processing of the same claim

Example pseudo code for publishing a message:

def publish_to_payments_service(claim: Claim):
    message = {
        "claim_id": claim.claim_id,
        "provider_npi": claim.provider_npi,
        "net_fee": str(claim.net_fee),
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Store message in outbox table
    outbox_entry = OutboxMessage(
        message_type="claim_processed",
        payload=json.dumps(message),
        status="pending"
    )
    session.add(outbox_entry)
    session.commit()
    
    # Outbox processor will pick up this message and publish it to the queue
"""
