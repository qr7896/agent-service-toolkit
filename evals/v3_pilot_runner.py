from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from agents.experience import ExperienceStore
from agents.trajectory import append_trajectory
from agents.workspace import EXCLUDED_DIRS, export_patch
from core import settings

ROOT = Path(__file__).resolve().parents[1]
V3_DIR = ROOT / ".codex" / "v3"
PILOT_DIR = V3_DIR / "pilot"
LEDGER = PILOT_DIR / "provider_calls.jsonl"
STATE = PILOT_DIR / "state.json"
TRAJECTORIES = ROOT / ".codex" / "trajectories" / "coding_agent.jsonl"
EXPERIENCES = PILOT_DIR / "experience.db"
CHROMA = PILOT_DIR / "chroma"

RUN_ID = "v3-prospective-001"
TOTAL_TOKEN_CEILING = 30_000
TASK_TOKEN_CEILING = 10_000
MAX_CALLS_PER_TASK = 4
MAX_OUTPUT_TOKENS = 600
TASK_RESERVE = 10_000
MAX_TOOL_RESULT_CHARS = 8_000
TOOL_SCHEMA_RESERVE_TOKENS = 3_500


@dataclass(frozen=True)
class PilotTask:
    instance_id: str
    base_commit: str
    fix_commit: str
    problem_statement: str
    restore_paths: tuple[str, ...]
    grader: str


TASKS = (
    PilotTask(
        "v3pilot__pytest-evals-import-01",
        "6bef74819e1e161cb8957095c243949e3d17808f",
        "9ffa8ad5f67dd88f72bfda12f357456a9bde9fd1",
        "pytest collection cannot import the repository-level evals package because its configured Python path only exposes src. Fix the configuration minimally without changing tests.",
        ("pyproject.toml",),
        "pytest_import",
    ),
    PilotTask(
        "v3pilot__direct-research-cli-02",
        "9ffa8ad5f67dd88f72bfda12f357456a9bde9fd1",
        "a1f4f78690c23bb6c9637ab0b4d5c524f1b4d74f",
        "Running scripts/make_research_tasks.py --help and evals/adaptive_retrieval_benchmark.py --help directly from the repository root fails during imports. Make both entry points runnable with a minimal change.",
        (
            "evals/adaptive_retrieval_benchmark.py",
            "scripts/make_research_tasks.py",
            "tests/test_research_mode.py",
        ),
        "direct_cli",
    ),
    PilotTask(
        "v3pilot__newline-portable-hash-03",
        "4e71447cf8c51d5c7fee4ac872d6f7a0bbcf61ee",
        "54242a09bcf1f2874d2c1bca831df72e4bba6fa5",
        "Frozen-policy artifact verification must produce the same SHA-256 for equivalent text files that differ only by CRLF versus LF line endings. Preserve byte hashing for non-text artifacts.",
        (
            "evals/v1_evaluate_frozen.py",
            "evals/v1_freeze_policy.py",
            "tests/test_v1_learning_policy.py",
        ),
        "portable_hash",
    ),
)

HIDDEN_FROM_AGENT = (
    "evals/v3_pilot_runner.py",
    "tests/test_model_budget.py",
    "tests/test_v3_pilot_runner.py",
    "docs/PROGRESS_RESEARCH_ROADMAP.md",
    "docs/research/PROGRESS_LOG_ARCHIVE.md",
    "docs/research/V3_PROSPECTIVE_PILOT_PLAN.md",
    "docs/research/V3_WEBGPT_HANDOFF.md",
)

