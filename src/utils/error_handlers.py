import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError

from src.core.exceptions import AppError
from src.core.response import error_response

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _handle_app_error(request: Request, exc: AppError):
        return error_response(
            code=exc.code,
            message=exc.message,
            details=exc.details,
            request=request,
            status_code=exc.status_code,
        )

    @app.exception_handler(RequestValidationError)
    async def _handle_validation_error(request: Request, exc: RequestValidationError):
        missing_fields: list[str] = []
        invalid_fields: list[dict[str, str]] = []

        for err in exc.errors():
            loc = ".".join(str(v) for v in err.get("loc", []) if v not in {"body", "query", "path"})
            if err.get("type") == "missing":
                missing_fields.append(loc or "unknown")
            else:
                invalid_fields.append(
                    {"field": loc or "unknown", "reason": err.get("msg", "invalid")}
                )

        if missing_fields:
            return error_response(
                code="E_VALID_001",
                message="필수 필드가 누락되었습니다.",
                details={"fields": missing_fields},
                request=request,
                status_code=400,
            )

        return error_response(
            code="E_VALID_002",
            message="필드 형식이 유효하지 않습니다.",
            details={"errors": invalid_fields},
            request=request,
            status_code=400,
        )

    @app.exception_handler(IntegrityError)
    async def _handle_integrity_error(request: Request, exc: IntegrityError):
        logger.warning("DB 무결성 제약 위반: %s", exc.orig)
        return error_response(
            code="E_VALID_003",
            message="요청 데이터가 무결성 제약 조건을 위반합니다.",
            request=request,
            status_code=409,
        )

    @app.exception_handler(Exception)
    async def _handle_unexpected_error(request: Request, exc: Exception):
        logger.exception("처리되지 않은 예외 발생 [%s %s]", request.method, request.url.path)
        return error_response(
            code="E_SERVER_001",
            message="서버 내부 오류가 발생했습니다.",
            details={},
            request=request,
            status_code=500,
        )
