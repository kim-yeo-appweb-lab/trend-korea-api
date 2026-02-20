from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class ErrorDetail:
    code: str
    message: str
    details: dict[str, Any] | None = None


class AppError(Exception):
    def __init__(
        self,
        *,
        code: str,
        message: str,
        status_code: int,
        details: dict[str, Any] | None = None,
        field: str | None = None,
    ) -> None:
        resolved_details = details
        if field is not None:
            resolved_details = {**(resolved_details or {}), "field": field}

        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = resolved_details
        self.field = field
        super().__init__(message)
