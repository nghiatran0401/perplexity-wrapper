from perplexity_wrapper.errors import PerplexityError


def test_error_string_has_fields() -> None:
    err = PerplexityError(
        message="failed",
        retryable=True,
        status_code=429,
        reason="rate_limit",
    )
    s = str(err)
    assert "failed" in s
    assert "status=429" in s
    assert "retryable=true" in s
    assert "reason=rate_limit" in s
