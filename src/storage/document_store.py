"""Document byte storage for admin-uploaded legal files (terms, privacy, cookies).

Shares the backend of :mod:`src.storage.image_store` (local ``temp/uploads/`` in
development, S3 when ``STORAGE_BACKEND=s3``) but accepts document content types
instead of images. Uploaded files are served publicly at ``/static/`` so the
footer can link straight to them.
"""
from __future__ import annotations

import uuid

from fastapi import HTTPException, status

from src.storage.image_store import store as _store

MAX_BYTES = 10 * 1024 * 1024  # 10 MB

# Content-Type → file extension. PDF is the recommended format (browsers render
# it inline); Word/plain-text are accepted because that is what admins often have.
ALLOWED_CONTENT_TYPES: dict[str, str] = {
    "application/pdf": "pdf",
    "application/msword": "doc",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "text/plain": "txt",
}


def store_document(file_bytes: bytes, content_type: str | None, prefix: str) -> tuple[str, str]:
    """Validate and store a document. Returns ``(public_url, storage_key)``.

    Raises 422 when the content type is not a document or the file is too large.
    """
    ext = ALLOWED_CONTENT_TYPES.get(content_type or "")
    if ext is None:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"Content-Type {content_type!r} not allowed. Use PDF, DOC, DOCX, or TXT.",
        )
    if len(file_bytes) > MAX_BYTES:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"File too large ({len(file_bytes)} bytes). Max 10 MB.",
        )

    storage_key = f"{prefix}-{uuid.uuid4()}.{ext}"
    return _store(file_bytes, storage_key), storage_key
