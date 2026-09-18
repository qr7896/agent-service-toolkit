import hashlib
import json
from pathlib import Path

from evals.e1b_autonomous_protocol import AutonomousConfig
from evals.e1b_editor_adapter import SYSTEM
from evals.protocol_paths import E1_B_EVAL_SPLIT, E1_B_TASKS

OUT = Path("evals/results/e1b_autonomous_dev_run.json")


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha_file(path):
    return sha_bytes(Path(path).read_bytes())


def experiment_identity(model_id, config=None):
    config = config or AutonomousConfig()
    payload = {
        "model_id": model_id,
        "prompt_sha256": sha_bytes(SYSTEM.encode()),
        "max_iterations": config.max_iterations,
        "max_files_written": config.max_files_written,
        "allow_test_file_writes": config.allow_test_file_writes,
        "split_sha256": sha_file(E1_B_EVAL_SPLIT),
        "tasks_sha256": sha_file(E1_B_TASKS),
    }
    payload["config_sha256"] = sha_bytes(json.dumps(payload, sort_keys=True).encode())
    return payload


def summarize_rows(rows):
    n = len(rows)
    resolved = sum(bool(r.get("resolved")) for r in rows)
    return {
        "tasks": n,
        "attempted_tasks": sum(int(r.get("model_calls", 0)) > 0 for r in rows),
        "resolved": resolved,
        "resolved_fraction": resolved / n if n else 0.0,
        "parse_failures": sum(r.get("failure") == "parse_failure" for r in rows),
        "model_failures": sum(r.get("failure") == "model_failure" for r in rows),
        "budget_exhaustions": sum(r.get("failure") == "budget_exhaustion" for r in rows),
        "total_model_calls": sum(int(r.get("model_calls", 0)) for r in rows),
        "input_tokens": sum(int(r.get("input_tokens", 0)) for r in rows),
        "output_tokens": sum(int(r.get("output_tokens", 0)) for r in rows),
        "total_tokens": sum(int(r.get("total_tokens", 0)) for r in rows),
        "wall_time_ms": sum(float(r.get("wall_time_ms", 0)) for r in rows),
    }


def write_dev_run(model_id, rows, dry_run=False, config=None, output=OUT):
    report = {
        "protocol": "e1b-autonomous-dev-run-v0",
        "scope": "DEV only; sealed TEST outcomes unopened",
        "dry_run": dry_run,
        "identity": experiment_identity(model_id, config),
        "summary": summarize_rows(rows),
        "rows": rows,
    }
    Path(output).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report
