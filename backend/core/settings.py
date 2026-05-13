import os
from pathlib import Path
from typing import Final, Set


BASE_DIR: Final[Path] = Path(__file__).resolve().parent.parent
PROJECT_ROOT: Final[Path] = BASE_DIR.parent


def _load_dotenv_file(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        if not key or key in os.environ:
            continue

        normalized_value = value.strip().strip('"').strip("'")
        os.environ[key] = normalized_value


_load_dotenv_file(PROJECT_ROOT / ".env")

STATIC_DIR: Final[Path] = BASE_DIR / "static"
UPLOAD_DIR: Final[Path] = STATIC_DIR / "uploads"
OUTPUT_DIR: Final[Path] = STATIC_DIR / "output"
BACKEND_LOG_DIR: Final[Path] = Path(
    os.getenv("BACKEND_LOG_DIR", str(BASE_DIR / "logs"))
)
BACKEND_LOG_FILE_PATH: Final[Path] = BACKEND_LOG_DIR / os.getenv(
    "BACKEND_LOG_FILE", "backend.log"
)

FONTS_DIR: Final[Path] = PROJECT_ROOT / "ttf"
BACKGROUND_DIR: Final[Path] = PROJECT_ROOT / "background"

ALLOWED_IMAGE_MIME_TYPES: Final[dict[str, str]] = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/webp": ".webp",
}

MAX_UPLOAD_SIZE_BYTES: Final[int] = 10 * 1024 * 1024  # 10 MB
MAX_IMAGE_PIXELS: Final[int] = 10_000_000  # 10 MP
CPU_COUNT: Final[int] = max(1, os.cpu_count() or 1)


def _parse_cors_origins(value: str | None) -> Set[str]:
    if not value:
        return set()

    parts = {p.strip().rstrip("/") for p in value.split(",") if p.strip()}
    if not parts:
        return set()

    if "*" in parts:
        raise ValueError("Wildcard CORS origins are not permitted in production.")

    return parts


CORS_ORIGINS_RAW = os.getenv(
    "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
)
try:
    DEFAULT_CORS_ORIGINS: Final[Set[str]] = _parse_cors_origins(CORS_ORIGINS_RAW)
except ValueError as exc:
    raise RuntimeError(
        "CORS_ORIGINS must be a comma-separated list of explicit origins."
    ) from exc

if not DEFAULT_CORS_ORIGINS:
    raise RuntimeError(
        "CORS_ORIGINS environment variable must declare at least one allowed origin."
    )

SESSION_SECRET_KEY_ENV = os.getenv("SESSION_SECRET_KEY", "")
if len(SESSION_SECRET_KEY_ENV) < 32:
    print("=" * 60)
    print(f"Invalid SESSION_SECRET_KEY: {SESSION_SECRET_KEY_ENV}")
    raise RuntimeError(
        "SESSION_SECRET_KEY must be set to a strong value of at least 32 characters."
    )
SESSION_SECRET_KEY: Final[str] = SESSION_SECRET_KEY_ENV


def _parse_positive_int(name: str, value: str | None) -> int | None:
    if value is None or not value.strip():
        return None
    try:
        parsed = int(value)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be a positive integer.") from exc
    if parsed < 1:
        raise RuntimeError(f"{name} must be greater than zero.")
    return parsed


_handwrite_workers_env = _parse_positive_int(
    "HANDWRITE_WORKERS", os.getenv("HANDWRITE_WORKERS")
)
DEFAULT_HANDWRITE_WORKERS: Final[int] = (
    min(_handwrite_workers_env, CPU_COUNT)
    if _handwrite_workers_env is not None
    else CPU_COUNT
)


def ensure_directories() -> None:
    """Create required directories if they are missing."""
    for path in (STATIC_DIR, UPLOAD_DIR, OUTPUT_DIR, BACKEND_LOG_DIR):
        path.mkdir(parents=True, exist_ok=True)


# Cleanup configuration
# How often the cleanup loop wakes up (in seconds)
CLEANUP_INTERVAL_SECONDS: Final[int] = int(os.getenv("CLEANUP_INTERVAL_SECONDS", "1200"))
# Delete files older than this many seconds
FILE_RETENTION_SECONDS: Final[int] = int(os.getenv("FILE_RETENTION_SECONDS", "1200"))

BACKEND_LOG_LEVEL: Final[str] = os.getenv("BACKEND_LOG_LEVEL", "INFO").upper()
BACKEND_LOG_MAX_BYTES: Final[int] = int(
    os.getenv("BACKEND_LOG_MAX_BYTES", str(10 * 1024 * 1024))
)
BACKEND_LOG_BACKUP_COUNT: Final[int] = int(os.getenv("BACKEND_LOG_BACKUP_COUNT", "5"))


def _validate_logging_settings() -> None:
    if BACKEND_LOG_LEVEL not in {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"}:
        raise RuntimeError(
            "BACKEND_LOG_LEVEL must be one of: CRITICAL, ERROR, WARNING, INFO, DEBUG"
        )
    if BACKEND_LOG_MAX_BYTES < 1:
        raise RuntimeError("BACKEND_LOG_MAX_BYTES must be greater than zero.")
    if BACKEND_LOG_BACKUP_COUNT < 1:
        raise RuntimeError("BACKEND_LOG_BACKUP_COUNT must be greater than zero.")


_validate_logging_settings()
