import argparse
import json
import sys

from .client import PerplexityClient
from .errors import PerplexityError


def main() -> int:
    parser = argparse.ArgumentParser(description="Query Perplexity from CLI")
    parser.add_argument("query", help="User query")
    parser.add_argument("--model", default="sonar-pro", help="Perplexity model")
    parser.add_argument("--timeout", type=float, default=20.0, help="HTTP timeout seconds")
    parser.add_argument("--cache-ttl", type=int, default=300, help="Cache TTL seconds")
    args = parser.parse_args()

    client = PerplexityClient(timeout_s=args.timeout)
    try:
        result = client.ask(args.query, model=args.model, cache_ttl_s=args.cache_ttl)
    except PerplexityError as err:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": {
                        "message": err.message,
                        "retryable": err.retryable,
                        "status_code": err.status_code,
                        "reason": err.reason,
                    },
                }
            ),
            file=sys.stderr,
        )
        return 1

    print(
        json.dumps(
            {
                "ok": True,
                "answer": result.answer,
                "sources": [{"title": s.title, "url": s.url} for s in result.sources],
                "confidence": result.confidence,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
