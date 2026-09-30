"""Task-agnostic source windows from public base failures, without gold patches."""

from __future__ import annotations

import argparse
import ast
import json
import re
from pathlib import Path

from evals.e1c_evidence_v22 import excerpts
from evals.e1c_live_runner import OUT, _manifest, _source

_FRAME = re.compile(r'File "/testbed/([^"\n]+\.py)"')
_WORD = re.compile(r"[a-z][a-z0-9]{3,}")


def _words(value: str) -> set[str]:
    words = _WORD.findall(re.sub(r"(?<=[a-z])(?=[A-Z])", " ", value).replace("_", " ").lower())
    return {word[:-3] + "y" if word.endswith("ies") else word.removesuffix("s").removesuffix("ed")
            for word in words}


def _source_paths(workspace: Path) -> list[str]:
    return [path.relative_to(workspace).as_posix() for path in workspace.rglob("*.py")
            if path.is_file() and not path.is_symlink()
            and path.name not in {"tests.py", "setup.py", "conftest.py"}
            and not path.name.startswith("test_")
            and not any(part in {"tests", "test", "testing", "docs", "examples"}
                        for part in path.relative_to(workspace).parts)]


def _failure_block(base_log: str) -> str:
    position = max(base_log.rfind("\nFAIL:"), base_log.rfind("\nERROR:"))
    if position < 0:
        return base_log[-4500:]
    return base_log[position:position + 4500]


def locate(statement: str, base_log: str, workspace: Path) -> list[dict]:
    """Return only high-confidence paths; abstain instead of a guessed file."""
    block = _failure_block(base_log)
    paths = set(_source_paths(workspace))
    frames = _FRAME.findall(block)
    candidates: dict[str, tuple[int, str]] = {}
    for frame in frames:
        if frame in paths and not frame.startswith(("django/test/", "sphinx/testing/")):
            candidates[frame] = (100, "public_source_traceback")
        if not frame.startswith(("tests/", "test/")):
            continue
        stem = Path(frame).stem.removeprefix("test_")
        if len(stem) < 5:
            continue
        matching = [path for path in paths if Path(path).stem == stem]
        if len(matching) == 1:
            candidates.setdefault(matching[0], (80, "unique_failing_test_stem"))
    # An explicit production path in the issue is stronger than lexical guessing.
    for path in paths:
        if path in statement:
            candidates[path] = (120, "explicit_issue_path")
    return [{"path": path, "confidence": score, "origin": origin}
            for path, (score, origin) in sorted(candidates.items(), key=lambda pair: (-pair[1][0], pair[0]))[:4]]


def windows(statement: str, base_log: str, workspace: Path, *, limit: int = 3) -> list[dict]:
    block = _failure_block(base_log)
    terms = _words(statement[:2500] + "\n" + block[:1800])
    result = []
    for candidate in locate(statement, base_log, workspace):
        path = candidate["path"]
        lines = (workspace / path).read_text(encoding="utf-8", errors="replace").splitlines()
        try:
            tree = ast.parse("\n".join(lines))
        except SyntaxError:
            continue
        functions = [node for node in ast.walk(tree)
                     if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
        ranked = []
        for node in functions:
            name_terms = _words(node.name)
            score = 20 * len(name_terms & terms)
            section = lines[node.lineno - 1:min(node.end_lineno or node.lineno + 50, len(lines))]
            score += min(8, sum(1 for line in section[:100] if _words(line) & terms))
            if score:
                ranked.append((score, node.lineno, node))
        ranked.sort(key=lambda item: (-item[0], item[1]))
        for _, _, node in ranked[:2]:
            start = max(0, node.lineno - 5)
            end = min(len(lines), (node.end_lineno or node.lineno + 50) + 3)
            section = "\n".join(lines[start:end])
            if len(section) > 5000:
                # Preserve a complete scored window, including the operation
                # being changed, rather than chopping a long function at head.
                blocks = [(index, "\n".join(lines[index:min(index + 45, end)]))
                          for index in range(start, end, 30)]
                start, section = max(blocks, key=lambda item: sum(
                    1 for line in item[1].splitlines() if _words(line) & terms))
            result.append({"path": path, "start_line": start + 1, "text": section[:5000],
                           "origin": candidate["origin"]})
            if len(result) >= limit:
                return result
    if result:
        return result
    return [{**item, "origin": "lexical_fallback"} for item in
            excerpts(statement + "\n" + block[:1200], workspace, max_files=limit, max_chars=3000)]


def audit() -> dict:
    rows = []
    for row in _manifest()["tasks"]:
        instance_id = row["instance_id"]
        statement = (OUT / "tasks" / instance_id / "problem_statement.md").read_text(encoding="utf-8")
        log = (OUT / "admission_v2" / instance_id / "base.log").read_text(encoding="utf-8", errors="replace")
        source = _source(row)
        found = locate(statement, log, source)
        excerpts = windows(statement, log, source)
        rows.append({"instance_id": instance_id, "paths": found, "windows": len(excerpts)})
    return {"schema": "e1c-failure-guided-localization-audit-v1", "task_count": len(rows),
            "path_coverage": sum(bool(row["paths"]) for row in rows),
            "window_coverage": sum(bool(row["windows"]) for row in rows), "rows": rows,
            "metric_boundary": "high-confidence path vs fallback evidence coverage only; no gold path/model calls"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("audit",))
    parser.parse_args()
    print(json.dumps(audit(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
