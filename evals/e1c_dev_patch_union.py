"""Bounded zero-model union of non-overlapping public DEV model patches."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import re
import subprocess
from pathlib import Path

from evals.e1c_docker_grade import grade
from evals.e1c_live_runner import MANIFEST_SHA256, OUT, _manifest, _patch, _save, _source

RUN_ID = "e1c-dev-patch-union-batch1-20260924"
RUN_DIR = OUT / RUN_ID
MAX_PAIRS = 12


def _hunks(patch: Path) -> list[tuple[str, int, int]]:
    file = ""
    result = []
    for line in patch.read_text(encoding="utf-8").splitlines():
        match = re.match(r"diff --git a/(\S+) b/\S+", line)
        if match:
            file = match.group(1)
        match = re.match(r"@@ -(\d+)(?:,(\d+))? \+", line)
        if match and file:
            start = int(match.group(1))
            result.append((file, start, start + max(1, int(match.group(2) or "1")) - 1))
    return result


def _disjoint(left: Path, right: Path) -> bool:
    a, b = _hunks(left), _hunks(right)
    return bool(a and b) and all(
        path_a != path_b or end_a + 3 < start_b or end_b + 3 < start_a
        for path_a, start_a, end_a in a for path_b, start_b, end_b in b
    )


def _candidates() -> dict[str, list[dict]]:
    admitted = {row["instance_id"] for row in _manifest()["tasks"]}
    grouped: dict[str, list[dict]] = {}
    for score_path in OUT.glob("e1c-dev-*/artifacts/*/grade.*.json"):
        scored = json.loads(score_path.read_text(encoding="utf-8"))
        instance_id = scored.get("instance_id")
        if instance_id not in admitted or scored.get("source_identity_valid") is not True:
            continue
        patch = score_path.with_name(score_path.name.replace("grade.", "patch.").replace(".json", ".diff"))
        if not patch.is_file() or scored.get("candidate_patch_sha256") != hashlib.sha256(patch.read_bytes()).hexdigest():
            continue
        if any("test" in Path(path).parts for path, _, _ in _hunks(patch)):
            continue
        grouped.setdefault(instance_id, []).append({"patch": patch, "score": scored})
    return grouped


def _pairs() -> list[dict]:
    grouped = _candidates()
    rows = []
    seen: set[tuple[str, str, str]] = set()
    order = [row["instance_id"] for row in _manifest()["tasks"]]
    for instance_id in order:
        candidates = grouped.get(instance_id, [])
        if any(item["score"]["resolved"] for item in candidates):
            continue
        candidates.sort(key=lambda item: str(item["patch"]))
        for left, right in itertools.combinations(candidates, 2):
            if (left["score"]["f2p_pass"] == 0 and right["score"]["f2p_pass"] == 0
                    and not all(item["score"]["p2p_maintained"] == item["score"]["p2p_total"]
                                for item in (left, right))):
                continue
            if not _disjoint(left["patch"], right["patch"]):
                continue
            left_sha = hashlib.sha256(left["patch"].read_bytes()).hexdigest()
            right_sha = hashlib.sha256(right["patch"].read_bytes()).hexdigest()
            key = (instance_id, *sorted((left_sha, right_sha)))
            if key in seen:
                continue
            seen.add(key)
            rows.append({"instance_id": instance_id,
                         "left": str(left["patch"]), "right": str(right["patch"]),
                         "left_sha256": left_sha, "right_sha256": right_sha,
                         "priority": max(left["score"]["f2p_pass"], right["score"]["f2p_pass"])})
    rows.sort(key=lambda row: (-row["priority"], order.index(row["instance_id"]), row["left"], row["right"]))
    selected = []
    per_task: dict[str, int] = {}
    for row in rows:
        count = per_task.get(row["instance_id"], 0)
        if count >= 2:
            continue
        selected.append(row)
        per_task[row["instance_id"]] = count + 1
        if len(selected) == MAX_PAIRS:
            break
    return selected


def preflight() -> dict:
    pairs = _pairs()
    return {"run_id": RUN_ID, "manifest_sha256": MANIFEST_SHA256,
            "run_dir_absent": not RUN_DIR.exists(), "ready": bool(pairs) and not RUN_DIR.exists(),
            "pair_count": len(pairs), "max_pairs": MAX_PAIRS, "pairs": pairs,
            "provider_calls": 0, "claim_boundary": "post-outcome public DEV patch ensemble; not model efficacy"}


def run() -> dict:
    gate = preflight()
    if not gate["ready"]:
        raise RuntimeError("zero-model patch-union preflight failed")
    RUN_DIR.mkdir(parents=True, exist_ok=False)
    _save(RUN_DIR / "identity.json", {**gate, "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})
    by_id = {row["instance_id"]: row for row in _manifest()["tasks"]}
    state = {"run_id": RUN_ID, "rows": [], "status": "started", "provider_calls": 0}
    solved = set()
    for index, pair in enumerate(gate["pairs"], 1):
        instance_id = pair["instance_id"]
        if instance_id in solved:
            continue
        row = by_id[instance_id]
        source = _source(row)
        workspace = RUN_DIR / "workspaces" / f"pair{index}-{instance_id}"
        workspace.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "-C", str(source), "worktree", "add", "--detach", str(workspace),
                        row["base_commit"]], check=True, capture_output=True, timeout=120)
        artifacts = RUN_DIR / "artifacts" / f"pair{index}-{instance_id}"
        artifacts.mkdir(parents=True)
        outcome = {"pair_index": index, "instance_id": instance_id, "resolved": False}
        try:
            for field in ("left", "right"):
                patch = pair[field]
                subprocess.run(["git", "-C", str(workspace), "apply", "--check", patch],
                               check=True, capture_output=True, timeout=30)
                subprocess.run(["git", "-C", str(workspace), "apply", patch],
                               check=True, capture_output=True, timeout=30)
            candidate = artifacts / "patch.final.diff"
            _patch(workspace, candidate)
            scored = grade(instance_id, f"pair{index}", candidate, artifacts)
            outcome.update({"status": "graded", "resolved": bool(scored["resolved"]),
                            "f2p_pass": scored["f2p_pass"], "f2p_total": scored["f2p_total"],
                            "p2p_maintained": scored["p2p_maintained"], "p2p_total": scored["p2p_total"]})
            if scored["resolved"]:
                solved.add(instance_id)
        except subprocess.CalledProcessError as exc:
            outcome.update({"status": "patch_conflict", "error": str(exc)[:300]})
        state["rows"].append(outcome)
        _save(RUN_DIR / "state.json", state)
        print(json.dumps(outcome), flush=True)
    state["status"] = "completed"
    _save(RUN_DIR / "state.json", state)
    return state


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("preflight", "run"))
    args = parser.parse_args()
    result = preflight() if args.command == "preflight" else run()
    print(json.dumps(result if args.command == "preflight" else {
        "run_id": RUN_ID, "status": result["status"], "rows": len(result["rows"]),
        "new_resolved": sum(row["resolved"] for row in result["rows"]), "provider_calls": 0,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
