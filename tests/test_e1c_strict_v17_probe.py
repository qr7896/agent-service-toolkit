from evals.e1c_strict_v17_probe import _relation_type_corroboration

def _row(path='pkg/models.py'):
 return {'execution_ready':True,'origin':'generic_relation_clause','witness':{'subject':'model','object':'to concrete model','candidate_path':path}}

def test_unique_relation_object_type_same_path_corroborates():
 loc={'candidates':[{'path':'pkg/models.py','symbol':'Model','origin':'issue_ast_definition'}]}
 assert len(_relation_type_corroboration([_row()],loc))==1

def test_relation_type_path_disagreement_fails_closed():
 loc={'candidates':[{'path':'pkg/base.py','symbol':'Model','origin':'issue_ast_definition'}]}
 assert _relation_type_corroboration([_row()],loc)==[]

def test_relation_type_duplicate_definition_fails_closed():
 loc={'candidates':[{'path':'pkg/models.py','symbol':'Model','origin':'issue_ast_definition'},{'path':'pkg/other.py','symbol':'model','origin':'issue_ast_definition'}]}
 assert _relation_type_corroboration([_row()],loc)==[]

def test_non_relation_witness_ignored():
 r=_row(); r['origin']='confidence_checked_clause_symbol_binding'
 loc={'candidates':[{'path':'pkg/models.py','symbol':'Model','origin':'issue_ast_definition'}]}
 assert _relation_type_corroboration([r],loc)==[]
