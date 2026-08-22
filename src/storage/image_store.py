"""Image byte storage shared by property and project image uploads.

In development files are written under ``temp/uploads/``. In production set
``STORAGE_BACKEND=s3`` plus the S3 env vars; ``storage_key`` becomes the S3
object key and the returned URL points at ``CDN_BASE_URL``.
"""
from __future__ import annotations

import os
from pathlib import Path

from fastapi import HTTPException

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_BYTES = 10 * 1024 * 1024  # 10 MB

_STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "local")
_LOCAL_UPLOAD_DIR = Path(os.getenv("LOCAL_UPLOAD_DIR", "temp/uploads"))
_CDN_BASE_URL = os.getenv("CDN_BASE_URL", "http://localhost:8000/static")


def _save_local(file_bytes: bytes, storage_key: str) -> str:
    dest = _LOCAL_UPLOAD_DIR / storage_key
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(file_bytes)
    return f"{_CDN_BASE_URL}/{storage_key}"


def _delete_local(storage_key: str) -> None:
    path = _LOCAL_UPLOAD_DIR / storage_key
    if path.exists():
        path.unlink()


def store(file_bytes: bytes, storage_key: str) -> str:
    """Save bytes and return the public CDN URL."""
    if _STORAGE_BACKEND == "s3":
        try:
            import boto3  # type: ignore

            s3 = boto3.client("s3")
            bucket = os.environ["S3_BUCKET"]
            s3.put_object(Bucket=bucket, Key=storage_key, Body=file_bytes)
            return f"{_CDN_BASE_URL}/{storage_key}"
        except ImportError:
            raise HTTPException(500, "boto3 not installed; set STORAGE_BACKEND=local")
    return _save_local(file_bytes, storage_key)


def read(storage_key: str) -> bytes:
    """Read an object by key for AI reference-image workflows."""
    if _STORAGE_BACKEND == "s3":
        try:
            import boto3  # type: ignore

            response = boto3.client("s3").get_object(
                Bucket=os.environ["S3_BUCKET"], Key=storage_key
            )
            return response["Body"].read()
        except ImportError as exc:
            raise RuntimeError("boto3 not installed; cannot read S3 object") from exc
    return (_LOCAL_UPLOAD_DIR / storage_key).read_bytes()


def remove(storage_key: str) -> None:
    if _STORAGE_BACKEND != "s3":
        _delete_local(storage_key)
    # S3 deletion omitted for brevity; add boto3.delete_object in production
