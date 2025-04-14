from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from fastapi.responses import JSONResponse
from sqlmodel import Session
from typing import List, Dict, Any
from typing import List as PyList
from pydantic import BaseModel
import json
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.database import get_session
from app.models import ClaimRead, TopProviderResponse
from app.services.claim_processor import ClaimProcessor

class ClaimItem(BaseModel):
    """Model for claim item in JSON payload"""
    service_date: str
    submitted_procedure: str
    quadrant: str = None
    plan_group: str = None
    subscriber: str = None
    provider_npi: str = None
    provider_fees: str = None
    allowed_fees: str = None
    member_coinsurance: str = None
    member_copay: str = None

class ClaimsPayload(BaseModel):
    """Model for claims payload"""
    claims: PyList[ClaimItem]

# Create rate limiter
limiter = Limiter(key_func=get_remote_address)

# Create router
router = APIRouter(prefix="/claims", tags=["claims"])

# Create claim processor instance
claim_processor = ClaimProcessor()


@router.post("/process", response_model=List[ClaimRead])
async def process_claims(
    claims_payload: ClaimsPayload, session: Session = Depends(get_session)
):
    """Process claims from JSON payload"""
    try:
        # Map standard JSON field names to CSV column names
        mapped_claims = []
        for claim in claims_payload.claims:
            claim_dict = claim.dict()
            mapped_claim = {
                "service date": claim_dict["service_date"],
                "submitted procedure": claim_dict["submitted_procedure"],
                "quadrant": claim_dict["quadrant"],
                "Plan/Group #": claim_dict["plan_group"],
                "Subscriber#": claim_dict["subscriber"],
                "Provider NPI": claim_dict["provider_npi"],
                "provider fees": claim_dict["provider_fees"],
                "Allowed fees": claim_dict["allowed_fees"],
                "member coinsurance": claim_dict["member_coinsurance"],
                "member copay": claim_dict["member_copay"]
            }
            mapped_claims.append(mapped_claim)
        
        # Convert mapped claims to JSON string
        claims_json_str = json.dumps(mapped_claims)
        
        # Process claims
        processed_claims = claim_processor.process_claims_json(claims_json_str, session)
        return processed_claims
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/process-csv", response_model=List[ClaimRead])
async def process_claims_csv(
    file: UploadFile = File(...), session: Session = Depends(get_session)
):
    """Process claims from CSV file"""
    try:
        # Save uploaded file temporarily
        file_path = f"/tmp/{file.filename}"
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # Process claims
        processed_claims = claim_processor.process_claims_csv(file_path, session)
        return processed_claims
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/top-providers", response_model=List[TopProviderResponse])
@limiter.limit("10/minute")
async def get_top_providers(
    request: Request, limit: int = 10, session: Session = Depends(get_session)
):
    """
    Get top providers by net fee
    
    This endpoint is rate limited to 10 requests per minute.
    
    The algorithm used:
    1. Group claims by provider_npi
    2. Sum the net_fee for each provider
    3. Sort providers by total net_fee in descending order
    4. Return the top N providers
    
    Time complexity: O(n log n) where n is the number of providers
    Space complexity: O(n) for storing the aggregated results
    """
    try:
        top_providers = claim_processor.get_top_providers_by_net_fee(session, limit)
        return top_providers
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
