"""Aggregate historical E1-C DEV failure modes without exposing per-task answers to runtime."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

from evals.e1c_admission import ROOT

MANIFEST = ROOT / "data" / "e1c_candidate_manifest.json"
OUT_JSON = ROOT / "data" / "e1c_strict_v5_failure_taxonomy.json"
OUT_CSV = ROOT / "data" / "e1c_strict_v5_failure_taxonomy.csv"
OUT_PARETO = ROOT / "data" / "e1c_strict_v5_failure_pareto.json"

PRIORITY = (
    "provider_or_budget_failure",
    "no_reproducer",
    "wrong_file_or_symbol",
    "window_truncation",
    "invalid_old_match",
    "duplicate_patch",
    "empty_edit_or_abstain",
    "p2p_regression",
    "target_not_fixed",
    "missing_artifact",
    "other_failure",
)


def _text(value: Any) -> str:
    try:
        return json.dumps(value, ensure_ascii=False).lower()
    except TypeError:
        return str(value).lower()


def _failure_text(record: dict) -> str:
    fields = [
        record.get("status"),
        record.get("failure_class"),
        record.get("failure"),
        record.get("error"),
        record.get("stop_reason"),
        record.get("reason"),
        record.get("verification_reasons"),
    ]
    steps = record.get("steps")
    if isinstance(steps, list):
        for step in steps:
            if isinstance(step, dict):
                fields.extend((step.get("action"), step.get("reason"), step.get("error")))
    return _text(fields)


def _has_p2p_regression(record: dict) -> bool:
    text = _failure_text(record)
    if "original_test_regression" in text or "p2p_regression" in text:
        return True
    grades = [
        record.get("grade"),
        record.get("first_grade"),
        record.get("final_grade"),
    ]
    steps = record.get("steps")
    if isinstance(steps, list):
        grades.extend(step for step in steps if isinstance(step, dict))
    for grade in grades:
        if not isinstance(grade, dict):
            continue
        maintained = grade.get("p2p_maintained")
        total = grade.get("p2p_total")
        if isinstance(maintained, int) and isinstance(total, int) and maintained < total:
            return True
    return False


def classify(record: dict) -> set[str]:
    text = _failure_text(record)
    full = _text(record)
    categories: set[str] = set()
    if any(
        token in text
        for token in (
            "provider_error",
            "provider failure",
            "budget_exceeded",
            "token ceiling",
            "over_budget",
            "timeout",
            "interrupted",
            "model_error",
        )
    ):
        categories.add("provider_or_budget_failure")
    if "no_reproducer" in text or "no_candidates" in text:
        categories.add("no_reproducer")
    if any(
        token in text
        for token in (
            "wrong_file",
            "wrong symbol",
            "target path",
            "path_not",
            "path was not exposed",
            "locator_miss",
        )
    ):
        categories.add("wrong_file_or_symbol")
    if any(token in text for token in ("window trunc", "truncated window", "context window")):
        categories.add("window_truncation")
    if "old text must occur exactly once" in text or "old_match" in text:
        categories.add("invalid_old_match")
    if "duplicate_patch" in text or "duplicate patch" in text:
        categories.add("duplicate_patch")
    if any(
        token in text
        for token in ("abstain", "no_edits", "noop", "empty_edit")
    ) or '"edits": []' in full:
        categories.add("empty_edit_or_abstain")
    if _has_p2p_regression(record):
        categories.add("p2p_regression")
    if (
        record.get("resolved") is False
        or "reproducer_still_fails" in text
        or "target_not_fixed" in text
        or "blind_verification_failed" in text
    ):
        categories.add("target_not_fixed")
    return categories or {"other_failure"}


def _primary(categories: set[str]) -> str:
    return next(name for name in PRIORITY if name in categories)


def _manifest_rows() -> list[dict]:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    rows = payload.get("tasks", payload if isinstance(payload, list) else [])
    if not isinstance(rows, list):
        raise ValueError("E1-C candidate manifest tasks missing")
    if len(rows) < 30:
        raise ValueError(f"expected at least 30 historical E1-C tasks, got {len(rows)}")
    return rows[:30]


def _historical_files() -> list[Path]:
    roots = sorted((ROOT / ".codex" / "e1c").glob("e1c-dev-*"))
    files: list[Path] = []
    for root in roots:
        for name in ("state.json", "audit.json", "result.json"):
            path = root / name
            if path.is_file():
                files.append(path)
    c4 = ROOT / ".codex" / "e1c" / "e1c-blind-postb4-c4-v1" / "result.json"
    if c4.is_file():
        files.append(c4)
    return files


def _records_by_id(files: list[Path]) -> dict[str, list[dict]]:
    by_id: dict[str, list[dict]] = {}
    for path in files:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        rows = payload.get("rows", []) if isinstance(payload, dict) else []
        if isinstance(payload, dict) and payload.get("instance_id"):
            rows = [payload]
        if not isinstance(rows, list):
            continue
        for row in rows:
            if not isinstance(row, dict):
                continue
            instance_id = row.get("instance_id") or row.get("task_id")
            if not isinstance(instance_id, str):
                continue
            by_id.setdefault(instance_id, []).append({
                "artifact": path.relative_to(ROOT).as_posix(),
                "record": row,
            })
    return by_id


def build() -> dict:
    tasks = _manifest_rows()
    files = _historical_files()
    records = _records_by_id(files)
    rows = []
    for task in tasks:
        instance_id = task["instance_id"]
        evidence = records.get(instance_id, [])
        if not evidence:
            categories = {"missing_artifact"}
        else:
            categories = set()
            for item in evidence:
                categories.update(classify(item["record"]))
        rows.append({
            "instance_id": instance_id,
            "repo": task.get("repo"),
            "primary_failure": _primary(categories),
            "failure_categories": sorted(categories),
            "artifact_count": len(evidence),
            "artifact_paths": sorted({item["artifact"] for item in evidence}),
        })
    counts = Counter(row["primary_failure"] for row in rows)
    denominator = len(rows)
    return {
        "schema": "e1c-strict-v5-failure-taxonomy-v1",
        "denominator": denominator,
        "provider_calls": 0,
        "runtime_answer_hints_exported": False,
        "rows": rows,
        "primary_counts": dict(sorted(counts.items(), key=lambda item: (-item[1], item[0]))),
        "source_artifact_count": len(files),
    }


def write_outputs() -> dict:
    result = build()
    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with OUT_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=("instance_id", "repo", "primary_failure", "failure_categories", "artifact_count"),
        )
        writer.writeheader()
        for row in result["rows"]:
            writer.writerow({
                **{key: row[key] for key in ("instance_id", "repo", "primary_failure", "artifact_count")},
                "failure_categories": "|".join(row["failure_categories"]),
            })
    pareto = {
        "schema": "e1c-strict-v5-failure-pareto-v1",
        "denominator": result["denominator"],
        "provider_calls": 0,
        "runtime_input": "aggregate_categories_only",
        "categories": [
            {"category": category, "count": count, "share": count / result["denominator"]}
            for category, count in result["primary_counts"].items()
        ],
    }
    OUT_PARETO.write_text(json.dumps(pareto, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "schema": "e1c-strict-v5-failure-taxonomy-write-v1",
        "denominator": result["denominator"],
        "provider_calls": 0,
        "json": OUT_JSON.as_posix(),
        "csv": OUT_CSV.as_posix(),
        "pareto": OUT_PARETO.as_posix(),
        "primary_counts": result["primary_counts"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("build",))
    parser.parse_args()
    print(json.dumps(write_outputs(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
