from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.backends.base import BackendExecutionError
from app.config import get_backend, get_settings
from app.models import CorpusUploadResponse, HealthResponse, SearchResponse

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI(title="SoftMatcha Playground", version="0.1.0")
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.exception_handler(BackendExecutionError)
async def backend_execution_error_handler(_, exc: BackendExecutionError) -> JSONResponse:
    return JSONResponse(status_code=502, content={"detail": str(exc)})


def _validate_query(query: str) -> str:
    trimmed = query.strip()
    if not trimmed:
        raise HTTPException(status_code=400, detail="Query parameter 'q' must not be empty")
    return trimmed


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(status="ok", backend=settings.backend_mode)


@app.get("/search", response_model=SearchResponse)
async def search(q: str = Query(..., description="Search query")) -> SearchResponse:
    backend = get_backend()
    return backend.search(_validate_query(q))


@app.get("/exact", response_model=SearchResponse)
async def exact(q: str = Query(..., description="Exact match query")) -> SearchResponse:
    backend = get_backend()
    return backend.exact(_validate_query(q))


@app.post("/corpus/upload", response_model=CorpusUploadResponse)
async def upload_corpus(file: UploadFile = File(...)) -> CorpusUploadResponse:
    if not file.filename or not file.filename.lower().endswith(".txt"):
        raise HTTPException(status_code=400, detail="Only .txt corpus uploads are supported")

    suffix = Path(file.filename).suffix or ".txt"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_path = Path(temp_file.name)
        temp_file.write(await file.read())

    try:
        payload = get_backend().upload_corpus(file.filename, temp_path)
    finally:
        temp_path.unlink(missing_ok=True)
        await file.close()

    return payload
