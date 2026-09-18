import pytest

from evals.evidence_runtime import EvidenceItem, EvidenceLedger, WorkspaceRetrievalAdapter
from evals.safe_workspace import SafeWorkspace


def test_ledger_deduplicates_and_scores_cost_risk():
    ledger = EvidenceLedger()
    a = EvidenceItem("a.py", "x", "lexical")
    first = ledger.add("lexical", [a])
    second = ledger.add("lexical", [a])
    assert first["new"] == 1 and second["new"] == 0
    assert second["redundancy"] == 1.0
    s = ledger.summary()
    assert s["unique_evidence"] == 1 and s["total_cost"] == 2.2 and s["total_risk"] == 0.6


def test_unknown_action_blocked():
    with pytest.raises(ValueError):
        EvidenceLedger().add("magic", [])


def test_workspace_adapter_produces_uniform_evidence(tmp_path):
    (tmp_path / "a.py").write_text("def alpha(): return 1")
    adapter = WorkspaceRetrievalAdapter(SafeWorkspace(tmp_path))
    listed = adapter.files()
    hits = adapter.lexical("alpha")
    full = adapter.read("a.py")
    assert listed[0].source == "files"
    assert hits[0].path == "a.py" and hits[0].source == "lexical"
    assert full.content.startswith("def alpha")
    assert adapter.ledger.summary()["action_count"] == 3


def test_payload_is_serializable_shape():
    ledger = EvidenceLedger()
    ledger.add("structural", [EvidenceItem("a.py", "caller", "structural", 0.8, "foo")])
    assert ledger.payload() == [
        {
            "path": "a.py",
            "content": "caller",
            "source": "structural",
            "score": 0.8,
            "symbol": "foo",
            "relation_type": None,
            "depth": None,
            "origin": None,
        }
    ]


def test_structural_adapter_integration(tmp_path):
    from evals.codegraph_adapter import CodeGraphAdapter

    (tmp_path / "a.py").write_text("def target(): return 1")
    ws = SafeWorkspace(tmp_path)
    adapter = WorkspaceRetrievalAdapter(ws, structural_adapter=CodeGraphAdapter(ws))
    hits = adapter.structural("target", "symbols")
    assert hits[0].symbol == "target"
    assert adapter.ledger.summary()["actions"][0]["action"] == "structural"
