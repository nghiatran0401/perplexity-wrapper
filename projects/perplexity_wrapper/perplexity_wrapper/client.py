import os
from typing import Any

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from .models import AskResult, Source


class PerplexityClient:
    """Thin resilient client for Perplexity Chat Completions API."""

    def __init__(self, api_key: str | None = None, timeout_s: float = 20.0):
        self.api_key = api_key or os.getenv("PERPLEXITY_API_KEY")
        if not self.api_key:
            raise ValueError("PERPLEXITY_API_KEY is required")

        self.timeout_s = timeout_s
        self.base_url = "https://api.perplexity.ai"

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.TransportError)),
        reraise=True,
    )
    def ask(self, query: str, model: str = "sonar-pro") -> AskResult:
        if not query.strip():
            raise ValueError("query must not be empty")

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

        with httpx.Client(timeout=self.timeout_s) as client:
            response = client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        answer = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
        citations = data.get("citations", []) or []
        sources = [
            Source(url=url)
            for url in citations
            if isinstance(url, str) and url.startswith(("http://", "https://"))
        ]

        confidence = 0.8 if len(sources) >= 2 else (0.6 if len(sources) == 1 else 0.4)

        if not answer:
            raise ValueError("Empty answer from Perplexity")

        return AskResult(answer=answer, sources=sources, confidence=confidence, raw=data)
