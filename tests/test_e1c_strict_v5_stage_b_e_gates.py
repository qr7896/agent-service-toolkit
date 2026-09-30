import json

import evals.e1c_strict_v5_engineering_readiness as aggregate
import evals.e1c_strict_v5_stage_b_gate as stage_b
import evals.e1c_strict_v5_stage_c_gate as stage_c
import evals.e1c_strict_v5_stage_d_gate as stage_d
import evals.e1c_strict_v5_stage_e_gate as stage_e


def test_stage_b_gate_is_ready_and_does_not_open_live(tmp_path) -> None:
    result = stage_b.build(tmp_path / "b.json")
    assert result["stage_b_ready"] is True
    assert all(result["checks"].values())
    assert result["live_allowed"] is False


def test_stage_c_gate_requires_exact_30_row_taxonomy(tmp_path, monkeypatch) -> None:
    taxonomy = tmp_path / "taxonomy.json"
    pareto = tmp_path / "pareto.json"
    taxonomy.write_text(
        json.dumps(
            {
                "denominator": 30,
                "provider_calls": 0,
                "runtime_answer_hints_exported": False,
                "rows": [
                    {"instance_id": f"x__{i}", "primary_failure": "failure"}
                    for i in range(30)
                ],
            }
        ),
        encoding="utf-8",
    )
    pareto.write_text(
        json.dumps(
            {
                "denominator": 30,
                "provider_calls": 0,
                "runtime_input": "aggregate_categories_only",
                "categories": [{"category": "failure", "count": 30}],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(stage_c, "TAXONOMY", taxonomy)
    monkeypatch.setattr(stage_c, "PARETO", pareto)
    result = stage_c.build(tmp_path / "c.json")
    assert result["stage_c_ready"] is True
    assert result["denominator"] == 30
    assert result["live_allowed"] is False


def test_stage_d_gate_separates_engineering_from_canary_coverage(tmp_path) -> None:
    result = stage_d.build(tmp_path / "d.json")
    assert result["stage_d_engineering_ready"] is True
    assert result["independent_canary_trusted_reproducer_requirement_met"] is False
    assert result["live_allowed"] is False


def test_stage_e_gate_is_ready_but_not_official_repair(tmp_path) -> None:
    result = stage_e.build(tmp_path / "e.json")
    assert result["stage_e_engineering_ready"] is True
    assert result["official_repair_claim_allowed"] is False
    assert result["live_allowed"] is False


def test_aggregate_a_e_ready_still_keeps_live_closed(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        aggregate,
        "stage_a",
        lambda: {"stage_a_ready": True},
    )
    monkeypatch.setattr(
        aggregate,
        "stage_b",
        lambda: {"stage_b_ready": True},
    )
    monkeypatch.setattr(
        aggregate,
        "stage_c",
        lambda: {"stage_c_ready": True},
    )
    monkeypatch.setattr(
        aggregate,
        "stage_d",
        lambda: {"stage_d_engineering_ready": True},
    )
    monkeypatch.setattr(
        aggregate,
        "stage_e",
        lambda: {"stage_e_engineering_ready": True},
    )
    result = aggregate.build(tmp_path / "all.json")
    assert result["engineering_ready_a_through_e"] is True
    assert result["independent_canary_admission_ready"] is False
    assert result["live_allowed"] is False
    assert result["c5_allowed"] is False
    assert result["fresh30_allowed"] is False
