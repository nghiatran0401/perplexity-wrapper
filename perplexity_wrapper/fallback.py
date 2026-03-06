from typing import Protocol

import httpx

from .models import AskResult, Source


class FallbackProvider(Protocol):
    def answer(self, query: str) -> AskResult: ...


class DuckDuckGoFallback:
    """Very lightweight no-key fallback provider using DuckDuckGo Instant Answer API."""

    def __init__(self, timeout_s: float = 10.0):
        self.timeout_s = timeout_s

    def answer(self, query: str) -> AskResult:
        params = {
            "q": query,
            "format": "json",
            "no_redirect": 1,
            "no_html": 1,
            "skip_disambig": 0,
        }
        with httpx.Client(timeout=self.timeout_s) as client:
            response = client.get("https://api.duckduckgo.com/", params=params)
            response.raise_for_status()
            data = response.json()

        abstract = (data.get("AbstractText") or "").strip()
        abstract_url = data.get("AbstractURL")

        if abstract:
            sources = [Source(url=abstract_url)] if isinstance(abstract_url, str) and abstract_url.startswith(("http://", "https://")) else []
            return AskResult(answer=abstract, sources=sources, confidence=0.35, raw=data)

        related = data.get("RelatedTopics") or []
        snippets: list[str] = []
        source_url = None
        for topic in related:
            if isinstance(topic, dict) and topic.get("Text"):
                snippets.append(topic["Text"])
                first_url = topic.get("FirstURL")
                if not source_url and isinstance(first_url, str):
                    source_url = first_url
            if len(snippets) >= 3:
                break

        if snippets:
            text = " ".join(snippets)
            sources = [Source(url=source_url)] if isinstance(source_url, str) and source_url.startswith(("http://", "https://")) else []
            return AskResult(answer=text, sources=sources, confidence=0.25, raw=data)

        return AskResult(
            answer="No reliable fallback answer found.",
            sources=[],
            confidence=0.1,
            raw=data,
        )
