import os
import uuid
import shutil
from abc import ABC, abstractmethod
from typing import Tuple
from fastapi import UploadFile, HTTPException, status
from app.core.logging import logger

ALLOWED_MIME_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "application/pdf": ".pdf",
}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


class StorageProvider(ABC):
    @abstractmethod
    async def save_file(self, upload_file: UploadFile) -> Tuple[str, str, int]:
        """Saves uploaded file and returns (stored_name, file_path, file_size_bytes)."""
        pass

    @abstractmethod
    def delete_file(self, file_path: str) -> bool:
        """Deletes file from storage."""
        pass


class LocalStorageProvider(StorageProvider):
    def __init__(self, base_dir: str = "uploads/evidence"):
        self.base_dir = os.path.abspath(base_dir)
        os.makedirs(self.base_dir, exist_ok=True)

    async def save_file(self, upload_file: UploadFile) -> Tuple[str, str, int]:
        content_type = upload_file.content_type
        if content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file format '{content_type}'. Allowed types: {list(ALLOWED_MIME_TYPES.keys())}",
            )

        ext = ALLOWED_MIME_TYPES[content_type]
        stored_name = f"evidence_{uuid.uuid4().hex}{ext}"
        destination_path = os.path.join(self.base_dir, stored_name)

        # Path traversal guard
        if not os.path.abspath(destination_path).startswith(self.base_dir):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Security violation: Path traversal detected in upload.",
            )

        # Read and enforce max file size
        file_bytes = await upload_file.read()
        file_size = len(file_bytes)
        if file_size > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File exceeds maximum allowed size of {MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB.",
            )

        with open(destination_path, "wb") as f:
            f.write(file_bytes)

        logger.info(f"Evidence file stored: {stored_name} ({file_size} bytes)")
        return stored_name, destination_path, file_size

    def delete_file(self, file_path: str) -> bool:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
        except Exception as err:
            logger.warning(f"Failed deleting evidence file {file_path}: {err}")
        return False


class FutureS3StorageProvider(StorageProvider):
    """Placeholder architecture stub for future AWS S3 / Google Cloud Storage integration."""
    def __init__(self, bucket_name: str = "reliefchain-evidence"):
        self.bucket_name = bucket_name

    async def save_file(self, upload_file: UploadFile) -> Tuple[str, str, int]:
        raise NotImplementedError("S3 storage is scheduled for Phase 6 cloud migration.")

    def delete_file(self, file_path: str) -> bool:
        raise NotImplementedError("S3 storage is scheduled for Phase 6 cloud migration.")


storage_provider = LocalStorageProvider()
