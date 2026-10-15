from pathlib import Path
from uuid import uuid4
from fastapi import UploadFile, HTTPException

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_SIZE = 5 * 1024 * 1024


async def save_image(file: UploadFile, upload_dir: str = "uploads") -> str:
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=415, detail="Only JPEG, PNG, and WebP images are allowed")
    content = await file.read(MAX_SIZE + 1)
    if len(content) > MAX_SIZE:
        raise HTTPException(status_code=413, detail="Image must be 5 MB or smaller")
    suffix = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}[file.content_type]
    target_dir = Path(upload_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    name = f"{uuid4().hex}{suffix}"
    (target_dir / name).write_bytes(content)
    return f"/uploads/{name}"