CHILD = r"""
import asyncio, json, sys
from pathlib import Path
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from agents.coding_agent import build_graph
from schema.models import DeepseekModelName

async def main():
    spec = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    async with AsyncSqliteSaver.from_conn_string(spec["checkpoint_path"]) as saver:
        graph = build_graph(checkpointer=saver)
        conf = {
            "thread_id": spec["task_id"],
            "model": DeepseekModelName.DEEPSEEK_FLASH,
            "allow_write": True,
            "require_approval": False,
            "record_experience": False,
            "trajectory_path": spec["raw_trajectory_path"],
            "experience_path": spec["experience_path"],
            "experience_chroma_path": spec["chroma_path"],
            "source_repo": spec["source_repo"],
            "source_commit_at_execution": spec["source_commit"],
            "planner_recon_steps": 0,
            "provider_ledger_path": spec["ledger_path"],
            "provider_run_id": spec["run_id"],
            "provider_task_id": spec["task_id"],
            "provider_total_token_ceiling": spec["total_token_ceiling"],
            "provider_task_token_ceiling": spec["task_token_ceiling"],
            "provider_max_calls_per_task": spec["max_calls_per_task"],
            "provider_max_output_tokens": spec["max_output_tokens"],
            "provider_max_tool_result_chars": spec["max_tool_result_chars"],
            "provider_tool_schema_reserve_tokens": spec["tool_schema_reserve_tokens"],
            "provider_min_call_reserve": 1000,
            "provider_disable_thinking": True,
        }
        config = {"configurable": conf, "recursion_limit": 30}
        prior = await saver.aget_tuple({"configurable": {"thread_id": spec["task_id"]}})
        graph_input = None if prior else {"messages": [HumanMessage(content=spec["task"])]}
        out = await graph.ainvoke(graph_input, config)
        print(json.dumps({"status": (out.get("trajectory") or {}).get("status", "")}, ensure_ascii=False))

asyncio.run(main())
"""


def _ignore(_directory: str, names: list[str]) -> set[str]:
    return {name for name in names if name in EXCLUDED_DIRS}


def _make_writable_and_retry(function: Any, path: str, _exc: Any) -> None:
    os.chmod(path, 0o700)
    function(path)


def _git(*args: str, cwd: Path = ROOT, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, check=check, timeout=120)


def _write_version(root: Path, commit: str, relative: str) -> None:
    result = _git("show", f"{commit}:{relative}")
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(result.stdout)


def _prepare(root: Path, task: PilotTask) -> None:
    if root.exists():
        if all((root / relative).is_file() for relative in task.restore_paths):
            return
        shutil.rmtree(root, onexc=_make_writable_and_retry)
    root.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(ROOT, root, ignore=_ignore, symlinks=False)
    for relative in HIDDEN_FROM_AGENT:
        path = root / relative
        if path.is_file():
            path.unlink()
    for relative in task.restore_paths:
        _write_version(root, task.base_commit, relative)
    _git("add", "-A", cwd=root)
    _git(
        "-c",
        "user.name=v3-pilot",
        "-c",
        "user.email=v3-pilot@local",
        "commit",
        "--allow-empty",
        "-q",
        "-m",
        f"v3 pilot base {task.instance_id}",
        cwd=root,
    )


