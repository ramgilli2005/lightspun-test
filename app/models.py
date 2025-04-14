from typing import Optional
from sqlmodel import Field, SQLModel
from datetime import date
from decimal import Decimal
from pydantic import validator


class ClaimBase(SQLModel):
    """Base model for claim data"""
    service_date: date
    submitted_procedure: str
    quadrant: Optional[str] = None
    plan_group: str = Field(default="GRP-1000")
    subscriber: str = Field(default="0000000000")
    provider_npi: str = Field(default="1234567890")
    provider_fees: Decimal = Field(default=Decimal("0.00"))
    allowed_fees: Decimal = Field(default=Decimal("0.00"))
    member_coinsurance: Decimal = Field(default=Decimal("0.00"))
    member_copay: Decimal = Field(default=Decimal("0.00"))

    @validator("submitted_procedure")
    def validate_submitted_procedure(cls, v):
        """Validate that submitted procedure begins with the letter 'D'"""
        if not v or not v.startswith("D"):
            raise ValueError("Submitted procedure must begin with the letter 'D'")
        return v

    @validator("provider_npi")
    def validate_provider_npi(cls, v):
        """Validate that provider NPI is a 10 digit number"""
        if not v or not v.isdigit() or len(v) != 10:
            raise ValueError("Provider NPI must be a 10 digit number")
        return v


class Claim(ClaimBase, table=True):
    """Claim model for database storage"""
    id: Optional[int] = Field(default=None, primary_key=True)
    claim_id: str = Field(default="", index=True)
    net_fee: Decimal = Field(default=Decimal("0.00"))


class ClaimCreate(ClaimBase):
    """Model for creating a new claim"""
    pass


class ClaimRead(SQLModel):
    """Model for reading a claim"""
    id: int
    claim_id: str
    net_fee: Decimal
    service_date: date
    submitted_procedure: str
    quadrant: Optional[str] = None
    plan_group: str
    subscriber: str
    provider_npi: str
    provider_fees: Decimal
    allowed_fees: Decimal
    member_coinsurance: Decimal
    member_copay: Decimal


class TopProviderResponse(SQLModel):
    """Model for top provider response"""
    provider_npi: str
    total_net_fee: Decimal
