import hashlib
import json
import sqlite3
import time
from pathlib import Path

from .models import AskResult, Source


class SQLiteCache:
    def __init__(self, db_path: str = ".perplexity_cache.sqlite"):
        self.db_path = Path(db_path)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    created_at INTEGER NOT NULL
                )
                """
            )
            conn.commit()

    @staticmethod
    def _key(query: str, model: str) -> str:
        normalized = " ".join(query.strip().lower().split())
        return hashlib.sha256(f"{model}:{normalized}".encode("utf-8")).hexdigest()

    def get(self, query: str, model: str, ttl_s: int) -> AskResult | None:
        if ttl_s <= 0:
            return None

        key = self._key(query, model)
        now = int(time.time())
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT value, created_at FROM cache WHERE key = ?",
                (key,),
            ).fetchone()

        if not row:
            return None

        value_json, created_at = row
        if now - int(created_at) >= ttl_s:
            return None

        payload = json.loads(value_json)
        sources = [Source(**s) for s in payload.get("sources", [])]
        return AskResult(
            answer=payload["answer"],
            sources=sources,
            confidence=payload.get("confidence", 0.5),
            raw=payload.get("raw", {}),
        )

    def set(self, query: str, model: str, result: AskResult) -> None:
        key = self._key(query, model)
        payload = {
            "answer": result.answer,
            "sources": [{"url": s.url, "title": s.title} for s in result.sources],
            "confidence": result.confidence,
            "raw": result.raw,
        }
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO cache (key, value, created_at) VALUES (?, ?, ?)",
                (key, json.dumps(payload), int(time.time())),
            )
            conn.commit()
