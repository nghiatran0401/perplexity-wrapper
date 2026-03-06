# Perplexity Wrapper (Python)

A small, resilient wrapper around Perplexity Chat Completions.

## Why this exists
- Keeps your app code stable behind one adapter (`PerplexityClient`)
- Returns typed output (`answer`, `sources`, `confidence`)
- Handles retry/timeout for transient network failures
- Adds SQLite cache to reduce cost/latency
- Includes DuckDuckGo fallback when Perplexity is unavailable

## Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export PERPLEXITY_API_KEY=your_key_here
pytest -q
```

## CLI usage
```bash
python -m perplexity_wrapper "Latest updates in Llama ecosystem?"
python -m perplexity_wrapper "What is RAG?" --model sonar-pro --cache-ttl 600
```

If Perplexity fails, the client can fallback to DuckDuckGo by default.

## Library usage
```python
from perplexity_wrapper.client import PerplexityClient
from perplexity_wrapper.errors import PerplexityError

client = PerplexityClient()

try:
    result = client.ask("Latest updates in Llama ecosystem?", cache_ttl_s=600)
    print(result.answer)
    print([str(s.url) for s in result.sources])
    print(result.confidence)
except PerplexityError as err:
    print(err.retryable, err.status_code, err.reason)
```

## Notes
- This package is intentionally minimal.
- API response shapes can evolve; validate with integration tests in your app.
- Never log or hardcode API keys.
