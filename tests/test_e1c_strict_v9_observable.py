from evals.e1c_strict_v9_observable import observable_contracts

def loc(symbol="unregister", path="pkg/core.py"):
    return {"candidates":[{"path":path,"symbol":symbol,"text":f"def {symbol}(): pass"}]}

def test_generic_should_clause_becomes_executable_observable():
    rows=observable_contracts("unregister() should clear the lookup cache.",loc())
    assert len(rows)==1 and rows[0]["execution_ready"] is True
    assert rows[0]["verb"]=="clear" and rows[0]["candidate_path"]=="pkg/core.py"

def test_generic_failure_clause_becomes_nonfailure_observable():
    rows=observable_contracts("exclude() crashes with a ValueError",loc(symbol="exclude"))
    assert len(rows)==1 and rows[0]["verb"]=="not_fail"

def test_ambiguous_localization_fails_closed():
    localization={"candidates":[{"path":"a.py","symbol":"other"},{"path":"b.py","symbol":"other2"}]}
    assert observable_contracts("exclude() crashes",localization)==[]

def test_expected_negative_clause_with_unique_production_path():
    rows=observable_contracts("Expected behavior: the variable should not link to any other variable.",loc(symbol="Project"))
    assert any(r["verb"]=="not_occur" for r in rows)

def test_attribute_relation_with_unique_production_path():
    rows=observable_contracts("The model attribute does not point to the concrete model.",loc(symbol="Field"))
    assert any(r["subject"]=="model" for r in rows)

def test_allow_clause_fails_closed_when_paths_are_ambiguous():
    localization={"candidates":[{"path":"a.py","symbol":"A"},{"path":"b.py","symbol":"B"}]}
    assert observable_contracts("I suggest to let initialization succeed even if the pk is absent.",localization)==[]
