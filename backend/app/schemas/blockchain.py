from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import Field
from app.schemas.common import BaseSchema


class BlockchainTransactionCreate(BaseSchema):
    event_type: str
    reference_id: str
    record_hash: str
    from_address: Optional[str] = None
    contract_address: Optional[str] = None


class BlockchainTransactionOut(BaseSchema):
    id: str
    transaction_id: Optional[str] = None
    event_type: str
    transaction_type: Optional[str] = None
    reference_id: str
    related_entity_id: Optional[str] = None
    record_hash: str
    data_hash: Optional[str] = None
    previous_hash: Optional[str] = None
    tx_hash: Optional[str] = None
    current_hash: Optional[str] = None
    block_number: Optional[int] = None
    from_address: Optional[str] = None
    contract_address: Optional[str] = None
    status: str
    raw_receipt: Optional[Dict[str, Any]] = None
    created_at: datetime
    timestamp: Optional[datetime] = None


class BlockchainVerifyRequest(BaseSchema):
    reference_id: Optional[str] = None
    record_hash: str


class BlockchainVerifyResponse(BaseSchema):
    is_verified: bool
    record_hash: str
    tx_hash: Optional[str] = None
    block_number: Optional[int] = None
    timestamp: Optional[datetime] = None
    status: str
    message: Optional[str] = None


class LedgerChainIntegrityResponse(BaseSchema):
    is_valid: bool
    total_blocks: int
    verified_blocks: int
    status: str
    broken_links: List[Dict[str, Any]] = Field(default_factory=list)
    message: str
