from dataclasses import dataclass


@dataclass(slots=True)
class PerplexityError(Exception):
    message: str
    retryable: bool = False
    status_code: int | None = None
    reason: str | None = None

    def __str__(self) -> str:
        code = f" status={self.status_code}" if self.status_code is not None else ""
        retry = " retryable=true" if self.retryable else " retryable=false"
        reason = f" reason={self.reason}" if self.reason else ""
        return f"{self.message}{code}{retry}{reason}"
