"""
Pydantic models for request/response validation.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import date


class TransactionCreate(BaseModel):
    """Model for creating a new transaction."""
    date: str = Field(..., description="Transaction date in YYYY-MM-DD format")
    account: str = Field(..., description="Account name")
    category: str = Field(..., description="Main category")
    subcategory: str = Field(..., description="Subcategory")
    description: str = Field(default="", description="Transaction note/description")
    amount: float = Field(..., gt=0, description="Transaction amount (positive)")
    type: str = Field(default="Expense", description="Transaction type (Expense/Income/Transfer/Asset)")
    status: str = Field(default="Normal", description="Transaction status (Normal/Flagged)")


class TransactionUpdate(BaseModel):
    """Model for updating an existing transaction."""
    date: Optional[str] = Field(None, description="Transaction date in YYYY-MM-DD format")
    account: Optional[str] = Field(None, description="Account name")
    category: Optional[str] = Field(None, description="Main category")
    subcategory: Optional[str] = Field(None, description="Subcategory")
    description: Optional[str] = Field(None, description="Transaction note/description")
    amount: Optional[float] = Field(None, gt=0, description="Transaction amount (positive)")
    type: Optional[str] = Field(None, description="Transaction type")
    status: Optional[str] = Field(None, description="Transaction status")


class InvestmentCreate(BaseModel):
    """Model for creating a new investment (stock purchase)."""
    symbol: str = Field(..., description="Stock ticker symbol")
    shares: float = Field(..., gt=0, description="Number of shares")
    price: float = Field(..., gt=0, description="Price per share")
    account: str = Field(..., description="Investment account (e.g., RDN Wallet)")
    source_account: Optional[str] = Field(None, description="Source bank account for transfer tracking")
    currency: str = Field(default="IDR", description="Currency (IDR/USD)")
    date: Optional[str] = Field(None, description="Purchase date in YYYY-MM-DD format")


class TransferCreate(BaseModel):
    """Model for creating a transfer between accounts."""
    date: str = Field(..., description="Transfer date in YYYY-MM-DD format")
    from_account: str = Field(..., description="Source account")
    to_account: str = Field(..., description="Destination account")
    amount: float = Field(..., gt=0, description="Transfer amount")
    note: Optional[str] = Field(None, description="Optional transfer note")


class TransactionResponse(BaseModel):
    """Model for transaction response."""
    count: int
    transactions: list[dict]


class CategoriesResponse(BaseModel):
    """Model for categories response."""
    count: int
    categories: list[dict]
    cached: bool = False


class AccountsResponse(BaseModel):
    """Model for accounts response."""
    count: int
    accounts: list[dict]
    cached: bool = False
