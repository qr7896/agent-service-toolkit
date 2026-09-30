import json

from evals.e1c_strict_v7_dev_replay import build


def test_dev_replay_is_explicitly_non_independent(tmp_path, monkeypatch) -> None:
    source = tmp_path / "v6.json"
    source.write_text(
        json.dumps(
            {
                "rows": [
                    {
                        "instance_id": "dev-only",
                        "witness_status": "no_reproducer",
                        "bundle": {
                            "issue": "normalize() should clear the cache.",
                            "localization": {
                                "candidates": [
                                    {
                                        "path": "pkg/engine.py",
                                        "symbol": "normalize",
                                        "source_sha256": "a" * 64,
                                        "text": "def normalize(): pass",
                                    }
                                ]
                            },
                        },
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    result = build(source)
    assert result["independent_evidence"] is False
    assert result["may_open_c5"] is False
    assert result["may_open_dev30"] is False
    assert result["may_open_fresh30"] is False
    assert result["typed_candidate_task_count"] == 1
