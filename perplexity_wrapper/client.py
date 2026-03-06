import os
from typing import Any

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from .cache import SQLiteCache
from .errors import PerplexityError
from .models import AskResult, Source


class PerplexityClient:
    """Thin resilient client for Perplexity Chat Completions API."""

    def __init__(
        self,
        api_key: str | None = None,
        timeout_s: float = 20.0,
        base_url: str = "https://api.perplexity.ai",
        cache_db_path: str = ".perplexity_cache.sqlite",
    ):
        self.api_key = api_key or os.getenv("PERPLEXITY_API_KEY")
        if not self.api_key:
            raise ValueError("PERPLEXITY_API_KEY is required")

        self.timeout_s = timeout_s
        self.base_url = base_url.rstrip("/")
        self.cache = SQLiteCache(cache_db_path)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.TransportError)),
        reraise=True,
    )
    def _request(self, payload: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
        with httpx.Client(timeout=self.timeout_s) as client:
            response = client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
            )

        if response.status_code >= 400:
            retryable = response.status_code in (408, 425, 429, 500, 502, 503, 504)
            raise PerplexityError(
                message="Perplexity API request failed",
                retryable=retryable,
                status_code=response.status_code,
                reason=response.text[:500],
            )

        return response.json()

    def ask(self, query: str, model: str = "sonar-pro", cache_ttl_s: int = 300) -> AskResult:
        if not query.strip():
            raise ValueError("query must not be empty")

        cached = self.cache.get(query, model, ttl_s=cache_ttl_s)
        if cached is not None:
            return cached

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload: dict[str, Any] = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": "Answer with evidence. Include citations when possible.",
                },
                {"role": "user", "content": query},
            ],
        }

        try:
            data = self._request(payload, headers)
        except (httpx.TimeoutException, httpx.TransportError) as exc:
            raise PerplexityError(
                message="Network error calling Perplexity",
                retryable=True,
                reason=str(exc),
            ) from exc

        answer = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
        citations = data.get("citations", []) or []
        sources = [
            Source(url=url)
            for url in citations
            if isinstance(url, str) and url.startswith(("http://", "https://"))
        ]

        confidence = 0.8 if len(sources) >= 2 else (0.6 if len(sources) == 1 else 0.4)

        if not answer:
            raise PerplexityError(
                message="Empty answer from Perplexity",
                retryable=False,
                reason="no_content",
            )

        result = AskResult(answer=answer, sources=sources, confidence=confidence, raw=data)
        self.cache.set(query, model, result)
        return result
