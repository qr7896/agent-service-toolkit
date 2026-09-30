from dataclasses import asdict

from evals.e1b_acquisition_policy_interface_v10_4 import action_set_manifest, sha256
from evals.e1b_evidence_acquisition_v10_3 import choose_action
from evals.e1b_semantic_evidence_ir_v10 import Evidence, Obligation, typed, verify
from evals.e1b_verification_decision_v10_1 import decide

SCHEMA_VERSION = "e1b-protocol-invariants-v1"

INVARIANT_IDS = (
    "INV-01-irrelevant-evidence-no-unblock",
    "INV-02-contradiction-no-improvement",
    "INV-03-budget-monotonicity",
    "INV-04-attempt-no-repeat",
    "INV-05-order-invariance",
    "INV-06-duplicate-conflict-fail-closed",
    "INV-07-contradiction-termination",
    "INV-08-allow-claim-boundary",
)


def _decision(obligations, evidence):
    verification = verify(obligations, evidence)
    return verification, decide(obligations, verification, 0)


def evaluate_invariants():
    failed = Obligation("x", "change", source=typed("failed"), target=typed("error"))
    wrong = Evidence("wrong", "change", "support", source=typed("failed"), target=typed("done"), path="x.py", construct="if")
    irrelevant = Evidence("other", "identity", "support", source=typed("pending"), path="y.py", construct="if")
    support = Evidence("support", "change", "support", source=typed("failed"), target=typed("error"), path="z.py", construct="if")
    base_v, base_d = _decision([failed], [wrong])
    irrelevant_v, irrelevant_d = _decision([failed], [wrong, irrelevant])
    conflict_v, conflict_d = _decision([failed], [support, wrong])
    unsupported = verify([failed], [])
    high_budget = choose_action([failed], unsupported, ["lexical"], 1)
    low_budget = choose_action([failed], unsupported, ["lexical"], 7)
    attempted = choose_action([failed], unsupported, ["lexical"], 0)
    order_a = verify([failed], [wrong, irrelevant])
    order_b = verify([failed], [irrelevant, wrong])
    duplicate = [
        Evidence("a", "change", "support", source=typed("failed"), target=typed("error"), path="same.py", function="f", construct="if"),
        Evidence("b", "change", "support", source=typed("failed"), target=typed("done"), path="same.py", function="f", construct="if"),
    ]
    duplicate_v, duplicate_d = _decision([failed], duplicate)
    satisfied_v, satisfied_d = _decision([failed], [support])

    checks = {
        INVARIANT_IDS[0]: base_d["action"] == "BLOCK_PATCH" and irrelevant_d["action"] == "BLOCK_PATCH",
        INVARIANT_IDS[1]: conflict_v["dispositions"][0]["disposition"] in {"contradicted", "ambiguous"} and conflict_d["action"] != "ALLOW_VERIFICATION",
        INVARIANT_IDS[2]: high_budget["action"] != "BUDGET_EXHAUSTED" and low_budget["action"] == "BUDGET_EXHAUSTED",
        INVARIANT_IDS[3]: attempted["action"] != "lexical",
        INVARIANT_IDS[4]: order_a["evidence_manifest_sha256"] == order_b["evidence_manifest_sha256"] and irrelevant_d["action"] == decide([failed], order_b, 0)["action"],
        INVARIANT_IDS[5]: duplicate_v["decision"] == "fail_closed" and duplicate_d["action"] != "ALLOW_VERIFICATION",
        INVARIANT_IDS[6]: base_d["action"] == "BLOCK_PATCH",
        INVARIANT_IDS[7]: satisfied_d["action"] == "ALLOW_VERIFICATION" and "not PASS or repair success" in satisfied_d["claim_boundary"],
    }
    rows = [{"invariant_id": key, "passed": checks[key]} for key in INVARIANT_IDS]
    return {
        "schema_version": SCHEMA_VERSION,
        "invariants": rows,
        "all_passed": all(checks.values()),
        "action_set_manifest_sha256": action_set_manifest(),
        "fixture_sha256": sha256({
            "obligation": asdict(failed),
            "wrong": asdict(wrong),
            "irrelevant": asdict(irrelevant),
            "support": asdict(support),
        }),
        "claim_boundary": "offline protocol/metamorphic validation only; no repair efficacy",
    }
