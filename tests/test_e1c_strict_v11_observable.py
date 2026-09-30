from evals.e1c_strict_v11_observable import observable_contracts
def test_exact_action_prefers_definition():
 loc={'candidates':[{'path':'query.py','symbol':'exclude','origin':'issue_ast_definition'},{'path':'expr.py','symbol':'OuterRef','origin':'issue_ast_definition'}]}; assert any(x['candidate_path']=='query.py' for x in observable_contracts("exclude(tags__id=OuterRef('pk')) # crashes",loc))
def test_ambiguous_action_fails_closed():
 loc={'candidates':[{'path':'a.py','symbol':'exclude','origin':'issue_ast_definition'},{'path':'b.py','symbol':'exclude','origin':'issue_ast_definition'}]}; assert observable_contracts("exclude(x=1) # crashes",loc)==[]
