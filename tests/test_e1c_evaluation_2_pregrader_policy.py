from evals.e1c_evaluation_2_pregrader_policy import choose


def test_selection_is_locked_on_base_and_control_not_gold():
    primary = {"status": "executed", "control_pass": True, "repeatable_failure_candidate": True, "gold_discriminating": False}
    fallback = {"status": "executed", "repeatable_failure_candidate": True, "gold_discriminating": True}
    assert choose(primary, fallback) == "B"
    assert choose({**primary, "control_pass": False}, fallback) == "A"
    assert choose({"status": "abstained"}, {"status": "executed", "repeatable_failure_candidate": False}) is None


def test_task_labels_do_not_affect_policy_selection():
    primary = {"status": "executed", "control_pass": True, "repeatable_nonsetup_failure": True}
    assert choose({**primary, "instance_id": "one"}, {}) == choose({**primary, "instance_id": "another"}, {}) == "B"
