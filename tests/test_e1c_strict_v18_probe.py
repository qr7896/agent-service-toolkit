from evals.e1c_strict_v18_probe import _property_symbols,_attribute_property_corroboration

def _row(path='pkg/fields.py'):
 return {'execution_ready':True,'origin':'generic_relation_clause','witness':{'subject':'model','object':'to concrete model','candidate_path':path}}

def test_visible_property_is_structural_evidence():
 loc={'candidates':[{'path':'pkg/fields.py','text':'@property\ndef model(self):\n return self.__dict__["model"]\n','origin':'issue_lexical'}]}
 assert _property_symbols(loc)=={'model':{'pkg/fields.py'}}
 assert len(_attribute_property_corroboration('model attribute should point to concrete model',[_row()],loc))==1

def test_indented_localization_window_is_parsed_after_dedent():
 loc={'candidates':[{'path':'pkg/fields.py','text':'    @property\n    def model(self):\n        return self.__dict__["model"]\n'}]}
 assert _property_symbols(loc)=={'model':{'pkg/fields.py'}}

def test_attribute_must_be_explicit_in_issue():
 loc={'candidates':[{'path':'pkg/fields.py','text':'@property\ndef model(self):\n return None\n'}]}
 assert _attribute_property_corroboration('model should point to concrete model',[_row()],loc)==[]

def test_duplicate_property_paths_fail_closed():
 loc={'candidates':[{'path':'pkg/a.py','text':'@property\ndef model(self):\n return None\n'},{'path':'pkg/b.py','text':'@property\ndef model(self):\n return None\n'}]}
 assert _attribute_property_corroboration('model attribute should point to concrete model',[_row('pkg/a.py')],loc)==[]

def test_non_relation_ignored():
 r=_row(); r['origin']='confidence_checked_clause_symbol_binding'; loc={'candidates':[{'path':'pkg/fields.py','text':'@property\ndef model(self):\n return None\n'}]}
 assert _attribute_property_corroboration('model attribute should point to concrete model',[r],loc)==[]
