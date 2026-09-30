import json

import pytest

from evals.e1b_autonomous_harness import (
    FORBIDDEN_GOLD_KEYS,
    MAX_PATCH_CONTENT_BYTES,
    apply_patch,
    dev_tasks,
    parse_patch_response,
    run_dev_with_editor,
    sanitize_editor_payload,
    validate_patch,
    validate_write_path,
)
from evals.e1b_autonomous_protocol import AutonomousConfig


def test_dev_only_and_no_gold_leakage():
    tasks = dev_tasks()
    assert len(tasks) == 4
    for task in tasks:
        payload = sanitize_editor_payload(task, {"files": ["src/example.py"]})
        assert not FORBIDDEN_GOLD_KEYS.intersection(payload)
        assert "problem_statement" in payload


@pytest.mark.parametrize("path", ["test_x.py", "tests/test_x.py", "src/test_x.py"])
def test_test_writes_blocked(path):
    with pytest.raises(PermissionError):
        validate_write_path(path)


@pytest.mark.parametrize("path", ["../secret.py", "/tmp/x.py", "C:/tmp/x.py"])
def test_workspace_escape_blocked(path):
    with pytest.raises(PermissionError):
        validate_write_path(path)


def test_patch_file_budget():
    cfg = AutonomousConfig(max_files_written=2)
    with pytest.raises(PermissionError):
        validate_patch({"a.py": "a", "b.py": "b", "c.py": "c"}, cfg)
    assert validate_patch({"a.py": "a", "b.py": "b"}, cfg) == {"a.py": "a", "b.py": "b"}


def test_structured_patch_contract():
    assert parse_patch_response({"patch": {"src/a.py": "x"}}) == {"src/a.py": "x"}
    with pytest.raises(ValueError):
        parse_patch_response({"patch": {}, "reason": "leak"})
    with pytest.raises(ValueError):
        parse_patch_response("not-json")


def test_dev_runner_with_deterministic_editor():
    def editor(payload):
        task = next(t for t in dev_tasks() if t.instance_id == payload["instance_id"])
        return {"patch": task.gold_sources}

    rows = run_dev_with_editor(
        editor, lambda task: {"files": sorted(task.setup_files), "contents": task.setup_files}
    )
    assert len(rows) == 4
    assert all(not r["base_resolved"] for r in rows)
    assert all(r["resolved"] for r in rows)


def test_async_model_adapter_without_network():
    import asyncio

    from evals.e1b_editor_adapter import propose_patch

    class R:
        content = '{"patch":{"src/a.py":"x"}}'

    class M:
        async def ainvoke(self, messages):
            assert messages[0][0] == "system"
            assert "gold_sources" not in messages[1][1]
            return R()

    payload = {
        "instance_id": "dev",
        "problem_statement": "fix",
        "evidence": {"contents": {"src/a.py": "bad"}},
    }
    raw = asyncio.run(propose_patch(M(), payload))
    assert parse_patch_response(raw) == {"src/a.py": "x"}


def test_review_adapter_sees_same_public_payload_and_candidate_only():
    from evals.e1b_editor_adapter import build_review_messages

    payload = {
        "instance_id": "dev",
        "problem_statement": "fix both visible layers",
        "evidence": {"items": [{"path": "src/a.py", "content": "bad"}]},
    }
    messages = build_review_messages(payload, {"src/a.py": "better"})
    body = messages[1][1]
    assert messages[0][0] == "system"
    assert '"candidate_patch"' in body
    assert '"src/a.py": "better"' in body
    assert "gold_" not in body


def test_usage_metadata_is_normalized():
    from evals.e1b_editor_adapter import usage_tokens

    class Response:
        usage_metadata = {"input_tokens": 10, "output_tokens": 4, "total_tokens": 14}
        response_metadata = {}

    assert usage_tokens(Response()) == {
        "input_tokens": 10,
        "output_tokens": 4,
        "total_tokens": 14,
    }


