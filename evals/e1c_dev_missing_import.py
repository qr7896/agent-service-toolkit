"""Model-free follow-up for a candidate's public missing-stdlib-import error."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

from evals.e1c_dev_v31 import _allowed_path
from evals.e1c_docker_grade import grade
from evals.e1c_live_runner import MANIFEST_SHA256, OUT, _manifest, _patch, _save, _source

PARENT = OUT / "e1c-dev-v47-public-import3-20260924"
RUN_ID = "e1c-dev-v48-public-nameerror-import-20260924"
RUN_DIR = OUT / RUN_ID
MISSING = re.compile(r"NameError: name '([A-Za-z_][A-Za-z_0-9]*)' is not defined")
FRAME = re.compile(r'File "/testbed/([^"\n]+\.py)"')


def add_import(text: str, module: str) -> str:
    tree = ast.parse(text)
    if any(isinstance(node, ast.Import) and any(alias.name == module for alias in node.names)
           for node in tree.body):
        raise ValueError("module already imported")
    lines = text.splitlines(keepends=True)
    at = 0
    if tree.body and isinstance(tree.body[0], ast.Expr) and isinstance(tree.body[0].value, ast.Constant):
        at = tree.body[0].end_lineno or 0
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module == "__future__":
            at = max(at, node.end_lineno or 0)
    lines.insert(at, f"import {module}\n")
    result = "".join(lines)
    ast.parse(result)
    return result


def candidates() -> list[dict]:
    state = json.loads((PARENT / "state.json").read_text(encoding="utf-8"))
    if state.get("status") != "completed" or len(state["rows"]) != 3:
        raise ValueError("v4.7 parent changed")
    rows = {row["instance_id"]: row for row in _manifest()["tasks"]}
    found = []
    for outcome in state["rows"]:
        instance_id = outcome["instance_id"]
        source = _source(rows[instance_id])
        artifacts = PARENT / "artifacts" / instance_id
        for step in reversed(range(1, len(outcome["steps"]) + 1)):
            grade_path = artifacts / f"grade.step{step}.json"
            if not grade_path.exists():
                continue
            scored = json.loads(grade_path.read_text(encoding="utf-8"))
            if scored["resolved"] or scored["f2p_pass"] == 0:
                continue
            log = (artifacts / f"grade.step{step}.log").read_text(encoding="utf-8", errors="replace")
            for match in MISSING.finditer(log):
                module = match.group(1)
                frames = FRAME.findall(log[max(0, match.start() - 1000):match.start()])
                paths = [path for path in frames if _allowed_path(source, path)]
                if module not in sys.stdlib_module_names or not paths:
                    continue
                path = paths[-1]
                patch_path = artifacts / f"patch.step{step}.diff"
                patch = patch_path.read_text(encoding="utf-8")
                section = next((part for part in patch.split("diff --git a/")
                                if part.startswith(f"{path} b/{path}\n")), "")
                if not any(re.search(rf"\b{module}\.", line) for line in section.splitlines()
                           if line.startswith("+") and not line.startswith("+++")):
                    continue
                found.append({"instance_id": instance_id, "row": rows[instance_id],
                              "step": step, "module": module, "path": path, "patch_path": patch_path,
                              "patch_sha256": hashlib.sha256(patch_path.read_bytes()).hexdigest()})
                break
            if found and found[-1]["instance_id"] == instance_id:
                break
    return found


def preflight() -> dict:
    items = []
    for item in candidates():
        row = item["row"]
        admission = OUT / "admission_v2" / row["instance_id"]
        base = json.loads((admission / "base.json").read_text(encoding="utf-8"))
        gold = json.loads((admission / "gold.json").read_text(encoding="utf-8"))
        digest = subprocess.check_output(
            ["docker", "image", "inspect", base["image"], "--format", "{{index .RepoDigests 0}}"],
            text=True,
        ).strip()
        items.append({key: item[key] for key in ("instance_id", "step", "module", "path", "patch_sha256")}
                     | {"ready": base["phase_pass"] and gold["phase_pass"] and
                        digest == base["image_digest"] == gold["image_digest"]})
    return {"run_id": RUN_ID, "manifest_sha256": MANIFEST_SHA256,
            "run_dir_absent": not RUN_DIR.exists(),
            "ready": len(items) == 1 and not RUN_DIR.exists() and all(item["ready"] for item in items),
            "rows": items, "provider_calls": 0,
            "selection": "all v4.7 partial-target candidates with unique public stdlib NameError and introduced module use",
            "claim_boundary": "outcome-selected repeated DEV, model-free repair, not independent efficacy"}


def run() -> dict:
    gate = preflight()
    if not gate["ready"]:
        raise RuntimeError("v4.8 zero-model preflight failed")
    RUN_DIR.mkdir(parents=True, exist_ok=False)
    _save(RUN_DIR / "identity.json", {**gate,
                                      "launcher_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})
    item = candidates()[0]
    row = item["row"]
    source = _source(row)
    workspace = RUN_DIR / "workspaces" / row["instance_id"]
    workspace.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "-C", str(source), "worktree", "add", "--detach", str(workspace),
                    row["base_commit"]], check=True, capture_output=True, timeout=120)
    subprocess.run(["git", "-C", str(workspace), "apply", "--check", str(item["patch_path"])],
                   check=True, capture_output=True, timeout=30)
    subprocess.run(["git", "-C", str(workspace), "apply", str(item["patch_path"])],
                   check=True, capture_output=True, timeout=30)
    target = workspace / item["path"]
    target.write_text(add_import(target.read_text(encoding="utf-8"), item["module"]), encoding="utf-8")
    artifacts = RUN_DIR / "artifacts" / row["instance_id"]
    artifacts.mkdir(parents=True)
    patch_path = artifacts / "patch.missing_import.diff"
    _patch(workspace, patch_path)
    try:
        scored = grade(row["instance_id"], "missing_import", patch_path, artifacts)
    except Exception as exc:
        _save(RUN_DIR / "state.json", {"run_id": RUN_ID, "status": "grade_interrupted_no_retry",
                                        "error": f"{type(exc).__name__}: {exc}"})
        raise
    state = {"run_id": RUN_ID, "status": "completed", "instance_id": row["instance_id"],
             "provider_calls": 0, "resolved": bool(scored["resolved"]),
             "f2p_pass": scored["f2p_pass"], "f2p_total": scored["f2p_total"],
             "p2p_maintained": scored["p2p_maintained"], "p2p_total": scored["p2p_total"],
             "patch_sha256": hashlib.sha256(patch_path.read_bytes()).hexdigest()}
    _save(RUN_DIR / "state.json", state)
    return state


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("preflight", "run"))
    args = parser.parse_args()
    print(json.dumps(preflight() if args.command == "preflight" else run(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
