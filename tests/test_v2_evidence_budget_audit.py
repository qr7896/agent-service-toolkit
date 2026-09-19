from evals.v2_evidence_budget_audit import approx_tokens,size
def test_proxy_is_deterministic():
 assert approx_tokens("def f(x): return x")==8
 assert size([{"content":"abc"}])["chars"]==3
