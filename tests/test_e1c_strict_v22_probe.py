from evals.e1c_strict_v22_probe import _v22_family

def test_callable_issue_binding_and_ast_corroboration_are_independent_families():
 assert _v22_family('explicit_issue_callable_binding')=='semantic_localization'
 assert _v22_family('explicit_callable_issue_type_corroboration')=='structural'

def test_unrelated_legacy_origin_is_not_promoted():
 assert _v22_family('unknown_origin') not in {'semantic_localization','structural'}
