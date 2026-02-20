-- ============================================================
-- Trend Korea API - Database Schema
-- PostgreSQL 16+
-- Generated from Alembic migration: 20260215_000001_init
-- ============================================================

-- 데이터베이스 생성 (psql에서 직접 실행 시 사용)
-- CREATE DATABASE trend_korea OWNER postgres;

-- ============================================================
-- 1. Core Entity Tables
-- ============================================================

CREATE TABLE users (
    id          VARCHAR(36)     PRIMARY KEY,
    nickname    VARCHAR(50)     NOT NULL,
    email       VARCHAR(255)    NOT NULL,
    password_hash VARCHAR(255)  NOT NULL,
    profile_image VARCHAR(500),
    role        VARCHAR(20)     NOT NULL,
    is_active   BOOLEAN         NOT NULL,
    withdrawn_at TIMESTAMPTZ,
    created_at  TIMESTAMPTZ     NOT NULL,
    updated_at  TIMESTAMPTZ     NOT NULL
);
CREATE UNIQUE INDEX ix_users_email    ON users (email);
CREATE UNIQUE INDEX ix_users_nickname ON users (nickname);

CREATE TABLE user_social_accounts (
    id               VARCHAR(36)  PRIMARY KEY,
    user_id          VARCHAR(36)  NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider         VARCHAR(20)  NOT NULL,
    provider_user_id VARCHAR(100) NOT NULL,
    email            VARCHAR(255),
    created_at       TIMESTAMPTZ  NOT NULL
);
CREATE INDEX ix_user_social_accounts_user_id ON user_social_accounts (user_id);

CREATE TABLE tags (
    id         VARCHAR(36)  PRIMARY KEY,
    name       VARCHAR(50)  NOT NULL,
    type       VARCHAR(20)  NOT NULL,
    slug       VARCHAR(80)  NOT NULL,
    updated_at TIMESTAMPTZ  NOT NULL
);
CREATE UNIQUE INDEX ix_tags_slug ON tags (slug);

CREATE TABLE events (
    id                  VARCHAR(36)  PRIMARY KEY,
    occurred_at         TIMESTAMPTZ  NOT NULL,
    title               VARCHAR(50)  NOT NULL,
    summary             TEXT         NOT NULL,
    importance          VARCHAR(20)  NOT NULL,
    verification_status VARCHAR(20)  NOT NULL,
    source_count        INTEGER      NOT NULL DEFAULT 0,
    created_at          TIMESTAMPTZ  NOT NULL,
    updated_at          TIMESTAMPTZ  NOT NULL
);
CREATE INDEX ix_events_occurred_at ON events (occurred_at);

CREATE TABLE issues (
    id                VARCHAR(36)  PRIMARY KEY,
    title             VARCHAR(50)  NOT NULL,
    description       TEXT         NOT NULL,
    status            VARCHAR(20)  NOT NULL,
    tracker_count     INTEGER      NOT NULL DEFAULT 0,
    latest_trigger_at TIMESTAMPTZ,
    created_at        TIMESTAMPTZ  NOT NULL,
    updated_at        TIMESTAMPTZ  NOT NULL
);
CREATE INDEX ix_issues_status            ON issues (status);
CREATE INDEX ix_issues_tracker_count     ON issues (tracker_count);
CREATE INDEX ix_issues_latest_trigger_at ON issues (latest_trigger_at);

CREATE TABLE triggers (
    id          VARCHAR(36)  PRIMARY KEY,
    issue_id    VARCHAR(36)  NOT NULL REFERENCES issues(id) ON DELETE CASCADE,
    occurred_at TIMESTAMPTZ  NOT NULL,
    summary     TEXT         NOT NULL,
    type        VARCHAR(20)  NOT NULL,
    created_at  TIMESTAMPTZ  NOT NULL,
    updated_at  TIMESTAMPTZ  NOT NULL
);
CREATE INDEX ix_triggers_issue_id    ON triggers (issue_id);
CREATE INDEX ix_triggers_occurred_at ON triggers (occurred_at);

-- ============================================================
-- 2. Community Tables
-- ============================================================

CREATE TABLE posts (
    id            VARCHAR(36)  PRIMARY KEY,
    author_id     VARCHAR(36)  NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title         VARCHAR(100) NOT NULL,
    content       TEXT         NOT NULL,
    is_anonymous  BOOLEAN      NOT NULL DEFAULT false,
    like_count    INTEGER      NOT NULL DEFAULT 0,
    dislike_count INTEGER      NOT NULL DEFAULT 0,
    comment_count INTEGER      NOT NULL DEFAULT 0,
    created_at    TIMESTAMPTZ  NOT NULL,
    updated_at    TIMESTAMPTZ  NOT NULL
);
CREATE INDEX ix_posts_author_id  ON posts (author_id);
CREATE INDEX ix_posts_created_at ON posts (created_at);

