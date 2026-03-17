from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil

from app.backends.base import SearchBackend
from app.models import CorpusUploadResponse, MatchItem, SearchResponse


@dataclass(frozen=True)
class MockDocument:
    id: str
    text: str
    source: str


MOCK_CORPUS: tuple[MockDocument, ...] = (
    MockDocument("m1", "What is the capital of France?", "mock_corpus.txt"),
    MockDocument("m2", "Paris is the capital of France.", "mock_corpus.txt"),
    MockDocument("m3", "France is a country in Western Europe.", "mock_corpus.txt"),
    MockDocument("m4", "Berlin is the capital of Germany.", "mock_corpus.txt"),
    MockDocument("m5", "Madrid is the capital of Spain.", "mock_corpus.txt"),
    MockDocument("m6", "The Eiffel Tower is one of the most famous landmarks in Paris.", "mock_corpus.txt"),
)


class MockSearchBackend(SearchBackend):
    backend_name = "mock"

    def __init__(self, settings) -> None:
        self._result_limit = max(1, settings.mock_result_count)
        self._corpus_storage_dir = settings.corpus_storage_dir

    def search(self, query: str) -> SearchResponse:
        ranked = self._rank_documents(query)
        matches = [
            MatchItem(
                id=document.id,
                text=document.text,
                score=score,
                match_type="soft",
                source=document.source,
                metadata={"rank": index},
            )
            for index, (document, score) in enumerate(ranked[: self._result_limit], start=1)
        ]
        return SearchResponse(query=query, backend=self.backend_name, matches=matches, raw_output=None)

    def exact(self, query: str) -> SearchResponse:
        normalized = query.casefold()
        matches: list[MatchItem] = []
        for document in self._get_corpus():
            position = document.text.casefold().find(normalized)
            if position < 0:
                continue
            left = document.text[max(0, position - 20) : position]
            right_start = position + len(query)
            right = document.text[right_start : right_start + 20]
            matches.append(
                MatchItem(
                    id=f"e{len(matches) + 1}",
                    text=document.text,
                    score=1.0,
                    match_type="exact",
                    source=document.source,
                    metadata={
                        "rank": len(matches) + 1,
                        "left_context": left,
                        "right_context": right,
                    },
                )
            )
            if len(matches) >= min(3, self._result_limit):
                break

        return SearchResponse(query=query, backend=self.backend_name, matches=matches, raw_output=None)

    def upload_corpus(self, filename: str, temp_path: Path) -> CorpusUploadResponse:
        self._corpus_storage_dir.mkdir(parents=True, exist_ok=True)
        target_path = self._corpus_storage_dir / "uploaded_corpus.txt"
        shutil.copyfile(temp_path, target_path)
        corpus_size = len(self._load_uploaded_corpus(target_path))
        return CorpusUploadResponse(
            status="ok",
            backend=self.backend_name,
            filename=filename,
            corpus_path=str(target_path),
            index_path=None,
            message=f"Uploaded txt corpus for mock mode with {corpus_size} searchable lines.",
            raw_output=None,
        )

    def _rank_documents(self, query: str) -> list[tuple[MockDocument, float]]:
        query_terms = {token for token in query.casefold().split() if token}
        if not query_terms:
            return []

        ranked: list[tuple[MockDocument, float]] = []
        for document in self._get_corpus():
            doc_terms = set(document.text.casefold().replace("?", "").replace(".", "").split())
            overlap = len(query_terms & doc_terms)
            if overlap == 0:
                continue
            coverage = overlap / len(query_terms)
            contains_full_query = query.casefold() in document.text.casefold()
            score = min(0.99, round(0.55 + coverage * 0.35 + (0.08 if contains_full_query else 0.0), 2))
            ranked.append((document, score))

        ranked.sort(key=lambda item: (-item[1], item[0].id))
        return ranked

    def _get_corpus(self) -> tuple[MockDocument, ...]:
        uploaded = self._load_uploaded_corpus(self._corpus_storage_dir / "uploaded_corpus.txt")
        return uploaded or MOCK_CORPUS

    @staticmethod
    def _load_uploaded_corpus(path: Path) -> tuple[MockDocument, ...]:
        if not path.exists():
            return ()

        documents: list[MockDocument] = []
        for index, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            line = raw_line.strip()
            if not line:
                continue
            documents.append(MockDocument(f"u{index}", line, path.name))
        return tuple(documents)
