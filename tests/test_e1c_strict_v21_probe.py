from pathlib import Path
from evals.e1c_strict_v21_probe import candidate_plan, _callable_type_corroboration

def test_callable_type_corroboration_is_task_agnostic(tmp_path: Path):
 p=tmp_path/'pkg.py';p.write_text('def build_widget():\n    class WidgetManager: pass\n    return WidgetManager()\n')
 issue='build_widget should allow introspection of the widget manager instance.'
 rows=[{'execution_ready':True,'origin':'explicit_issue_callable_binding','witness':{'candidate_path':'pkg.py','subject':'build_widget'}}]
 out=_callable_type_corroboration(issue,rows,tmp_path)
 assert [x['origin'] for x in out]==['explicit_callable_issue_type_corroboration']
 assert out[0]['witness']['benchmark_assertion_used'] is False

def test_no_type_noun_means_no_new_witness(tmp_path: Path):
 p=tmp_path/'pkg.py';p.write_text('def build_widget():\n    return 1\n')
 plan=candidate_plan('build_widget returns one.',{'candidates':[{'path':'pkg.py','text':p.read_text(),'symbol':'build_widget'}]},source_root=tmp_path)
 assert 'explicit_callable_issue_type_corroboration' not in [x.get('origin') for x in plan['candidates']]
