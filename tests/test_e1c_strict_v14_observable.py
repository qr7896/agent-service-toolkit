from evals.e1c_strict_v14_observable import observable_contracts
def test_multi_evidence_requires_margin():
 loc={'candidates':[{'path':'query.py','symbol':'resolve_ref','origin':'issue_ast_definition'},{'path':'other.py','symbol':'helper','origin':'fallback'}]}; r=observable_contracts('resolve_ref should preserve query behavior.',loc); assert any(x['origin']=='multi_evidence_structural_binding' and x['candidate_path']=='query.py' for x in r)
def test_multi_evidence_tie_fails_closed():
 loc={'candidates':[{'path':'a.py','symbol':'resolve_ref','origin':'issue_ast_definition'},{'path':'b.py','symbol':'resolve_ref','origin':'issue_ast_definition'}]}; assert not any(x['origin']=='multi_evidence_structural_binding' for x in observable_contracts('resolve_ref should work.',loc))
