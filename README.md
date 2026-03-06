# Perplexity Wrapper (Python)

A small, resilient wrapper around Perplexity Chat Completions.

## Why this exists
- Keeps your app code stable behind one adapter (`PerplexityClient`)
- Returns typed output (`answer`, `sources`, `confidence`)
- Handles retry/timeout for transient network failures

## Setup
```bash
cd projects/perplexity_wrapper
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export PERPLEXITY_API_KEY=your_key_here
pytest -q
```

## Usage
```python
from perplexity_wrapper.client import PerplexityClient

client = PerplexityClient()
result = client.ask("Latest updates in Llama ecosystem?")

print(result.answer)
print([str(s.url) for s in result.sources])
print(result.confidence)
```

## Notes
- This package is intentionally minimal.
- API response shapes can evolve; validate with integration tests in your app.
- Never log or hardcode API keys.
