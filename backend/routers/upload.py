from __future__ import annotations

from fastapi import APIRouter, File, Request, UploadFile, status
from pydantic import BaseModel

from ..core.api import ApiResponse, AppError, success_response
from ..core.settings import ALLOWED_IMAGE_MIME_TYPES
from ..core.utils import sanitize_upload_image, save_uploaded_image

router = APIRouter(prefix="/upload", tags=["upload"])


class UploadResponse(BaseModel):
    path: str
    width: int
    height: int


@router.post("", response_model=ApiResponse[UploadResponse])
async def upload_background(
    request: Request, file: UploadFile = File(...)
) -> ApiResponse[UploadResponse]:
    if not file.content_type:
        raise AppError(
            code=4001,
            message="无法识别文件类型",
            http_status=status.HTTP_400_BAD_REQUEST,
        )

    content_type = file.content_type.lower()
    if content_type not in ALLOWED_IMAGE_MIME_TYPES:
        raise AppError(
            code=4002,
            message="仅支持 PNG/JPEG/WebP 图片",
            http_status=status.HTTP_400_BAD_REQUEST,
        )

    data = await file.read()
    try:
        image = sanitize_upload_image(data)
    except ValueError as exc:
        raise AppError(
            code=4003,
            message=str(exc),
            http_status=status.HTTP_400_BAD_REQUEST,
        ) from exc

    saved_path = save_uploaded_image(image)
    session_uploads = request.session.get("uploaded_backgrounds", [])
    if saved_path.name not in session_uploads:
        # Persist uploaded backgrounds per session so users can reuse them later
        session_uploads.append(saved_path.name)
        request.session["uploaded_backgrounds"] = session_uploads

    return success_response(
        UploadResponse(
            path=f"/static/uploads/{saved_path.name}",
            width=image.width,
            height=image.height,
        )
    )
