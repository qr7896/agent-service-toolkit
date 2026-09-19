from evals.evidence_controller import EvidenceController
from evals.evidence_policy import EvidenceBudget, EvidencePolicy
from evals.evidence_runtime import WorkspaceRetrievalAdapter
from evals.safe_workspace import SafeWorkspace
from evals.v2_decision_log import DecisionJSONLWriter
from evals.v2_shadow_logger import V2ShadowDecisionLogger


def make(tmp_path, logger=None, max_actions=2):
    tmp_path.mkdir(parents=True, exist_ok=True)
    (tmp_path / "a.py").write_text("def alpha(): return 1")
    adapter = WorkspaceRetrievalAdapter(SafeWorkspace(tmp_path))
    policy = EvidencePolicy(EvidenceBudget(max_actions=max_actions, max_cost=10, max_risk=10))
    return EvidenceController(adapter, policy, decision_logger=logger)


def test_shadow_logger_records_pre_action_choice_without_changing_action(tmp_path):
    writer = DecisionJSONLWriter(tmp_path / "decisions.jsonl")
    logger = V2ShadowDecisionLogger("task-1", writer, {"split": "train", "cluster": "shadow", "source_commit": "c1"})
    controller = make(tmp_path, logger)
    row = controller.step(["lexical"], {"lexical": {"query": "alpha"}}, {"lexical": 1.0})
    records = writer.read_all()
    assert row["action"] == "lexical"
    assert records[0]["chosen_action"] == "lexical"
    assert records[0]["state"]["policy_state"]["spent"]["actions"] == 0
    assert {c["action"] for c in records[0]["candidates"]} == {"lexical", "stop"}


def test_shadow_logger_records_policy_stop(tmp_path):
    writer = DecisionJSONLWriter(tmp_path / "decisions.jsonl")
    logger = V2ShadowDecisionLogger("task-stop", writer)
    controller = make(tmp_path, logger)
    row = controller.step(["lexical"], {"lexical": {"query": "alpha"}}, {"lexical": 0.0})
    assert row["action"] == "stop"
    assert writer.read_all()[0]["chosen_action"] == "stop"


def test_shadow_logging_does_not_change_controller_trace(tmp_path):
    plain = make(tmp_path / "plain")
    writer = DecisionJSONLWriter(tmp_path / "logged.jsonl")
    logged = make(tmp_path / "logged", V2ShadowDecisionLogger("task", writer))
    a = plain.step(["files"], {}, {"files": 1.0})
    b = logged.step(["files"], {}, {"files": 1.0})
    assert (a["action"], a["reason"], a["items"]) == (b["action"], b["reason"], b["items"])
