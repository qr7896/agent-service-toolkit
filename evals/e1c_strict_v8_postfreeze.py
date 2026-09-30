"""Post-freeze zero-provider assessment for the independent strict-v8 canary."""

from __future__ import annotations

import hashlib
import io
import json
import shutil
import subprocess
import urllib.request
import zipfile
from pathlib import Path

from evals.e1c_admission import ROOT
from evals.e1c_strict_v6_postfreeze import fetch_statement
from evals.e1c_strict_v6_runtime import build_bundle
from evals.e1c_strict_v8_prereg import build as build_prereg
from evals.e1c_strict_v8_probe import candidate_plan
from evals.e1c_strict_v8_selection_boundary import build as build_boundary

MANIFEST = ROOT / "data" / "e1c_strict_v8_canary_manifest.json"
PREREG = ROOT / "data" / "e1c_strict_v8_prereg.json"
BOUNDARY = ROOT / "data" / "e1c_strict_v8_selection_boundary.json"
ROOT_OUT = ROOT / ".codex" / "e1c" / "strict-v8" / "postfreeze-v1"
OUT = ROOT / "data" / "e1c_strict_v8_postfreeze_assessment.json"


def materialize_source_bounded(row: dict, destination: Path) -> dict:
    """Materialize the frozen base commit without an unbounded git transport wait."""
    repo=row["repo"]; commit=row["base_commit"]
    marker=destination/".e1c_base_commit"
    if destination.is_dir() and marker.is_file() and marker.read_text(encoding="utf-8").strip() == commit:
        return {"ready":True,"status":"already_materialized_archive","repo_url":f"https://github.com/{repo}","head":commit,"base_commit":commit}
    url=f"https://codeload.github.com/{repo}/zip/{commit}"
    curl=shutil.which("curl.exe") or shutil.which("curl")
    if not curl: return {"ready":False,"status":"curl_missing","base_commit":commit}
    try:
        completed=subprocess.run([curl,"-L","--fail","--silent","--show-error","--max-time","45",url],check=False,capture_output=True,timeout=50)
    except (OSError,subprocess.TimeoutExpired) as exc:
        return {"ready":False,"status":"github_archive_download_failed","detail":f"{type(exc).__name__}: {exc}","base_commit":commit}
    if completed.returncode != 0 or not completed.stdout:
        return {"ready":False,"status":"github_archive_download_failed","detail":completed.stderr.decode("utf-8",errors="replace")[-2000:],"base_commit":commit}
    raw=completed.stdout
    if destination.exists(): shutil.rmtree(destination)
    destination.mkdir(parents=True)
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            names=archive.namelist(); roots={n.split("/",1)[0] for n in names if "/" in n}
            if len(roots) != 1: return {"ready":False,"status":"github_archive_root_invalid","base_commit":commit}
            root=next(iter(roots))
            for member in archive.infolist():
                name=member.filename
                if not name.startswith(root+"/"): continue
                rel=Path(name[len(root)+1:])
                if not rel.parts: continue
                if rel.is_absolute() or ".." in rel.parts: return {"ready":False,"status":"github_archive_path_escape","base_commit":commit}
                target=destination/rel
                if member.is_dir(): target.mkdir(parents=True,exist_ok=True); continue
                target.parent.mkdir(parents=True,exist_ok=True)
                with archive.open(member) as source, target.open("wb") as sink: shutil.copyfileobj(source,sink)
    except (OSError,zipfile.BadZipFile) as exc:
        return {"ready":False,"status":"github_archive_extract_failed","detail":f"{type(exc).__name__}: {exc}","base_commit":commit}
    marker.write_text(commit+"\n",encoding="utf-8")
    return {"ready":True,"status":"github_archive_materialized","repo_url":f"https://github.com/{repo}","head":commit,"base_commit":commit,"archive_sha256":hashlib.sha256(raw).hexdigest(),"archive_bytes":len(raw)}


def fetch_statement_bounded(instance_id: str, revision: str, cache_path: Path) -> tuple[str, str]:
    if cache_path.is_file():
        raw = cache_path.read_bytes()
        return raw.decode("utf-8"), hashlib.sha256(raw).hexdigest()
    curl = shutil.which("curl.exe") or shutil.which("curl")
    if curl:
        url = f"https://raw.githubusercontent.com/SWE-bench/swe-bench-tasks/{revision}/tasks/{instance_id}/problem_statement.md"
        try:
            completed = subprocess.run([curl, "-L", "--fail", "--silent", "--show-error", "--max-time", "20", url], check=False, capture_output=True, timeout=25)
        except (OSError, subprocess.TimeoutExpired):
            completed = None
        if completed is not None and completed.returncode == 0 and completed.stdout:
            raw = completed.stdout
            return raw.decode("utf-8"), hashlib.sha256(raw).hexdigest()
    raise RuntimeError(f"statement_fetch_failed_bounded: {instance_id}")


