import pytest

from evals.evidence_policy import EvidenceBudget
from evals.evidence_runtime import EvidenceItem, EvidenceLedger
from evals.frozen_v1_policy_adapter import FrozenV1PolicyAdapter


def test_frozen_v1_policy_adapter_fixed_fixture():
    ledger = EvidenceLedger()
    ledger.add(
        "files",
        [EvidenceItem("src/service.py", "def invoke(): return 1", "files", symbol="invoke")],
    )
    adapter = FrozenV1PolicyAdapter(
        "fix the service invocation path",
        EvidenceBudget(max_actions=4, max_cost=10, max_risk=10),
    )

    decision = adapter.choose(ledger, ["lexical", "semantic", "structural"])

    assert decision == "structural"
    assert adapter.state(ledger)["policy_version"] == "frozen-v1-adapter"
    assert adapter.state(ledger)["frozen_v1"]["manifest_verified"] is True
    assert adapter.last_decision == {
        "decision": "structural",
        "stop_probability": pytest.approx(0.375485),
        "threshold": 0.942382,
        "rank_scores": {
            "lexical": pytest.approx(0.001554),
            "semantic": pytest.approx(0.002608),
            "structural": pytest.approx(0.771267),
        },
    }
