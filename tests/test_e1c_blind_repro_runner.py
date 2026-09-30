from evals.e1c_blind_repro_runner import _repair_payload, _summary


def _bundle() -> dict:
    return {
        "problem_statement": "Thing should behave correctly.",
        "base_commit": "a" * 40,
        "structured_evidence": {
            "contract": {"schema": "contract", "symbols": ["Thing"]},
            "windows": [
                {
                    "path": "pkg/core.py",
                    "start_line": 1,
                    "end_line": 2,
                    "text": "class Thing:\n    pass",
                    "origin": "issue_ast_definition",
                    "depth": 0,
                    "source_sha256": "b" * 64,
                }
            ],
        },
        "reproducer_context": {
            "status": "reproduced_failure",
            "kind": "issue_snippet",
            "exit_code": 1,
            "tail": "TypeError: bad",
            "log_sha256": "c" * 64,
        },
    }


def test_reproducer_canary_arms_share_structural_evidence() -> None:
    bundle = _bundle()
    baseline = _repair_payload(bundle, arm="baseline")
    treatment = _repair_payload(bundle, arm="treatment")
    assert baseline["candidate_paths"] == treatment["candidate_paths"]
    assert baseline["excerpts"] == treatment["excerpts"]
    assert baseline["contract"] == treatment["contract"]
    assert baseline["reproducer"]["status"] == "withheld_from_baseline"
    assert treatment["reproducer"]["status"] == "reproduced_failure"


def test_reproducer_summary_only_opens_c5_for_treatment_only_gain() -> None:
    rows = [
        {"instance_id": "a", "arm": "baseline", "resolved": False, "usages": []},
        {"instance_id": "a", "arm": "treatment", "resolved": True, "usages": []},
        {"instance_id": "b", "arm": "baseline", "resolved": False, "usages": []},
        {"instance_id": "b", "arm": "treatment", "resolved": False, "usages": []},
    ]
    result = _summary(rows)
    assert result["treatment_only_resolved"] == ["a"]
    assert result["baseline_only_resolved"] == []
    assert result["expand_c5"] is True
