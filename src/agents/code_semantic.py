"""Local semantic search over Python symbol chunks using the existing BGE-M3 embedding."""

from __future__ import annotations

import ast
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from agents.code_intel import SKIP_DIRS
from agents.code_tools import PROJECT_ROOT


@dataclass(frozen=True)
class CodeChunk:
    path: str
    line: int
    symbol: str
    text: str

    @property
    def document(self) -> str:
        return f"{self.path} {self.symbol}\n{self.text}"


def code_chunks(root: Path | None = None) -> list[CodeChunk]:
    base = Path(root or PROJECT_ROOT)
    chunks: list[CodeChunk] = []
    for path in base.rglob("*.py"):
        if any(part in SKIP_DIRS for part in path.relative_to(base).parts):
            continue
        source = path.read_text(encoding="utf-8", errors="replace")
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
        rel = path.relative_to(base).as_posix()
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                text = ast.get_source_segment(source, node) or ""
                chunks.append(CodeChunk(rel, node.lineno, node.name, text[:4000]))
    return chunks


def _cosine(left: list[float], right: list[float]) -> float:
    dot = sum(a * b for a, b in zip(left, right))
    scale = math.sqrt(sum(a * a for a in left) * sum(b * b for b in right))
    return dot / scale if scale else 0.0


def semantic_search(
    query: str,
    root: Path | None = None,
    limit: int = 10,
    embedding_function: Any | None = None,
) -> str:
    chunks = code_chunks(root)
    if not query.strip() or not chunks:
        return f"no semantic matches: {query}"
    if embedding_function is None:
        from agents.tools import get_embeddings

        embedding_function = get_embeddings()
    vectors = embedding_function.embed_documents([chunk.document for chunk in chunks])
    query_vector = embedding_function.embed_query(query)
    ranked = sorted(
        ((_cosine(query_vector, vector), chunk) for chunk, vector in zip(chunks, vectors)),
        key=lambda item: item[0],
        reverse=True,
    )[: max(1, limit)]
    return "\n".join(
        f"{chunk.path}:{chunk.line} semantic {chunk.symbol} score={score:.4f}"
        for score, chunk in ranked
    )


__all__ = ["CodeChunk", "code_chunks", "semantic_search"]
