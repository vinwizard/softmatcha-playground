from __future__ import annotations

import logging
import tempfile
from logging.handlers import RotatingFileHandler
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.backends.base import BackendExecutionError
from app.config import get_backend, get_settings
from app.models import CorpusUploadResponse, HealthResponse, SearchResponse

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
logger = logging.getLogger("softmatcha_playground")

def _configure_logging() -> None:
    settings = get_settings()
    settings.log_dir.mkdir(parents=True, exist_ok=True)
    formatter = logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level, logging.INFO))
    root_logger.handlers.clear()

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    file_handler = RotatingFileHandler(
        settings.log_dir / "app.log",
        maxBytes=settings.log_max_bytes,
        backupCount=settings.log_backup_count,
    )
    file_handler.setFormatter(formatter)

    root_logger.addHandler(stream_handler)
    root_logger.addHandler(file_handler)


_configure_logging()

app = FastAPI(title="SoftMatcha Playground", version="0.1.0")
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.exception_handler(BackendExecutionError)
async def backend_execution_error_handler(_, exc: BackendExecutionError) -> JSONResponse:
    logger.exception("Backend execution failed: %s", exc)
    return JSONResponse(status_code=502, content={"detail": str(exc)})


def _validate_query(query: str) -> str:
    trimmed = query.strip()
    if not trimmed:
        raise HTTPException(status_code=400, detail="Query parameter 'q' must not be empty")
    return trimmed


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/upload", include_in_schema=False)
async def upload_page() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "upload.html")


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    settings = get_settings()
    logger.info("Health check requested; backend_mode=%s", settings.backend_mode)
    return HealthResponse(status="ok", backend=settings.backend_mode)


@app.get("/search", response_model=SearchResponse)
async def search(q: str = Query(..., description="Search query")) -> SearchResponse:
    backend = get_backend()
    query = _validate_query(q)
    logger.info("Search endpoint hit; backend=%s query=%r", backend.backend_name, query)
    return backend.search(query)


@app.get("/soft", response_model=SearchResponse)
async def soft(q: str = Query(..., description="Soft search query")) -> SearchResponse:
    backend = get_backend()
    query = _validate_query(q)
    logger.info("Soft endpoint hit; backend=%s query=%r", backend.backend_name, query)
    return backend.search(query)


@app.get("/exact", response_model=SearchResponse)
async def exact(q: str = Query(..., description="Exact match query")) -> SearchResponse:
    backend = get_backend()
    query = _validate_query(q)
    logger.info("Exact endpoint hit; backend=%s query=%r", backend.backend_name, query)
    return backend.exact(query)


@app.post("/corpus/upload", response_model=CorpusUploadResponse)
async def upload_corpus(file: UploadFile = File(...)) -> CorpusUploadResponse:
    if not file.filename or not file.filename.lower().endswith(".txt"):
        raise HTTPException(status_code=400, detail="Only .txt corpus uploads are supported")
    logger.info("Corpus upload requested; filename=%s", file.filename)

    suffix = Path(file.filename).suffix or ".txt"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_path = Path(temp_file.name)
        temp_file.write(await file.read())

    try:
        payload = get_backend().upload_corpus(file.filename, temp_path)
    finally:
        temp_path.unlink(missing_ok=True)
        await file.close()

    logger.info(
        "Corpus upload completed; backend=%s filename=%s corpus_path=%s index_path=%s",
        payload.backend,
        payload.filename,
        payload.corpus_path,
        payload.index_path,
    )
    return payload
