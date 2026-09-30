from evals.e1c_strict_v24_probe import _v24_family

def test_issue_python_scenario_is_behavioral():
    assert _v24_family('projected_issue_python_scenario') == 'behavioral'

def test_existing_family_semantics_are_preserved():
    assert _v24_family('explicit_issue_callable_binding') == 'semantic_localization'
    assert _v24_family('explicit_callable_issue_type_corroboration') == 'structural'
