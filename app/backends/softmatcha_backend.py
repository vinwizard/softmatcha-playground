from __future__ import annotations

import re
import shlex
import subprocess
from pathlib import Path
import shutil

from app.backends.base import BackendExecutionError, SearchBackend
from app.models import CorpusUploadResponse, MatchItem, SearchResponse

ANSI_ESCAPE_RE = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")
SEARCH_ROW_RE = re.compile(
    r"^\|\s*(?P<rank>\d+)\s*\|\s*(?P<score>\d+(?:\.\d+)?)\s*\|\s*(?P<match_count>[\d,]+)\s*\|\s*(?P<text>.+?)\s*$"
)
EXACT_ROW_RE = re.compile(r"^\[(?P<rank>\d+)\]\s*(?P<text>.+?)\s*$")


class SoftMatchaSearchBackend(SearchBackend):
    backend_name = "softmatcha"

    def __init__(self, settings) -> None:
        self._project_dir = settings.softmatcha_project_dir
        self._corpus_storage_dir = settings.corpus_storage_dir
        self._index_dir = settings.softmatcha_index_dir
        self._index_build_cmd = settings.softmatcha_index_build_cmd
        self._search_cmd = settings.softmatcha_search_cmd
        self._exact_cmd = settings.softmatcha_exact_cmd
        self._index_flag = settings.softmatcha_index_flag
        self._timeout = settings.softmatcha_command_timeout

    def search(self, query: str) -> SearchResponse:
        stdout = self._run_cli(self._search_cmd, query)
        matches = self._parse_search_output(stdout)
        return SearchResponse(query=query, backend=self.backend_name, matches=matches, raw_output=stdout)

    def exact(self, query: str) -> SearchResponse:
        stdout = self._run_cli(self._exact_cmd, query)
        matches = self._parse_exact_output(stdout)
        return SearchResponse(query=query, backend=self.backend_name, matches=matches, raw_output=stdout)

    def upload_corpus(self, filename: str, temp_path: Path) -> CorpusUploadResponse:
        self._corpus_storage_dir.mkdir(parents=True, exist_ok=True)
        target_path = self._corpus_storage_dir / "uploaded_corpus.txt"
        shutil.copyfile(temp_path, target_path)
        stdout = self._run_index_build(target_path)
        return CorpusUploadResponse(
            status="ok",
            backend=self.backend_name,
            filename=filename,
            corpus_path=str(target_path),
            index_path=self._index_dir,
            message="Uploaded txt corpus and rebuilt the SoftMatcha index.",
            raw_output=stdout,
        )

    def _run_cli(self, base_command: str, query: str) -> str:
        command = shlex.split(base_command) + [self._index_flag, self._index_dir, query]
        return self._run_command(command)

    def _run_index_build(self, corpus_path: Path) -> str:
        command = shlex.split(self._index_build_cmd) + [self._index_flag, self._index_dir, str(corpus_path)]
        return self._run_command(command)

    def _run_command(self, command: list[str]) -> str:
        try:
            completed = subprocess.run(
                command,
                cwd=self._project_dir,
                capture_output=True,
                text=True,
                timeout=self._timeout,
                check=False,
            )
        except FileNotFoundError as exc:
            raise BackendExecutionError(f"SoftMatcha command not found: {command[0]}") from exc
        except subprocess.TimeoutExpired as exc:
            raise BackendExecutionError(f"SoftMatcha command timed out after {self._timeout} seconds") from exc

        stdout = self._clean_output(completed.stdout)
        stderr = self._clean_output(completed.stderr)
        if completed.returncode != 0:
            detail = stderr or stdout or f"SoftMatcha command exited with status {completed.returncode}"
            raise BackendExecutionError(detail)
        return stdout

    @staticmethod
    def _clean_output(output: str) -> str:
        return ANSI_ESCAPE_RE.sub("", output).strip()

    def _parse_search_output(self, stdout: str) -> list[MatchItem]:
        matches: list[MatchItem] = []
        for line in stdout.splitlines():
            match = SEARCH_ROW_RE.match(line.strip())
            if not match:
                continue
            score_value = None
            try:
                score_value = round(float(match.group("score")) / 100.0, 4)
            except ValueError:
                score_value = None
            rank = int(match.group("rank"))
            matches.append(
                MatchItem(
                    id=f"s{rank}",
                    text=match.group("text"),
                    score=score_value,
                    match_type="soft",
                    source=self._index_dir,
                    metadata={
                        "rank": rank,
                        "match_count": int(match.group("match_count").replace(",", "")),
                    },
                )
            )
        return matches

    def _parse_exact_output(self, stdout: str) -> list[MatchItem]:
        matches: list[MatchItem] = []
        lines = stdout.splitlines()
        index = 0
        while index < len(lines):
            current = lines[index].strip()
            match = EXACT_ROW_RE.match(current)
            if not match:
                index += 1
                continue

            rank = int(match.group("rank"))
            text = match.group("text")
            metadata = {"rank": rank}
            context_parts = self._split_context(text)
            if context_parts is not None:
                metadata["left_context"], metadata["right_context"] = context_parts

            matches.append(
                MatchItem(
                    id=f"e{rank}",
                    text=text,
                    score=1.0,
                    match_type="exact",
                    source=self._index_dir,
                    metadata=metadata,
                )
            )
            index += 1
        return matches

    @staticmethod
    def _split_context(text: str) -> tuple[str, str] | None:
        if not text:
            return None
        midpoint = len(text) // 2
        split_at = text.rfind(" ", 0, midpoint)
        if split_at <= 0 or split_at >= len(text) - 1:
            return None
        return text[:split_at], text[split_at + 1 :]
