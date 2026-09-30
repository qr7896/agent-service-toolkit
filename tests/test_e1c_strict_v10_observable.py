from evals.e1c_strict_v10_observable import observable_contracts
def L(symbol='exclude',path='pkg/query.py'): return {'candidates':[{'path':path,'symbol':symbol,'text':''}]}
def test_inline_crash(): assert any(r['execution_ready'] for r in observable_contracts("exclude(tags__id=OuterRef('pk')) # crashes",L()))
def test_relation_clause(): assert any(r['origin']=='generic_relation_clause' for r in observable_contracts("The model attribute doesn't point to the concrete model.",L('model','pkg/field.py')))
def test_let_clause(): assert any(r['execution_ready'] and r['verb'] in {'allow','succeed'} for r in observable_contracts("I would suggest to let the __init__ succeed even if the instance has no pk.",L('__init__','pkg/manager.py')))
def test_negative_link_clause(): assert any(r['origin']=='generic_negative_link_clause' for r in observable_contracts("The class variable documentation should not be linked to any other variable.",L('resolve','pkg/domain.py')))
def test_ambiguous_paths_fail_closed(): assert observable_contracts("The class variable documentation should not be linked to any other variable.",{'candidates':[{'path':'a.py','symbol':'A'},{'path':'b.py','symbol':'B'}]})==[]
