# SoftMatcha Playground

Small wrapper app around SoftMatcha 2 with a stable FastAPI contract and a plain HTML frontend.

This repo is intentionally separate from the upstream `softmatcha2` codebase. It owns the wrapper product layer, not the underlying SoftMatcha algorithm implementation.

## Repo Structure

```text
softmatcha-playground/
  app/
    main.py
    config.py
    models.py
    backends/
      base.py
      mock_backend.py
      softmatcha_backend.py
  frontend/
    index.html
    app.js
    styles.css
  deploy/
    nginx/
    caddy/
    systemd/
  data/
    corpora/
  requirements.txt
  README.md
  AGENTS.md
  .env.example
```

## Documentation Rule

This repo keeps two top-level docs in sync:

- `README.md` for usage, setup, deployment, and operator-facing instructions
- `AGENTS.md` for repo intent, structure, constraints, and maintenance expectations

When behavior, routes, env vars, deployment files, or repo structure change, update both files in the same change.

## Files

- `app/main.py`: FastAPI app, API routes, static frontend serving, upload handling, and backend error handling.
- `app/config.py`: Environment-backed settings and backend factory.
- `app/models.py`: Shared response models for `/health`, `/search`, and `/exact`.
- `app/backends/base.py`: Abstract backend interface and backend execution error type.
- `app/backends/mock_backend.py`: Deterministic local development backend with fake ranked results.
- `app/backends/softmatcha_backend.py`: Real backend that shells out to the SoftMatcha CLI and parses text output into the stable response schema.
- `frontend/index.html`: Minimal UI shell.
- `frontend/app.js`: Client-side request flow and result rendering.
- `frontend/styles.css`: Visual styling for the frontend.
- `deploy/nginx/softmatcha-playground.conf`: Nginx reverse proxy with request forwarding to `127.0.0.1:8000`.
- `deploy/caddy/Caddyfile`: Caddy reverse proxy with request forwarding to `127.0.0.1:8000`.
- `deploy/systemd/softmatcha-playground.service`: Example `systemd` unit for running the app behind a reverse proxy.
- `data/corpora/`: runtime storage for uploaded txt corpora.
- `requirements.txt`: Wrapper app dependencies.
- `AGENTS.md`: repo-level guidance and maintenance rules.
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
- `CORPUS_STORAGE_DIR`: where uploaded txt corpora are stored by the wrapper
- `SOFTMATCHA_PROJECT_DIR`: path to the working SoftMatcha repo on GCP
- `SOFTMATCHA_INDEX_DIR`: index directory passed to the CLI
- `SOFTMATCHA_INDEX_BUILD_CMD`: index build command prefix
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

The home page also includes a txt-only upload form. In `mock` mode, the uploaded file becomes the active searchable line corpus.

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
export SOFTMATCHA_INDEX_BUILD_CMD='uv run softmatcha-index'
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

For a reverse-proxy deployment, bind the app to localhost instead:

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

If your installed CLI needs a different flag or command form, override:

```bash
export SOFTMATCHA_INDEX_FLAG=--index
export CORPUS_STORAGE_DIR=~/softmatcha-playground/data/corpora
export SOFTMATCHA_SEARCH_CMD='uv run softmatcha-search'
export SOFTMATCHA_EXACT_CMD='uv run softmatcha-exact'
```

## Upload And Reindex

- `POST /corpus/upload` accepts a single `.txt` file
- in `mock` mode, the uploaded file replaces the default mock corpus for search and exact lookup
- in `softmatcha` mode, the uploaded file is stored and immediately passed to `softmatcha-index` to rebuild `SOFTMATCHA_INDEX_DIR`

## Reverse Proxy

Both provided proxy configs forward all requests to the FastAPI app on `127.0.0.1:8000`, including:

- frontend requests like `GET /`
- API requests like `GET /search` and `GET /exact`
- upload requests like `POST /corpus/upload`

### Nginx

Use [`deploy/nginx/softmatcha-playground.conf`](/Users/vinwizard/Documents/Projects/softmatcha-playground/deploy/nginx/softmatcha-playground.conf).

Example install on Debian/GCP:

```bash
sudo apt-get update
sudo apt-get install -y nginx
sudo cp deploy/nginx/softmatcha-playground.conf /etc/nginx/sites-available/softmatcha-playground
sudo ln -s /etc/nginx/sites-available/softmatcha-playground /etc/nginx/sites-enabled/softmatcha-playground
sudo nginx -t
sudo systemctl reload nginx
```

### Caddy

Use [`deploy/caddy/Caddyfile`](/Users/vinwizard/Documents/Projects/softmatcha-playground/deploy/caddy/Caddyfile).

Before deploying it, replace `softmatcha.example.com` in the Caddyfile with your real domain or subdomain.

Example install:

```bash
sudo apt-get update
sudo apt-get install -y caddy
sudo cp deploy/caddy/Caddyfile /etc/caddy/Caddyfile
sudo systemctl reload caddy
```

Once DNS points your domain to the VM, Caddy can provision HTTPS automatically.

## Make It A Website

To expose the app at a real domain instead of a raw VM IP:

1. Buy or choose a domain or subdomain, for example `softmatcha.example.com`
2. Point DNS `A` record for that host to the GCP VM external IP
3. Make sure GCP firewall rules allow inbound `80` and `443`
4. Keep the app running on `127.0.0.1:8000`
5. Update [`deploy/caddy/Caddyfile`](/Users/vinwizard/Documents/Projects/softmatcha-playground/deploy/caddy/Caddyfile) with your real domain
6. Copy that file to `/etc/caddy/Caddyfile` on the VM and reload Caddy

Example DNS target lookup from your local machine:

```bash
gcloud compute instances describe softmatcha-dev \
  --zone "us-west1-a" \
  --project "llm-serving-427823" \
  --format='get(networkInterfaces[0].accessConfigs[0].natIP)'
```

Example GCP firewall rules:

```bash
gcloud compute firewall-rules create allow-http \
  --project "llm-serving-427823" \
  --allow tcp:80 \
  --target-tags=http-server

gcloud compute firewall-rules create allow-https \
  --project "llm-serving-427823" \
  --allow tcp:443 \
  --target-tags=https-server
```

Then add the matching network tags to the VM if needed:

```bash
gcloud compute instances add-tags softmatcha-dev \
  --zone "us-west1-a" \
  --project "llm-serving-427823" \
  --tags=http-server,https-server
```

After DNS propagation, your site should load at:

```text
https://your-domain-or-subdomain
```

### systemd app service

Use [`deploy/systemd/softmatcha-playground.service`](/Users/vinwizard/Documents/Projects/softmatcha-playground/deploy/systemd/softmatcha-playground.service) as a starting point.

Example:

```bash
sudo cp deploy/systemd/softmatcha-playground.service /etc/systemd/system/softmatcha-playground.service
sudo sed -i "s/%i/$USER/g" /etc/systemd/system/softmatcha-playground.service
sudo systemctl daemon-reload
sudo systemctl enable softmatcha-playground
sudo systemctl start softmatcha-playground
sudo systemctl status softmatcha-playground
```
