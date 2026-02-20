# Trend Korea API 엔드포인트 명세 (구현 기준)

기준 코드:
- `src/trend_korea/main.py`
- `src/trend_korea/api/routers/v1/*.py`

기준 시점:
- 2026-02-16

## 1. 공통 정보

- Base URL: `http://localhost:8000`
- API Prefix: `/api/v1`
- Health:
  - `GET /health/live`
  - `GET /health/ready`
- Content-Type: `application/json`
- 인증 헤더: `Authorization: Bearer {accessToken}`

## 2. 공통 응답 형식

성공:

```json
{
  "success": true,
  "data": {},
  "message": "요청 성공",
  "timestamp": "2026-02-16T10:00:00.000Z"
}
```

실패:

```json
{
  "success": false,
  "error": {
    "code": "E_VALID_002",
    "message": "필드 형식이 유효하지 않습니다.",
    "details": {}
  },
  "timestamp": "2026-02-16T10:00:00.000Z"
}
```

## 3. 권한 정책

- `Public`: 인증 불필요
- `Member`: `member | admin`
- `Admin`: `admin`

## 4. 엔드포인트 목록

## Auth

1. `POST /api/v1/auth/register`
- 권한: `Public`
- 요청 본문:
  - `nickname` (2~20)
  - `email` (email)
  - `password` (8~72)
- 응답: `user`, `tokens(accessToken, refreshToken, expiresIn)`

2. `POST /api/v1/auth/login`
- 권한: `Public`
- 요청 본문:
  - `email`
  - `password`
- 응답: `user`, `tokens(accessToken, refreshToken, expiresIn, expiresAt)`

3. `POST /api/v1/auth/refresh`
- 권한: `Public`
- 요청 본문:
  - `refreshToken`
- 응답: `accessToken`, `expiresIn`, `expiresAt`

4. `POST /api/v1/auth/logout`
- 권한: `Member`
- 요청 본문: 없음
- 응답: `data: null`

5. `GET /api/v1/auth/social/providers`
- 권한: `Public`
- 응답: `["kakao","naver","google"]`

6. `POST /api/v1/auth/social-login`
- 권한: `Public`
- 요청 본문:
  - `provider` (`kakao|naver|google`)
  - `code`
  - `redirectUri`
- 응답: `user`, `tokens`, `isNewUser`

7. `DELETE /api/v1/auth/withdraw`
- 권한: `Member`
- 요청 본문:
  - `password` (optional)
- 응답: `data: null`

## Users

8. `GET /api/v1/users/me`
- 권한: `Member`
- 응답: 내 정보 (`email`, `nickname`, `socialProviders`, `trackedIssueIds`, `savedEventIds` 등)

9. `PATCH /api/v1/users/me`
- 권한: `Member`
- 요청 본문:
  - `nickname` (optional)
  - `profileImage` (optional)
- 응답: `id`, `nickname`, `profileImage`, `updatedAt`

10. `POST /api/v1/users/me/change-password`
- 권한: `Member`
- 요청 본문:
  - `currentPassword`
  - `newPassword`
- 응답: `data: null`

11. `POST /api/v1/users/me/social-connect`
- 권한: `Member`
- 요청 본문:
  - `provider`
  - `code`
- 응답: `socialProviders`

12. `DELETE /api/v1/users/me/social-disconnect`
- 권한: `Member`
- 요청 본문:
  - `provider`
- 응답: `socialProviders`

13. `GET /api/v1/users/me/activity`
- 권한: `Member`
- 쿼리:
  - `page` (default 1)
  - `limit` (default 10)
  - `type` (default `all`)
- 응답: `items`, `pagination`

14. `GET /api/v1/users/{user_id}`
- 권한: `Public`
- 응답: 공개 사용자 정보(`nickname`, `profileImage`, `activityStats`)

## Events

15. `GET /api/v1/events`
- 권한: `Public`
- 쿼리:
  - `cursor`
  - `limit` (1~100, default 10)
  - `importance` (`low|medium|high`)
  - `startDate`, `endDate`
  - `sortBy` (default `occurredAt`)
  - `order` (`asc|desc`, default `desc`)
- 응답: `items`, `cursor(next, hasMore)`

16. `GET /api/v1/events/{event_id}`
- 권한: `Public`
- 응답: 사건 상세

17. `POST /api/v1/events/{event_id}/save`
- 권한: `Member`
- 응답: `eventId`, `isSaved`, `savedAt`
- 충돌: 이미 저장 시 `E_CONFLICT_003`

18. `DELETE /api/v1/events/{event_id}/save`
- 권한: `Member`
- 응답: `data: null`

19. `POST /api/v1/events`
- 권한: `Admin`
- 요청 본문:
  - `occurredAt`, `title`, `summary`, `importance`, `verificationStatus`, `tagIds`, `sourceIds`
