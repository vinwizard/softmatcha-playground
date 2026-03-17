from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from app.models import CorpusUploadResponse, SearchResponse


class BackendExecutionError(RuntimeError):
    """Raised when the underlying backend cannot satisfy a request."""


class SearchBackend(ABC):
    backend_name: str

    @abstractmethod
    def search(self, query: str) -> SearchResponse:
        raise NotImplementedError

    @abstractmethod
    def exact(self, query: str) -> SearchResponse:
        raise NotImplementedError

    @abstractmethod
    def upload_corpus(self, filename: str, temp_path: Path) -> CorpusUploadResponse:
        raise NotImplementedError
