"""Read-only E1-C runner inventory. No download, Docker pull, or model call.

Run this on the actual runner (not on the user's browser/host) before live work.
It deliberately reports missing prerequisites as BLOCKED, not as agent failures.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / ".codex" / "e1c"
PARSER_COMMIT = "02e7a74ffd0b707aab73d203fe87bdc7c76afc8e"


def command(*args: str, timeout: int = 20) -> tuple[bool, str]:
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False)
        return result.returncode == 0, (result.stdout or result.stderr).strip()[-300:]
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, str(exc)[-300:]


def network_probe(url: str) -> tuple[bool, str]:
    try:
        request = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "e1c-preflight"})
        with urllib.request.urlopen(request, timeout=10) as response:
            return True, f"HTTP {response.status}"
    except urllib.error.HTTPError as exc:
        return exc.code in {401, 403, 404, 405, 429}, f"HTTP {exc.code} (endpoint reachable)"
    except (OSError, urllib.error.URLError) as exc:
        return False, str(exc)[-300:]


def inventory(*, network: bool = False) -> dict:
    checks: dict[str, dict] = {}

    def add(name: str, ok: bool, detail: object) -> None:
        checks[name] = {"status": "PASS" if ok else "BLOCKED", "detail": detail}

    ok, detail = command("git", "--version")
    add("git", ok, detail)
    ok, detail = command("docker", "--version")
    add("docker_cli", ok, detail)
    ok, detail = command("docker", "info", "--format", "{{.ServerVersion}}") if ok else (False, "CLI unavailable")
    add("docker_daemon", ok, detail)
    daemon = ok
    parser = OUT / "swebench-harness"
    ok, head = command("git", "-C", str(parser), "rev-parse", "HEAD") if parser.is_dir() else (False, "checkout missing")
    add("official_parser", ok and head == PARSER_COMMIT, head)
    manifest_path = OUT / "candidate_manifest.json"
    manifest = None
    try:
        raw = manifest_path.read_bytes()
        manifest = json.loads(raw)
        rows = manifest["tasks"]
        ids = [row["instance_id"] for row in rows]
        valid = (
            manifest["count"] == len(rows) == 30
            and manifest["status"] == "selected_not_admitted"
            and len(set(ids)) == 30
            and all(re.fullmatch(r"[0-9a-f]{40}", row["base_commit"]) for row in rows)
        )
        digest = hashlib.sha256(raw).hexdigest()
        expected = (OUT / "candidate_manifest.sha256").read_text(encoding="utf-8").strip()
        add("candidate_manifest", valid and digest == expected, {"count": len(rows), "sha256": digest, "hash_match": digest == expected})
    except (OSError, KeyError, TypeError, ValueError) as exc:
        add("candidate_manifest", False, str(exc))
    if manifest is not None:
        task_ok = source_ok = clean_ok = image_ok = base_ok = gold_ok = 0
        try:
            task_inventory = json.loads((OUT / "task_inventory.json").read_text(encoding="utf-8"))
            task_records = {item["instance_id"]: item for item in task_inventory["tasks"]}
        except (OSError, KeyError, TypeError, ValueError):
            task_records = {}
        failures = []
        for row in manifest["tasks"]:
            iid, repo, commit = row["instance_id"], row["repo"], row["base_commit"]
            task_dir = OUT / "tasks" / iid
            record = task_records.get(iid, {})
            task_files = (
                record.get("materialization_status") == "complete"
                and all(
                    (task_dir / file["path"]).is_file()
                    and hashlib.sha256((task_dir / file["path"]).read_bytes()).hexdigest() == file["sha256"]
                    for file in record.get("files", [])
                )
                and len(record.get("files", [])) == record.get("expected_file_count", 0)
            )
            task_ok += task_files
            source = OUT / "repos" / repo.replace("/", "__") / commit
            source_match, actual = command("git", "-C", str(source), "rev-parse", "HEAD") if source.is_dir() else (False, "missing")
            source_ok += source_match and actual == commit
            clean, changes = command("git", "-C", str(source), "status", "--porcelain") if source_match else (False, "missing")
            clean_ok += clean and not changes
            image = None
            if task_files:
                text = (task_dir / "task.yaml").read_text(encoding="utf-8")
                match = re.search(r"^image:\s*['\"]?([^\s'\"]+)", text, re.MULTILINE)
                image = match.group(1) if match else None
            image_present = False
            if daemon and image and re.fullmatch(r"swebench/[A-Za-z0-9_.-]+:latest", image):
                image_present, _ = command("docker", "image", "inspect", image)
            image_ok += image_present
            admission = OUT / "admission_v2" / iid
            phases = {}
            for phase in ("base", "gold"):
                try:
                    record = json.loads((admission / f"{phase}.json").read_text(encoding="utf-8"))
                    phases[phase] = (
                        record["instance_id"] == iid
                        and record["phase"] == phase
                        and record["expected_base_commit"] == commit
                        and record["official_parser_commit"] == PARSER_COMMIT
                        and record["schema"] == "e1c-admission-phase-v2"
                        and record["source_identity_valid"] is True
                        and record["phase_pass"] is True
                        and hashlib.sha256((admission / f"{phase}.log").read_bytes()).hexdigest() == record["log_sha256"]
                    )
                except (OSError, KeyError, TypeError, ValueError):
                    phases[phase] = False
            base_ok += phases["base"]
            gold_ok += phases["gold"]
            if not (task_files and source_match and actual == commit and clean and not changes and image_present and all(phases.values())):
                failures.append(iid)
        for name, count in (("task_files", task_ok), ("source_commits", source_ok), ("source_clean", clean_ok), ("local_images", image_ok), ("base_fail", base_ok), ("gold_pass", gold_ok)):
            add(name, count == 30, f"{count}/30")
        checks["cohort_failures"] = {"status": "INFO", "detail": failures}
    writable = OUT.exists() and os.access(OUT, os.W_OK)
    add("output_writable", writable, str(OUT))
    checks["hugging_face"] = {"status": "NOT_REQUIRED", "detail": "Frozen public task source is GitHub; no HF download in this path"}
    if network:
        for name, url in (
            ("github_https", "https://api.github.com/repos/SWE-bench/swe-bench-tasks"),
            ("docker_hub_auth_https", "https://auth.docker.io/token?service=registry.docker.io"),
            ("deepseek_https", "https://api.deepseek.com"),
        ):
            ok, detail = network_probe(url)
            add(name, ok, detail)
    else:
        checks["external_network"] = {"status": "NOT_TESTED", "detail": "Pass --network for public endpoint reachability; no provider inference"}
    checks["deepseek_live"] = {"status": "NOT_AUTHORIZED", "detail": "No API request or secret inspection; exact live command needs user confirmation"}
    blocked = [name for name, item in checks.items() if item["status"] == "BLOCKED"]
    return {"schema": "e1c-runner-preflight-v1", "runner": str(ROOT), "provider_calls": 0, "entry_gate": "BLOCKED" if blocked or checks["deepseek_live"]["status"] != "PASS" else "READY", "blocked_checks": blocked, "checks": checks}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--network", action="store_true", help="Probe public HTTPS endpoints; never use credentials or call inference")
    args = parser.parse_args()
    result = inventory(network=args.network)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["entry_gate"] != "READY":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
