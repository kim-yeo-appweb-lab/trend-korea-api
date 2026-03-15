from enum import Enum


class UserRole(str, Enum):
    GUEST = "guest"
    MEMBER = "member"
    ADMIN = "admin"


class SocialProvider(str, Enum):
    KAKAO = "kakao"
    NAVER = "naver"
    GOOGLE = "google"


class TagType(str, Enum):
    CATEGORY = "category"
    REGION = "region"


class Importance(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class VerificationStatus(str, Enum):
    VERIFIED = "verified"
    UNVERIFIED = "unverified"


class IssueStatus(str, Enum):
    ONGOING = "ongoing"
    CLOSED = "closed"
    REIGNITED = "reignited"
    UNVERIFIED = "unverified"


class TriggerType(str, Enum):
    ARTICLE = "article"
    RULING = "ruling"
    ANNOUNCEMENT = "announcement"
    CORRECTION = "correction"
    STATUS_CHANGE = "status_change"


class VoteType(str, Enum):
    LIKE = "like"
    DISLIKE = "dislike"


class SourceEntityType(str, Enum):
    EVENT = "event"
    ISSUE = "issue"
    TRIGGER = "trigger"


class NewsChannelCategory(str, Enum):
    BROADCAST = "broadcast"
    NEWSPAPER = "newspaper"
    ONLINE = "online"


class UpdateType(str, Enum):
    NEW = "NEW"
    MINOR_UPDATE = "MINOR_UPDATE"
    MAJOR_UPDATE = "MAJOR_UPDATE"
    DUP = "DUP"


class KeywordLinkStatus(str, Enum):
    ACTIVE = "active"
    COOLDOWN = "cooldown"
    CLOSED = "closed"


class FeedType(str, Enum):
    BREAKING = "breaking"
    MAJOR = "major"
    ALL = "all"


class NotificationType(str, Enum):
    MAJOR_UPDATE = "major_update"
    TRIGGER_UPDATE = "trigger_update"
    COMMENT_REPLY = "comment_reply"
    KEYWORD_MATCH = "keyword_match"
    SYSTEM = "system"
