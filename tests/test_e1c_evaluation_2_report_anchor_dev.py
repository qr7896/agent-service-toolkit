import json

from langchain_core.messages import HumanMessage, SystemMessage

from evals import e1c_evaluation_2_report_anchor_dev as runner

ISSUE = "It works for\npkg.normal(model, labels=names)\nbut not for\npkg.broken(model, labels=names)\n"


def test_comparative_fact_anchor_is_not_reported_promise_or_certificate():
    result = runner.report_anchors(ISSUE)
    assert result["public_API_pair"] == ["normal", "broken"]
    anchor = result["anchors"][0]
    assert anchor["kind"] == "comparative_report" and anchor["quote_ref"] == 0
    assert not anchor["reported_promise_proven"] and not anchor["semantic_alignment_proven"]


def test_regression_public_quote_anchor_not_explicit_promise():
    anchor = runner.report_anchors("The previous release works without raising errors.\n")["anchors"][0]
    assert anchor["kind"] == "regression_report" and not anchor["reported_promise_proven"]


def test_explicit_request_keeps_public_request_origin():
    anchor = runner.report_anchors("Please expose `flag` in `Thing.__init__()`.\n")["anchors"][0]
    assert anchor["kind"] == "explicit_interface_request" and anchor["origin"] == "explicit_public_request"


def test_trace_and_unknown_question_do_not_receive_anchor():
    result = runner.report_anchors('File "previous_works.py", line 4, in api\nCan somebody help?\n')
    assert result["anchors"] == [] and result["unknown_if_no_anchor"]


def test_new_metadata_preserves_existing_public_fields(monkeypatch):
    original = {"public_issue_spans": [[0, "It works for\n"]], "windows": [], "previous_probe": None}
    monkeypatch.setattr(runner, "_messages", lambda *a: [SystemMessage(content="Missing desired behavior requires abstention."), HumanMessage(content=json.dumps(original))])
    result = runner.messages({"issue": ISSUE})
    body = json.loads(result[1].content)
    assert all(body[k] == v for k, v in original.items())
    assert "public_report_anchors" in body
    assert "Missing desired behavior requires abstention." not in result[0].content


def test_rejected_quote_feedback_retains_comparative_fact(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "_execute", lambda *a: ({"status": "action_rejected"}, None, None, None))
    payload = {"expected_quote": "pkg.broken(model, labels=names)\n", "oracle": "call_completes"}
    feedback, *rest = runner.execute_probe(payload, {"issue": ISSUE}, tmp_path, "image", tmp_path, {})
    assert feedback["public_report_anchors"]["public_API_pair"] == ["normal", "broken"]
    assert rest == [None, None, None]


def test_contradictory_next_turn_expectation_policy_revised():
    text = runner.revise_policy("Unknown EXPECTATION requires abstention; Unknown desired behavior still requires abstention.")
    assert "Unknown EXPECTATION requires abstention" not in text
    assert "labeled completion hypothesis" in text


def test_inner_owner_and_loop_keep_new_hook_restore_both():
    old = runner._compiled.execute_probe, runner._compiled.base.loop.execute_probe
    with runner.configured():
        with runner._compiled.configured():
            assert runner._compiled.base.loop.execute_probe is runner.execute_probe
            assert runner._compiled.CAP == 50000 and runner._compiled.TASK_CAP == 24000
    assert (runner._compiled.execute_probe, runner._compiled.base.loop.execute_probe) == old
