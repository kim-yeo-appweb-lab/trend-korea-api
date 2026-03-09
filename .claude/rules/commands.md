## 의존성 설치

```bash
uv sync
uv sync --extra crawler
uv sync --extra summarizer
uv sync --extra crawler --extra summarizer
```

## 크롤러/파이프라인

```bash
uv run trend-korea-crawl-keywords --top-n 30 --save-db
uv run trend-korea-crawl-news --keyword "키워드" --limit 3
uv run trend-korea-summarize-news --input news.json --model gemma3:4b
uv run trend-korea-crawl-naver-news "반도체" "AI" --display 10 --save-db
uv run trend-korea-crawl-products --max-pages 2 --save-db
uv run trend-korea-full-cycle --repeat 1 --max-keywords 3
```

## 테스트/린트

```bash
uv run pytest
uv run pytest tests/test_auth.py -v
uv run pytest --cov=src
uv run ruff check src/
uv run ruff format src/
```

## DB 마이그레이션

```bash
uv run alembic upgrade head
uv run alembic revision --autogenerate -m "설명"
```

필수 환경변수: `DATABASE_URL`
