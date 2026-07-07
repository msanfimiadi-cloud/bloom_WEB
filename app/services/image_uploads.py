from __future__ import annotations

from pathlib import Path
from secrets import token_urlsafe
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings

ALLOWED_IMAGE_KINDS = {"logo", "cover"}
ALLOWED_CONTENT_TYPES = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024
MAX_CONTENT_IMAGE_SIZE_BYTES = 10 * 1024 * 1024
_READ_CHUNK_SIZE = 1024 * 1024


def validate_image_kind(kind: str) -> str:
    normalized = str(kind or "").strip().lower()
    if normalized not in ALLOWED_IMAGE_KINDS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid image kind"
        )
    return normalized


async def save_content_image_upload(file: UploadFile) -> dict[str, object]:
    _validate_content_type(file.content_type)
    original_extension = _validate_required_filename_extension(file.filename)
    content = await _read_upload_bytes(
        file, max_size_bytes=MAX_CONTENT_IMAGE_SIZE_BYTES
    )
    detected_extension = _detect_image_extension(content)
    _validate_content_matches_extension(detected_extension, original_extension)
    _validate_content_matches_type(detected_extension, file.content_type)

    destination_parts = ("content",)
    destination_dir = Path(settings.UPLOAD_DIR).joinpath(*destination_parts)
    destination_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid4()}{original_extension}"
    destination_path = destination_dir / filename
    destination_path.write_bytes(content)

    public_prefix = settings.PUBLIC_UPLOADS_PATH.rstrip("/") or "/uploads"
    public_path = f"{public_prefix}/content/{filename}"
    return {
        "url": f"{settings.WEB_PUBLIC_URL.rstrip('/')}{public_path}",
        "path": public_path,
        "filename": filename,
        "content_type": file.content_type or "",
        "size": len(content),
    }


async def save_partner_image_upload(
    partner_id: int, kind: str, file: UploadFile
) -> str:
    normalized_kind = validate_image_kind(kind)
    return await _save_validated_image_upload(
        file=file,
        destination_parts=("partners", str(partner_id)),
        filename_prefix=normalized_kind,
    )


async def save_partner_photo_image_upload(partner_id: int, file: UploadFile) -> str:
    return await _save_validated_image_upload(
        file=file,
        destination_parts=("partners", str(partner_id), "photos"),
        filename_prefix="photo",
    )


async def save_partner_offer_image_upload(
    partner_id: int, offer_id: int, file: UploadFile
) -> str:
    return await _save_validated_image_upload(
        file=file,
        destination_parts=("partners", str(partner_id), "offers", str(offer_id)),
        filename_prefix="offer",
    )


async def save_offer_photo_image_upload(
    partner_id: int, offer_id: int, file: UploadFile
) -> str:
    return await _save_validated_image_upload(
        file=file,
        destination_parts=(
            "partners",
            str(partner_id),
            "offers",
            str(offer_id),
            "photos",
        ),
        filename_prefix="offer-photo",
    )


async def _save_validated_image_upload(
    *,
    file: UploadFile,
    destination_parts: tuple[str, ...],
    filename_prefix: str,
) -> str:
    _validate_content_type(file.content_type)
    _validate_filename_extension(file.filename)
    content = await _read_upload_bytes(file)
    extension = _detect_image_extension(content)

    destination_dir = Path(settings.UPLOAD_DIR).joinpath(*destination_parts)
    destination_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{filename_prefix}-{token_urlsafe(16)}.{extension}"
    destination_path = destination_dir / filename
    destination_path.write_bytes(content)

    public_prefix = settings.PUBLIC_UPLOADS_PATH.rstrip("/") or "/uploads"
    return f"{public_prefix}/{'/'.join(destination_parts)}/{filename}"


def _validate_content_type(content_type: str | None) -> None:
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid image content type"
        )


def _validate_filename_extension(filename: str | None) -> None:
    if not filename:
        return
    suffix = Path(filename).suffix.lower()
    if suffix and suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid image extension"
        )


def _validate_required_filename_extension(filename: str | None) -> str:
    suffix = Path(filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid image extension"
        )
    return suffix


def _validate_content_matches_extension(
    detected_extension: str, filename_extension: str
) -> None:
    normalized_extension = (
        "jpg"
        if filename_extension in {".jpg", ".jpeg"}
        else filename_extension.removeprefix(".")
    )
    if detected_extension != normalized_extension:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid image bytes"
        )


def _validate_content_matches_type(
    detected_extension: str, content_type: str | None
) -> None:
    expected_extension = ALLOWED_CONTENT_TYPES.get(content_type or "")
    if expected_extension != detected_extension:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid image content type"
        )


async def _read_upload_bytes(
    file: UploadFile, *, max_size_bytes: int = MAX_IMAGE_SIZE_BYTES
) -> bytes:
    chunks: list[bytes] = []
    size = 0
    while True:
        chunk = await file.read(_READ_CHUNK_SIZE)
        if not chunk:
            break
        size += len(chunk)
        if size > max_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Image file is too large",
            )
        chunks.append(chunk)
    content = b"".join(chunks)
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid image bytes"
        )
    return content


def _detect_image_extension(content: bytes) -> str:
    if content.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if len(content) >= 12 and content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return "webp"
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid image bytes"
    )
