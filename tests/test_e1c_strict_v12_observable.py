from evals.e1c_strict_v12_observable import observable_contracts
def test_generic_bad_clause_binds_unique_symbol():
 loc={'candidates':[{'path':'q.py','symbol':'exclude','origin':'issue_ast_definition'},{'path':'e.py','symbol':'OuterRef','origin':'issue_ast_definition'}]}; r=observable_contracts("exclude(tags=OuterRef('pk')) crashes.",loc); assert any(x['candidate_path']=='q.py' and x['origin']=='generic_clause_symbol_binding' for x in r)
def test_duplicate_symbol_fails_closed():
 loc={'candidates':[{'path':'a.py','symbol':'run','origin':'issue_ast_definition'},{'path':'b.py','symbol':'run','origin':'issue_ast_definition'}]}; assert not any(x['origin']=='generic_clause_symbol_binding' for x in observable_contracts('run() fails.',loc))
