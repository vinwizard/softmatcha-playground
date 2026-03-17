from __future__ import annotations

from abc import ABC, abstractmethod

from app.models import SearchResponse


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
