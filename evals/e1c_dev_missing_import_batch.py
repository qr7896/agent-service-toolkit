"""Model-free missing-stdlib-import recovery over v4.3 public DEV grades."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

from evals.e1c_dev_missing_import import FRAME, MISSING, add_import
from evals.e1c_dev_v31 import _allowed_path
from evals.e1c_docker_grade import grade
from evals.e1c_live_runner import MANIFEST_SHA256, OUT, _manifest, _patch, _save, _source

PARENT = OUT / "e1c-dev-v43-auto-remaining19-20260924"
RUN_ID = "e1c-dev-v49-public-nameerror-batch-20260924"
RUN_DIR = OUT / RUN_ID


def candidates() -> list[dict]:
    state = json.loads((PARENT / "state.json").read_text(encoding="utf-8"))
    if state.get("status") != "completed" or len(state["rows"]) != 19:
        raise ValueError("v4.3 parent changed")
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
            if json.loads(grade_path.read_text(encoding="utf-8"))["resolved"]:
                continue
            log = (artifacts / f"grade.step{step}.log").read_text(encoding="utf-8", errors="replace")
            for match in MISSING.finditer(log):
                module = match.group(1)
                paths = [path for path in FRAME.findall(log[max(0, match.start() - 1000):match.start()])
                         if _allowed_path(source, path)]
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
                found.append({"instance_id": instance_id, "row": rows[instance_id], "step": step,
                              "module": module, "path": path, "patch_path": patch_path,
                              "parent_patch_sha256": hashlib.sha256(patch_path.read_bytes()).hexdigest()})
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
        items.append({key: item[key] for key in ("instance_id", "step", "module", "path",
                                                     "parent_patch_sha256")}
                     | {"ready": base["phase_pass"] and gold["phase_pass"] and
                        digest == base["image_digest"] == gold["image_digest"]})
    return {"run_id": RUN_ID, "manifest_sha256": MANIFEST_SHA256,
            "run_dir_absent": not RUN_DIR.exists(),
            "ready": len(items) == 2 and not RUN_DIR.exists() and all(item["ready"] for item in items),
            "rows": items, "provider_calls": 0,
            "selection": "all v4.3 unresolved grades with standard-library NameError caused by candidate-added module access",
            "claim_boundary": "historical outcome-selected DEV, model-free diagnostic, no independent efficacy"}


def run() -> dict:
    gate = preflight()
    if not gate["ready"]:
        raise RuntimeError("v4.9 zero-model preflight failed")
    RUN_DIR.mkdir(parents=True, exist_ok=False)
    _save(RUN_DIR / "identity.json", {**gate,
                                      "launcher_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                                      "import_helper_sha256": hashlib.sha256(Path(add_import.__code__.co_filename).read_bytes()).hexdigest()})
    state = {"run_id": RUN_ID, "rows": []}
    for item in candidates():
        row = item["row"]
        source = _source(row)
        workspace = RUN_DIR / "workspaces" / row["instance_id"]
        workspace.parent.mkdir(parents=True, exist_ok=True)
        try:
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
            scored = grade(row["instance_id"], "missing_import", patch_path, artifacts)
        except Exception as exc:
            state.update({"status": "interrupted_no_retry", "interrupted_task": row["instance_id"],
                          "error": f"{type(exc).__name__}: {exc}"})
            _save(RUN_DIR / "state.json", state)
            raise
        state["rows"].append({"instance_id": row["instance_id"], "provider_calls": 0,
                              "resolved": bool(scored["resolved"]),
                              "f2p_pass": scored["f2p_pass"], "f2p_total": scored["f2p_total"],
                              "p2p_maintained": scored["p2p_maintained"], "p2p_total": scored["p2p_total"],
                              "patch_sha256": hashlib.sha256(patch_path.read_bytes()).hexdigest()})
        _save(RUN_DIR / "state.json", state)
    state["status"] = "completed"
    _save(RUN_DIR / "state.json", state)
    return state


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("preflight", "run"))
    args = parser.parse_args()
    print(json.dumps(preflight() if args.command == "preflight" else run(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
