# SoftMatcha Playground

Small wrapper app around SoftMatcha 2 with a stable FastAPI contract and a plain HTML frontend.

## Files

- `app/main.py`: FastAPI app, API routes, static frontend serving, and backend error handling.
- `app/config.py`: Environment-backed settings and backend factory.
- `app/models.py`: Shared response models for `/health`, `/search`, and `/exact`.
- `app/backends/base.py`: Abstract backend interface and backend execution error type.
- `app/backends/mock_backend.py`: Deterministic local development backend with fake ranked results.
- `app/backends/softmatcha_backend.py`: Real backend that shells out to the SoftMatcha CLI and parses text output into the stable response schema.
- `frontend/index.html`: Minimal UI shell.
- `frontend/app.js`: Client-side request flow and result rendering.
- `frontend/styles.css`: Visual styling for the frontend.
- `requirements.txt`: Wrapper app dependencies.
- `.env.example`: Suggested environment variables for local and GCP use.

## Response Contract

Both `/search` and `/exact` return:

```json
{
  "query": "capital of France",
  "backend": "mock",
  "matches": [
    {
      "id": "m1",
      "text": "What is the capital of France?",
      "score": 0.94,
      "match_type": "soft",
      "source": "mock_corpus.txt",
      "metadata": {
        "rank": 1
      }
    }
  ],
  "raw_output": null
}
```

In `softmatcha` mode, `raw_output` contains the cleaned CLI stdout so the outer schema stays stable even if parsing is partial.

## Environment Variables

- `BACKEND_MODE`: `mock` or `softmatcha`
- `HOST`: bind host for `uvicorn`
- `PORT`: bind port for `uvicorn`
- `SOFTMATCHA_PROJECT_DIR`: path to the working SoftMatcha repo on GCP
- `SOFTMATCHA_INDEX_DIR`: index directory passed to the CLI
- `SOFTMATCHA_SEARCH_CMD`: search command prefix
- `SOFTMATCHA_EXACT_CMD`: exact command prefix
- `SOFTMATCHA_INDEX_FLAG`: index flag, defaults to `--index`
- `SOFTMATCHA_COMMAND_TIMEOUT`: subprocess timeout in seconds
- `MOCK_RESULT_COUNT`: number of fake matches returned in mock mode

## Local Development

```bash
cd ~/softmatcha-playground
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
export BACKEND_MODE=mock
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Then open `http://127.0.0.1:8000`.

## GCP Run Mode

Keep this repo separate from the existing SoftMatcha install, then sync only this directory:

```bash
rsync -avz ~/softmatcha-playground user@your-vm:~/
```

On the VM:

```bash
cd ~/softmatcha-playground
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export BACKEND_MODE=softmatcha
export SOFTMATCHA_PROJECT_DIR=~/softmatcha2
export SOFTMATCHA_INDEX_DIR=corpus_index
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

If your installed CLI needs a different flag or command form, override:

```bash
export SOFTMATCHA_INDEX_FLAG=--index
export SOFTMATCHA_SEARCH_CMD='uv run softmatcha-search'
export SOFTMATCHA_EXACT_CMD='uv run softmatcha-exact'
```
