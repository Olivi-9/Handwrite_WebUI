from __future__ import annotations

from typing import Generic, TypeVar

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette import status

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    code: int
    message: str
    data: T | None


class AppError(Exception):
    def __init__(self, *, code: int, message: str, http_status: int) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.http_status = http_status


def success_response(data: T, message: str = "success") -> ApiResponse[T]:
    return ApiResponse(code=200, message=message, data=data)


def error_json_response(*, code: int, message: str, http_status: int) -> JSONResponse:
    payload = ApiResponse[None](code=code, message=message, data=None)
    return JSONResponse(status_code=http_status, content=payload.model_dump())


def extract_validation_message(exc: RequestValidationError) -> str:
    first_error = exc.errors()[0] if exc.errors() else {}
    return str(first_error.get("msg") or "请求参数不合法")


def build_unhandled_error_response(_: Request, __: Exception) -> JSONResponse:
    return error_json_response(
        code=5000,
        message="服务暂时不可用，请稍后重试",
        http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
