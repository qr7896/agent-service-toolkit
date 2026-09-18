from evals.codegraph_adapter import CodeGraphAdapter
from evals.evidence_controller import EvidenceController
from evals.evidence_policy import EvidenceBudget, EvidencePolicy
from evals.evidence_runtime import WorkspaceRetrievalAdapter
from evals.safe_workspace import SafeWorkspace


def make_controller(tmp_path, max_actions=3):
    (tmp_path / "a.py").write_text("def alpha(): return 1")
    adapter = WorkspaceRetrievalAdapter(SafeWorkspace(tmp_path))
    policy = EvidencePolicy(EvidenceBudget(max_actions=max_actions, max_cost=10, max_risk=10))
    return EvidenceController(adapter, policy)


def test_controller_step_executes_and_updates_ledger(tmp_path):
    c = make_controller(tmp_path)
    row = c.step(["lexical"], {"lexical": {"query": "alpha"}}, {"lexical": 1.0})
    assert row["action"] == "lexical" and row["reason"] == "executed"
    assert row["items"] == 1
    assert row["after"]["spent"]["actions"] == 1


def test_controller_policy_stop(tmp_path):
    c = make_controller(tmp_path)
    row = c.step(["lexical"], {"lexical": {"query": "alpha"}}, {"lexical": 0.0})
    assert row["action"] == "stop" and row["reason"] == "policy_stop"


def test_controller_records_execution_error(tmp_path):
    c = make_controller(tmp_path)
    row = c.step(["semantic"], {"semantic": {"query": "alpha"}}, {"semantic": 1.0})
    assert row["reason"] == "execution_error"
    assert row["error"] == "NotImplementedError"


def test_controller_loop_stops_at_budget(tmp_path):
    c = make_controller(tmp_path, max_actions=2)

    def planner(state):
        return {
            "candidates": ["lexical"],
            "requests": {"lexical": {"query": "alpha"}},
            "utility": {"lexical": 1.0},
        }

    out = c.run(planner)
    assert out["policy"]["spent"]["actions"] == 2
    assert out["trace"][-1]["action"] == "stop"
    assert len(out["trace"]) == 3


def test_snapshot_is_runtime_observable(tmp_path):
    c = make_controller(tmp_path)
    c.step(["files"], {}, {"files": 1.0})
    snap = c.snapshot()
    assert snap["trace"][0]["action"] == "files"
    assert snap["policy"]["unique_evidence"] == 1
    assert snap["evidence"][0]["path"] == "a.py"


def test_controller_runs_structural_traversal_then_stops(tmp_path):
    (tmp_path / "a.py").write_text("def target(): return 1\n")
    (tmp_path / "b.py").write_text("from a import target\ndef caller(): return target()\n")
    workspace = SafeWorkspace(tmp_path)
    adapter = WorkspaceRetrievalAdapter(workspace, structural_adapter=CodeGraphAdapter(workspace))
    controller = EvidenceController(
        adapter,
        EvidencePolicy(EvidenceBudget(max_actions=1, max_cost=10, max_risk=10)),
    )

    def planner(_state):
        return {
            "candidates": ["structural"],
            "requests": {"structural": {"seed": "target", "max_depth": 1, "max_nodes": 5}},
            "utility": {"structural": 1.0},
        }

    result = controller.run(planner)
    assert [row["action"] for row in result["trace"]] == ["structural", "stop"]
    assert result["evidence"]
    assert all(item["origin"] == "target" for item in result["evidence"])
    assert result["policy"]["spent"]["actions"] == 1
