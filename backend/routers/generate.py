from __future__ import annotations

from fastapi import APIRouter, status
from pydantic import BaseModel, Field, field_validator

from ..core.api import ApiResponse, AppError, success_response
from ..core.generator import (
    DEFAULT_END_CHARS,
    DEFAULT_START_CHARS,
    HandwritingConfig,
    generate_handwriting,
)
from ..core.utils import list_available_fonts

router = APIRouter(prefix="/generate", tags=["generate"])


def _default_font_name() -> str:
    fonts = list_available_fonts()
    if not fonts:
        raise AppError(
            code=5001,
            message="无可用字体，请先添加字体文件",
            http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    return fonts[0]["file"]


class GenerateRequest(BaseModel):
    text: str = Field(
        ..., min_length=1, max_length=20000, description="需要生成的文字内容"
    )
    font: str | None = Field(None, description="字体文件名，例如 example.ttf")
    font_size: int = Field(48, ge=8, le=200, description="字体大小")
    line_spacing: int = Field(60, ge=16, le=400, description="行间距")
    word_spacing: float = Field(-8.0, ge=-100.0, le=100.0, description="字间距")
    fill_color: list[int] = Field(
        default_factory=lambda: [0, 0, 0], description="RGB 颜色值"
    )
    left_margin: int = Field(80, ge=0, le=1000, description="左边距")
    top_margin: int = Field(110, ge=0, le=1000, description="上边距")
    right_margin: int = Field(80, ge=0, le=1000, description="右边距")
    bottom_margin: int = Field(150, ge=0, le=1000, description="下边距")
    line_spacing_sigma: float = Field(
        2.0, ge=0.0, le=20.0, description="行间距随机扰动"
    )
    word_spacing_sigma: float = Field(
        2.0, ge=0.0, le=20.0, description="字间距随机扰动"
    )
    font_size_sigma: float = Field(2.0, ge=0.0, le=20.0, description="字体大小随机扰动")
    perturb_x_sigma: float = Field(1.0, ge=0.0, le=20.0, description="横向偏移扰动")
    perturb_y_sigma: float = Field(1.0, ge=0.0, le=20.0, description="纵向偏移扰动")
    perturb_theta_sigma: float = Field(0.05, ge=0.0, le=1.0, description="旋转角度扰动")
    start_chars: str | None = Field(None, description="需要提前换行的字符集")
    end_chars: str | None = Field(None, description="避免出现在行首的字符集")
    background: str | None = Field(None, description="背景图片路径或文件名")
    background_scale: float = Field(1.0, ge=0.1, le=10.0, description="背景缩放比例")
    output_format: str = Field("webp", description="输出格式，支持 webp / png")
    max_workers: int | None = Field(
        None,
        ge=1,
        le=64,
        description="并行渲染所使用的最大核心数，留空则使用后端默认值",
    )

    @field_validator("fill_color")
    @classmethod
    def _validate_fill_color(cls, value: list[int]) -> list[int]:
        if len(value) != 3:
            raise ValueError("fill_color 需提供 3 个 RGB 通道值")
        return [max(0, min(255, int(channel))) for channel in value]


class GenerateResponse(BaseModel):
    outputs: list[str]
    count: int


@router.post("", response_model=ApiResponse[GenerateResponse])
async def generate_endpoint(payload: GenerateRequest) -> ApiResponse[GenerateResponse]:
    font_name = payload.font or _default_font_name()
    config = HandwritingConfig(
        text=payload.text,
        font_name=font_name,
        font_size=payload.font_size,
        line_spacing=payload.line_spacing,
        word_spacing=payload.word_spacing,
        fill_color=payload.fill_color,
        left_margin=payload.left_margin,
        top_margin=payload.top_margin,
        right_margin=payload.right_margin,
        bottom_margin=payload.bottom_margin,
        line_spacing_sigma=payload.line_spacing_sigma,
        word_spacing_sigma=payload.word_spacing_sigma,
        font_size_sigma=payload.font_size_sigma,
        perturb_x_sigma=payload.perturb_x_sigma,
        perturb_y_sigma=payload.perturb_y_sigma,
        perturb_theta_sigma=payload.perturb_theta_sigma,
        start_chars=payload.start_chars or DEFAULT_START_CHARS,
        end_chars=payload.end_chars or DEFAULT_END_CHARS,
        background_path=payload.background,
        background_scale=payload.background_scale,
        output_format=payload.output_format,
        max_workers=payload.max_workers,
    )

    try:
        outputs = generate_handwriting(config)
    except ValueError as exc:
        raise AppError(
            code=4004,
            message=str(exc),
            http_status=status.HTTP_400_BAD_REQUEST,
        ) from exc

    return success_response(GenerateResponse(outputs=outputs, count=len(outputs)))
