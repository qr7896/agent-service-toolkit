from evals.e1c_strict_v13_observable import observable_contracts
def test_confidence_checked_generic_binding():
 loc={'candidates':[{'path':'q.py','symbol':'exclude','origin':'issue_ast_definition'}]}; r=observable_contracts('exclude(x=1) crashes.',loc); assert any(x['origin']=='confidence_checked_clause_symbol_binding' and x['confidence_evidence']['unique_production_symbol'] for x in r)
def test_no_polarity_no_generic_binding():
 loc={'candidates':[{'path':'q.py','symbol':'exclude','origin':'issue_ast_definition'}]}; assert not any(x['origin']=='confidence_checked_clause_symbol_binding' for x in observable_contracts('exclude(x=1) is mentioned.',loc))
