# SoftMatcha Playground Repo Guide

## Purpose

This repository is a wrapper application around an existing SoftMatcha 2 installation.

It is intentionally separate from the upstream `softmatcha2` repo. The code here owns:

- the FastAPI app
- the backend abstraction layer
- the mock backend for local development
- the subprocess adapter for the real SoftMatcha CLI
- the static frontend
- deployment assets such as reverse proxy and service configs

It does not own or reimplement the SoftMatcha algorithm itself.

## Repo Rules

- Keep this repo independent from `softmatcha2`
- Do not copy upstream SoftMatcha source into this repo unless explicitly requested
- Preserve the stable JSON contract for `/search` and `/exact`
- Prefer environment-variable configuration over hardcoded machine-specific paths
- Treat `mock` mode and `softmatcha` mode as interchangeable backend providers behind one API contract
- Keep upload support txt-only unless requirements change
- keep the UI explicit about user-selectable modes; `/search`, `/soft`, and `/exact` may share implementation internally, but the interface should keep those choices visible

## Current Structure

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
    upload.html
    app.js
    upload.js
    styles.css
  deploy/
    nginx/
    caddy/
    systemd/
  scripts/
    deploy_gcp.sh
  data/
    corpora/
  requirements.txt
  README.md
  AGENTS.md
  .env.example
  .gitignore
```

## Ownership By Area

- `app/`
  FastAPI routes, data models, configuration, and backend implementations
- `frontend/`
  browser UI for search and upload, split across separate pages
- `deploy/`
  infrastructure-facing configs for reverse proxies and service management
- `scripts/`
  operator helpers such as the VM-side GCP deployment script
- `data/corpora/`
  runtime upload storage only; generated/runtime content, not source-controlled

## Behavioral Expectations

- `mock` mode must work locally without requiring a real SoftMatcha install
- `softmatcha` mode may shell out to the real CLI using subprocess calls
- uploads in `mock` mode affect the local mock corpus only
- uploads in `softmatcha` mode store the uploaded txt corpus and rebuild the configured SoftMatcha index
- keep upload isolated on its own page rather than mixing search and corpus-management controls in one view
- reverse proxy configs must forward both frontend traffic and API/upload traffic to the FastAPI app
- the Caddy config is the preferred website-facing config and should stay domain-ready with a clear placeholder host
- the checked-in deploy script should remain aligned with the current VM-side restart flow, Caddy reload flow, and service name
- `scripts/deploy_gcp.sh` is a VM-side deployment helper
- request-path and subprocess logging should remain explicit enough to debug whether `/search` or `/exact` was invoked and which SoftMatcha CLI command ran
- rotating file logging should remain enabled by default, with runtime log files kept out of version control
- soft-search CLI tuning that affects behavior, such as minimum similarity, should be explicit and env-configurable rather than left implicit in CLI defaults

## Documentation Rule

When the repository behavior, structure, deployment flow, environment variables, or public API changes:

- update `README.md`
- update `AGENTS.md`

Do not treat one as optional. They should stay aligned:

- `README.md` explains usage and operator-facing setup
- `AGENTS.md` explains repo intent, structure, constraints, and maintenance rules

When domain, reverse proxy, or public website setup changes, update both docs and the checked-in proxy config together.

## Preferred Future Additions

- add automated tests before major backend or upload changes
- keep deployment examples production-oriented but minimal
- if the repo grows substantially, consider a `tests/` directory and a packaging-oriented Python layout
