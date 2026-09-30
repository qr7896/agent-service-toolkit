from pathlib import Path
from evals.e1c_strict_v20_probe import _bounded_attribute_assignments,_bounded_corroboration,_ownership_semantic_binding
def row():return {'execution_ready':True,'origin':'generic_relation_clause','witness':{'subject':'model','candidate_path':'x'}}
def test_issue_type_noun_bounds_assignment(tmp_path:Path):
 (tmp_path/'fields.py').write_text('class Field:\n def bind(self,x):\n  self.model=x\nclass Manager:\n def bind(self,x):\n  self.model=x\n')
 h=_bounded_attribute_assignments('model attribute of image fields',tmp_path);assert len(h)==1 and h[0]['class']=='Field';assert len(_bounded_corroboration('model attribute of image fields',[row()],tmp_path))==1
def test_no_type_noun_no_boundary(tmp_path:Path):
 (tmp_path/'x.py').write_text('class Field:\n def f(self,x):\n  self.model=x\n');assert _bounded_attribute_assignments('model attribute is wrong',tmp_path)==[]
def test_ambiguous_bounded_files_fail_closed(tmp_path:Path):
 (tmp_path/'a.py').write_text('class Field:\n def f(self,x):\n  self.model=x\n');(tmp_path/'b.py').write_text('class ImageField:\n def f(self,x):\n  self.model=x\n');assert _bounded_corroboration('model attribute of image fields',[row()],tmp_path)==[]
def test_explicit_ownership_clause_is_independent_semantic_binding(tmp_path:Path):
 (tmp_path/'fields.py').write_text('class Field:\n def f(self,x):\n  self.model=x\n');r=_ownership_semantic_binding('model attribute of image fields should find the concrete model an image field belongs to',tmp_path);assert len(r)==1 and r[0]['origin']=='explicit_issue_ownership_clause_binding'
def test_without_explicit_ownership_clause_no_semantic_binding(tmp_path:Path):
 (tmp_path/'fields.py').write_text('class Field:\n def f(self,x):\n  self.model=x\n');assert _ownership_semantic_binding('model attribute of image fields is wrong',tmp_path)==[]
def test_ownership_clause_allows_normal_descriptive_distance(tmp_path:Path):
 (tmp_path/'fields.py').write_text('class Field:\n def f(self,x):\n  self.model=x\n');issue='model attribute of image fields can be used to find the concrete model the image field belongs to';assert len(_ownership_semantic_binding(issue,tmp_path))==1
