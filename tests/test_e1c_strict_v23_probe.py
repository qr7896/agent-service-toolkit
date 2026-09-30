from evals.e1c_strict_v23_probe import _v23_family
def test_preserves_v20_ownership_semantics(): assert _v23_family('explicit_issue_ownership_clause_binding')=='semantic_localization'
def test_callable_semantic_and_ast_structural_are_independent():
 assert _v23_family('explicit_issue_callable_binding')=='semantic_localization'
 assert _v23_family('explicit_callable_issue_type_corroboration')=='structural'
def test_bounded_assignment_remains_structural(): assert _v23_family('issue_noun_bounded_full_source_assignment')=='structural'
