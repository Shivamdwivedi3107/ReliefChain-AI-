import os
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_active_user
from app.models.user import User
from app.models.evidence import Evidence
from app.models.relief_request import ReliefRequest
from app.models.distribution import Distribution
from app.services.storage_service import storage_provider

router = APIRouter(prefix="/evidence", tags=["Disaster Evidence Management"])


@router.post("/upload", status_code=status.HTTP_201_CREATED, summary="Upload photographic or document proof of disaster/delivery")
async def upload_evidence(
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    relief_request_id: Optional[str] = Form(None),
    distribution_id: Optional[str] = Form(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    # Validate linked entity existence if provided
    if relief_request_id:
        req = db.query(ReliefRequest).filter(ReliefRequest.id == relief_request_id).first()
        if not req:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Relief request '{relief_request_id}' not found.",
            )
    if distribution_id:
        dist = db.query(Distribution).filter(Distribution.id == distribution_id).first()
        if not dist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Distribution record '{distribution_id}' not found.",
            )

    stored_name, file_path, file_size = await storage_provider.save_file(file)

    evidence = Evidence(
        uploaded_by=current_user.id,
        relief_request_id=relief_request_id,
        distribution_id=distribution_id,
        file_name=file.filename or "attachment",
        stored_name=stored_name,
        file_path=file_path,
        content_type=file.content_type or "application/octet-stream",
        file_size=file_size,
        description=description,
    )
    db.add(evidence)
    db.commit()
    db.refresh(evidence)

    return {
        "success": True,
        "message": "Evidence file uploaded securely.",
        "evidence": {
            "id": evidence.id,
            "uploaded_by": evidence.uploaded_by,
            "file_name": evidence.file_name,
            "stored_name": evidence.stored_name,
            "content_type": evidence.content_type,
            "file_size": evidence.file_size,
            "description": evidence.description,
            "relief_request_id": evidence.relief_request_id,
            "distribution_id": evidence.distribution_id,
            "created_at": evidence.created_at.isoformat() if evidence.created_at else None,
        },
    }


@router.get("/{evidence_id}", summary="Get evidence record metadata")
def get_evidence_metadata(
    evidence_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    ev = db.query(Evidence).filter(Evidence.id == evidence_id).first()
    if not ev:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence record not found.")

    return {
        "success": True,
        "evidence": {
            "id": ev.id,
            "uploaded_by": ev.uploaded_by,
            "file_name": ev.file_name,
            "stored_name": ev.stored_name,
            "content_type": ev.content_type,
            "file_size": ev.file_size,
            "description": ev.description,
            "relief_request_id": ev.relief_request_id,
            "distribution_id": ev.distribution_id,
            "created_at": ev.created_at.isoformat() if ev.created_at else None,
        },
    }


@router.get("/{evidence_id}/download", summary="Download/Stream verified evidence file")
def download_evidence_file(
    evidence_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    ev = db.query(Evidence).filter(Evidence.id == evidence_id).first()
    if not ev or not os.path.exists(ev.file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence file not found on disk.")

    return FileResponse(
        path=ev.file_path,
        media_type=ev.content_type,
        filename=ev.file_name,
    )


@router.delete("/{evidence_id}", summary="Delete an evidence file (Uploader or Admin only)")
def delete_evidence(
    evidence_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    ev = db.query(Evidence).filter(Evidence.id == evidence_id).first()
    if not ev:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence record not found.")

    # Only uploader or admin can delete
    if ev.uploaded_by != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized to delete this evidence record.")

    storage_provider.delete_file(ev.file_path)
    db.delete(ev)
    db.commit()

    return {"success": True, "message": "Evidence record deleted successfully."}
