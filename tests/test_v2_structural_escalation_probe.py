from evals.v2_structural_escalation_probe import visible_symbols
def test_visible_call_symbols(): assert "prompt" in visible_symbols({"t.py":"m.prompt('x')"})
