from evals.v2_coverage_failure import tokens
def test_tokens_extract_symbols(): assert "prompt" in tokens("assert m.prompt('x', [])")