CREATE TABLE comments (
    id         VARCHAR(36)  PRIMARY KEY,
    post_id    VARCHAR(36)  NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    parent_id  VARCHAR(36)           REFERENCES comments(id) ON DELETE CASCADE,
    author_id  VARCHAR(36)  NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content    TEXT         NOT NULL,
    like_count INTEGER      NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ  NOT NULL,
    updated_at TIMESTAMPTZ  NOT NULL
);
CREATE INDEX ix_comments_post_id    ON comments (post_id);
CREATE INDEX ix_comments_created_at ON comments (created_at);

CREATE TABLE comment_likes (
    id         VARCHAR(36)  PRIMARY KEY,
    comment_id VARCHAR(36)  NOT NULL REFERENCES comments(id) ON DELETE CASCADE,
    user_id    VARCHAR(36)  NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ  NOT NULL,
    CONSTRAINT uq_comment_like_user UNIQUE (comment_id, user_id)
);
CREATE INDEX ix_comment_likes_comment_id ON comment_likes (comment_id);
CREATE INDEX ix_comment_likes_user_id    ON comment_likes (user_id);

CREATE TABLE post_votes (
    id         VARCHAR(36)  PRIMARY KEY,
    post_id    VARCHAR(36)  NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    user_id    VARCHAR(36)  NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    vote_type  VARCHAR(10)  NOT NULL,
    created_at TIMESTAMPTZ  NOT NULL,
    CONSTRAINT uq_post_vote_user UNIQUE (post_id, user_id)
);
CREATE INDEX ix_post_votes_post_id ON post_votes (post_id);
CREATE INDEX ix_post_votes_user_id ON post_votes (user_id);

-- ============================================================
-- 3. Authentication Tables
-- ============================================================

CREATE TABLE refresh_tokens (
    id         VARCHAR(36)  PRIMARY KEY,
    user_id    VARCHAR(36)  NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(64)  NOT NULL,
    jti        VARCHAR(36)  NOT NULL,
    expires_at TIMESTAMPTZ  NOT NULL,
    revoked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ  NOT NULL
);
CREATE INDEX        ix_refresh_tokens_user_id    ON refresh_tokens (user_id);
CREATE UNIQUE INDEX ix_refresh_tokens_token_hash ON refresh_tokens (token_hash);
CREATE UNIQUE INDEX ix_refresh_tokens_jti        ON refresh_tokens (jti);

-- ============================================================
-- 4. Source & Search Tables
-- ============================================================

CREATE TABLE sources (
    id           VARCHAR(36)  PRIMARY KEY,
    entity_type  VARCHAR(20)  NOT NULL,
    entity_id    VARCHAR(36)  NOT NULL,
    url          VARCHAR(500) NOT NULL,
    title        VARCHAR(255) NOT NULL,
    publisher    VARCHAR(100) NOT NULL,
    published_at TIMESTAMPTZ  NOT NULL
);
CREATE INDEX ix_sources_entity_type ON sources (entity_type);
CREATE INDEX ix_sources_entity_id   ON sources (entity_id);

CREATE TABLE search_rankings (
    id            VARCHAR(36)  PRIMARY KEY,
    keyword       VARCHAR(100) NOT NULL,
    rank          INTEGER      NOT NULL,
    score         INTEGER      NOT NULL,
    calculated_at TIMESTAMPTZ  NOT NULL
);
CREATE INDEX ix_search_rankings_keyword       ON search_rankings (keyword);
CREATE INDEX ix_search_rankings_calculated_at ON search_rankings (calculated_at);

CREATE TABLE search_histories (
    id         VARCHAR(36)  PRIMARY KEY,
    user_id    VARCHAR(36)  NOT NULL,
    keyword    VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ  NOT NULL
);
CREATE INDEX ix_search_histories_user_id    ON search_histories (user_id);
CREATE INDEX ix_search_histories_created_at ON search_histories (created_at);

-- ============================================================
-- 5. Job Tables
-- ============================================================

CREATE TABLE job_runs (
    id          VARCHAR(36)  PRIMARY KEY,
    job_name    VARCHAR(100) NOT NULL,
    status      VARCHAR(20)  NOT NULL,
    detail      TEXT,
    started_at  TIMESTAMPTZ  NOT NULL,
    finished_at TIMESTAMPTZ
);
CREATE INDEX ix_job_runs_job_name ON job_runs (job_name);

-- ============================================================
-- 6. Junction / Association Tables
-- ============================================================

CREATE TABLE event_tags (
    event_id VARCHAR(36) NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    tag_id   VARCHAR(36) NOT NULL REFERENCES tags(id)   ON DELETE CASCADE,
    PRIMARY KEY (event_id, tag_id)
);

CREATE TABLE user_saved_events (
    user_id  VARCHAR(36) NOT NULL REFERENCES users(id)  ON DELETE CASCADE,
    event_id VARCHAR(36) NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    saved_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (user_id, event_id)
);

CREATE TABLE issue_tags (
    issue_id VARCHAR(36) NOT NULL REFERENCES issues(id) ON DELETE CASCADE,
    tag_id   VARCHAR(36) NOT NULL REFERENCES tags(id)   ON DELETE CASCADE,
    PRIMARY KEY (issue_id, tag_id)
);

