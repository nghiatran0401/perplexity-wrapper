from perplexity_wrapper.cache import SQLiteCache
from perplexity_wrapper.models import AskResult


def test_cache_roundtrip(tmp_path) -> None:
    db = tmp_path / "cache.sqlite"
    cache = SQLiteCache(str(db))

    query = "What is perplexity ai?"
    model = "sonar-pro"
    value = AskResult(answer="test answer", confidence=0.6)

    cache.set(query, model, value)
    out = cache.get(query, model, ttl_s=60)

    assert out is not None
    assert out.answer == "test answer"
    assert out.confidence == 0.6


def test_cache_expired(tmp_path) -> None:
    db = tmp_path / "cache.sqlite"
    cache = SQLiteCache(str(db))

    query = "q"
    model = "m"
    value = AskResult(answer="x")
    cache.set(query, model, value)

    assert cache.get(query, model, ttl_s=0) is None
