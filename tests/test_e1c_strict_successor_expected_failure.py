from evals.e1c_strict_successor_expected_failure import (
    FailureContract,
    classify_failure,
    compile_import_lift,
    extract_failure_contract,
    extract_public_production_path,
    render_compiled,
)


def test_extracts_last_public_exception_contract():
    text = "Traceback\nValueError: earlier\nmore\nTypeError: A Vector must be supplied\n"
    assert extract_failure_contract(text) == FailureContract("TypeError", "A Vector must be supplied")


def test_extracts_public_traceback_production_path_without_tests():
    text = "/env/site-packages/pkg/engine.py in run\n/env/site-packages/tests/test_x.py in test_x"
    assert extract_public_production_path(text) == "pkg/engine.py"
    assert extract_public_production_path("/env/site-packages/tests/test_x.py in test_x") is None


def test_import_lift_compiles_import_and_from_import_without_raw_imports():
    issue = "Example fails:\nValueError: documented failure\n"
    source = (
        "import package.submodule as sub\n"
        "from package.api import Factory, consume as use\n"
        "obj = Factory('x')\n"
        "use(sub.transform(obj))\n"
    )
    compiled = compile_import_lift(issue, source, candidate_path="package/engine.py")
    assert compiled is not None
    assert "import " not in compiled.body_source
    assert [b.local_name for b in compiled.bindings] == ["sub", "Factory", "use"]
    rendered = render_compiled(compiled)
    assert "import importlib" in rendered
    assert "package.submodule" in rendered


def test_import_lift_rejects_relative_star_nested_and_ambiguous_dotted_imports():
    issue = "TypeError: expected\n"
    assert compile_import_lift(issue, "from .local import x\nx()\n", candidate_path="pkg/a.py") is None
    assert compile_import_lift(issue, "from pkg import *\nx()\n", candidate_path="pkg/a.py") is None
    assert compile_import_lift(issue, "def f():\n import pkg\n return pkg.x()\nf()\n", candidate_path="pkg/a.py") is None
    assert compile_import_lift(issue, "import pkg.sub\npkg.sub.x()\n", candidate_path="pkg/a.py") is None


def test_import_lift_rejects_no_exception_contract_and_unsafe_body():
    assert compile_import_lift("visual mismatch only", "import pkg\npkg.x()\n", candidate_path="pkg/a.py") is None
    issue = "RuntimeError: expected\n"
    assert compile_import_lift(issue, "import pkg\nopen('secret')\n", candidate_path="pkg/a.py") is None


def test_classification_requires_exact_public_exception_type_and_message():
    expected = FailureContract("TypeError", "A Vector must be supplied")
    ok, reason, observed = classify_failure(expected, "trace\nTypeError: A Vector must be supplied\n", 1)
    assert ok is True
    assert reason == "trusted_expected_failure_reproduced"
    assert observed == expected
    assert classify_failure(expected, "NameError: N is not defined\n", 1)[0] is False
    assert classify_failure(expected, "TypeError: different\n", 1)[0] is False
    assert classify_failure(expected, "", 0)[1] == "semantic_failure_not_reproduced"
