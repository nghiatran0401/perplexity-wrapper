from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass(slots=True)
class Source:
    url: str
    title: Optional[str] = None


@dataclass(slots=True)
class AskResult:
    answer: str
    sources: list[Source] = field(default_factory=list)
    confidence: float = 0.5
    raw: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.answer or not self.answer.strip():
            raise ValueError("answer must not be empty")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
