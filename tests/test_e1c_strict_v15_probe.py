from evals.e1c_strict_v15_probe import _family,_corroborating_binding
def test_evidence_families_are_distinct():
 assert _family('projected_issue_python_scenario') != _family('confidence_checked_clause_symbol_binding')
 assert _family('never_used_claim') != _family('multi_evidence_structural_binding')

def test_unique_symbol_same_path_can_corroborate():
 rows=[{'execution_ready':True,'origin':'never_used_claim','witness':{'symbol':'check_x','candidate_path':'pkg/checks.py'}}]
 loc={'candidates':[{'path':'pkg/checks.py','symbol':'check_x','origin':'issue_ast_definition'}]}
 out=_corroborating_binding(rows,loc)
 assert len(out)==1 and out[0]['origin']=='unique_localized_symbol_corroboration'

def test_duplicate_symbol_is_fail_closed():
 rows=[{'execution_ready':True,'origin':'generic_relation_clause','witness':{'subject':'model','candidate_path':'a.py'}}]
 loc={'candidates':[{'path':'a.py','symbol':'model'},{'path':'b.py','symbol':'model'}]}
 assert _corroborating_binding(rows,loc)==[]

def test_path_disagreement_is_fail_closed():
 rows=[{'execution_ready':True,'origin':'generic_behavior_clause','witness':{'subject':'run','candidate_path':'a.py'}}]
 loc={'candidates':[{'path':'b.py','symbol':'run'}]}
 assert _corroborating_binding(rows,loc)==[]