- 응답: 생성된 사건 객체

20. `PATCH /api/v1/events/{event_id}`
- 권한: `Admin`
- 요청 본문(선택):
  - `title`, `summary`, `importance`, `verificationStatus`, `tagIds`, `sourceIds`
- 응답: `id`, `title`, `importance`, `updatedAt`

21. `DELETE /api/v1/events/{event_id}`
- 권한: `Admin`
- 응답: `data: null`

## Issues / Triggers

22. `GET /api/v1/issues`
- 권한: `Public`
- 쿼리:
  - `page`, `limit`
  - `status` (`ongoing|closed|reignited|unverified`)
  - `startDate`, `endDate`
  - `sortBy` (default `updatedAt`)
  - `order` (`asc|desc`)
- 응답: `items`, `pagination`

23. `GET /api/v1/issues/{issue_id}`
- 권한: `Public`
- 응답: 이슈 상세

24. `POST /api/v1/issues`
- 권한: `Admin`
- 요청 본문:
  - `title`, `description`, `status`, `tagIds`, `sourceIds`, `relatedEventIds(optional)`
- 응답: 생성된 이슈 객체

25. `PATCH /api/v1/issues/{issue_id}`
- 권한: `Admin`
- 요청 본문(선택):
  - `title`, `description`, `status`, `tagIds`, `sourceIds`, `relatedEventIds`
- 응답: `id`, `title`, `status`, `updatedAt`

26. `DELETE /api/v1/issues/{issue_id}`
- 권한: `Admin`
- 응답: `data: null`

27. `GET /api/v1/issues/{issue_id}/triggers`
- 권한: `Public`
- 쿼리:
  - `sortBy` (default `occurredAt`)
  - `order` (`asc|desc`)
- 응답: trigger 배열

28. `POST /api/v1/issues/{issue_id}/track`
- 권한: `Member`
- 응답: `issueId`, `isTracking`, `trackedAt`
- 충돌: 이미 추적 중 `E_CONFLICT_002`

29. `DELETE /api/v1/issues/{issue_id}/track`
- 권한: `Member`
- 응답: `data: null`

30. `POST /api/v1/issues/{issue_id}/triggers`
- 권한: `Admin`
- 요청 본문:
  - `occurredAt`, `summary`, `type`, `sourceIds`
- 응답: 생성된 trigger 객체

31. `PATCH /api/v1/triggers/{trigger_id}`
- 권한: `Admin`
- 요청 본문(선택):
  - `summary`, `type`, `occurredAt`
- 응답: `id`, `summary`, `updatedAt`

32. `DELETE /api/v1/triggers/{trigger_id}`
- 권한: `Admin`
- 응답: `data: null`

## Community (Posts / Comments)

33. `GET /api/v1/posts`
- 권한: `Public`
- 쿼리:
  - `cursor`
  - `limit` (1~100, default 10)
  - `tab` (default `latest`)
  - `sortBy` (default `createdAt`)
- 응답: `items`, `cursor(next, hasMore)`

34. `POST /api/v1/posts`
- 권한: `Member`
- 요청 본문:
  - `title` (1~100)
  - `content`
  - `tagIds` (max 3)
  - `isAnonymous`
- 응답: 생성된 post

35. `GET /api/v1/posts/{post_id}`
- 권한: `Public`
- 응답: 게시글 상세

36. `PATCH /api/v1/posts/{post_id}`
- 권한: `Member` (작성자/관리자)
- 요청 본문(선택):
  - `title`, `content`, `tagIds`
- 응답: 수정된 post

37. `DELETE /api/v1/posts/{post_id}`
- 권한: `Member` (작성자/관리자)
- 응답: `data: null`

38. `GET /api/v1/posts/{post_id}/comments`
- 권한: `Public`
- 쿼리:
  - `cursor`
  - `limit` (1~100, default 20)
- 응답: 댓글 배열

39. `POST /api/v1/posts/{post_id}/comments`
- 권한: `Member`
- 요청 본문:
  - `content`
  - `parentId` (optional)
- 응답: 생성된 comment

40. `POST /api/v1/posts/{post_id}/like`
- 권한: `Member`
- 요청 본문:
  - `type` (`like|dislike`)
- 응답: 추천/비추천 집계 결과

41. `PATCH /api/v1/comments/{comment_id}`
- 권한: `Member` (작성자/관리자)
- 요청 본문:
  - `content`
- 응답: `id`, `content`, `updatedAt`

42. `DELETE /api/v1/comments/{comment_id}`
- 권한: `Member` (작성자/관리자)
- 응답: `data: null`

43. `POST /api/v1/comments/{comment_id}/like`
- 권한: `Member`
- 응답: 댓글 좋아요 결과

44. `DELETE /api/v1/comments/{comment_id}/like`
- 권한: `Member`
- 응답: 댓글 좋아요 취소 결과

