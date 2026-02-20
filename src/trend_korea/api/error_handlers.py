from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError

from trend_korea.core.exceptions import AppError
from trend_korea.core.response import error_response


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
                invalid_fields.append({"field": loc or "unknown", "reason": err.get("msg", "invalid")})

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

    @app.exception_handler(Exception)
    async def _handle_unexpected_error(request: Request, _: Exception):
        return error_response(
            code="E_SERVER_001",
            message="서버 내부 오류가 발생했습니다.",
            details={},
            request=request,
            status_code=500,
        )
