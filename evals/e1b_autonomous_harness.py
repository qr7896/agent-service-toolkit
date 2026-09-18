import json
import tempfile
from pathlib import Path

from evals.e1b_autonomous_protocol import AutonomousConfig, public_task
from evals.protocol_paths import E1_B_EVAL_SPLIT, E1_B_TASKS
from evals.swe_tasks import grade, load_tasks, prepare

FORBIDDEN_GOLD_KEYS = {
    "gold_sources",
    "gold_files",
    "gold_symbols",
    "gold_callers",
    "gold_tests",
    "gold_context",
}
TEST_PREFIXES = ("test_", "tests/")
PROTECTED_PREFIXES = (".git/", ".env", ".codex/")
MAX_PATCH_CONTENT_BYTES = 200_000


def assert_no_gold_keys(value):
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key).lower().startswith("gold_") or key in FORBIDDEN_GOLD_KEYS:
                raise ValueError(f"gold leakage blocked: {key}")
            assert_no_gold_keys(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            assert_no_gold_keys(child)


def sanitize_editor_payload(task, evidence=None):
    payload = public_task(task)
    payload["evidence"] = evidence or {}
    assert_no_gold_keys(payload)
    return payload


def validate_write_path(path, config=None):
    config = config or AutonomousConfig()
    raw = str(path).replace(chr(92), "/")
    if raw.startswith("../") or raw.startswith("/") or ":" in raw:
        raise PermissionError(f"workspace escape blocked: {path}")
    normalized = raw[2:] if raw.startswith("./") else raw
    if not normalized or normalized in {".", ".."} or "/../" in f"/{normalized}/":
        raise PermissionError(f"workspace escape blocked: {path}")
    if normalized.startswith(PROTECTED_PREFIXES):
        raise PermissionError(f"protected path blocked: {path}")
    if not config.allow_test_file_writes and (
        normalized.startswith(TEST_PREFIXES) or "/test_" in normalized
    ):
        raise PermissionError(f"test write blocked: {path}")
    return normalized


def validate_patch(patch, config=None):
    config = config or AutonomousConfig()
    if not isinstance(patch, dict):
        raise TypeError("patch must be a mapping of relative path to content")
    if len(patch) > config.max_files_written:
        raise PermissionError("max_files_written exceeded")
    normalized = {}
    for path, content in patch.items():
        if not isinstance(content, str):
            raise TypeError("patch content must be a string")
        if len(content.encode("utf-8")) > MAX_PATCH_CONTENT_BYTES:
            raise PermissionError("patch content byte limit exceeded")
        rel = validate_write_path(path, config)
        if rel in normalized:
            raise ValueError(f"normalized path collision: {rel}")
        normalized[rel] = content
    return normalized


def parse_patch_response(response):
    if isinstance(response, str):
        response = json.loads(response)
    if not isinstance(response, dict) or set(response) != {"patch"}:
        raise ValueError("editor response must contain only a patch object")
    return validate_patch(response["patch"])


def resolve_write_target(root, rel):
    root = Path(root).resolve()
    target = (root / rel).resolve()
    if target != root and root not in target.parents:
        raise PermissionError(f"resolved workspace escape blocked: {rel}")
    return target


def apply_patch(root, patch):
    written = []
    for rel, content in validate_patch(patch).items():
        target = resolve_write_target(root, rel)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        written.append(rel)
    return written


def run_dev_with_editor(editor, evidence_builder=None):
    rows = []
    with tempfile.TemporaryDirectory(prefix="e1b-auto-dev-") as d:
        base = Path(d)
        for task in dev_tasks():
            root = base / task.instance_id
            prepare(task, root)
            before = grade(task, root)
            evidence = evidence_builder(task) if evidence_builder else {}
            payload = sanitize_editor_payload(task, evidence)
            response = editor(payload)
            patch = parse_patch_response(response)
            written = apply_patch(root, patch)
            after = grade(task, root)
            rows.append(
                {
                    "instance_id": task.instance_id,
                    "base_resolved": before["resolved"],
                    "resolved": after["resolved"],
                    "files_written": written,
                    "fail_to_pass": after["fail_to_pass"],
                    "pass_to_pass": after["pass_to_pass"],
                }
            )
    return rows


def dev_tasks():
    split = json.loads(E1_B_EVAL_SPLIT.read_text(encoding="utf-8"))
    by_id = {t.instance_id: t for t in load_tasks(E1_B_TASKS)}
    return [by_id[i] for i in split["dev_ids"]]


def main():
    tasks = dev_tasks()
    payloads = [sanitize_editor_payload(t) for t in tasks]
    print(
        json.dumps(
            {
                "dev_tasks": len(tasks),
                "payloads_sanitized": len(payloads),
                "model_calls": 0,
                "test_outcomes_opened": 0,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
