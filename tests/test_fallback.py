from perplexity_wrapper.client import PerplexityClient
from perplexity_wrapper.errors import PerplexityError
from perplexity_wrapper.models import AskResult


class DummyFallback:
    def answer(self, query: str) -> AskResult:
        return AskResult(answer=f"fallback:{query}", confidence=0.2)


def test_client_uses_fallback_on_perplexity_error() -> None:
    client = PerplexityClient(
        api_key="test-key",
        base_url="https://example.invalid",
        fallback_provider=DummyFallback(),
    )

    def _boom(*_args, **_kwargs):
        raise PerplexityError(message="boom", retryable=True, status_code=503)

    client._request = _boom  # type: ignore[method-assign]

    out = client.ask("hello", enable_fallback=True)
    assert out.answer == "fallback:hello"


def test_client_raises_when_fallback_disabled() -> None:
    client = PerplexityClient(
        api_key="test-key",
        base_url="https://example.invalid",
        fallback_provider=DummyFallback(),
    )

    def _boom(*_args, **_kwargs):
        raise PerplexityError(message="boom", retryable=False, status_code=400)

    client._request = _boom  # type: ignore[method-assign]

    try:
        client.ask("hello", enable_fallback=False)
        assert False, "Expected PerplexityError"
    except PerplexityError:
        assert True