## Search

45. `GET /api/v1/search`
- 권한: `Public`
- 쿼리:
  - `q` (required)
  - `page`, `limit`
  - `tab` (`all|events|issues|community`)
  - `sortBy`
- 응답: `items`, `pagination`

46. `GET /api/v1/search/events`
- 권한: `Public`
- 쿼리: `q`, `page`, `limit`, `sortBy`
- 응답: `items`, `pagination`

47. `GET /api/v1/search/issues`
- 권한: `Public`
- 쿼리: `q`, `page`, `limit`, `sortBy`
- 응답: `items`, `pagination`

48. `GET /api/v1/search/posts`
- 권한: `Public`
- 쿼리: `q`, `page`, `limit`, `sortBy`
- 응답: `items`, `pagination`

## Tracking

49. `GET /api/v1/users/me/tracked-issues`
- 권한: `Member`
- 쿼리:
  - `page`, `limit`
  - `sortBy` (default `trackedAt`)
- 응답: `items`, `pagination`

50. `GET /api/v1/users/me/saved-events`
- 권한: `Member`
- 쿼리:
  - `page`, `limit`
  - `sortBy` (default `savedAt`)
- 응답: `items`, `pagination`

## Tags / Sources

51. `GET /api/v1/tags`
- 권한: `Public`
- 쿼리:
  - `type` (`all|category|region`, default `all`)
  - `search` (optional)
- 응답: 태그 배열

52. `POST /api/v1/tags`
- 권한: `Admin`
- 요청 본문:
  - `name`, `type(category|region)`, `slug`
- 응답: 생성된 tag

53. `PATCH /api/v1/tags/{tag_id}`
- 권한: `Admin`
- 요청 본문(선택):
  - `name`, `slug`
- 응답: 수정된 tag

54. `DELETE /api/v1/tags/{tag_id}`
- 권한: `Admin`
- 응답: `data: null`

55. `GET /api/v1/sources`
- 권한: `Public`
- 쿼리:
  - `page` (default 1)
  - `limit` (1~100, default 20)
  - `publisher` (optional)
- 응답: `items`, `pagination`

56. `POST /api/v1/sources`
- 권한: `Admin`
- 요청 본문:
  - `url`, `title`, `publisher`, `publishedAt`
- 응답: 생성된 source

57. `DELETE /api/v1/sources/{source_id}`
- 권한: `Admin`
- 응답: `data: null`

## Home

58. `GET /api/v1/home/breaking-news`
- 권한: `Public`
- 쿼리: `limit` (1~20, default 10)
- 응답: 속보 목록

59. `GET /api/v1/home/hot-posts`
- 권한: `Public`
- 쿼리:
  - `limit` (1~20, default 5)
  - `period` (default `24h`)
- 응답: 인기 게시글 목록

60. `GET /api/v1/home/search-rankings`
- 권한: `Public`
- 쿼리:
  - `limit` (1~20, default 10)
  - `period` (`daily|weekly`)
- 응답: 검색 랭킹 목록

61. `GET /api/v1/home/trending`
- 권한: `Public`
- 쿼리:
  - `limit` (1~20, default 10)
  - `period` (default `24h`)
- 응답: 트렌딩 목록

62. `GET /api/v1/home/timeline-minimap`
- 권한: `Public`
- 쿼리: `days` (1~30, default 7)
- 응답: 날짜별 밀도 정보

63. `GET /api/v1/home/featured-news`
- 권한: `Public`
- 쿼리: `limit` (1~20, default 5)
- 응답: 추천 뉴스 목록

64. `GET /api/v1/home/community-media`
- 권한: `Public`
- 쿼리: `limit` (1~20, default 6)
- 응답: 커뮤니티 미디어 목록

## 5. 주요 에러 코드 (현재 구현)

- `E_AUTH_001`: 인증 토큰 없음 / 비밀번호 불일치 등 인증 실패
- `E_AUTH_002`: 인증 토큰 만료
- `E_AUTH_003`: 유효하지 않은 토큰
- `E_PERM_001`: 권한 없음
- `E_PERM_002`: 관리자 권한 필요
- `E_VALID_001`: 필수 필드 누락
- `E_VALID_002`: 필드 형식 오류
- `E_RESOURCE_001`: 사건 없음
- `E_RESOURCE_002`: 이슈 없음
- `E_RESOURCE_003`: 게시글 없음
- `E_RESOURCE_004`: 댓글 없음
- `E_RESOURCE_005`: 사용자/트리거 없음(라우터별 사용 상이)
- `E_RESOURCE_006`: 태그 없음
- `E_RESOURCE_007`: 출처 없음
- `E_CONFLICT_002`: 이미 추적 중인 이슈
- `E_CONFLICT_003`: 이미 저장된 사건
- `E_SERVER_001`: 서버 내부 오류
