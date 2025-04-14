import pytest
from decimal import Decimal
from datetime import datetime
from unittest.mock import MagicMock, patch
import json

from app.services.claim_processor import ClaimProcessor
from app.models import Claim


@pytest.fixture
def claim_processor():
    """Fixture for ClaimProcessor"""
    return ClaimProcessor()


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


def test_generate_claim_id(claim_processor):
    """Test generate_claim_id method"""
    claim_id = claim_processor.generate_claim_id()
    assert claim_id.startswith("CLM-")
    assert len(claim_id) == 12  # "CLM-" + 8 hex characters


def test_calculate_net_fee(claim_processor):
    """Test calculate_net_fee method"""
    provider_fees = Decimal("100.00")
    member_coinsurance = Decimal("10.00")
    member_copay = Decimal("5.00")
    allowed_fees = Decimal("80.00")

    net_fee = claim_processor.calculate_net_fee(
        provider_fees, member_coinsurance, member_copay, allowed_fees
    )

    # 100 + 10 + 5 - 80 = 35
    assert net_fee == Decimal("35.00")


def test_parse_decimal(claim_processor):
    """Test parse_decimal method"""
    assert claim_processor.parse_decimal("$100.00 ") == Decimal("100.00")
    assert claim_processor.parse_decimal("$0.00 ") == Decimal("0.00")
    assert claim_processor.parse_decimal("100.00") == Decimal("100.00")


def test_parse_date(claim_processor):
    """Test parse_date method"""
    date = claim_processor.parse_date("3/28/18 0:00")
    assert date == datetime(2018, 3, 28).date()


def test_process_claim_data(claim_processor, sample_claim_data):
    """Test process_claim_data method"""
    # Mock session
    mock_session = MagicMock()
    
    # Mock Claim.from_orm to return a mock claim
    mock_claim = MagicMock(spec=Claim)
    
    with patch("app.services.claim_processor.Claim") as mock_claim_class:
        mock_claim_class.from_orm.return_value = mock_claim
        
        # Call the method
        result = claim_processor.process_claim_data(sample_claim_data, mock_session)
        
        # Assertions
        assert result == mock_claim
        assert mock_claim.claim_id.startswith("CLM-")
        assert mock_claim.net_fee == Decimal("0.00")  # 100 + 0 + 0 - 100 = 0
        
        # Verify session methods were called
        mock_session.add.assert_called_once_with(mock_claim)
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once_with(mock_claim)


def test_process_claims_json(claim_processor, sample_claim_data):
    """Test process_claims_json method"""
    # Mock session
    mock_session = MagicMock()
    
    # Mock process_claim_data to return a mock claim
    mock_claim = MagicMock(spec=Claim)
    
    with patch.object(claim_processor, "process_claim_data", return_value=mock_claim) as mock_process:
        # Create JSON with two claims
        claims_json = json.dumps([sample_claim_data, sample_claim_data])
        
        # Call the method
        result = claim_processor.process_claims_json(claims_json, mock_session)
        
        # Assertions
        assert len(result) == 2
        assert result[0] == mock_claim
        assert result[1] == mock_claim
        
        # Verify process_claim_data was called twice
        assert mock_process.call_count == 2


def test_get_top_providers_by_net_fee(claim_processor):
    """Test get_top_providers_by_net_fee method"""
    # Mock session
    mock_session = MagicMock()
    
    # Mock session.exec to return a list of tuples (provider_npi, total_net_fee)
    mock_session.exec.return_value.all.return_value = [
        ("1234567890", Decimal("100.00")),
        ("0987654321", Decimal("50.00")),
    ]
    
    # Call the method
    result = claim_processor.get_top_providers_by_net_fee(mock_session, 2)
    
    # Assertions
    assert len(result) == 2
    assert result[0]["provider_npi"] == "1234567890"
    assert result[0]["total_net_fee"] == Decimal("100.00")
    assert result[1]["provider_npi"] == "0987654321"
    assert result[1]["total_net_fee"] == Decimal("50.00")
