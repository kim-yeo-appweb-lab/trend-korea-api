FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# lxml 런타임(libxml2, libxslt1.1) + 헬스체크용 curl
RUN apt-get update \
    && apt-get install -y --no-install-recommends libxml2 libxslt1.1 curl \
    && rm -rf /var/lib/apt/lists/*

# non-root 사용자 (클라우드타입 권장)
RUN groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid 1000 --create-home appuser

WORKDIR /app

# 의존성 캐싱: pyproject.toml 먼저 복사 → 의존성만 설치
COPY pyproject.toml ./
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir pip-tools \
    && pip-compile --extra=crawler -o requirements.txt pyproject.toml \
    && pip install --no-cache-dir -r requirements.txt

# 소스 복사 + 패키지 등록 (entry points)
COPY . .
RUN pip install --no-cache-dir --no-deps ".[crawler]"

COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health/live || exit 1

ENTRYPOINT ["/docker-entrypoint.sh"]
