"""Freeze a strict-v8 metadata-only canary after mechanism preregistration."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from evals.e1c_admission import ROOT
from evals.e1c_strict_v8_selection_boundary import build as build_boundary

OUT = ROOT / "data" / "e1c_strict_v8_canary_manifest.json"
PREREG = ROOT / "data" / "e1c_strict_v8_prereg.json"
REQUIRED = ("instance_id", "repo", "base_commit", "image")
SALT = "e1c-strict-v8-independent-canary"


def denylist() -> frozenset[str]:
    boundary = build_boundary()
    return frozenset(boundary["explicit_prior_canary_exclusions"])


def freeze(rows: list[dict], *, source_revision: str, output: Path = OUT) -> dict:
    prereg = json.loads(PREREG.read_text(encoding="utf-8"))
    if prereg.get("selection_salt") != SALT or prereg.get("canary_selected_at_freeze") is not False:
        raise RuntimeError("strict-v8 prereg is incompatible with reserve selection")
    touched = denylist()
    ranked = []
    for row in rows:
        if not isinstance(row, dict) or set(row) != set(REQUIRED):
            continue
        if not all(isinstance(row.get(key), str) and row[key] for key in REQUIRED):
            continue
        if len(row["base_commit"]) != 40 or row["instance_id"] in touched:
            continue
        rank = hashlib.sha256(f"{SALT}|{row['instance_id']}".encode()).hexdigest()
        ranked.append((rank, {key: row[key] for key in REQUIRED}))
    ranked.sort(key=lambda item: (item[0], item[1]["instance_id"]))
    selected = []
    seen = set()
    for _, row in ranked:
        if row["instance_id"] in seen:
            continue
        seen.add(row["instance_id"])
        selected.append(row)
        if len(selected) == 3:
            break
    if len(selected) != 3:
        raise ValueError(f"need 3 untouched strict-v8 identities, got {len(selected)}")
    value = {
        "schema": "e1c-strict-v8-external-canary-reserve-v1",
        "source": "official_swebench_task_repo_task_yaml",
        "source_revision": source_revision,
        "identity_frozen_before_statement_materialization": True,
        "selection_salt": SALT,
        "mechanism_prereg_sha256": prereg["prereg_sha256"],
        "tasks": selected,
        "provider_calls": 0,
        "task_content_inspected": False,
    }
    encoded = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(encoded, encoding="utf-8")
    return {"instance_ids": [row["instance_id"] for row in selected], "manifest_sha256": hashlib.sha256(encoded.encode()).hexdigest(), "provider_calls": 0}
