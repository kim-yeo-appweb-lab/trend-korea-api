from datetime import datetime, timezone
from typing import Callable
from uuid import uuid4

from sqlalchemy.orm import Session

from trend_korea.infrastructure.db.models.job import JobRun
from trend_korea.infrastructure.db.session import SessionLocal


def run_job(job_name: str, handler: Callable[[Session], str | None]) -> None:
    started_at = datetime.now(timezone.utc)
    status = "success"
    detail: str | None = None

    try:
        with SessionLocal() as db:
            detail = handler(db)
            db.commit()
    except Exception as exc:
        status = "failed"
        detail = f"{type(exc).__name__}: {exc}"

    with SessionLocal() as db:
        db.add(
            JobRun(
                id=str(uuid4()),
                job_name=job_name,
                status=status,
                detail=detail,
                started_at=started_at,
                finished_at=datetime.now(timezone.utc),
            )
        )
        db.commit()
