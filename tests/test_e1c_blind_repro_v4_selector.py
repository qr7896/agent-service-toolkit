import json

from evals.e1c_blind_repro_v4_selector import CONTAMINATED_IDS, reserve_status


def test_v4_reserve_fails_closed_when_missing(tmp_path) -> None:
    result = reserve_status(tmp_path / "missing.json")
    assert result["ready"] is False
    assert result["new_task_tree_touched"] is False


def test_v4_reserve_rejects_contaminated_id(tmp_path) -> None:
    path = tmp_path / "reserve.json"
    contaminated = sorted(CONTAMINATED_IDS)[0]
    path.write_text(
        json.dumps({
            "source": "external_disjoint_canary_reserve",
            "identity_frozen_before_statement_materialization": True,
            "tasks": [
                {"instance_id": contaminated, "repo": "x/y", "base_commit": "a" * 40, "image": "swebench/x:latest"},
                {"instance_id": "fresh-2", "repo": "x/y", "base_commit": "b" * 40, "image": "swebench/y:latest"},
                {"instance_id": "fresh-3", "repo": "x/y", "base_commit": "c" * 40, "image": "swebench/z:latest"},
            ],
        }),
        encoding="utf-8",
    )
    result = reserve_status(path)
    assert result["ready"] is False
    assert result["overlap_with_contaminated"] == [contaminated]


def test_v4_reserve_accepts_metadata_only_disjoint_identity(tmp_path) -> None:
    path = tmp_path / "reserve.json"
    path.write_text(
        json.dumps({
            "source": "external_disjoint_canary_reserve",
            "identity_frozen_before_statement_materialization": True,
            "tasks": [
                {"instance_id": f"fresh-{i}", "repo": "x/y", "base_commit": str(i) * 40, "image": f"swebench/fresh-{i}:latest"}
                for i in range(1, 4)
            ],
        }),
        encoding="utf-8",
    )
    result = reserve_status(path)
    assert result["ready"] is True
    assert result["forbidden_metadata_keys"] == []


def test_v4_reserve_rejects_context_exposed_candidate(tmp_path) -> None:
    path = tmp_path / "reserve.json"
    path.write_text(
        json.dumps({
            "source": "external_disjoint_canary_reserve",
            "identity_frozen_before_statement_materialization": True,
            "tasks": [
                {"instance_id": "sympy__sympy-20590", "repo": "sympy/sympy", "base_commit": "a" * 40, "image": "swebench/x:latest"},
                {"instance_id": "fresh-2", "repo": "x/y", "base_commit": "b" * 40, "image": "swebench/y:latest"},
                {"instance_id": "fresh-3", "repo": "x/y", "base_commit": "c" * 40, "image": "swebench/z:latest"},
            ],
        }),
        encoding="utf-8",
    )
    result = reserve_status(path)
    assert result["ready"] is False
    assert result["overlap_with_contaminated"] == ["sympy__sympy-20590"]
