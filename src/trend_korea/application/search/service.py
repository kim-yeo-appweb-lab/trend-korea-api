from trend_korea.core.pagination import decode_cursor, encode_cursor
from trend_korea.infrastructure.db.repositories.search_repository import SearchRepository


class SearchService:
    def __init__(self, repository: SearchRepository) -> None:
        self.repository = repository

    def search(
        self,
        *,
        q: str,
        entity_type: str,
        sort: str,
        size: int,
        cursor: str | None,
    ) -> tuple[list[dict], str | None, int]:
        offset = decode_cursor(cursor)
        items, next_offset, total_count = self.repository.search(
            q=q,
            entity_type=entity_type,
            sort=sort,
            size=size,
            offset=offset,
        )
        return items, encode_cursor(next_offset) if next_offset is not None else None, total_count

    def suggestions(self, *, q: str, limit: int = 10) -> list[str]:
        return self.repository.suggestions(q=q, limit=limit)

    def rankings(self, *, limit: int = 10) -> list[dict]:
        return self.repository.rankings(limit=limit)