def certify_identity() -> dict:
    manifest=json.loads(MANIFEST.read_text(encoding="utf-8")); prereg=json.loads(PREREG.read_text(encoding="utf-8")); boundary=json.loads(BOUNDARY.read_text(encoding="utf-8"))
    rows=manifest.get("tasks", [])
    checks={
        "manifest_schema": manifest.get("schema") == "e1c-strict-v8-external-canary-reserve-v1",
        "exact_task_count": len(rows) == 3,
        "identity_frozen_before_statement": manifest.get("identity_frozen_before_statement_materialization") is True,
        "provider_calls_zero": manifest.get("provider_calls") == prereg.get("provider_calls") == 0,
        "task_content_inspected_false": manifest.get("task_content_inspected") is False,
        "mechanism_prereg_matches": manifest.get("mechanism_prereg_sha256") == prereg.get("prereg_sha256"),
        "prereg_current": prereg == build_prereg(),
        "boundary_current": boundary == build_boundary(),
    }
    ids=[r.get("instance_id") for r in rows]
    checks["unique_nonempty_ids"] = len(ids) == len(set(ids)) == 3 and all(ids)
    return {"ready": all(checks.values()), "checks": checks, "instance_ids": ids}


def run(output: Path = OUT) -> dict:
    cert=certify_identity()
    if not cert["ready"]: raise RuntimeError("strict_v8_identity_integrity_failed")
    manifest=json.loads(MANIFEST.read_text(encoding="utf-8")); rows=[]
    for task in manifest["tasks"]:
        iid=task["instance_id"]; root=ROOT_OUT/iid; root.mkdir(parents=True, exist_ok=True)
        statement_path=root/"problem_statement.md"
        statement, statement_sha=fetch_statement_bounded(iid, manifest["source_revision"], statement_path)
        statement_path.write_text(statement, encoding="utf-8")
        source=materialize_source_bounded(task, root/"source")
        plan=None; status="source_incomplete"; error=None
        if source["ready"]:
            try:
                bundle=build_bundle(statement=statement, workspace=root/"source", base_commit=task["base_commit"], forbidden_values=(iid, task["image"]))
                plan=candidate_plan(bundle["issue"], bundle["localization"]); status="supported"
            except Exception as exc:
                status="unsupported"; error=f"{type(exc).__name__}: {exc}"
        rows.append({"instance_id":iid,"statement_sha256":statement_sha,"source":source,"projection_status":status,"projection_error":error,"candidate_count":int(plan.get("candidate_count",0)) if plan else 0,"executable_candidate_count":int(plan.get("executable_candidate_count",0)) if plan else 0,"plan":plan,"provider_calls":0})
    source_ready=sum(bool(r["source"]["ready"]) for r in rows); supported=sum(r["projection_status"]=="supported" for r in rows); executable=sum(r["executable_candidate_count"]>0 for r in rows)
    gate=source_ready == supported == 3 and executable >= 2
    value={"schema":"e1c-strict-v8-postfreeze-assessment-v1","provider_calls":0,"live_model_run":False,"identity_certificate":cert,"source_ready_count":source_ready,"projection_supported_count":supported,"candidate_task_count":sum(r["candidate_count"]>0 for r in rows),"executable_candidate_task_count":executable,"minimum_executable_candidate_tasks":2,"candidate_gate_passed":gate,"image_pull_allowed_by_candidate_gate":gate,"official_admission_allowed_by_candidate_gate":gate,"live_allowed":False,"reason":"ready_for_image_and_official_admission" if gate else "seal_pre_live_insufficient_executable_reproducers","rows":rows}
    value["summary_sha256"]=hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",", ":")).encode()).hexdigest(); output.write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); return value

if __name__ == "__main__":
    r=run(); print(json.dumps({k:r[k] for k in ("source_ready_count","projection_supported_count","candidate_task_count","executable_candidate_task_count","candidate_gate_passed","reason","provider_calls","summary_sha256")}, indent=2))
