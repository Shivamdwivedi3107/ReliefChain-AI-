from sqlalchemy import Column, String, Integer, DateTime, JSON
from app.database import Base
from app.models.base import generate_uuid, get_utc_now


class BlockchainTransaction(Base):
    __tablename__ = "blockchain_transactions"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    event_type = Column(String(50), nullable=False, index=True)  # donation, allocation, distribution, qr_verification
    reference_id = Column(String(36), nullable=False, index=True)  # ID of donation, request, distribution
    record_hash = Column(String(64), nullable=False, index=True)  # SHA-256 hash of payload
    previous_hash = Column(String(64), nullable=True, default="0000000000000000000000000000000000000000000000000000000000000000")
    tx_hash = Column(String(66), nullable=True, unique=True, index=True)
    block_number = Column(Integer, nullable=True, index=True)
    from_address = Column(String(42), nullable=True)
    contract_address = Column(String(42), nullable=True)
    status = Column(String(30), nullable=False, default="confirmed", index=True)  # pending, confirmed, failed
    raw_receipt = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False, index=True)

    @property
    def transaction_id(self) -> str:
        return self.id

    @property
    def current_hash(self) -> str:
        return self.tx_hash or self.record_hash

    @property
    def transaction_type(self) -> str:
        return self.event_type

    @property
    def related_entity_id(self) -> str:
        return self.reference_id

    @property
    def data_hash(self) -> str:
        return self.record_hash
