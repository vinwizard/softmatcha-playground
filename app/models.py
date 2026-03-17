from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class MatchItem(BaseModel):
    id: str
    text: str
    score: float | None = None
    match_type: str
    source: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class SearchResponse(BaseModel):
    query: str
    backend: str
    matches: list[MatchItem] = Field(default_factory=list)
    raw_output: str | None = None


class HealthResponse(BaseModel):
    status: str
    backend: str


class CorpusUploadResponse(BaseModel):
    status: str
    backend: str
    filename: str
    corpus_path: str
    index_path: str | None = None
    message: str
    raw_output: str | None = None
