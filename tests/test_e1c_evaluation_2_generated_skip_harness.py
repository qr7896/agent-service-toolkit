import ast

import pytest

from evals.e1c_evaluation_2_generated_skip_harness import build_driver, validate_fixture

CASE = "import pytest\n@pytest.mark.skip\ndef test_case():\n    pass\n"


def test_driver_has_fixed_file_collection_no_existing_conftest_or_plugins():
    driver = build_driver(CASE, ["-rs"], ["-rs", "--runxfail"])
    ast.parse(driver)
    assert "--noconftest" in driver and "--confcutdir=" in driver and "PYTEST_DISABLE_PLUGIN_AUTOLOAD" in driver
    assert "str(case)" in driver and "cwd=folder" in driver
    assert len(validate_fixture(CASE)) == 64


@pytest.mark.parametrize("source", [CASE.replace("pass", "open('tests/answer.py')"),
                                    CASE.replace("test_case()", "test_case(pytester)"),
                                    CASE.replace("pytest.mark.skip", "pytest.mark.skipif(custom)"),
                                    CASE.replace("import pytest", "import os\nimport pytest"),
                                    CASE + "pytest.main([])\n"])
def test_generated_fixture_cannot_add_arbitrary_execution_or_injection(source):
    with pytest.raises(ValueError):
        validate_fixture(source)


@pytest.mark.parametrize("flags", [["tests/official.py"], ["--pyargs"], ["-c", "other.ini"], ["-p", "custom"], ["-rs", "-rs"]])
def test_model_cannot_select_paths_config_or_plugins(flags):
    with pytest.raises(ValueError):
        build_driver(CASE, flags, ["-rs"])
