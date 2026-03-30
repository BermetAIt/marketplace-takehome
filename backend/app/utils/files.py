import re
import uuid
from pathlib import Path
from typing import Tuple

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings

ALLOWED_IMAGE = {"image/jpeg", "image/png", "image/webp", "image/gif"}
ALLOWED_DOC = {"application/pdf"}
ALLOWED_MESSAGE = ALLOWED_IMAGE | ALLOWED_DOC


def _safe_ext(mime: str) -> str:
    return {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
        "image/gif": ".gif",
        "application/pdf": ".pdf",
    }.get(mime, ".bin")


def sanitize_original_name(name: str) -> str:
    base = Path(name).name
    base = re.sub(r"[^a-zA-Z0-9._-]", "_", base)
    return base[:200] if base else "file"


async def save_upload_file(
    file: UploadFile,
    *,
    subdir: str,
    allowed_mime: set[str],
    max_bytes: int,
) -> Tuple[str, str, int, str]:
    if not file.content_type or file.content_type not in allowed_mime:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type",
        )
    data = await file.read()
    if len(data) > max_bytes:
        raise HTTPException(status_code=400, detail="File too large")
    ext = _safe_ext(file.content_type)
    name = f"{uuid.uuid4().hex}{ext}"
    base = settings.upload_path / subdir
    base.mkdir(parents=True, exist_ok=True)
    path = base / name
    path.write_bytes(data)
    rel = f"{subdir}/{name}"
    return rel, sanitize_original_name(file.filename or name), len(data), file.content_type
