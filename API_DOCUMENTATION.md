# Trend Korea - Backend API & System Documentation

> **Version**: 0.1.0 | **Last Updated**: 2026-02-20 | **Database**: PostgreSQL 16+

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Tech Stack](#2-tech-stack)
3. [Getting Started](#3-getting-started)
4. [API Endpoints](#4-api-endpoints)
   - [Health Check](#41-health-check)
   - [Authentication](#42-authentication)
   - [Users](#43-users)
   - [Events](#44-events)
   - [Issues](#45-issues)
   - [Triggers](#46-triggers)
   - [Community (Posts & Comments)](#47-community)
   - [Search](#48-search)
   - [Home (Dashboard)](#49-home-dashboard)
   - [Tags](#410-tags)
   - [Sources](#411-sources)
5. [Authentication & Authorization](#5-authentication--authorization)
6. [Error Handling](#6-error-handling)
7. [Database Schema](#7-database-schema)
8. [Enums & Constants](#8-enums--constants)
9. [Keyword Crawler (CLI)](#9-keyword-crawler-cli)
10. [News Crawl Pipeline](#10-news-crawl-pipeline)

---

## 1. Project Overview

**Trend Korea**는 대한민국의 주요 사회 이슈와 사건을 추적, 분석하는 플랫폼입니다.

### System Components

| Component | Description | Location |
|-----------|-------------|----------|
| **Backend API** | FastAPI 기반 REST API 서버 | `trend-korea-backend/` |
| **Keyword Crawler** | 뉴스 채널 메인 페이지 키워드 추출 CLI | `trend-korea-backend/src/trend_korea/keyword_crawler/` |
| **News Pipeline** | 키워드 기반 뉴스 기사 수집 파이프라인 | `news-crawl-pipeline/` |

### Architecture

```
Frontend (React/Next.js)
    │
    ▼
Backend API (FastAPI)  ←──  PostgreSQL 16
    │
    ├── Keyword Crawler (CLI, 주기적 실행)
    │     └── 10개 뉴스 채널 메인 페이지 → 키워드 추출 → DB 저장
    │
    └── News Pipeline (CLI, 독립 실행)
          └── 5개 뉴스 채널 × 키워드 → 기사 본문 수집 → JSON
```

---

## 2. Tech Stack

| Category | Technology |
|----------|-----------|
| Framework | FastAPI >= 0.116.0 |
| Language | Python >= 3.11 |
| ORM | SQLAlchemy 2.0 (Mapped type annotations) |
| Migration | Alembic >= 1.14.0 |
| Database | PostgreSQL 16+ (psycopg3) |
| Auth | JWT (python-jose), bcrypt (passlib) |
| Validation | Pydantic >= 2.10.0 |
| HTTP Client | httpx >= 0.28.0 (async) |
| HTML Parser | BeautifulSoup4 + lxml |
| Korean NLP | kiwipiepy (형태소 분석) |
| Scheduler | APScheduler >= 3.11.0 |

---

## 3. Getting Started

### Prerequisites

```bash
# PostgreSQL 16 (Homebrew)
brew install postgresql@16
brew services start postgresql@16

# PATH 설정 (~/.zshrc)
export PATH="/opt/homebrew/opt/postgresql@16/bin:$PATH"
```

### Database Setup

```bash
# DB 생성
createdb trend_korea

# 스키마 초기화
psql -d trend_korea -f init_db.sql
```

### Backend 실행

```bash
cd trend-korea-backend
pip install -e ".[crawler]"

# 서버 실행
uvicorn trend_korea.main:app --reload --port 8000
```

### 환경변수 (`.env`)

```env
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/trend_korea
JWT_SECRET_KEY=your-secret-key
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
```

---

## 4. API Endpoints

> **Base URL**: `http://localhost:8000/api/v1`
>
> **Auth Header**: `Authorization: Bearer <access_token>`

---

### 4.1 Health Check

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/health/live` | - | Liveness check |
| `GET` | `/health/ready` | - | Readiness check |

**Response** `200`:
```json
{ "data": { "status": "ok" }, "message": "string" }
```

---

### 4.2 Authentication

#### `POST /auth/register` - 회원가입

**Request Body:**
```json
{
  "nickname": "string (2-20자)",
  "email": "string (이메일 형식)",
  "password": "string (8-72자)"
}
```

**Response** `201`:
```json
{
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "nickname": "닉네임",
    "role": "member",
    "createdAt": "2026-02-20T09:00:00Z"
  },
  "tokens": {
    "accessToken": "eyJ...",
    "refreshToken": "eyJ...",
    "expiresIn": 1800
  }
}
```

---

#### `POST /auth/login` - 로그인

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response** `200`:
```json
{
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "nickname": "닉네임",
    "profileImage": "https://...",
    "role": "member",
    "trackedIssueIds": ["issue-id-1"],
    "savedEventIds": ["event-id-1"]
  },
  "tokens": {
    "accessToken": "eyJ...",
    "refreshToken": "eyJ...",
    "expiresIn": 1800,
    "expiresAt": "2026-02-20T09:30:00Z"
  }
}
```

---

#### `POST /auth/refresh` - 토큰 갱신

**Request Body:**
```json
{ "refreshToken": "eyJ..." }
```

**Response** `200`:
```json
{
  "accessToken": "eyJ...",
  "expiresIn": 1800,
  "expiresAt": "2026-02-20T10:00:00Z"
}
```

---

#### `POST /auth/logout` - 로그아웃

**Auth**: Required (Member/Admin)

**Response** `200`:
```json
{ "data": null, "message": "로그아웃 성공" }
```

---

#### `POST /auth/social-login` - 소셜 로그인

**Request Body:**
```json
{
  "provider": "kakao | naver | google",
  "code": "authorization-code",
  "redirectUri": "https://your-app.com/callback"
}
```

**Response** `200`:
```json
{
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "nickname": "닉네임",
    "role": "member",
    "socialProviders": ["kakao"],
    "profileImage": "https://..."
  },
  "tokens": {
    "accessToken": "eyJ...",
    "refreshToken": "eyJ...",
    "expiresIn": 1800
  },
  "isNewUser": true
}
```

---

#### `GET /auth/social/providers` - 소셜 로그인 제공자 목록

**Response** `200`:
```json
{ "data": ["kakao", "naver", "google"] }
```

---

#### `DELETE /auth/withdraw` - 회원 탈퇴

**Auth**: Required (Member/Admin)

**Request Body:**
```json
{ "password": "current-password (optional)" }
```

---

### 4.3 Users

#### `GET /users/me` - 내 프로필 조회

**Auth**: Required (Member/Admin)

**Response** `200`:
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "nickname": "닉네임",
  "profileImage": "https://...",
  "role": "member",
  "socialProviders": ["kakao"],
  "trackedIssueIds": ["issue-1"],
  "savedEventIds": ["event-1"],
  "createdAt": "2026-02-20T09:00:00Z",
  "updatedAt": "2026-02-20T09:00:00Z"
}
```

---

#### `PATCH /users/me` - 프로필 수정

**Auth**: Required (Member/Admin)

**Request Body:**
```json
{
  "nickname": "새닉네임 (2-20자, optional)",
  "profileImage": "https://... (max 500자, optional)"
}
```

**Response** `200`:
```json
{
  "id": "uuid",
  "nickname": "새닉네임",
  "profileImage": "https://...",
  "updatedAt": "2026-02-20T09:30:00Z"
}
```

**Errors**: `409` Nickname already taken

---

#### `POST /users/me/change-password` - 비밀번호 변경

**Auth**: Required (Member/Admin)

**Request Body:**
```json
{
  "currentPassword": "old-password (8-72자)",
  "newPassword": "new-password (8-72자)"
}
```

**Errors**: `401` Current password incorrect

---

#### `POST /users/me/social-connect` - 소셜 계정 연결

**Auth**: Required

**Request Body:**
```json
{ "provider": "kakao", "code": "auth-code" }
```

---

#### `DELETE /users/me/social-disconnect` - 소셜 계정 해제

**Auth**: Required

**Request Body:**
```json
{ "provider": "kakao" }
```

---

#### `GET /users/me/activity` - 활동 내역

**Auth**: Required | **Query**: `page`, `limit`, `type`

---

#### `GET /users/me/tracked-issues` - 추적 중인 이슈 목록

**Auth**: Required

**Query Parameters:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `page` | int | 1 | 페이지 번호 |
| `limit` | int | 10 | 페이지 크기 (1-100) |
| `sortBy` | string | "trackedAt" | 정렬 기준 |

---

#### `GET /users/me/saved-events` - 저장한 이벤트 목록

**Auth**: Required

**Query Parameters:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `page` | int | 1 | 페이지 번호 |
| `limit` | int | 10 | 페이지 크기 (1-100) |
| `sortBy` | string | "savedAt" | 정렬 기준 |

---

#### `GET /users/{user_id}` - 사용자 프로필 조회 (공개)

**Auth**: None

**Response** `200`:
```json
{
  "id": "uuid",
  "nickname": "닉네임",
  "profileImage": "https://...",
  "bio": null,
  "createdAt": "2026-02-20T09:00:00Z",
  "activityStats": {
    "postCount": 5,
    "commentCount": 12,
    "likeCount": 8
  }
}
```

---

### 4.4 Events

#### `GET /events` - 이벤트 목록 (커서 페이지네이션)

**Query Parameters:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `cursor` | string | null | 페이지네이션 커서 |
| `limit` | int | 10 | 1-100 |
| `importance` | string | null | `low` / `medium` / `high` |
| `startDate` | datetime | null | 시작일 |
| `endDate` | datetime | null | 종료일 |
| `sortBy` | string | "occurredAt" | 정렬 기준 |
| `order` | string | "desc" | `asc` / `desc` |

**Response** `200`:
```json
{
  "items": [
    {
      "id": "uuid",
      "occurredAt": "2026-02-20T09:00:00Z",
      "title": "이벤트 제목",
      "summary": "이벤트 요약 내용",
      "importance": "high",
      "verificationStatus": "verified",
      "tags": [{ "id": "tag-1", "name": "정치" }],
      "sources": [{ "id": "src-1", "title": "출처 제목" }]
    }
  ],
  "cursor": {
    "next": "cursor-string",
    "hasMore": true
  }
}
```

---

#### `GET /events/{event_id}` - 이벤트 상세

**Errors**: `404` Event not found

---

#### `POST /events` - 이벤트 생성 (Admin)

**Auth**: Required (Admin)

**Request Body:**
```json
{
  "occurredAt": "2026-02-20T09:00:00Z",
  "title": "이벤트 제목 (max 50자)",
  "summary": "이벤트 요약",
  "importance": "low | medium | high",
  "verificationStatus": "verified | unverified",
  "tagIds": ["tag-1", "tag-2"],
  "sourceIds": ["src-1"]
}
```

---

#### `PATCH /events/{event_id}` - 이벤트 수정 (Admin)

#### `DELETE /events/{event_id}` - 이벤트 삭제 (Admin)

---

#### `POST /events/{event_id}/save` - 이벤트 저장

**Auth**: Required (Member/Admin)

**Response** `200`:
```json
{
  "eventId": "uuid",
  "isSaved": true,
  "savedAt": "2026-02-20T09:00:00Z"
}
```

**Errors**: `409` Already saved

---

#### `DELETE /events/{event_id}/save` - 이벤트 저장 취소

**Auth**: Required (Member/Admin)

---

### 4.5 Issues

#### `GET /issues` - 이슈 목록 (페이지 페이지네이션)

**Query Parameters:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `page` | int | 1 | 페이지 번호 |
| `limit` | int | 10 | 1-100 |
| `status` | string | null | `ongoing` / `closed` / `reignited` / `unverified` |
| `startDate` | datetime | null | 시작일 |
| `endDate` | datetime | null | 종료일 |
| `sortBy` | string | "updatedAt" | 정렬 기준 |
| `order` | string | "desc" | `asc` / `desc` |

**Response** `200`:
```json
{
  "items": [
    {
      "id": "uuid",
      "title": "이슈 제목",
      "description": "이슈 설명",
      "status": "ongoing",
      "tags": [{ "id": "tag-1", "name": "경제" }],
      "sources": [{ "id": "src-1", "title": "출처" }],
      "relatedEvents": [{ "id": "evt-1", "title": "관련 이벤트" }],
      "latestTriggerAt": "2026-02-19T15:00:00Z",
      "updatedAt": "2026-02-20T09:00:00Z"
    }
  ],
  "pagination": {
    "currentPage": 1,
    "totalPages": 5,
    "totalItems": 42,
    "itemsPerPage": 10,
    "hasNext": true,
    "hasPrev": false
  }
}
```

---

#### `GET /issues/{issue_id}` - 이슈 상세

#### `POST /issues` - 이슈 생성 (Admin)

**Request Body:**
```json
{
  "title": "이슈 제목",
  "description": "이슈 설명",
  "status": "ongoing | closed | reignited | unverified",
  "tagIds": ["tag-1"],
  "sourceIds": ["src-1"],
  "relatedEventIds": ["evt-1"]
}
```

#### `PATCH /issues/{issue_id}` - 이슈 수정 (Admin)

#### `DELETE /issues/{issue_id}` - 이슈 삭제 (Admin)

---

#### `POST /issues/{issue_id}/track` - 이슈 추적 시작

**Auth**: Required (Member/Admin)

**Response** `200`:
```json
{
  "issueId": "uuid",
  "isTracking": true,
  "trackedAt": "2026-02-20T09:00:00Z"
}
```

#### `DELETE /issues/{issue_id}/track` - 이슈 추적 해제

---

#### `GET /issues/{issue_id}/triggers` - 이슈 트리거 목록

**Response** `200`:
```json
[
  {
    "id": "uuid",
    "type": "article",
    "summary": "트리거 요약",
    "occurredAt": "2026-02-19T15:00:00Z",
    "sources": [{ "id": "src-1", "title": "출처" }],
    "createdAt": "2026-02-19T16:00:00Z"
  }
]
```

#### `POST /issues/{issue_id}/triggers` - 트리거 생성 (Admin)

**Request Body:**
```json
{
  "occurredAt": "2026-02-19T15:00:00Z",
  "summary": "트리거 요약",
  "type": "article | ruling | announcement | correction | status_change",
  "sourceIds": ["src-1"]
}
```

---

### 4.6 Triggers

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `PATCH` | `/triggers/{trigger_id}` | Admin | 트리거 수정 |
| `DELETE` | `/triggers/{trigger_id}` | Admin | 트리거 삭제 |

---

### 4.7 Community

#### `GET /posts` - 게시글 목록

**Query Parameters:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `cursor` | string | null | 커서 |
| `limit` | int | 10 | 1-100 |
| `tab` | string | "latest" | 탭 필터 |
| `sortBy` | string | "createdAt" | 정렬 기준 |

**Response** `200`:
```json
{
  "items": [
    {
      "id": "uuid",
      "title": "게시글 제목",
      "content": "게시글 내용",
      "author": { "id": "uuid", "nickname": "작성자" },
      "tags": [{ "id": "tag-1", "name": "태그" }],
      "likeCount": 5,
      "dislikeCount": 1,
      "commentCount": 3,
      "isAnonymous": false,
      "createdAt": "2026-02-20T09:00:00Z"
    }
  ],
  "cursor": { "next": "cursor-string", "hasMore": true }
}
```

---

#### `POST /posts` - 게시글 작성

**Auth**: Required (Member/Admin)

**Request Body:**
```json
{
  "title": "게시글 제목 (1-100자)",
  "content": "게시글 내용 (min 1자)",
  "tagIds": ["tag-1"],
  "isAnonymous": false
}
```

---

#### `GET /posts/{post_id}` - 게시글 상세

#### `PATCH /posts/{post_id}` - 게시글 수정 (작성자/Admin)

#### `DELETE /posts/{post_id}` - 게시글 삭제 (작성자/Admin)

---

#### `GET /posts/{post_id}/comments` - 댓글 목록

**Response** `200`:
```json
[
  {
    "id": "uuid",
    "content": "댓글 내용",
    "author": { "id": "uuid", "nickname": "댓글작성자" },
    "likeCount": 2,
    "parentId": null,
    "replies": [],
    "createdAt": "2026-02-20T09:30:00Z"
  }
]
```

#### `POST /posts/{post_id}/comments` - 댓글 작성

**Request Body:**
```json
{
  "content": "댓글 내용",
  "parentId": "parent-comment-id (대댓글시)"
}
```

#### `PATCH /comments/{comment_id}` - 댓글 수정

#### `DELETE /comments/{comment_id}` - 댓글 삭제

---

#### 좋아요 / 싫어요

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/posts/{post_id}/like` | Member | 게시글 좋아요/싫어요 (`{ "type": "like\|dislike" }`) |
| `POST` | `/comments/{comment_id}/like` | Member | 댓글 좋아요 |
| `DELETE` | `/comments/{comment_id}/like` | Member | 댓글 좋아요 취소 |

**게시글 좋아요 Response:**
```json
{
  "postId": "uuid",
  "likeCount": 6,
  "dislikeCount": 1,
  "userVoteType": "like"
}
```

---

### 4.8 Search

#### `GET /search` - 통합 검색

**Query Parameters:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `q` | string | (required) | 검색어 (min 1자) |
| `page` | int | 1 | 페이지 번호 |
| `limit` | int | 10 | 1-100 |
| `tab` | string | "all" | `all` / `events` / `issues` / `community` |
| `sortBy` | string | "relevance" | 정렬 기준 |

**Response** `200`:
```json
{
  "items": [
    {
      "id": "uuid",
      "type": "event | issue | post",
      "title": "검색 결과 제목",
      "summary": "요약 내용",
      "date": "2026-02-20T09:00:00Z",
      "tags": []
    }
  ],
  "pagination": { "currentPage": 1, "totalPages": 3, "totalItems": 25, "itemsPerPage": 10, "hasNext": true, "hasPrev": false }
}
```

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/search/events` | 이벤트만 검색 |
| `GET` | `/search/issues` | 이슈만 검색 |
| `GET` | `/search/posts` | 게시글만 검색 |

---

### 4.9 Home (Dashboard)

> 모든 Home 엔드포인트는 **Auth 불필요**

#### `GET /home/breaking-news` - 속보

**Query**: `limit` (1-20, default 10)

```json
[
  {
    "id": "uuid",
    "number": 1,
    "time": "14:30",
    "title": "속보 제목",
    "summary": "속보 요약",
    "tags": [],
    "importance": "high"
  }
]
```

---

#### `GET /home/trending` - 실시간 트렌딩 이슈

**Query**: `limit` (1-20, default 10), `period` (default "24h")

```json
[
  {
    "rank": 1,
    "issue": {
      "id": "uuid",
      "title": "트렌딩 이슈",
      "status": "ongoing"
    },
    "relatedEventCount": 5,
    "trackerCount": 120,
    "change": "+2"
  }
]
```

---

#### `GET /home/search-rankings` - 검색어 순위

**Query**: `limit` (1-20, default 10), `period` ("daily" / "weekly")

```json
[
  { "rank": 1, "keyword": "대통령", "count": 28, "change": "+3" },
  { "rank": 2, "keyword": "경제", "count": 15, "change": "-1" }
]
```

---

#### `GET /home/hot-posts` - 인기 게시글

**Query**: `limit` (1-20, default 5), `period` (default "24h")

```json
[
  {
    "id": "uuid",
    "number": 1,
    "title": "인기 게시글",
    "category": "정치",
    "commentCount": 45,
    "author": "닉네임",
    "createdAt": "2026-02-20T08:00:00Z",
    "isHot": true
  }
]
```

---

#### `GET /home/timeline-minimap` - 타임라인 미니맵

**Query**: `days` (1-30, default 7)

```json
{
  "dates": [
    { "date": "2026-02-20", "eventCount": 12, "density": "high" },
    { "date": "2026-02-19", "eventCount": 3, "density": "low" }
  ]
}
```

---

#### `GET /home/featured-news` - 추천 뉴스

**Query**: `limit` (1-20, default 5)

```json
[
  {
    "id": "uuid",
    "author": "기자명",
    "authorImage": "https://...",
    "title": "추천 뉴스 제목",
    "summary": "요약",
    "imageUrl": "https://...",
    "createdAt": "2026-02-20T07:00:00Z"
  }
]
```

---

#### `GET /home/community-media` - 커뮤니티 미디어

**Query**: `limit` (1-20, default 6)

```json
[
  {
    "id": "uuid",
    "title": "게시글 제목",
    "imageUrl": "https://...",
    "viewCount": 1200,
    "createdAt": "2026-02-20T06:00:00Z"
  }
]
```

---

### 4.10 Tags

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/tags` | - | 태그 목록 (`?type=category\|region&search=검색어`) |
| `POST` | `/tags` | Admin | 태그 생성 |
| `PATCH` | `/tags/{tag_id}` | Admin | 태그 수정 |
| `DELETE` | `/tags/{tag_id}` | Admin | 태그 삭제 |

**Tag Object:**
```json
{ "id": "uuid", "name": "정치", "type": "category", "slug": "politics" }
```

---

### 4.11 Sources

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/sources` | - | 출처 목록 (`?page=1&limit=20&publisher=조선일보`) |
| `POST` | `/sources` | Admin | 출처 생성 |
| `DELETE` | `/sources/{source_id}` | Admin | 출처 삭제 |

**Source Object:**
```json
{
  "id": "uuid",
  "title": "기사 제목",
  "url": "https://www.chosun.com/...",
  "publisher": "조선일보",
  "publishedAt": "2026-02-20T08:00:00Z"
}
```

---

## 5. Authentication & Authorization

### Token Types

| Type | Lifetime | Usage |
|------|----------|-------|
| **Access Token** | 30분 | API 요청 헤더 (`Authorization: Bearer <token>`) |
| **Refresh Token** | 7일 | Access Token 갱신 (`POST /auth/refresh`) |

### Role Permissions

| Role | Description | Permissions |
|------|-------------|-------------|
| `guest` | 미인증 사용자 | 읽기 전용 (목록/상세 조회) |
| `member` | 일반 회원 | 읽기 + 글쓰기 + 좋아요 + 이슈 추적 + 이벤트 저장 |
| `admin` | 관리자 | 모든 권한 (CRUD 전체) |

### Auth Flow

```
1. 회원가입/로그인 → accessToken + refreshToken 발급
2. API 요청 시 → Authorization: Bearer <accessToken>
3. accessToken 만료 → POST /auth/refresh (refreshToken 전송)
4. 새 accessToken 수령
5. refreshToken 만료 → 재로그인 필요
```

---

## 6. Error Handling

### HTTP Status Codes

| Code | Description |
|------|-------------|
| `200` | 성공 |
| `201` | 생성 성공 |
| `400` | 잘못된 요청 (유효성 검증 실패) |
| `401` | 인증 실패 (토큰 없음/만료) |
| `403` | 권한 없음 (작성자/관리자만 가능) |
| `404` | 리소스 없음 |
| `409` | 충돌 (중복 닉네임, 이미 저장됨 등) |

### Error Response Format

```json
{
  "code": "E_AUTH_003",
  "message": "인증 토큰이 유효하지 않습니다",
  "detail": null
}
```

### Error Codes

| Code | Description |
|------|-------------|
| `E_AUTH_001` | 인증 토큰 없음 |
| `E_AUTH_003` | 유효하지 않은 토큰 |
| `E_VALID_001` | 필수 필드 누락 |
| `E_VALID_002` | 필드 값/형식 오류 |
| `E_RESOURCE_001` | 이벤트 없음 |
| `E_RESOURCE_002` | 이슈 없음 |
| `E_RESOURCE_003` | 게시글 없음 |
| `E_RESOURCE_004` | 댓글 없음 |
| `E_RESOURCE_005` | 사용자 없음 |
| `E_RESOURCE_006` | 태그 없음 |
| `E_RESOURCE_007` | 출처 없음 |
| `E_CONFLICT_002` | 닉네임 중복 / 이미 추적 중 |
| `E_CONFLICT_003` | 이미 저장됨 |
| `E_PERM_001` | 권한 없음 (작성자가 아님) |
| `E_PERM_002` | 관리자 권한 필요 |

---

## 7. Database Schema

### ER Diagram (Summary)

```
users ──┬── user_social_accounts
        ├── posts ──┬── comments ── comment_likes
        │           ├── post_votes
        │           └── post_tags ── tags
        ├── user_saved_events ── events ──┬── event_tags ── tags
        │                                 └── sources
        └── user_tracked_issues ── issues ──┬── issue_tags ── tags
                                            ├── issue_events ── events
                                            └── triggers ── sources

news_channels (독립)
crawled_keywords (독립)
search_rankings (독립)
search_histories (독립)
job_runs (독립)
refresh_tokens ── users
```

### Tables Overview

#### Core Entity Tables

| Table | Description | Key Columns |
|-------|-------------|-------------|
| `users` | 사용자 | id, nickname(unique), email(unique), password_hash, role, is_active |
| `user_social_accounts` | 소셜 계정 연동 | user_id(FK), provider, provider_user_id |
| `tags` | 태그 (카테고리/지역) | name, type(category/region), slug(unique) |
| `events` | 사건/이벤트 | occurred_at, title, summary, importance, verification_status, source_count |
| `issues` | 이슈 | title, description, status, tracker_count, latest_trigger_at |
| `triggers` | 이슈 트리거 | issue_id(FK), occurred_at, summary, type |
| `sources` | 출처 (뉴스 기사) | entity_type, entity_id, url, title, publisher, published_at |

#### Community Tables

| Table | Description | Key Columns |
|-------|-------------|-------------|
| `posts` | 게시글 | author_id(FK), title, content, is_anonymous, like_count, dislike_count, comment_count |
| `comments` | 댓글 (대댓글 지원) | post_id(FK), parent_id(self FK), author_id(FK), content, like_count |
| `comment_likes` | 댓글 좋아요 | comment_id(FK), user_id(FK), UNIQUE(comment_id, user_id) |
| `post_votes` | 게시글 좋아요/싫어요 | post_id(FK), user_id(FK), vote_type, UNIQUE(post_id, user_id) |

#### Auth & Search Tables

| Table | Description | Key Columns |
|-------|-------------|-------------|
| `refresh_tokens` | JWT Refresh Token | user_id(FK), token_hash(unique), jti(unique), expires_at, revoked_at |
| `search_rankings` | 검색어 순위 | keyword, rank, score, calculated_at |
| `search_histories` | 사용자 검색 기록 | user_id, keyword, created_at |

#### Junction Tables

| Table | PK | Description |
|-------|-----|-------------|
| `event_tags` | (event_id, tag_id) | 이벤트-태그 연결 |
| `issue_tags` | (issue_id, tag_id) | 이슈-태그 연결 |
| `issue_events` | (issue_id, event_id) | 이슈-이벤트 연결 |
| `post_tags` | (post_id, tag_id) | 게시글-태그 연결 |
| `user_saved_events` | (user_id, event_id) | 사용자 이벤트 저장 (+saved_at) |
| `user_tracked_issues` | (user_id, issue_id) | 사용자 이슈 추적 (+tracked_at) |

#### Crawler & Job Tables

| Table | Description | Key Columns |
|-------|-------------|-------------|
| `news_channels` | 뉴스 채널 목록 | code(unique), symbol(unique), name, url, category, is_active |
| `crawled_keywords` | 크롤링된 키워드 | keyword, count, rank, channel_code, source_type, crawled_at |
| `job_runs` | 배치 작업 실행 이력 | job_name, status, detail, started_at, finished_at |

### News Channels (Seed Data)

| Code | Symbol | Name | Category | URL |
|------|--------|------|----------|-----|
| `yonhapnews_tv` | YNA | 연합뉴스TV | broadcast | https://m.yonhapnewstv.co.kr/ |
| `sbs` | SBS | SBS 뉴스 | broadcast | https://news.sbs.co.kr/ |
| `mbc` | MBC | MBC 뉴스 | broadcast | https://imnews.imbc.com/ |
| `kbs` | KBS | KBS | broadcast | https://www.kbs.co.kr/ |
| `jtbc` | JTBC | JTBC | broadcast | https://jtbc.co.kr/ |
| `chosun` | CHO | 조선일보 | newspaper | https://www.chosun.com/ |
| `donga` | DGA | 동아일보 | newspaper | https://www.donga.com/ |
| `hani` | HAN | 한겨레 | newspaper | https://www.hani.co.kr/ |
| `khan` | KHN | 경향신문 | newspaper | https://www.khan.co.kr/ |
| `mk` | MK | 매일경제 | newspaper | https://www.mk.co.kr/ |

---

## 8. Enums & Constants

| Enum | Values | Used In |
|------|--------|---------|
| `UserRole` | `guest`, `member`, `admin` | users.role |
| `SocialProvider` | `kakao`, `naver`, `google` | user_social_accounts.provider |
| `TagType` | `category`, `region` | tags.type |
| `Importance` | `low`, `medium`, `high` | events.importance |
| `VerificationStatus` | `verified`, `unverified` | events.verification_status |
| `IssueStatus` | `ongoing`, `closed`, `reignited`, `unverified` | issues.status |
| `TriggerType` | `article`, `ruling`, `announcement`, `correction`, `status_change` | triggers.type |
| `VoteType` | `like`, `dislike` | post_votes.vote_type |
| `SourceEntityType` | `event`, `issue`, `trigger` | sources.entity_type |
| `NewsChannelCategory` | `broadcast`, `newspaper`, `online` | news_channels.category |

---

## 9. Keyword Crawler (CLI)

> 뉴스 채널 메인 페이지에서 헤드라인을 수집하고, 한국어 형태소 분석으로 핵심 키워드를 추출합니다.

### 설치 & 실행

```bash
cd trend-korea-backend
pip install -e ".[crawler]"

# 실행
trend-korea-crawl-keywords --pretty --out /tmp/keywords.json

# DB에 저장
trend-korea-crawl-keywords --save-db
```

### CLI Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--top-n` | int | 30 | 통합 키워드 수 |
| `--per-channel` | int | 20 | 채널별 키워드 수 |
| `--timeout` | float | 15.0 | HTTP 타임아웃 (초) |
| `--category` | string | null | `broadcast` / `newspaper` 필터 |
| `--out` | string | stdout | 출력 파일 경로 |
| `--pretty` | flag | false | JSON 들여쓰기 |
| `--save-db` | flag | false | 결과를 `crawled_keywords` 테이블에 저장 |

### Output JSON Format

```json
{
  "crawled_at": "2026-02-17T06:21:32Z",
  "total_channels": 10,
  "successful_channels": 10,
  "failed_channels": 0,
  "channels": [
    {
      "channel_code": "chosun",
      "channel_name": "조선일보",
      "channel_url": "https://www.chosun.com/",
      "category": "newspaper",
      "headlines": [
        "트럼프 대통령 한일 정상회담 중재 나서",
        "서울 아파트 매수심리 살아나..."
      ],
      "keywords": [
        { "word": "대통령", "count": 8, "rank": 1 },
        { "word": "경제", "count": 5, "rank": 2 }
      ],
      "fetch_status": "success",
      "error_message": null,
      "fetch_duration_ms": 1230
    }
  ],
  "aggregated_keywords": [
    { "word": "대통령", "count": 28, "rank": 1 },
    { "word": "경제", "count": 15, "rank": 2 },
    { "word": "트럼프", "count": 10, "rank": 3 }
  ]
}
```

### Architecture

```
keyword_crawler/
├── cli.py                 # CLI 진입점 (argparse)
├── crawler.py             # 오케스트레이터: DB 조회 → 비동기 fetch → 추출 → JSON
├── http_client.py         # httpx 비동기 HTTP (UA 로테이션, charset 폴백, 재시도)
├── headline_extractor.py  # 사이트별 CSS 셀렉터 + RSS 피드 + 제너릭 폴백
└── keyword_analyzer.py    # kiwipiepy 한국어 명사 추출 + 빈도 랭킹
```

**Processing Flow:**

```
DB (news_channels, is_active=true)
    │
    ▼
asyncio.gather (10개 채널 동시 fetch)
    │
    ├── RSS 피드 있는 채널 → XML 파싱 → 헤드라인 추출
    │
    ├── HTML 채널 → CSS 셀렉터 → 헤드라인 추출
    │   ├── 사이트별 셀렉터 (우선)
    │   ├── JSON-LD 폴백
    │   └── 제너릭 폴백 (h1~h3, <a> 태그)
    │
    ▼
kiwipiepy 형태소 분석 (NNG + NNP 명사 추출)
    │
    ├── 채널별 키워드 top-N
    └── 전체 통합 키워드 top-N
    │
    ▼
JSON 출력 / DB 저장 (crawled_keywords)
```

---

## 10. News Crawl Pipeline

> 키워드 기반으로 5개 뉴스 채널에서 기사를 검색하고, 본문을 추출하는 독립형 파이프라인입니다.

### 설치 & 실행

```bash
cd news-crawl-pipeline
pip install -e .

# 기본 실행
news-pipeline --keyword "서울 지하철" --limit 5 --out results.jsonl

# 여러 키워드
news-pipeline --keyword "경제" --keyword "부동산" --limit 3

# 특정 채널만
news-pipeline --keyword "환율" --channels mk cho hani

# SPA 렌더링 비활성화 (빠른 실행)
news-pipeline --keyword "날씨" --no-spa
```

### CLI Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--keyword` | string | (required) | 검색 키워드 (복수 지정 가능) |
| `--channels` | list | all 5 | 채널 선택: `mk`, `mi`, `cho`, `hani`, `naver` |
| `--limit` | int | 5 | 채널당 최대 기사 수 |
| `--no-spa` | flag | false | SPA 렌더링 비활성화 |
| `--format` | string | "json" | 출력 형식: `json` / `jsonl` |
| `--out` | string | results.{format} | 출력 파일 경로 |
| `--report-out` | string | crawl_report.json | 진단 리포트 경로 |
| `--workers` | int | 8 | 병렬 워커 수 |

### Supported Channels

| Code | Channel | Search Method |
|------|---------|--------------|
| `mk` | 매일경제 | HTML 검색 페이지 |
| `mi` | 매일일보 | HTML 검색 페이지 |
| `cho` | 조선일보 | Fusion CMS API (JSON) |
| `hani` | 한겨레 | HTML 검색 페이지 |
| `naver` | 네이버 뉴스 | HTML 검색 페이지 |

### Output Format

**Article Record (JSONL):**
```json
{
  "channel": "mk",
  "title": "기사 제목",
  "url": "https://www.mk.co.kr/news/...",
  "keyword": "서울 지하철",
  "content_text": "기사 본문 텍스트...",
  "content_chars": 1200,
  "fetch_mode": "static",
  "confidence": 0.91,
  "fetched_at": "2026-02-16T11:00:00.000Z",
  "published_at": null
}
```

**Diagnostic Report:**
```json
[
  {
    "channel": "mk",
    "keyword": "서울 지하철",
    "search_fetch_fail": 0,
    "search_blocked": 0,
    "search_link_count": 19,
    "article_fetch_fail": 0,
    "article_blocked": 3,
    "extract_fail": 0,
    "short_text_skip": 0,
    "collected": 3
  }
]
```

### Text Extraction Strategy

| Stage | Mode | Description | Confidence |
|-------|------|-------------|------------|
| 1 | `static` | HTML `<p>` 태그 파싱 | 0.45-0.95 |
| 2 | `spr_json` | JSON-LD / `__NEXT_DATA__` / Fusion API | 0.58-0.92 |
| 3 | `spa_rendered` | Playwright 브라우저 렌더링 (fallback) | +0.05 boost |

### Architecture

```
news-crawl-pipeline/
├── cli.py              # CLI 진입점
├── pipeline.py         # 코어 파이프라인 (ThreadPoolExecutor)
├── base_channel.py     # 채널 추상 베이스 클래스
├── extractor.py        # 3단계 텍스트 추출 엔진
├── http_client.py      # HTTP 클라이언트 (재시도, UA 로테이션, charset 폴백)
├── spa_renderer.py     # Playwright SPA 렌더링
├── types.py            # 데이터 구조 (ArticleRecord)
├── utils.py            # 유틸리티 함수
└── channels/           # 채널별 구현
    ├── mk.py
    ├── mi.py
    ├── chosun.py
    ├── hani.py
    └── naver.py
```
