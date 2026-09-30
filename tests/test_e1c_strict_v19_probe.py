from pathlib import Path
from evals.e1c_strict_v19_probe import _full_source_attribute_corroboration
def _row(): return {'execution_ready':True,'origin':'generic_relation_clause','witness':{'subject':'model','object':'concrete model','candidate_path':'old.py'}}
def test_unique_full_source_assignment_path_corroborates(tmp_path:Path):
 (tmp_path/'fields.py').write_text('class Field:\n def bind(self, cls):\n  self.model = cls\n')
 r=_full_source_attribute_corroboration('model attribute points to concrete model',[_row()],tmp_path); assert len(r)==1 and r[0]['witness']['candidate_path']=='fields.py'
def test_multiple_assignment_files_fail_closed(tmp_path:Path):
 (tmp_path/'a.py').write_text('def f(self,x):\n self.model=x\n'); (tmp_path/'b.py').write_text('def g(self,x):\n self.model=x\n')
 assert _full_source_attribute_corroboration('model attribute points to concrete model',[_row()],tmp_path)==[]
def test_attribute_must_be_issue_visible(tmp_path:Path):
 (tmp_path/'a.py').write_text('def f(self,x):\n self.model=x\n'); assert _full_source_attribute_corroboration('field belongs to concrete model',[_row()],tmp_path)==[]