def test_live_resume_selects_only_budget_exhaustion(tmp_path, monkeypatch):
    from evals import e1b_run_dev_live

    result = tmp_path / "run.json"
    result.write_text(
        json.dumps(
            {
                "summary": {"total_tokens": 100},
                "rows": [
                    {"instance_id": "done", "failure": None},
                    {"instance_id": "pending", "failure": "budget_exhaustion"},
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(e1b_run_dev_live, "RESULT_PATH", result)
    rows, pending, spent, ceiling = e1b_run_dev_live.resume_state(50)
    assert [row["instance_id"] for row in rows] == ["done"]
    assert pending == {"pending"}
    assert (spent, ceiling) == (100, 150)


def test_r10_v2_uses_one_thinking_disabled_call_per_task(tmp_path, monkeypatch):
    from evals import e1b_run_dev_live

    monkeypatch.setattr(e1b_run_dev_live, "LEDGER_PATH", tmp_path / "calls.jsonl")
    config = e1b_run_dev_live.provider_config("dev-task")
    values = config["configurable"]
    assert values["provider_task_token_ceiling"] == 2_200
    assert values["provider_max_calls_per_task"] == 1
    assert values["provider_max_output_tokens"] == 600
    assert values["provider_disable_thinking"] is True


def test_r10_v3_uses_bounded_two_pass_review(tmp_path, monkeypatch):
    from evals import e1b_run_dev_live_v3

    monkeypatch.setattr(e1b_run_dev_live_v3, "LEDGER_PATH", tmp_path / "calls.jsonl")
    values = e1b_run_dev_live_v3.provider_config("dev-task")["configurable"]
    assert values["provider_task_token_ceiling"] == 4_000
    assert values["provider_total_token_ceiling"] == 16_000
    assert values["provider_max_calls_per_task"] == 2
    assert values["provider_max_output_tokens"] == 600
    assert values["provider_disable_thinking"] is True


def test_r10_v3_preflight_is_zero_call_and_reserve_safe():
    from evals.e1b_run_dev_live_v3 import preflight

    report = preflight()
    assert report["provider_calls"] == 0
    assert report["ready"] is True
    assert len(report["rows"]) == 4
    assert all(row["proposal_reserve_fits"] for row in report["rows"])
    assert all(row["review_reserve_fits"] for row in report["rows"])


def test_dev_v2_audit_marks_valid_failed_result_without_freeze():
    from evals.e1b_dev_audit import audit

    old = {
        "summary": {"tasks": 1, "resolved": 1, "total_model_calls": 1, "total_tokens": 100},
        "rows": [{"instance_id": "x", "resolved": True, "patch_sha256": "a"}],
    }
    current = {
        "summary": {
            "tasks": 1,
            "resolved": 0,
            "total_model_calls": 1,
            "total_tokens": 50,
            "budget_exhaustions": 0,
            "model_failures": 0,
            "parse_failures": 0,
        },
        "execution": {"budget_status": "within_limit"},
        "rows": [
            {
                "instance_id": "x",
                "resolved": False,
                "patch_sha256": "a",
                "fail_to_pass": {"fix": False},
                "pass_to_pass": {"regression": True},
            }
        ],
    }
    report = audit(old, current)
    assert report["status"] == "valid_failed_dev"
    assert report["budget_and_call_chain_valid"] is True
    assert report["freeze_ready"] is False
    assert report["regressed_from_old_dev"] == ["x"]
    assert report["repeated_failed_patch"] == ["x"]


def test_dev_v3_audit_marks_partial_and_not_freeze_ready():
    from evals.e1b_dev_v3_audit import audit

    v2 = {
        "summary": {"tasks": 1},
        "rows": [{"instance_id": "x", "resolved": False}],
    }
    v3 = {
        "summary": {"tasks": 1, "resolved": 1, "parse_failures": 0, "model_failures": 0, "budget_exhaustions": 0, "total_model_calls": 2, "total_tokens": 100},
        "execution": {"original_token_budget": 1000, "test_outcomes_opened": 0},
        "rows": [{"instance_id": "x", "resolved": True, "review_changed_patch": True, "fail_to_pass": {"fix": True}, "pass_to_pass": {"keep": True}}],
    }
    report = audit(v2, v3)
    assert report["protocol_valid"] is False
    assert report["freeze_ready"] is False


def test_r10_v4_contract_review_preflight_is_zero_call_and_safe():
    from evals.e1b_run_dev_live_v4 import preflight, provider_config

    report = preflight()
    assert report["provider_calls"] == 0
    assert report["ready"] is True
    assert len(report["rows"]) == 4
    assert all(row["proposal_reserve_fits"] for row in report["rows"])
    assert all(row["review_reserve_fits"] for row in report["rows"])
    values = provider_config("dev-task")["configurable"]
    assert values["provider_max_calls_per_task"] == 2
    assert values["provider_max_output_tokens"] == 550
    assert values["provider_task_token_ceiling"] == 4_000
    assert values["provider_total_token_ceiling"] == 16_000


def test_r10_v6_deterministic_contract_preflight_is_zero_call_and_safe():
    from evals.e1b_run_dev_live_v6 import preflight, provider_config

    report = preflight()
    assert report["provider_calls"] == 0
    assert len(report["rows"]) == 4
    assert all(row["proposal_reserve_fits"] for row in report["rows"])
    assert all(row["review_reserve_fits"] for row in report["rows"])
    if report["result_exists"] or report["ledger_exists"]:
        assert report["ready"] is False
    else:
        assert report["ready"] is True
    values = provider_config("dev-task")["configurable"]
    assert values["provider_max_calls_per_task"] == 2
    assert values["provider_max_output_tokens"] == 550
    assert values["provider_task_token_ceiling"] == 4_000
    assert values["provider_total_token_ceiling"] == 16_000


def test_r10_v6_contract_audit_uses_dev_public_statements_only():
    from evals.e1b_contract_audit_v6 import audit

    report = audit()
    assert report["provider_calls"] == 0
    assert report["scope"] == "DEV public problem statements only"
    assert report["valid"] is True
    assert len(report["rows"]) == 4
    assert all(row["default_transition"] == "identity" for row in report["rows"])


def test_run_identity_and_dry_run_artifact(tmp_path):
    from evals.e1b_autonomous_runlog import experiment_identity, write_dev_run

    a = experiment_identity("fake-model")
    b = experiment_identity("fake-model")
    assert a == b and len(a["config_sha256"]) == 64 and len(a["prompt_sha256"]) == 64
    report = write_dev_run("fake-model", [], dry_run=True, output=tmp_path / "run.json")
    assert report["dry_run"] is True
    assert report["scope"] == "DEV only; sealed TEST outcomes unopened"
    assert report["summary"]["total_model_calls"] == 0


def test_recursive_gold_leakage_blocked():
    task = dev_tasks()[0]
    with pytest.raises(ValueError):
        sanitize_editor_payload(task, {"nested": [{"gold_secret": "nope"}]})


@pytest.mark.parametrize("path", [".git/config", ".env", ".codex/state.json"])
def test_protected_paths_blocked(path):
    with pytest.raises(PermissionError):
        validate_write_path(path)


def test_patch_content_must_be_string():
    with pytest.raises(TypeError):
        validate_patch({"src/a.py": {"not": "text"}})


def test_normalized_path_collision_blocked():
    with pytest.raises(ValueError):
        validate_patch({"a.py": "x", "./a.py": "y"})


def test_patch_content_limit():
    with pytest.raises(PermissionError):
        validate_patch({"a.py": "x" * (MAX_PATCH_CONTENT_BYTES + 1)})


def test_apply_patch_resolved_root_containment(tmp_path):
    apply_patch(tmp_path, {"src/a.py": "x"})
    assert (tmp_path / "src/a.py").read_text() == "x"
