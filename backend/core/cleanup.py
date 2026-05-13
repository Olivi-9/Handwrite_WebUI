from __future__ import annotations

import asyncio
import os
import time
from pathlib import Path

from .settings import (
    CLEANUP_INTERVAL_SECONDS,
    FILE_RETENTION_SECONDS,
    OUTPUT_DIR,
    UPLOAD_DIR,
)


def _is_older_than(path: Path, threshold_seconds: int, now: float) -> bool:
    try:
        mtime = path.stat().st_mtime
    except FileNotFoundError:
        return False
    return (now - mtime) > threshold_seconds


def _safe_unlink(path: Path) -> None:
    try:
        if path.is_file() or (path.is_symlink() and not path.is_dir()):
            path.unlink(missing_ok=True)
    except Exception:
        pass


def cleanup_once(retention_seconds: int = FILE_RETENTION_SECONDS) -> None:
    """Delete files older than retention in uploads and output dirs."""
    now = time.time()
    for base in (UPLOAD_DIR, OUTPUT_DIR):
        if not base.exists():
            continue
        for entry in base.iterdir():
            # Only target regular files; skip directories
            if not entry.exists():
                continue
            if entry.is_dir():
                continue
            if _is_older_than(entry, retention_seconds, now):
                _safe_unlink(entry)


async def run_cleanup_loop(
    interval_seconds: int = CLEANUP_INTERVAL_SECONDS,
    retention_seconds: int = FILE_RETENTION_SECONDS,
) -> None:
    """Periodic cleanup loop. Runs until cancelled."""
    # Initial delay to avoid doing work immediately on cold start
    try:
        await asyncio.sleep(min(10, interval_seconds))
        while True:
            cleanup_once(retention_seconds=retention_seconds)
            await asyncio.sleep(interval_seconds)
    except asyncio.CancelledError:
        raise
