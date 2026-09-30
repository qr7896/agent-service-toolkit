"""Combine two non-overlapping, model-produced public DEV patch hunks."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

from evals.e1c_docker_grade import grade
from evals.e1c_live_runner import MANIFEST_SHA256, OUT, _manifest, _patch, _save, _source

RUN_ID = "e1c-dev-v42-model-patch-union1-20260924"
RUN_DIR = OUT / RUN_ID
INSTANCE_ID = "django__django-13809"
PARTS = (
    OUT / "e1c-dev-v40-suggested-path2-20260924" / "artifacts" / INSTANCE_ID / "patch.step1.diff",
    OUT / "e1c-dev-v41-assertion-source1-20260924" / "artifacts" / INSTANCE_ID / "patch.step1.diff",
)


def _row() -> dict:
    return next(row for row in _manifest()["tasks"] if row["instance_id"] == INSTANCE_ID)


def preflight() -> dict:
    source = _source(_row())
    selected = []
    for patch in PARTS:
        value = patch.read_bytes()
        scored = json.loads(patch.with_name(patch.name.replace("patch.", "grade.").replace(".diff", ".json")).read_text(
            encoding="utf-8"))
        text = value.decode("utf-8")
        paths = re.findall(r"(?m)^diff --git a/(\S+) b/\S+", text)
        if (scored["resolved"] or scored["f2p_pass"] >= scored["f2p_total"]
                or scored["p2p_maintained"] != scored["p2p_total"]
                or not scored["source_identity_valid"]
                or scored["candidate_patch_sha256"] != hashlib.sha256(value).hexdigest()
                or not paths or any("test" in Path(path).parts for path in paths)):
            raise ValueError("prior patch is not a valid regression-preserving DEV candidate")
        selected.append({"path": str(patch), "sha256": hashlib.sha256(value).hexdigest(),
                         "changed_paths": paths})
    return {"run_id": RUN_ID, "manifest_sha256": MANIFEST_SHA256,
            "run_dir_absent": not RUN_DIR.exists(), "ready": not RUN_DIR.exists() and source.is_dir(),
            "instance_id": INSTANCE_ID, "parts": selected, "provider_calls": 0,
            "selection": "first v4.0 grade patch plus first v4.1 grade patch; disjoint hunks checked by git apply",
            "claim_boundary": "outcome-selected public DEV patch composition; not independent efficacy"}


def run() -> dict:
    gate = preflight()
    if not gate["ready"]:
        raise RuntimeError("v4.2 zero-call preflight failed")
    RUN_DIR.mkdir(parents=True, exist_ok=False)
    _save(RUN_DIR / "identity.json", {**gate, "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})
    row = _row()
    source = _source(row)
    workspace = RUN_DIR / "workspaces" / INSTANCE_ID
    workspace.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "-C", str(source), "worktree", "add", "--detach", str(workspace), row["base_commit"]],
                   check=True, capture_output=True, timeout=120)
    artifacts = RUN_DIR / "artifacts" / INSTANCE_ID
    artifacts.mkdir(parents=True)
    state = {"run_id": RUN_ID, "status": "started", "provider_calls": 0}
    _save(RUN_DIR / "state.json", state)
    for patch in PARTS:
        subprocess.run(["git", "-C", str(workspace), "apply", "--check", str(patch)],
                       check=True, capture_output=True, timeout=30)
        subprocess.run(["git", "-C", str(workspace), "apply", str(patch)],
                       check=True, capture_output=True, timeout=30)
    candidate = artifacts / "patch.final.diff"
    _patch(workspace, candidate)
    scored = grade(INSTANCE_ID, "final", candidate, artifacts)
    state.update({"status": "completed", "grade": scored,
                  "resolved": bool(scored["resolved"]), "candidate_sha256": hashlib.sha256(candidate.read_bytes()).hexdigest()})
    _save(RUN_DIR / "state.json", state)
    return state


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("preflight", "run"))
    args = parser.parse_args()
    value = preflight() if args.command == "preflight" else run()
    print(json.dumps(value if args.command == "preflight" else {
        "run_id": RUN_ID, "status": value["status"], "resolved": value["resolved"],
        "f2p": [value["grade"]["f2p_pass"], value["grade"]["f2p_total"]],
        "p2p": [value["grade"]["p2p_maintained"], value["grade"]["p2p_total"]],
        "provider_calls": 0}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
