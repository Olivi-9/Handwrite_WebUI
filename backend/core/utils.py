from __future__ import annotations

import io
import uuid
from pathlib import Path
from typing import Sequence, Tuple

from PIL import Image, UnidentifiedImageError

from .settings import (
    BACKGROUND_DIR,
    FONTS_DIR,
    MAX_IMAGE_PIXELS,
    MAX_UPLOAD_SIZE_BYTES,
    OUTPUT_DIR,
    UPLOAD_DIR,
)

ALLOWED_IMAGE_FORMATS = {"PNG", "JPEG", "JPG", "WEBP"}


def _ensure_within_directory(base: Path, target: Path) -> Path:
    resolved = target.resolve()
    if base.resolve() not in resolved.parents and resolved != base.resolve():
        raise ValueError("路径不允许访问")
    return resolved


def resolve_font_path(font_name: str) -> Path:
    """Resolve a font filename within the fonts directory."""
    candidate = (FONTS_DIR / font_name).resolve()
    try:
        return _ensure_within_directory(FONTS_DIR, candidate)
    except ValueError as exc:
        raise ValueError("字体路径无效") from exc


def resolve_background_path(path_str: str) -> Path:
    """Resolve a background path within allowed directories."""
    raw_path = Path(path_str)
    candidate_paths: list[Path] = []

    if raw_path.is_absolute():
        candidate_paths.append(raw_path)
    else:
        candidate_paths.extend(
            [
                BACKGROUND_DIR / raw_path,
                UPLOAD_DIR / raw_path,
                BACKGROUND_DIR / raw_path.name,
                UPLOAD_DIR / raw_path.name,
            ]
        )
        parts = raw_path.parts
        if len(parts) >= 2 and parts[0] == "static":
            if parts[1] == "uploads":
                candidate_paths.append(UPLOAD_DIR / Path(*parts[2:]))
            elif parts[1] == "background":
                candidate_paths.append(BACKGROUND_DIR / Path(*parts[2:]))

    for candidate in candidate_paths:
        if not candidate.exists():
            continue
        try:
            if candidate.resolve().parent == BACKGROUND_DIR.resolve():
                return _ensure_within_directory(BACKGROUND_DIR, candidate)
            if candidate.resolve().parent == UPLOAD_DIR.resolve():
                return _ensure_within_directory(UPLOAD_DIR, candidate)
        except ValueError:
            continue

    raise ValueError("背景图片未找到或不在允许的目录中")


def list_available_fonts() -> list[dict[str, str]]:
    """Return available font metadata."""
    fonts: list[dict[str, str]] = []
    for font_path in sorted(FONTS_DIR.glob("*.ttf")):
        fonts.append({"name": font_path.stem, "file": font_path.name})
    for font_path in sorted(FONTS_DIR.glob("*.otf")):
        fonts.append({"name": font_path.stem, "file": font_path.name})
    return fonts


def sanitize_color(color: Sequence[int]) -> Tuple[int, int, int]:
    """Normalize fill color to an RGB tuple."""
    if len(color) not in (3, 4):
        raise ValueError("颜色必须包含 3 或 4 个通道值")
    rgb = tuple(int(max(0, min(255, channel))) for channel in color[:3])
    if len(rgb) != 3:
        raise ValueError("颜色格式无效")
    return rgb  # type: ignore[return-value]


def sanitize_upload_image(data: bytes) -> Image.Image:
    """Validate uploaded image bytes and return a sanitized Pillow Image."""
    if len(data) > MAX_UPLOAD_SIZE_BYTES:
        raise ValueError("文件大小超出限制")
    try:
        image = Image.open(io.BytesIO(data))
    except UnidentifiedImageError as exc:
        raise ValueError("文件不是有效的图片格式") from exc

    if image.format and image.format.upper() not in ALLOWED_IMAGE_FORMATS:
        raise ValueError("暂不支持该图片格式")

    width, height = image.size
    if width * height > MAX_IMAGE_PIXELS:
        raise ValueError("图片像素数量超出限制")

    image.load()
    if image.mode not in ("RGB", "RGBA"):
        image = image.convert("RGBA")
    return image


def save_uploaded_image(image: Image.Image, suffix: str = ".png") -> Path:
    """Save sanitized image into upload directory."""
    filename = f"{uuid.uuid4().hex}{suffix}"
    target_path = UPLOAD_DIR / filename
    image.save(target_path, format="PNG")
    return target_path


def create_output_path(extension: str = ".webp") -> Path:
    """Return a unique output path for generated handwriting."""
    filename = f"{uuid.uuid4().hex}{extension}"
    return OUTPUT_DIR / filename
