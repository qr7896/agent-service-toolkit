import ast
import hashlib

import pytest

from evals.e1c_evaluation_2_contract_recovery import (
    compile_contract,
    failure_phase,
    normalize_comparison,
    tree_sha,
)


def payload(assertion="count == 20"):
    return {"issue_quote": "support the option", "expected_quote": "should complete", "oracle": "value_relation",
            "setup_source": "from core import Engine\nseed = 3\ne = Engine(new_option=True)\ncount = e.run()",
            "control_action": "Engine().run()", "target_action": "count = e.run()", "assertion": assertion}


def test_expression_contract_adds_only_assert_wrapper():
    original = payload()
    normalized, proof = normalize_comparison(original)
    assert normalized["assertion"] == "assert count == 20" and original["assertion"] == "count == 20"
    assert tree_sha(ast.parse(original["assertion"]).body[0].value) == tree_sha(ast.parse(normalized["assertion"]).body[0].test)
    assert proof["wrapper_added"] and not proof["raw_program_equivalence_claimed"]
    assert all(normalized[k] == original[k] for k in original if k != "assertion")


def test_existing_assertion_is_not_rewritten():
    original = payload("assert count == 20, 'message'")
    normalized, proof = normalize_comparison(original)
    assert normalized == original and not proof["wrapper_added"]


@pytest.mark.parametrize("source", ["True", "count", "count == count", "count == 20\nother == 3", "assert True", "print(count)"])
def test_no_fabricated_or_extended_predicate(source):
    with pytest.raises(ValueError):
        normalize_comparison(payload(source))


def test_source_frontier_preserves_full_target_after_grammar_normalization(tmp_path):
    source = "class Engine:\n    def __init__(self, count=1): self.count = count\n    def run(self): return self.count\n"
    (tmp_path / "core.py").write_bytes(source.encode())
    frozen = {"candidate_paths": ["core.py"], "windows": [{"path": "core.py", "source_sha256": hashlib.sha256(source.encode()).hexdigest()}]}
    canonical, proof = compile_contract(payload(), frozen, tmp_path)
    assert proof["frontier"]["source_proven_unsupported_keywords"] == ["new_option"]
    assert proof["target_action_program_ast_unchanged_after_frontier"]
    assert canonical["setup_source"] == payload()["setup_source"]
    assert canonical["target_action"] == payload()["target_action"]


@pytest.mark.parametrize("line,phase", [(1, "setup"), (2, "control_action"), (3, "controller_check")])
def test_failure_is_located_in_actual_generated_phase(line, phase):
    source = "x = 1\napi(x)\nassert True\n"
    control = {"source": source}
    execution = {"probe_sha256": hashlib.sha256(source.encode()).hexdigest(),
                 "runs": [{"log_tail": f'Traceback:\n  File "/e1c2_probe.py", line {line}, in <module>\nValueError: failure'}]}
    value = failure_phase(control, execution, {"setup_source": "x = 1", "control_action": "api(x)"})
    assert value["rows"][0]["phase"] == phase and not value["program_changed"]
    assert not value["semantic_bug_alignment_proven"]


def test_trace_from_other_program_cannot_justify_frontier():
    with pytest.raises(ValueError, match="does not match"):
        failure_phase({"source": "x = 1"}, {"probe_sha256": "wrong"}, {})
