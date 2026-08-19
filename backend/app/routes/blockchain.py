from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_active_user, require_roles
from app.models.blockchain import BlockchainTransaction
from app.models.user import User
from app.schemas.blockchain import (
    BlockchainTransactionCreate,
    BlockchainTransactionOut,
    BlockchainVerifyRequest,
    BlockchainVerifyResponse,
    LedgerChainIntegrityResponse,
)
from app.schemas.common import PaginatedResponse
from app.services.blockchain_service import blockchain_service

router = APIRouter(prefix="", tags=["Blockchain & Tamper-Evident Transparency Ledger"])


@router.post("/blockchain/record", response_model=BlockchainTransactionOut, status_code=status.HTTP_201_CREATED, summary="Submit a record hash to the audit ledger")
@router.post("/ledger/record", response_model=BlockchainTransactionOut, status_code=status.HTTP_201_CREATED, include_in_schema=False)
def record_to_blockchain(
    payload: BlockchainTransactionCreate,
    current_user: User = Depends(require_roles(["ngo", "admin", "volunteer"])),
    db: Session = Depends(get_db),
):
    # Fetch most recent transaction to link previous_hash in chain
    latest_tx = db.query(BlockchainTransaction).order_by(BlockchainTransaction.created_at.desc()).first()
    previous_hash = latest_tx.current_hash if latest_tx else "0000000000000000000000000000000000000000000000000000000000000000"

    tx_hash, block_num, tx_status = blockchain_service.record_hash_on_chain(
        record_hash=payload.record_hash,
        event_type=payload.event_type,
        reference_id=payload.reference_id,
        caller_address=payload.from_address,
        previous_hash=previous_hash,
    )

    bc_tx = BlockchainTransaction(
        event_type=payload.event_type,
        reference_id=payload.reference_id,
        record_hash=payload.record_hash,
        previous_hash=previous_hash,
        tx_hash=tx_hash,
        block_number=block_num,
        from_address=payload.from_address,
        contract_address=payload.contract_address,
        status=tx_status,
    )
    db.add(bc_tx)
    db.commit()
    db.refresh(bc_tx)
    return bc_tx


@router.post("/blockchain/verify", response_model=BlockchainVerifyResponse, summary="Verify state integrity of a record hash against the ledger")
def verify_blockchain_record(
    payload: BlockchainVerifyRequest,
    db: Session = Depends(get_db),
):
    bc_tx = (
        db.query(BlockchainTransaction)
        .filter(BlockchainTransaction.record_hash == payload.record_hash)
        .first()
    )

    if not bc_tx:
        return BlockchainVerifyResponse(
            is_verified=False,
            record_hash=payload.record_hash,
            status="not_found_on_ledger",
            message="Record hash not found on transparency ledger.",
        )

    verify_info = blockchain_service.verify_hash_on_chain(payload.record_hash)

    return BlockchainVerifyResponse(
        is_verified=verify_info["is_valid"],
        record_hash=payload.record_hash,
        tx_hash=bc_tx.tx_hash,
        block_number=bc_tx.block_number,
        timestamp=bc_tx.created_at,
        status=bc_tx.status,
        message=verify_info["audit_guarantee"],
    )


@router.get("/ledger/verify", response_model=LedgerChainIntegrityResponse, summary="Verify whole ledger cryptographic chain integrity")
@router.get("/blockchain/verify-chain", response_model=LedgerChainIntegrityResponse, include_in_schema=False)
def verify_ledger_chain(db: Session = Depends(get_db)):
    transactions = db.query(BlockchainTransaction).order_by(BlockchainTransaction.created_at.asc()).all()
    result = blockchain_service.verify_ledger_chain_integrity(transactions)
    return LedgerChainIntegrityResponse(
        is_valid=result["is_valid"],
        total_blocks=result["total_blocks"],
        verified_blocks=result["verified_blocks"],
        status=result["status"],
        broken_links=result.get("broken_links", []),
        message=result["message"],
    )


@router.get("/ledger", response_model=PaginatedResponse[BlockchainTransactionOut], summary="List transparency ledger transactions")
@router.get("/blockchain/transactions", response_model=PaginatedResponse[BlockchainTransactionOut], summary="List all blockchain audit ledger transactions")
def list_blockchain_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    event_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(BlockchainTransaction)
    if event_type:
        query = query.filter(BlockchainTransaction.event_type == event_type)
    if status:
        query = query.filter(BlockchainTransaction.status == status)

    total = query.count()
    items = (
        query.order_by(BlockchainTransaction.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return PaginatedResponse(
        success=True,
        total=total,
        page=page,
        page_size=page_size,
        data=items,
    )


@router.get("/ledger/{transaction_id}", response_model=BlockchainTransactionOut, summary="Get ledger transaction by ID")
@router.get("/blockchain/transactions/{transaction_id}", response_model=BlockchainTransactionOut, include_in_schema=False)
def get_ledger_transaction_by_id(transaction_id: str, db: Session = Depends(get_db)):
    tx = db.query(BlockchainTransaction).filter(BlockchainTransaction.id == transaction_id).first()
    if not tx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ledger transaction not found")
    return tx