def _run(command: list[str], root: Path, timeout: int = 90) -> dict[str, Any]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(root / "src")
    result = subprocess.run(
        command,
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return {
        "command": command,
        "exit_code": result.returncode,
        "passed": result.returncode == 0,
        "stdout": result.stdout[-2000:],
        "stderr": result.stderr[-2000:],
    }


def _grade(task: PilotTask, root: Path) -> dict[str, Any]:
    if task.grader == "pytest_import":
        hidden = root / ".codex" / "v3_hidden" / "test_eval_import.py"
        hidden.parent.mkdir(parents=True, exist_ok=True)
        hidden.write_text(
            "from evals.swe_tasks import load_tasks\n\ndef test_import():\n    assert callable(load_tasks)\n",
            encoding="utf-8",
        )
        pytest_executable = Path(sys.executable).with_name(
            "pytest.exe" if os.name == "nt" else "pytest"
        )
        command = (
            [str(pytest_executable)]
            if pytest_executable.exists()
            else [sys.executable, "-m", "pytest"]
        )
        return _run([*command, "-q", str(hidden), "-c", "pyproject.toml"], root)
    if task.grader == "direct_cli":
        rows = [
            _run([sys.executable, script, "--help"], root, timeout=45)
            for script in (
                "scripts/make_research_tasks.py",
                "evals/adaptive_retrieval_benchmark.py",
            )
        ]
        return {
            "command": [row["command"] for row in rows],
            "exit_code": max(row["exit_code"] for row in rows),
            "passed": all(row["passed"] for row in rows),
            "rows": rows,
        }
    if task.grader == "rebuild_incomplete_workspace":
        code = """
from pathlib import Path
from tempfile import TemporaryDirectory
import evals.v3_pilot_runner as runner

real_rmtree = runner.shutil.rmtree
remove_calls = []

def checked_rmtree(path, **kwargs):
    callback = kwargs.get("onexc") or kwargs.get("onerror")
    assert callable(callback)
    remove_calls.append(Path(path))
    return real_rmtree(path)

def fake_copytree(_source, target, **_kwargs):
    Path(target).mkdir(parents=True)

def fake_write(root, _commit, relative):
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("restored", encoding="utf-8")

runner.shutil.rmtree = checked_rmtree
runner.shutil.copytree = fake_copytree
runner._write_version = fake_write
runner._git = lambda *_args, **_kwargs: None

with TemporaryDirectory() as directory:
    root = Path(directory) / "repo"
    root.mkdir()
    task = runner.TASKS[0]
    runner._prepare(root, task)
    restored = root / task.restore_paths[0]
    assert restored.is_file()
    marker = root / "complete-workspace-marker"
    marker.write_text("keep", encoding="utf-8")
    removals_after_rebuild = len(remove_calls)
    runner._prepare(root, task)
    assert marker.is_file()
    assert len(remove_calls) == removals_after_rebuild
"""
        return _run([sys.executable, "-c", code], root, timeout=120)
    code = (
        "from pathlib import Path; from tempfile import TemporaryDirectory; "
        "from evals.v1_evaluate_frozen import sha256; "
        "d=TemporaryDirectory(); p=Path(d.name); "
        "a=p/'a.json'; b=p/'b.json'; "
        "a.write_bytes(b'{\\r\\n  \"frozen\": true\\r\\n}\\r\\n'); "
        "b.write_bytes(b'{\\n  \"frozen\": true\\n}\\n'); "
        "assert sha256(a)==sha256(b)"
    )
    return _run([sys.executable, "-c", code], root)


def _preflight() -> dict[str, Any]:
    rows = []
    for task in TASKS:
        with tempfile.TemporaryDirectory(prefix="v3-pilot-preflight-") as directory:
            root = Path(directory) / "repo"
            _prepare(root, task)
            before = _grade(task, root)
            for relative in task.restore_paths:
                _write_version(root, task.fix_commit, relative)
            after = _grade(task, root)
            rows.append(
                {
                    "instance_id": task.instance_id,
                    "base_fails": not before["passed"],
                    "gold_passes": after["passed"],
                    "base_exit_code": before["exit_code"],
                    "gold_exit_code": after["exit_code"],
                }
            )
    return {
        "protocol": "v3-pilot-task-preflight-v1",
        "ready": all(row["base_fails"] and row["gold_passes"] for row in rows),
        "rows": rows,
    }


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def _spent() -> int:
    if not LEDGER.exists():
        return 0
    latest = {}
    for line in LEDGER.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("run_id") == RUN_ID:
            latest[row["call_id"]] = row
    return sum(
        int(row.get("total_tokens") or 0)
        for row in latest.values()
        if row.get("status") == "completed"
    )


def _invoke_spec(task: PilotTask, workspace: Path) -> Path:
    secret = settings.DEEPSEEK_API_KEY
    if secret is None:
        raise RuntimeError("DEEPSEEK_API_KEY is not configured")
    spec = {
        "run_id": RUN_ID,
        "task_id": task.instance_id,
        "task": task.problem_statement,
        "source_repo": "qr7896/agent-service-toolkit",
        "source_commit": task.base_commit,
        "checkpoint_path": str(workspace / ".codex" / "v3" / "checkpoints.sqlite"),
        "raw_trajectory_path": str(workspace / ".codex" / "v3" / "raw.jsonl"),
        "experience_path": str(EXPERIENCES),
        "chroma_path": str(CHROMA),
        "ledger_path": str(LEDGER),
        "total_token_ceiling": TOTAL_TOKEN_CEILING,
        "task_token_ceiling": TASK_TOKEN_CEILING,
        "max_calls_per_task": MAX_CALLS_PER_TASK,
        "max_output_tokens": MAX_OUTPUT_TOKENS,
        "max_tool_result_chars": MAX_TOOL_RESULT_CHARS,
        "tool_schema_reserve_tokens": TOOL_SCHEMA_RESERVE_TOKENS,
    }
    path = workspace / ".codex" / "v3" / "invoke.json"
    _write_json(path, spec)
    return path


def _sync_runtime_guard(workspace: Path) -> None:
    relative = Path("src/agents/model_budget.py")
    source = ROOT / relative
    target = workspace / relative
    if target.read_bytes() == source.read_bytes():
        return
    shutil.copy2(source, target)
    _git("add", relative.as_posix(), cwd=workspace)
    _git(
        "-c",
        "user.name=v3-pilot",
        "-c",
        "user.email=v3-pilot@local",
        "commit",
        "-q",
        "-m",
        "sync v3 provider guard",
        cwd=workspace,
    )


def _run_task(task: PilotTask) -> dict[str, Any]:
    workspace = PILOT_DIR / "workspaces" / task.instance_id
    _prepare(workspace, task)
    _sync_runtime_guard(workspace)
    spec = _invoke_spec(task, workspace)
    env = dict(os.environ)
    env["PYTHONPATH"] = str(workspace / "src")
    env["DEEPSEEK_API_KEY"] = settings.DEEPSEEK_API_KEY.get_secret_value()  # type: ignore[union-attr]
    try:
        result = subprocess.run(
            [sys.executable, "-c", CHILD, str(spec)],
            cwd=workspace,
            env=env,
            capture_output=True,
            text=True,
            timeout=1800,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "instance_id": task.instance_id,
            "status": "interrupted",
            "reason": "child_timeout",
            "stdout": str(exc.stdout or "")[-2000:],
            "stderr": str(exc.stderr or "")[-4000:],
            "workspace": str(workspace),
        }
    if result.returncode != 0:
        return {
            "instance_id": task.instance_id,
            "status": "interrupted",
            "returncode": result.returncode,
            "stdout": result.stdout[-2000:],
            "stderr": result.stderr[-4000:],
            "workspace": str(workspace),
        }

    raw_path = workspace / ".codex" / "v3" / "raw.jsonl"
    raw = json.loads(raw_path.read_text(encoding="utf-8").splitlines()[-1])
    grade = _grade(task, workspace)
    raw["external_grader"] = grade
    raw["test_result"] = {
        "status": "passed" if grade["passed"] else "failed",
        "passed": grade["passed"],
        "exit_code": grade["exit_code"],
        "summary": "hidden grader passed" if grade["passed"] else "hidden grader failed",
    }
    raw["status"] = "succeeded" if grade["passed"] else "failed"
    raw["final_success"] = grade["passed"]
    append_trajectory(raw, TRAJECTORIES)
    with ExperienceStore(EXPERIENCES) as store:
        created = store.record_trajectory(raw, root=workspace)

    artifact = PILOT_DIR / "artifacts" / task.instance_id
    artifact.mkdir(parents=True, exist_ok=True)
    patch = export_patch(workspace)
    (artifact / "patch.diff").write_text(patch["patch"], encoding="utf-8")
    _write_json(artifact / "trajectory.json", raw)
    _write_json(artifact / "grade.json", grade)
    return {
        "instance_id": task.instance_id,
        "status": raw["status"],
        "trajectory_id": raw["id"],
        "experience_ids": created,
        "provider_tokens_total": _spent(),
        "changed_files": patch["changed_files"],
        "workspace": str(workspace),
    }


def _run_pilot(manifest_path: Path) -> dict[str, Any]:
    manifest = _read_json(manifest_path, {})
    if manifest.get("collection_id") != RUN_ID or manifest.get("sealed_test") is not False:
        raise ValueError("expected the non-sealed v3-prospective-001 collection manifest")
    state = _read_json(
        STATE,
        {
            "protocol": "v3-prospective-pilot-run-v1",
            "run_id": RUN_ID,
            "model": "deepseek-flash",
            "token_ceiling": TOTAL_TOKEN_CEILING,
            "rows": [],
        },
    )
    completed = {row["instance_id"] for row in state["rows"] if row["status"] != "interrupted"}
    for task in TASKS:
        if task.instance_id in completed:
            continue
        if _spent() + TASK_RESERVE > TOTAL_TOKEN_CEILING:
            state["stop_reason"] = "next_task_reserve_does_not_fit"
            break
        row = _run_task(task)
        state["rows"] = [r for r in state["rows"] if r["instance_id"] != task.instance_id]
        state["rows"].append(row)
        state["provider_tokens_total"] = _spent()
        _write_json(STATE, state)
        if row["status"] == "interrupted":
            state["stop_reason"] = "task_interrupted_no_auto_retry"
            _write_json(STATE, state)
            break
    return state


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("preflight")
    run = sub.add_parser("run")
    run.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    artifact = _preflight() if args.command == "preflight" else _run_pilot(args.manifest)
    print(json.dumps(artifact, ensure_ascii=False, indent=2))
    if args.command == "preflight" and not artifact["ready"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