CREATE TABLE issue_events (
    issue_id VARCHAR(36) NOT NULL REFERENCES issues(id) ON DELETE CASCADE,
    event_id VARCHAR(36) NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    PRIMARY KEY (issue_id, event_id)
);

CREATE TABLE user_tracked_issues (
    user_id    VARCHAR(36) NOT NULL REFERENCES users(id)  ON DELETE CASCADE,
    issue_id   VARCHAR(36) NOT NULL REFERENCES issues(id) ON DELETE CASCADE,
    tracked_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (user_id, issue_id)
);

CREATE TABLE post_tags (
    post_id VARCHAR(36) NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    tag_id  VARCHAR(36) NOT NULL REFERENCES tags(id)  ON DELETE CASCADE,
    PRIMARY KEY (post_id, tag_id)
);

-- ============================================================
-- 7. News Channel Table
-- ============================================================

CREATE TABLE news_channels (
    id          VARCHAR(36)  PRIMARY KEY,
    code        VARCHAR(20)  NOT NULL,
    symbol      VARCHAR(10)  NOT NULL,
    name        VARCHAR(50)  NOT NULL,
    url         VARCHAR(500) NOT NULL,
    category    VARCHAR(20)  NOT NULL,
    is_active   BOOLEAN      NOT NULL DEFAULT true,
    description TEXT,
    created_at  TIMESTAMPTZ  NOT NULL,
    updated_at  TIMESTAMPTZ  NOT NULL
);
CREATE UNIQUE INDEX ix_news_channels_code     ON news_channels (code);
CREATE UNIQUE INDEX ix_news_channels_symbol   ON news_channels (symbol);
CREATE INDEX        ix_news_channels_category  ON news_channels (category);
CREATE INDEX        ix_news_channels_is_active ON news_channels (is_active);

-- ============================================================
-- 8. Seed Data: News Channels
-- ============================================================

INSERT INTO news_channels (id, code, symbol, name, url, category, is_active, description, created_at, updated_at) VALUES
('nc-001', 'yonhapnews_tv', 'YNA', '연합뉴스TV',  'https://m.yonhapnewstv.co.kr/', 'broadcast',  true, '대한민국 대표 뉴스 통신사 연합뉴스의 24시간 보도채널', NOW(), NOW()),
('nc-002', 'sbs',           'SBS', 'SBS 뉴스',     'https://news.sbs.co.kr/',        'broadcast',  true, 'SBS 방송사 뉴스 포털',                                NOW(), NOW()),
('nc-003', 'mbc',           'MBC', 'MBC 뉴스',     'https://imnews.imbc.com/',       'broadcast',  true, 'MBC 방송사 뉴스 포털',                                NOW(), NOW()),
('nc-004', 'kbs',           'KBS', 'KBS',          'https://www.kbs.co.kr/',         'broadcast',  true, 'KBS 공영방송 뉴스 포털',                              NOW(), NOW()),
('nc-005', 'jtbc',          'JTBC','JTBC',         'https://jtbc.co.kr/',            'broadcast',  true, 'JTBC 종합편성채널 뉴스 섹션',                         NOW(), NOW()),
('nc-006', 'chosun',        'CHO', '조선일보',      'https://www.chosun.com/',        'newspaper',  true, '대한민국 주요 종합일간지',                             NOW(), NOW()),
('nc-007', 'donga',         'DGA', '동아일보',      'https://www.donga.com/',         'newspaper',  true, '대한민국 주요 종합일간지',                             NOW(), NOW()),
('nc-008', 'hani',          'HAN', '한겨레',        'https://www.hani.co.kr/',        'newspaper',  true, '대한민국 진보 성향 종합일간지',                        NOW(), NOW()),
('nc-009', 'khan',          'KHN', '경향신문',      'https://www.khan.co.kr/',        'newspaper',  true, '대한민국 진보 성향 종합일간지',                        NOW(), NOW()),
('nc-010', 'mk',            'MK',  '매일경제',      'https://www.mk.co.kr/',          'newspaper',  true, '대한민국 대표 경제 일간지',                            NOW(), NOW());

-- ============================================================
-- 9. Crawled Keywords Table
-- ============================================================

CREATE TABLE crawled_keywords (
    id           VARCHAR(36)  PRIMARY KEY,
    keyword      VARCHAR(100) NOT NULL,
    count        INTEGER      NOT NULL,
    rank         INTEGER      NOT NULL,
    channel_code VARCHAR(20),
    channel_name VARCHAR(50),
    category     VARCHAR(20),
    source_type  VARCHAR(20)  NOT NULL,
    crawled_at   TIMESTAMPTZ  NOT NULL,
    created_at   TIMESTAMPTZ  NOT NULL
);
CREATE INDEX ix_crawled_keywords_keyword      ON crawled_keywords (keyword);
CREATE INDEX ix_crawled_keywords_channel_code ON crawled_keywords (channel_code);
CREATE INDEX ix_crawled_keywords_source_type  ON crawled_keywords (source_type);
CREATE INDEX ix_crawled_keywords_crawled_at   ON crawled_keywords (crawled_at);
