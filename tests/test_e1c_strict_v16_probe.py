from evals.e1c_strict_v16_probe import _explicit_callable_bindings,_callable_context_corroboration

def test_explicit_issue_callable_unique_definition_binds():
 issue='create_reverse_many_to_one_manager should allow introspection.'
 loc={'candidates':[{'path':'pkg/related.py','symbol':'create_reverse_many_to_one_manager','origin':'issue_ast_definition'}]}
 out=_explicit_callable_bindings(issue,loc)
 assert len(out)==1 and out[0]['witness']['candidate_path']=='pkg/related.py'

def test_identifier_not_in_issue_does_not_bind():
 loc={'candidates':[{'path':'pkg/related.py','symbol':'hidden_helper','origin':'issue_ast_definition'}]}
 assert _explicit_callable_bindings('manager should allow introspection',loc)==[]

def test_duplicate_definition_is_fail_closed():
 loc={'candidates':[{'path':'a.py','symbol':'target_call','origin':'issue_ast_definition'},{'path':'b.py','symbol':'target_call','origin':'issue_ast_definition'}]}
 assert _explicit_callable_bindings('target_call should work',loc)==[]

def test_non_definition_origin_does_not_bind():
 loc={'candidates':[{'path':'a.py','symbol':'target_call','origin':'ast_caller'}]}
 assert _explicit_callable_bindings('target_call should work',loc)==[]

def test_callable_context_requires_same_path():
 issue='target_call should allow manager introspection'
 loc={'candidates':[{'path':'pkg/related.py','symbol':'target_call','origin':'issue_ast_definition'}]}
 rows=[{'execution_ready':True,'origin':'confidence_checked_clause_symbol_binding','witness':{'subject':'manager','candidate_path':'pkg/related.py'}}]
 assert len(_callable_context_corroboration(issue,loc,rows))==1
 rows[0]['witness']['candidate_path']='pkg/manager.py'
 assert _callable_context_corroboration(issue,loc,rows)==[]
