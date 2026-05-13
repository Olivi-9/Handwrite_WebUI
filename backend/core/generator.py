from __future__ import annotations

import multiprocessing
import re
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from typing import Callable, Iterable, Sequence

from PIL import Image, ImageFont
from handright import Template, handwrite

from .settings import BACKGROUND_DIR, DEFAULT_HANDWRITE_WORKERS
from .utils import (
    create_output_path,
    resolve_background_path,
    resolve_font_path,
    sanitize_color,
)

DEFAULT_START_CHARS = "“（【[<"
DEFAULT_END_CHARS = "，。！？、)）】。：:"

SUPPORTED_OUTPUT_FORMATS: dict[str, tuple[str, str]] = {
    "webp": (".webp", "WEBP"),
    "png": (".png", "PNG"),
}

_EN_WORD_PATTERN = re.compile(r"[A-Za-z0-9]+(?:['-][A-Za-z0-9]+)*")


@dataclass(slots=True)
class HandwritingConfig:
    text: str
    font_name: str = "字小魂清风体.ttf"
    font_size: int = 85
    line_spacing: int = 100
    word_spacing: float = -8.0
    fill_color: Sequence[int] = (0, 0, 0)
    left_margin: int = 80
    top_margin: int = 335
    right_margin: int = 80
    bottom_margin: int = 150
    line_spacing_sigma: float = 2.0
    word_spacing_sigma: float = 2.0
    font_size_sigma: float = 2.0
    perturb_x_sigma: float = 1.0
    perturb_y_sigma: float = 1.0
    perturb_theta_sigma: float = 0.08
    start_chars: str = "（【([<"
    end_chars: str = "，,。！？、)）】。：:"
    background_path: str | None = "2.png"
    background_scale: float = 2.0
    output_format: str = "webp"
    max_workers: int | None = None


def _pick_default_background() -> str:
    candidates = list(BACKGROUND_DIR.glob("*"))
    if not candidates:
        raise FileNotFoundError("缺少默认背景图，请先上传或添加背景图片")
    return candidates[0].name


def _load_background(path_str: str | None, scale: float) -> Image.Image:
    target_path = resolve_background_path(path_str or _pick_default_background())
    background = Image.open(target_path)
    if background.mode != "RGBA":
        background = background.convert("RGBA")
    scale = max(scale, 0.1)
    if scale != 1.0:
        new_width = max(1, int(background.width * scale))
        new_height = max(1, int(background.height * scale))
        background = background.resize(
            (new_width, new_height), resample=Image.Resampling.LANCZOS
        )
    return background


def _tokenize_line(line: str) -> list[str]:
    tokens: list[str] = []
    last_index = 0
    for match in _EN_WORD_PATTERN.finditer(line):
        if match.start() > last_index:
            tokens.extend(line[last_index : match.start()])
        tokens.append(match.group())
        last_index = match.end()
    if last_index < len(line):
        tokens.extend(line[last_index:])
    return tokens


def _wrap_text_for_template(
    text: str,
    config: HandwritingConfig,
    background: Image.Image,
    font: ImageFont.FreeTypeFont,
) -> str:
    usable_width = background.width - config.right_margin - font.size
    start_x = config.left_margin
    word_spacing = int(config.word_spacing)

    if usable_width <= start_x:
        return text

    char_width_cache: dict[str, float] = {}

    def char_advance(char: str) -> float:
        cached = char_width_cache.get(char)
        if cached is not None:
            return cached
        left, _, right, _ = font.getbbox(char)
        width = max(right - left + word_spacing, 1)
        char_width_cache[char] = width
        return width

    def token_fits(start_pos: float, token: str) -> bool:
        pos = start_pos
        for char in token:
            if pos > usable_width:
                return False
            pos += char_advance(char)
        return True

    def append_token(buffer: list[str], start_pos: float, token: str) -> float:
        pos = start_pos
        for char in token:
            if not buffer and char == " ":
                continue
            buffer.append(char)
            pos += char_advance(char)
        return pos

    def wrap_single_line(raw_line: str) -> list[str]:
        if not raw_line:
            return [""]

        buffer: list[str] = []
        lines: list[str] = []
        pos = start_x

        for token in _tokenize_line(raw_line):
            if not token:
                continue

            is_word = _EN_WORD_PATTERN.fullmatch(token) is not None

            if is_word and buffer and not token_fits(pos, token):
                lines.append("".join(buffer))
                buffer = []
                pos = start_x

            if is_word and not token_fits(pos, token):
                for char in token:
                    if buffer and not token_fits(pos, char):
                        lines.append("".join(buffer))
                        buffer = []
                        pos = start_x
                    if not buffer and char == " ":
                        continue
                    buffer.append(char)
                    pos += char_advance(char)
                continue

            if buffer and not token_fits(pos, token):
                lines.append("".join(buffer))
                buffer = []
                pos = start_x

            pos = append_token(buffer, pos, token)

        lines.append("".join(buffer))
        return lines

    wrapped_lines: list[str] = []
    for raw_line in text.split("\n"):
        wrapped_lines.extend(wrap_single_line(raw_line))

    def adjust_wrapped_lines(lines: list[str]) -> list[str]:
        if not lines:
            return lines

        start_chars = set(config.start_chars or "")
        end_chars = set(config.end_chars or "")

        # Prevent start_chars from appearing at the end of a line.
        for idx in range(len(lines) - 1):
            current = lines[idx]
            if not current:
                continue
            while current and current[-1] in start_chars:
                char = current[-1]
                current = current[:-1]
                lines[idx + 1] = char + lines[idx + 1]
            lines[idx] = current

        # Prevent end_chars from appearing at the beginning of a line.
        for idx in range(1, len(lines)):
            following = lines[idx]
            if not following:
                continue
            while following and following[0] in end_chars and lines[idx - 1]:
                char = following[0]
                following = following[1:]
                lines[idx - 1] += char
            lines[idx] = following

        return lines

    wrapped_lines = adjust_wrapped_lines(wrapped_lines)

    return "\n".join(wrapped_lines)


