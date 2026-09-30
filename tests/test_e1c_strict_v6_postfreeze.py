import base64
import json
from contextlib import contextmanager
from pathlib import Path

from evals.e1c_strict_v6_postfreeze import certify_identity, run
from evals.e1c_strict_v6_postfreeze import fetch_statement


def _manifest() -> dict:
    return {
        "schema": "e1c-strict-v6-external-canary-reserve-v1",
        "source": "official_swebench_task_repo_task_yaml",
        "source_revision": "rev",
        "identity_frozen_before_statement_materialization": True,
        "selection_salt": "salt",
        "tasks": [
            {
                "instance_id": f"task-{index}",
                "repo": "owner/repo",
                "base_commit": str(index) * 40,
                "image": f"image-{index}",
            }
            for index in range(1, 4)
        ],
        "provider_calls": 0,
        "task_content_inspected": False,
    }


def test_certify_identity_rejects_boundary_drift(tmp_path: Path, monkeypatch) -> None:
    manifest = tmp_path / "manifest.json"
    prereg = tmp_path / "prereg.json"
    boundary = tmp_path / "boundary.json"
    manifest.write_text(json.dumps(_manifest()), encoding="utf-8")
    prereg.write_text(
        json.dumps(
            {
                "provider_calls": 0,
                "live_allowed_before_admission": False,
                "selection_salt": "salt",
            }
        ),
        encoding="utf-8",
    )
    boundary.write_text(
        json.dumps({"selection_salt": "salt", "task_repo_revision": "rev", "x": 1}),
        encoding="utf-8",
    )
    monkeypatch.setattr("evals.e1c_strict_v6_postfreeze.MANIFEST", manifest)
    monkeypatch.setattr("evals.e1c_strict_v6_postfreeze.PREREG", prereg)
    monkeypatch.setattr("evals.e1c_strict_v6_postfreeze.BOUNDARY", boundary)
    monkeypatch.setattr(
        "evals.e1c_strict_v6_postfreeze.build_selection_boundary",
        lambda: {"selection_salt": "salt", "task_repo_revision": "rev", "x": 2},
    )
    result = certify_identity()
    assert result["ready"] is False
    assert result["checks"]["boundary_current"] is False


def test_run_materializes_only_frozen_statements_and_builds_witness_gate(
    tmp_path: Path, monkeypatch
) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps(_manifest()), encoding="utf-8")
    root_out = tmp_path / "postfreeze"
    summary = tmp_path / "summary.json"
    monkeypatch.setattr("evals.e1c_strict_v6_postfreeze.ROOT", tmp_path)
    monkeypatch.setattr("evals.e1c_strict_v6_postfreeze.MANIFEST", manifest)
    monkeypatch.setattr("evals.e1c_strict_v6_postfreeze.ROOT_OUT", root_out)
    monkeypatch.setattr(
        "evals.e1c_strict_v6_postfreeze.certify_identity",
        lambda: {
            "ready": True,
            "reason": "strict_v6_identity_certified",
            "source_revision": "rev",
        },
    )
    fetched = []

    def fake_fetch(instance_id: str, revision: str) -> tuple[str, str]:
        fetched.append((instance_id, revision))
        return f"foo({len(fetched)}) should return 1", "a" * 64

    def fake_source(task: dict, destination: Path) -> dict:
        destination.mkdir(parents=True)
        return {"ready": True, "status": "materialized", "head": task["base_commit"]}

    def fake_bundle(**kwargs) -> dict:
        index = int(kwargs["statement"].split("(")[1].split(")")[0])
        witnesses = [{"id": index}] if index < 3 else []
        return {
            "witness_plan": {
                "status": "candidate_executable_witnesses" if witnesses else "no_reproducer",
                "witnesses": witnesses,
            }
        }

    monkeypatch.setattr("evals.e1c_strict_v6_postfreeze.fetch_statement", fake_fetch)
    monkeypatch.setattr("evals.e1c_strict_v6_postfreeze.materialize_source", fake_source)
    monkeypatch.setattr("evals.e1c_strict_v6_postfreeze.build_bundle", fake_bundle)
    result = run(output=summary)
    assert fetched == [("task-1", "rev"), ("task-2", "rev"), ("task-3", "rev")]
    assert result["candidate_reproducer_task_count"] == 2
    assert result["image_pull_allowed_by_candidate_gate"] is True
    assert result["provider_calls"] == 0
    assert all(row["forbidden_task_files_read"] == [] for row in result["rows"])
    assert not list(tmp_path.rglob("tests.json"))
    assert not list(tmp_path.rglob("gold.patch"))


def test_fetch_statement_falls_back_to_fixed_revision_contents_api(monkeypatch) -> None:
    calls = []

    @contextmanager
    def fake_urlopen(request, timeout):
        calls.append(request.full_url)
        if "raw.githubusercontent.com" in request.full_url:
            raise OSError("raw unavailable")
        payload = json.dumps(
            {"content": base64.b64encode(b"foo() should return 1").decode("ascii")}
        ).encode("utf-8")

        class Response:
            def read(self):
                return payload

        yield Response()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    statement, digest = fetch_statement("task-a", "a" * 40)
    assert statement == "foo() should return 1"
    assert len(digest) == 64
    assert len(calls) == 3
    assert calls[-1].endswith("?ref=" + "a" * 40)
