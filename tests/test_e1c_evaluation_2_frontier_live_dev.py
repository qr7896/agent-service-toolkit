import pytest

from evals import e1c_evaluation_2_frontier_live_dev as live


def test_new_namespace_and_task_cap_do_not_modify_original_adapter():
    old = live.ready.OUT, live.ready.compiled.TASK_CAP, live.ready.compiled.CAP, live.ready.messages
    with live.configured():
        assert live.ready.OUT == live.OUT and live.ready.compiled.OUT == live.OUT
        assert live.ready.compiled.CAP == 50000 and live.ready.compiled.TASK_CAP == 24000
        assert live.ready.execute_probe is live.frontier.execute_probe
        assert len(live.ready.REFERENCE_TASKS) == 4
    assert old == (live.ready.OUT, live.ready.compiled.TASK_CAP, live.ready.compiled.CAP, live.ready.messages)


def test_prompt_declares_limits_not_a_semantic_certificate():
    with live.configured():
        messages = live.messages({"issue": "Public API should complete normally.", "windows": []})
    assert "Alias/global independence is not proven" in messages[0].content
    assert "never change the expected behavior" in messages[0].content


def test_scope_restored_after_exception():
    old = live.ready.execute_probe
    with pytest.raises(RuntimeError), live.configured():
        raise RuntimeError("failure")
    assert live.ready.execute_probe is old
