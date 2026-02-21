from datetime import datetime, timezone
from typing import Any

from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def success_response(
    *,
    data: Any,
    request: Request | None,
    status_code: int = 200,
    message: str = "요청 성공",
    meta: dict[str, Any] | None = None,
    links: dict[str, str] | None = None,
) -> JSONResponse:
    payload_data: Any = data

    if meta is not None or links is not None:
        if isinstance(data, dict):
            payload_data = dict(data)
        else:
            payload_data = {"items": data}
        if meta is not None:
            payload_data["meta"] = meta
        if links is not None:
            payload_data["links"] = links

    payload: dict[str, Any] = {
        "success": True,
        "data": payload_data,
        "message": message,
        "timestamp": _timestamp(),
    }
    return JSONResponse(status_code=status_code, content=jsonable_encoder(payload))


def error_response(
    *,
    code: str,
    message: str,
    request: Request | None,
    status_code: int,
    details: dict[str, Any] | None = None,
) -> JSONResponse:
    payload = {
        "success": False,
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
        },
        "timestamp": _timestamp(),
    }
    return JSONResponse(status_code=status_code, content=jsonable_encoder(payload))
