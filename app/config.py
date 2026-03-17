from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from app.backends.base import SearchBackend
from app.backends.mock_backend import MockSearchBackend
from app.backends.softmatcha_backend import SoftMatchaSearchBackend

VALID_BACKEND_MODES = {"mock", "softmatcha"}


@dataclass(frozen=True)
class Settings:
    base_dir: Path
    backend_mode: str
    host: str
    port: int
    corpus_storage_dir: Path
    softmatcha_project_dir: Path
    softmatcha_index_dir: str
    softmatcha_index_build_cmd: str
    softmatcha_search_cmd: str
    softmatcha_exact_cmd: str
    softmatcha_index_flag: str
    softmatcha_command_timeout: int
    mock_result_count: int


def _get_env(name: str, default: str) -> str:
    value = os.getenv(name, default).strip()
    return value or default


def _expand_path(raw_path: str) -> Path:
    return Path(raw_path).expanduser().resolve()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    backend_mode = _get_env("BACKEND_MODE", "mock").lower()
    if backend_mode not in VALID_BACKEND_MODES:
        allowed = ", ".join(sorted(VALID_BACKEND_MODES))
        raise ValueError(f"Invalid BACKEND_MODE={backend_mode!r}. Expected one of: {allowed}")

    base_dir = Path(__file__).resolve().parent.parent

    return Settings(
        base_dir=base_dir,
        backend_mode=backend_mode,
        host=_get_env("HOST", "127.0.0.1"),
        port=int(_get_env("PORT", "8000")),
        corpus_storage_dir=_expand_path(_get_env("CORPUS_STORAGE_DIR", str(base_dir / "data" / "corpora"))),
        softmatcha_project_dir=_expand_path(_get_env("SOFTMATCHA_PROJECT_DIR", "~/softmatcha2")),
        softmatcha_index_dir=_get_env("SOFTMATCHA_INDEX_DIR", "corpus_index"),
        softmatcha_index_build_cmd=_get_env("SOFTMATCHA_INDEX_BUILD_CMD", "uv run softmatcha-index"),
        softmatcha_search_cmd=_get_env("SOFTMATCHA_SEARCH_CMD", "uv run softmatcha-search"),
        softmatcha_exact_cmd=_get_env("SOFTMATCHA_EXACT_CMD", "uv run softmatcha-exact"),
        softmatcha_index_flag=_get_env("SOFTMATCHA_INDEX_FLAG", "--index"),
        softmatcha_command_timeout=int(_get_env("SOFTMATCHA_COMMAND_TIMEOUT", "30")),
        mock_result_count=int(_get_env("MOCK_RESULT_COUNT", "5")),
    )


@lru_cache(maxsize=1)
def get_backend() -> SearchBackend:
    settings = get_settings()
    if settings.backend_mode == "softmatcha":
        return SoftMatchaSearchBackend(settings)
    return MockSearchBackend(settings)
