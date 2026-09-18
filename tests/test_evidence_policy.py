from evals.evidence_policy import EvidenceBudget, EvidencePolicy, RuntimeEvidencePolicyV1
from evals.evidence_runtime import EvidenceItem, EvidenceLedger


def test_policy_respects_action_budget():
    ledger = EvidenceLedger()
    ledger.add("files", [])
    policy = EvidencePolicy(EvidenceBudget(max_actions=1, max_cost=10, max_risk=10))
    assert (
        policy.choose(ledger, ["lexical", "structural"], {"lexical": 1, "structural": 1}) == "stop"
    )


def test_policy_respects_cost_and_risk():
    ledger = EvidenceLedger()
    policy = EvidencePolicy(EvidenceBudget(max_actions=4, max_cost=1.0, max_risk=0.15))
    assert policy.allowed(ledger, "structural")
    assert not policy.allowed(ledger, "lexical")


def test_policy_prefers_higher_net_utility():
    ledger = EvidenceLedger()
    policy = EvidencePolicy(EvidenceBudget(max_actions=4, max_cost=10, max_risk=10))
    chosen = policy.choose(ledger, ["lexical", "structural"], {"lexical": 0.5, "structural": 0.8})
    assert chosen == "structural"


def test_policy_stops_when_utility_not_positive():
    ledger = EvidenceLedger()
    policy = EvidencePolicy()
    assert policy.choose(ledger, ["structural"], {"structural": 0.01}) == "stop"


def test_policy_state_tracks_runtime():
    ledger = EvidenceLedger()
    ledger.add("structural", [EvidenceItem("a.py", "x", "structural")])
    state = EvidencePolicy().state(ledger)
    assert state["spent"]["actions"] == 1
    assert state["unique_evidence"] == 1
    assert state["remaining"]["actions"] == 3


def test_runtime_v1_penalizes_redundancy_without_changing_v0():
    ledger = EvidenceLedger()
    item = EvidenceItem("a.py", "x", "structural", depth=0)
    ledger.add("structural", [item])
    ledger.add("structural", [item])
    utility = {"lexical": 0.8, "structural": 0.8}
    budget = EvidenceBudget(max_actions=4, max_cost=10, max_risk=10)
    assert EvidencePolicy(budget).choose(ledger, ["lexical", "structural"], utility) == "structural"
    assert (
        RuntimeEvidencePolicyV1(budget).choose(ledger, ["lexical", "structural"], utility)
        == "lexical"
    )


def test_runtime_v1_penalizes_deep_structural_expansion():
    ledger = EvidenceLedger()
    ledger.add("structural", [EvidenceItem("a.py", "x", "structural", depth=3)])
    policy = RuntimeEvidencePolicyV1(EvidenceBudget(max_actions=4, max_cost=10, max_risk=10))
    chosen = policy.choose(
        ledger,
        ["lexical", "structural"],
        {"lexical": 0.75, "structural": 0.8},
    )
    assert chosen == "lexical"
    assert policy.state(ledger)["policy_version"] == "runtime-v1"
