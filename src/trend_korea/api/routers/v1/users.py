from fastapi import APIRouter, Request

from trend_korea.api.deps import DbSession
from trend_korea.core.exceptions import AppError
from trend_korea.core.response import success_response
from trend_korea.infrastructure.db.repositories.user_repository import UserRepository

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/{user_id}")
def get_user(user_id: str, request: Request, db: DbSession):
    repo = UserRepository(db)
    user = repo.get_by_id(user_id)
    if user is None:
        raise AppError(code="E_RESOURCE_005", message="사용자를 찾을 수 없습니다", status_code=404)

    return success_response(
        request=request,
        data={
            "id": user.id,
            "nickname": user.nickname,
            "profileImage": user.profile_image,
            "bio": None,
            "createdAt": user.created_at.isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            "activityStats": {
                "postCount": 0,
                "commentCount": 0,
                "likeCount": 0,
            },
        },
        message="조회 성공",
    )
