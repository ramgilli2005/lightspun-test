import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from decimal import Decimal
from datetime import datetime
import json
import os

from app.main import app
from app.services.claim_processor import ClaimProcessor


@pytest.fixture
def client():
    """Fixture for FastAPI test client"""
    return TestClient(app)


@pytest.fixture
def sample_claim_data():
    """Fixture for sample claim data"""
    return {
        "service date": "3/28/18 0:00",
        "submitted procedure": "D0180",
        "quadrant": "",
        "Plan/Group #": "GRP-1000",
        "Subscriber#": "3730189502",
        "Provider NPI": "1497775530",
        "provider fees": "$100.00 ",
        "Allowed fees": "$100.00 ",
        "member coinsurance": "$0.00 ",
        "member copay": "$0.00 "
    }


def test_root_endpoint(client):
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "message": "Welcome to the Claim Processing Service",
        "docs": "/docs",
    }


def test_health_endpoint(client):
    """Test health endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_process_claims_endpoint(client, sample_claim_data):
    """Test process claims endpoint"""
    # Mock ClaimProcessor.process_claims_json
    mock_claim = MagicMock()
    mock_claim.id = 1
    mock_claim.claim_id = "CLM-12345678"
    mock_claim.net_fee = Decimal("0.00")
    mock_claim.service_date = datetime(2018, 3, 28).date()
    mock_claim.submitted_procedure = "D0180"
    mock_claim.quadrant = None
    mock_claim.plan_group = "GRP-1000"
    mock_claim.subscriber = "3730189502"
    mock_claim.provider_npi = "1497775530"
    mock_claim.provider_fees = Decimal("100.00")
    mock_claim.allowed_fees = Decimal("100.00")
    mock_claim.member_coinsurance = Decimal("0.00")
    mock_claim.member_copay = Decimal("0.00")

    with patch.object(ClaimProcessor, "process_claims_json", return_value=[mock_claim]):
        # Create payload with one claim
        payload = {
            "claims": [
                {
                    "service_date": "3/28/18 0:00",
                    "submitted_procedure": "D0180",
                    "quadrant": "",
                    "plan_group": "GRP-1000",
                    "subscriber": "3730189502",
                    "provider_npi": "1497775530",
                    "provider_fees": "$100.00",
                    "allowed_fees": "$100.00",
                    "member_coinsurance": "$0.00",
                    "member_copay": "$0.00"
                }
            ]
        }
        
        # Call the endpoint
        response = client.post("/claims/process", json=payload)
        
        # Assertions
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["claim_id"] == "CLM-12345678"


def test_process_claims_csv_endpoint(client, sample_claim_data):
    """Test process claims CSV endpoint"""
    # Mock ClaimProcessor.process_claims_csv
    mock_claim = MagicMock()
    mock_claim.id = 1
    mock_claim.claim_id = "CLM-12345678"
    mock_claim.net_fee = Decimal("0.00")
    mock_claim.service_date = datetime(2018, 3, 28).date()
    mock_claim.submitted_procedure = "D0180"
    mock_claim.quadrant = None
    mock_claim.plan_group = "GRP-1000"
    mock_claim.subscriber = "3730189502"
    mock_claim.provider_npi = "1497775530"
    mock_claim.provider_fees = Decimal("100.00")
    mock_claim.allowed_fees = Decimal("100.00")
    mock_claim.member_coinsurance = Decimal("0.00")
    mock_claim.member_copay = Decimal("0.00")

    # Mock open function to avoid writing to disk
    mock_open = MagicMock()
    
    with patch.object(ClaimProcessor, "process_claims_csv", return_value=[mock_claim]), \
         patch("builtins.open", mock_open):
        
        # Create a mock CSV file
        csv_content = "service date,submitted procedure,quadrant,Plan/Group #,Subscriber#,Provider NPI,provider fees,Allowed fees,member coinsurance,member copay\n"
        csv_content += "3/28/18 0:00,D0180,,GRP-1000,3730189502,1497775530,$100.00 ,$100.00 ,$0.00 ,$0.00 "
        
        # Call the endpoint
        response = client.post(
            "/claims/process-csv",
            files={"file": ("test.csv", csv_content.encode(), "text/csv")}
        )
        
        # Assertions
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["claim_id"] == "CLM-12345678"


def test_get_top_providers_endpoint(client):
    """Test get top providers endpoint"""
    # Mock ClaimProcessor.get_top_providers_by_net_fee
    mock_providers = [
        {"provider_npi": "1234567890", "total_net_fee": Decimal("100.00")},
        {"provider_npi": "0987654321", "total_net_fee": Decimal("50.00")},
    ]
    
    with patch.object(ClaimProcessor, "get_top_providers_by_net_fee", return_value=mock_providers):
        # Call the endpoint
        response = client.get("/claims/top-providers")
        
        # Assertions
        assert response.status_code == 200
        assert len(response.json()) == 2
        assert response.json()[0]["provider_npi"] == "1234567890"
        assert float(response.json()[0]["total_net_fee"]) == float("100.00")
        assert response.json()[1]["provider_npi"] == "0987654321"
        assert float(response.json()[1]["total_net_fee"]) == float("50.00")
