import json
import subprocess
import sys

import pytest

from evals.e1c_evaluation_2_executable_dev import augmented
from evals.e1c_evaluation_2_execution_contract import (
    ExecutionContractViolation,
    parse_response,
    prepare_source,
)

DIRECT = {"mode": "direct_script", "entrypoint": None, "fixture_source": "generated_public_issue_only"}
ENTRY = {**DIRECT, "mode": "call_entrypoint", "entrypoint": "reproduce"}


def test_uninvoked_body_is_rejected_without_guessing_fixtures():
    with pytest.raises(ExecutionContractViolation, match="not_invoked"):
        prepare_source("def reproduce(testdir):\n    assert False\n", DIRECT)
    with pytest.raises(ExecutionContractViolation, match="parameters"):
        prepare_source("def reproduce(testdir):\n    assert False\n", ENTRY)


def test_explicit_entry_really_runs_check(tmp_path):
    source = "def reproduce():\n    print('GENERATED_CHECK_REACHED')\n    assert False, 'synthetic witness'\n"
    compiled = prepare_source(source, ENTRY)
    path = tmp_path / "synthetic_probe.py"
    path.write_text(compiled, encoding="utf-8")
    result = subprocess.run([sys.executable, "-X", "utf8", str(path)], capture_output=True, text=True, encoding="utf-8", timeout=10)
    assert result.returncode == 1 and "GENERATED_CHECK_REACHED" in result.stdout and "synthetic witness" in result.stderr
    assert compiled == source.rstrip() + "\n\nreproduce()\n"


@pytest.mark.parametrize("source", ["async def reproduce():\n    assert False", "@deco\ndef reproduce():\n    assert False",
    "def reproduce():\n    assert False\nreproduce()", "def reproduce():\n    reproduce = None\n    assert False",
    "def other():\n    assert False", "def reproduce():\n    pass"])
def test_illegal_or_ambiguous_entry_is_rejected(source):
    with pytest.raises(ExecutionContractViolation):
        prepare_source(source, ENTRY)


def test_new_schema_preserves_old_contract_and_abstention():
    payload = {"source": "assert 1 == 1", "execution": DIRECT}
    assert parse_response(json.dumps(payload), "A")["payload"] == {"source": "assert 1 == 1"}
    assert parse_response('{"abstain_reason":"insufficient public source"}', "A")["status"] == "abstained"
    for execution in (None, {**DIRECT, "fixture_source": "official_tests"}, {**DIRECT, "entrypoint": "object.method"}):
        with pytest.raises(ExecutionContractViolation):
            parse_response(json.dumps({"source": "assert True", "execution": execution}), "A")


def test_terminal_import_lexical_order_and_same_budget():
    def row(symbol):
        return {"path": f"pkg/{symbol}.py", "symbol": symbol, "text": "def f(): pass", "source_sha256": "synthetic"}
    frozen = {"issue": "public expected behavior", "windows": [row("lexical")], "input_sha256": "old"}
    facts = {"terminal_production_windows": [row("terminal")], "blocks": [], "statement_sha256": "public"}
    result = augmented(frozen, facts, [row("imported"), row("imported")])
    assert [w["symbol"] for w in result["windows"]] == ["terminal", "imported", "lexical"]
    assert result["candidate_count"] <= 4
    with pytest.raises(ValueError, match="budget"):
        augmented({**frozen, "issue": "x" * 23001}, facts, [row("imported")])
