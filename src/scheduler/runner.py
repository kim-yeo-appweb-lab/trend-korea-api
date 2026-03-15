from datetime import datetime, timezone
from typing import Callable
from uuid import uuid4

from sqlalchemy.orm import Session

from src.db.session import SessionLocal


def run_job(job_name: str, handler: Callable[[Session], str | None]) -> None:
    from src.models.scheduler import JobRun

    started_at = datetime.now(timezone.utc)
    status = "success"
    detail: str | None = None
    metrics: dict | None = None

    try:
        with SessionLocal() as db:
            result = handler(db)
            db.commit()

            # 핸들러가 tuple (detail, metrics)를 반환하면 metrics 추출
            if isinstance(result, tuple):
                detail, metrics = result
            else:
                detail = result
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
                metrics=metrics,
            )
        )
        db.commit()
