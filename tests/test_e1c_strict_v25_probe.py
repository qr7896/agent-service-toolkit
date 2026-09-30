from evals.e1c_strict_v25_probe import _callable_behavior

def test_callable_behavior_requires_explicit_behavior_word():
    rows=[{'execution_ready':True,'origin':'explicit_issue_callable_binding','witness':{'subject':'make_manager','candidate_path':'a.py'}}]
    assert _callable_behavior('make_manager refuses an unbound instance',rows)[0]['origin']=='explicit_callable_behavior_claim'
    assert _callable_behavior('make_manager is documented here',rows)==[]
