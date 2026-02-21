from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, delete, or_
from sqlalchemy.orm import Session

from src.models.auth import RefreshToken


def cleanup_refresh_tokens(db: Session) -> str:
    now = datetime.now(timezone.utc)
    revoke_boundary = now - timedelta(days=30)

    deleted = db.execute(
        delete(RefreshToken).where(
            or_(
                RefreshToken.expires_at < now,
                and_(
                    RefreshToken.revoked_at.is_not(None),
                    RefreshToken.revoked_at < revoke_boundary,
                ),
            )
        )
    ).rowcount

    return f"deleted={deleted or 0}"
