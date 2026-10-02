"""
Pydantic Schemas for Google AdSense Publisher & Transaction Resolution.
Compatible with Google Antigravity & Gemini 3.8.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class AdSenseTransaction(BaseModel):
    transaction_id: str = Field(..., description="AdSense payment reference / transaction number")
    publisher_id: str = Field(..., description="Google AdSense Publisher ID (e.g. pub-8501247963214589)")
    payment_date: str = Field(..., description="Date of transaction disbursement (YYYY-MM-DD)")
    currency: str = Field(default="USD", description="Currency code (USD, IDR, EUR, etc.)")
    gross_amount: float = Field(..., description="Gross advertising earnings before withholding")
    tax_withheld: float = Field(default=0.0, description="Withheld US or local taxes")
    net_amount: float = Field(..., description="Net payout amount received by the publisher")
    payment_method: str = Field(default="Electronic Funds Transfer (EFT)", description="Disbursement method")
    status: str = Field(default="COMPLETED", description="Transaction status (COMPLETED, PENDING, PROCESSED)")
    description: Optional[str] = Field(default="Google AdSense Monthly Revenue Distribution", description="Description")
    audit_hash: Optional[str] = Field(default=None, description="SHA256 audit verification fingerprint")


class AdSenseResolveRequest(BaseModel):
    transaction: Optional[AdSenseTransaction] = Field(default=None, description="Structured transaction object")
    raw_receipt_text: Optional[str] = Field(
        default=None,
        description="Raw AdSense receipt, bank transfer remark, or payment email snippet"
    )
    verify_against_ledger: bool = Field(default=True, description="Whether to audit against local knowledge base")


class AdSenseResolveResponse(BaseModel):
    status: str = Field(..., description="Resolution status (VALIDATED, RECONCILED, DISCREPANCY_DETECTED)")
    publisher_id: str = Field(..., description="Audited Publisher ID")
    transaction_id: str = Field(..., description="Audited Transaction Reference ID")
    net_payout: float = Field(..., description="Net verified payout amount")
    currency: str = Field(..., description="Currency")
    is_valid_pub_format: bool = Field(..., description="Whether pub ID matches ^pub-\\d{16}$")
    ads_txt_compliant: bool = Field(..., description="Whether ads.txt is valid and served")
    audit_summary: str = Field(..., description="Gemini 3.8 audit assessment summary")
    discrepancies: List[str] = Field(default_factory=list, description="Any detected discrepancies or flags")
    reconciled_at: str = Field(..., description="Timestamp of reconciliation")
    gemini_model: str = Field(..., description="Gemini model that performed the audit")


class AdSenseStatusResponse(BaseModel):
    publisher_id: str
    client_id: str
    ads_txt_url: str
    ads_txt_line: str
    is_compliant: bool
    total_transactions: int
    total_earnings_usd: float
    active_model: str


class AdSenseLedgerResponse(BaseModel):
    publisher_id: str
    total_earnings_usd: float
    total_payouts_completed: int
    transactions: List[AdSenseTransaction]
