from __future__ import annotations

import asyncio
import logging
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse
from starlette.middleware.sessions import SessionMiddleware

from backend.core.api import (
    AppError,
    build_unhandled_error_response,
    error_json_response,
    extract_validation_message,
    success_response,
)
from backend.core.settings import (
    BACKGROUND_DIR,
    DEFAULT_CORS_ORIGINS,
    SESSION_SECRET_KEY,
    STATIC_DIR,
    ensure_directories,
)
from backend.routers import backgrounds, fonts, generate, upload
from backend.core.cleanup import run_cleanup_loop
from backend.core.logging_config import configure_logging

ensure_directories()
configure_logging()
logger = logging.getLogger("backend.main")

app = FastAPI(
    title="Handwrite Generator API",
    version="0.1.0",
    description="为手写体生成器 Web 应用提供后端接口.",
)

app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET_KEY)

# Configure CORS. If wildcard "*" is present, Starlette does not allow
# credentials to be enabled. In that case, disable credentials; otherwise
# allow credentials so session cookies can be used from specific origins
# (e.g., Vite preview at http://localhost:30000).
origins = list(DEFAULT_CORS_ORIGINS)
allow_credentials = "*" not in DEFAULT_CORS_ORIGINS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(generate.router, prefix="/api")
app.include_router(upload.router, prefix="/api")
app.include_router(fonts.router, prefix="/api")
app.include_router(backgrounds.router, prefix="/api")

app.mount("/static", StaticFiles(directory=STATIC_DIR, check_dir=False), name="static")
app.mount(
    "/background",
    StaticFiles(directory=BACKGROUND_DIR, check_dir=False),
    name="background",
)


@app.exception_handler(AppError)
async def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
    return error_json_response(
        code=exc.code,
        message=exc.message,
        http_status=exc.http_status,
    )


@app.exception_handler(RequestValidationError)
async def handle_validation_error(
    _: Request, exc: RequestValidationError
) -> JSONResponse:
    return error_json_response(
        code=4000,
        message=extract_validation_message(exc),
        http_status=422,
    )


@app.exception_handler(StarletteHTTPException)
async def handle_http_exception(
    _: Request, exc: StarletteHTTPException
) -> JSONResponse:
    detail = exc.detail if isinstance(exc.detail, str) else "请求处理失败"
    code = 4040 if exc.status_code == 404 else 4009
    return error_json_response(code=code, message=detail, http_status=exc.status_code)


@app.exception_handler(Exception)
async def handle_unhandled_error(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception during request: %s %s", request.method, request.url.path)
    return build_unhandled_error_response(request, exc)


@app.get("/health")
async def health_check():
    return success_response({"status": "ok"})


# Background cleanup task lifecycle
_cleanup_task: Optional[asyncio.Task] = None


@app.on_event("startup")
async def _startup() -> None:
    global _cleanup_task
    loop = asyncio.get_event_loop()
    _cleanup_task = loop.create_task(run_cleanup_loop())
    logger.info("Cleanup loop task started")


@app.on_event("shutdown")
async def _shutdown() -> None:
    global _cleanup_task
    if _cleanup_task is not None:
        _cleanup_task.cancel()
        try:
            await _cleanup_task
        except asyncio.CancelledError:
            pass
        _cleanup_task = None
    logger.info("Application shutdown complete")
