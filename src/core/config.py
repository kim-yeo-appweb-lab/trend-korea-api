from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", ".env.example"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Trend Korea API"
    app_env: str = "local"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    api_v1_prefix: str = "/api/v1"

    database_url: str = Field(..., min_length=10)

    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 14
    jwt_secret_key: str = Field(default="change-me-in-env", min_length=16)
    jwt_algorithm: str = "HS256"

    scheduler_timezone: str = "Asia/Seoul"
    auto_create_tables: bool = True

    cors_origins: str = "*"

    # Pipeline
    ollama_base_url: str = "http://localhost:11434/v1"
    ollama_default_model: str = "gemma3:4b"
    news_pipeline_dir: str = ""

    # Naver Search API
    naver_api_client: str = ""
    naver_api_client_secret: str = ""

    # OpenAPI (data.go.kr 생필품 가격)
    openapi_product_price_encoding_key: str = ""
    openapi_product_price_decoding_key: str = ""
    openapi_product_price_endpoint: str = (
        "http://openapi.price.go.kr/openApiImpl/ProductPriceInfoService"
    )

    # 기사 분류기 임계값
    classifier_score_new: float = 0.45
    classifier_score_major: float = 0.70
    classifier_candidate_window_hours: int = 72

    # 분류기 점수 가중치
    classifier_weight_keyword: float = 0.15
    classifier_weight_entity: float = 0.20
    classifier_weight_semantic: float = 0.35
    classifier_weight_time: float = 0.20
    classifier_weight_source: float = 0.10

    # 피드 설정
    feed_breaking_score_threshold: float = 0.85
    feed_major_boost: float = 1.5

    # 스케줄러 — 뉴스 수집 파이프라인
    schedule_news_collect_minutes: int = 15
    schedule_keyword_cleanup_minutes: int = 60

    @property
    def cors_origins_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()] or ["*"]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
