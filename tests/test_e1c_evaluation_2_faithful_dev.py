import pytest

from evals.e1c_evaluation_2_faithful_dev import augmented, messages


def test_new_terminal_window_and_safe_fixture_are_in_actual_model_view():
    old = {"issue": "Inputs should work.", "windows": [{"path": "pkg/old.py", "symbol": "seed", "text": "def seed(): pass"}], "input_sha256": "old"}
    facts = {"statement_sha256": "public", "blocks": [{"facts": [{"kind": "fixture_binding", "name": "x", "value": {"kind": "reference", "name": "object"}}]}],
             "terminal_production_windows": [{"path": "pkg/api.py", "symbol": "fit", "text": "def fit(X): return X"}]}
    value = augmented(old, facts)
    assert value["windows"][0]["symbol"] == "fit" and len(value["windows"]) <= 4
    assert "object" in messages(value, "B")[-1].content
    assert value["public_statement_sha256"] == "public"


def test_faithful_context_cannot_silently_overrun_evidence_budget():
    old = {"issue": "Inputs should work.", "windows": [], "input_sha256": "old"}
    facts = {"statement_sha256": "public", "blocks": [{"value": "x" * 24000}], "terminal_production_windows": [{"path": "pkg/api.py", "text": "code"}]}
    with pytest.raises(ValueError, match="budget"):
        augmented(old, facts)
