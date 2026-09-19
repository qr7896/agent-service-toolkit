from evals.v2_external_eval_gate import gate
def test_fail_closed_without_checkout(tmp_path):
 r=gate(tmp_path/"missing")
 assert not r["example_allowed"] and not r["cal500_allowed"] and not r["test500_allowed"]
 assert "upstream_checkout_unavailable" in r["blockers"]
