from perplexity_wrapper.models import AskResult


def test_contract_shape() -> None:
    obj = AskResult(answer="hello", confidence=0.7)
    assert obj.answer == "hello"
    assert 0 <= obj.confidence <= 1
    assert obj.sources == []


def test_contract_rejects_invalid_confidence() -> None:
    try:
        AskResult(answer="ok", confidence=1.2)
        assert False, "Expected ValueError"
    except ValueError:
        assert True
