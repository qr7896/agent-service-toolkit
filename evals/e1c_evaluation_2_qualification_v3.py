"""Qualification-only authority overlay; original model inputs are untouched."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess

from evals import e1c_evaluation_2_qualification_v2 as base
from evals.e1c_blind_boundary import assert_agent_path
from evals.e1c_strict_v5_boundary import assert_production_relative_path


def load_authority(path, expected_sha256):
    raw = path.read_bytes()
    if not re.fullmatch(r"[0-9a-f]{64}", expected_sha256) or hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise ValueError("authority receipt digest differs")
    value = json.loads(raw)
    if value.get("provider_calls") != 0 or value.get("Gold_read") is not False:
        raise ValueError("zero-model production authority receipt required")
    return value


def git_blob(workspace, base_commit, path):
    return subprocess.check_output(["git", "-C", str(workspace), "show", base_commit + ":" + path], timeout=15)


def authority_overlay(frozen, workspace, scope, authority):
    if scope["base_commit"] != frozen["base_commit"] or not re.fullmatch(r"[0-9a-f]{40}", scope["base_commit"]):
        raise ValueError("qualification base scope differs")
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", scope["image"]):
        raise ValueError("immutable qualification image required")
    additions, proofs, seen = [], [], set()
    existing = {r["path"]: r["source_sha256"] for r in frozen["windows"]}
    for row in authority["rows"]:
        if row["instance_id"] != scope["instance_id"]:
            continue
        if row["base_commit"] != scope["base_commit"] or row["immutable_image"] != scope["image"]:
            raise ValueError("authority task/base/image scope differs")
        name = assert_production_relative_path(row["path"])
        if name in seen:
            raise ValueError("duplicate authority source")
        seen.add(name)
        file = assert_agent_path(workspace / name, workspace=workspace)
        if file.is_symlink() or file.stat().st_size > 1_000_000:
            raise ValueError("regular bounded production source required")
        raw = file.read_bytes()
        host_sha = hashlib.sha256(raw).hexdigest()
        effective_sha = hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()
        blob_sha = hashlib.sha256(git_blob(workspace, scope["base_commit"], name)).hexdigest()
        runtime = row["runtime_source_identity"]
        if (host_sha != row["host_bytes_sha256"] or runtime["live_equals_git_blob"] is not True
                or len({effective_sha, blob_sha, row["effective_LF_sha256"], row["canonical_base_blob_sha256"],
                        runtime["live_sha256"], runtime["canonical_git_sha256"]}) != 1):
            raise ValueError("authority host/effective/canonical/runtime identity differs")
        if name in existing and existing[name] != host_sha:
            raise ValueError("authority conflicts with original exposed identity")
        if name not in existing:
            additions.append({"path": name, "source_sha256": host_sha, "origin": "qualification_only_authority_not_model_exposure"})
        proofs.append({"path": name, "host_sha256": host_sha, "effective_LF_sha256": effective_sha,
                       "canonical_runtime_sha256": blob_sha, "original_model_exposure": name in existing})
    return {**frozen, "windows": [*frozen["windows"], *additions]}, proofs


def qualify(payload, frozen, workspace, candidate, observation, *, scope, authority,
            normal_controls_pass, target_repeatable_failure):
    augmented, proofs = authority_overlay(frozen, workspace, scope, authority)
    result = base.qualify(payload, augmented, workspace, candidate, observation,
                          normal_controls_pass=normal_controls_pass, target_repeatable_failure=target_repeatable_failure)
    return {**result, "schema": "e1c2-bounded-qualification-v3", "additional_authority": proofs,
            "model_inputs_modified": False, "new_model_exposure_claimed": False}
