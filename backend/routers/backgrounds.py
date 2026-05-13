from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel

from ..core.api import ApiResponse, success_response
from ..core.settings import BACKGROUND_DIR, UPLOAD_DIR
from ..core.utils import ALLOWED_IMAGE_FORMATS

router = APIRouter(prefix="/backgrounds", tags=["backgrounds"])


class BackgroundItem(BaseModel):
    name: str
    file: str
    url: str


class BackgroundsResponse(BaseModel):
    backgrounds: list[BackgroundItem]
    count: int


def _is_supported_background(path: str) -> bool:
    suffix = path.rsplit(".", 1)[-1].upper() if "." in path else ""
    return suffix in ALLOWED_IMAGE_FORMATS


@router.get("", response_model=ApiResponse[BackgroundsResponse])
async def list_backgrounds(request: Request) -> ApiResponse[BackgroundsResponse]:
    items: list[BackgroundItem] = []
    seen_files: set[str] = set()

    for file_path in sorted(BACKGROUND_DIR.iterdir()):
        if not file_path.is_file():
            continue
        if not _is_supported_background(file_path.name):
            continue
        items.append(
            BackgroundItem(
                name=file_path.stem,
                file=file_path.name,
                url=f"/background/{file_path.name}",
            )
        )
        seen_files.add(file_path.name)

    session_uploads = request.session.get("uploaded_backgrounds", [])
    for file_name in session_uploads:
        candidate = UPLOAD_DIR / file_name
        if not candidate.exists():
            continue
        if not candidate.is_file():
            continue
        if not _is_supported_background(candidate.name):
            continue
        if candidate.name in seen_files:
            continue
        items.append(
            BackgroundItem(
                name=candidate.stem,
                file=candidate.name,
                url=f"/static/uploads/{candidate.name}",
            )
        )
        seen_files.add(candidate.name)

    return success_response(BackgroundsResponse(backgrounds=items, count=len(items)))
