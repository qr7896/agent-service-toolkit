from evals.evidence_runtime import WorkspaceRetrievalAdapter
from evals.safe_workspace import SafeWorkspace
from evals.semantic_adapter import SemanticAdapter


class Embedding:
    def embed_documents(self, texts):
        return [[1.0, 0.0] if "invoice" in text else [0.0, 1.0] for text in texts]

    def embed_query(self, _text):
        return [1.0, 0.0]


def test_semantic_adapter_uses_safe_workspace_and_ledger(tmp_path):
    (tmp_path / "billing.py").write_text("def invoice_total():\n    return 1\n")
    (tmp_path / "users.py").write_text("def user_name():\n    return 'x'\n")
    workspace = SafeWorkspace(tmp_path)
    semantic = SemanticAdapter(workspace, Embedding())
    adapter = WorkspaceRetrievalAdapter(workspace, semantic_adapter=semantic)

    hits = adapter.semantic("invoice", max_results=1)

    assert hits[0].path == "billing.py" and hits[0].source == "semantic"
    assert hits[0].symbol == "invoice_total" and hits[0].score == 1.0
    assert adapter.ledger.summary()["actions"][0]["action"] == "semantic"
    assert workspace.evidence_summary()["read_calls"] == 2
