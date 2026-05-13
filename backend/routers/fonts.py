from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from ..core.api import ApiResponse, success_response
from ..core.utils import list_available_fonts

router = APIRouter(prefix="/fonts", tags=["fonts"])


class FontItem(BaseModel):
    name: str
    file: str


class FontsResponse(BaseModel):
    fonts: list[FontItem]


@router.get("", response_model=ApiResponse[FontsResponse])
async def list_fonts() -> ApiResponse[FontsResponse]:
    fonts = [FontItem(**font) for font in list_available_fonts()]
    return success_response(FontsResponse(fonts=fonts))