def _build_template(
    config: HandwritingConfig, background: Image.Image, font: ImageFont.FreeTypeFont
) -> Template:
    fill = sanitize_color(config.fill_color)

    return Template(
        background=background,
        font=font,
        line_spacing=config.line_spacing,
        fill=fill,
        left_margin=config.left_margin,
        top_margin=config.top_margin,
        right_margin=config.right_margin,
        bottom_margin=config.bottom_margin,
        word_spacing=int(config.word_spacing),
        line_spacing_sigma=config.line_spacing_sigma,
        word_spacing_sigma=config.word_spacing_sigma,
        font_size_sigma=config.font_size_sigma,
        start_chars=config.start_chars,
        end_chars=config.end_chars,
        perturb_x_sigma=config.perturb_x_sigma,
        perturb_y_sigma=config.perturb_y_sigma,
        perturb_theta_sigma=config.perturb_theta_sigma,
    )


def _normalize_output_format(format_name: str) -> tuple[str, str]:
    normalized = format_name.lower()
    if normalized not in SUPPORTED_OUTPUT_FORMATS:
        raise ValueError("输出格式不受支持")
    return SUPPORTED_OUTPUT_FORMATS[normalized]


def _should_enable_parallelism(workers: int | None) -> tuple[int, bool]:
    if workers is None:
        workers = DEFAULT_HANDWRITE_WORKERS
    cpu_count = max(1, multiprocessing.cpu_count() or 1)
    normalized = max(1, min(workers, cpu_count))
    return normalized, normalized > 1


def _parallel_mapper(
    worker_count: int | None,
) -> tuple[Callable, ProcessPoolExecutor | None]:
    normalized_count, enabled = _should_enable_parallelism(worker_count)
    if not enabled:
        return map, None
    ctx = multiprocessing.get_context("spawn")
    executor = ProcessPoolExecutor(max_workers=normalized_count, mp_context=ctx)

    def mapper(func, iterable):
        return executor.map(func, iterable)

    return mapper, executor


def generate_handwriting(config: HandwritingConfig) -> list[str]:
    """Generate handwriting images and return relative static paths."""
    if not config.text.strip():
        raise ValueError("生成内容不能为空")

    extension, pillow_format = _normalize_output_format(config.output_format)
    background = _load_background(config.background_path, config.background_scale)
    font_path = resolve_font_path(config.font_name)
    font = ImageFont.truetype(str(font_path), size=config.font_size)
    prepared_text = _wrap_text_for_template(config.text, config, background, font)
    template = _build_template(config, background, font)

    mapper, executor = _parallel_mapper(config.max_workers)
    images: Iterable[Image.Image] = handwrite(prepared_text, template, mapper=mapper)
    output_urls: list[str] = []

    try:
        for image in images:
            try:
                output_path = create_output_path(extension=extension)
                image.save(output_path, format=pillow_format)
                output_urls.append(f"/static/output/{output_path.name}")
            finally:
                # Ensure Pillow image buffers are released ASAP
                try:
                    image.close()
                except Exception:
                    pass
    finally:
        # Explicitly close background to release memory sooner
        try:
            background.close()
        except Exception:
            pass
        if executor is not None:
            executor.shutdown(wait=True, cancel_futures=True)

    if not output_urls:
        raise ValueError("未能生成任何图片，请检查输入内容")

    return output_urls
