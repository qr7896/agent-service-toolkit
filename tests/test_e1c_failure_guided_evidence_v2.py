from evals.e1c_failure_guided_evidence_v2 import locate, windows


def test_public_test_import_resolves_one_hop_reexport(tmp_path):
    forms = tmp_path / "django" / "forms"
    forms.mkdir(parents=True)
    (forms / "__init__.py").write_text("from django.forms.fields import *\n", encoding="utf-8")
    (forms / "fields.py").write_text(
        "class JSONField:\n    def prepare_value(self, value):\n        return value\n", encoding="utf-8")
    tests = tmp_path / "tests" / "forms_tests" / "field_tests"
    tests.mkdir(parents=True)
    (tests / "test_jsonfield.py").write_text(
        "from django.forms import JSONField\n\ndef test_prepare_value():\n    pass\n", encoding="utf-8")
    selector = "test_prepare_value (forms_tests.field_tests.test_jsonfield.JSONFieldTest)"
    found = locate("Unicode in JSONFields", "", tmp_path, [selector])
    assert found == [{"path": "django/forms/fields.py", "confidence": 75,
                      "origin": "public_failing_test_import", "symbol": "JSONField"}]
    shown = windows("Unicode in JSONFields", "", tmp_path, [selector])
    assert shown[0]["path"] == "django/forms/fields.py"
    assert "class JSONField" in shown[0]["text"]


def test_generic_issue_symbol_does_not_claim_high_confidence(tmp_path):
    production = tmp_path / "package"
    production.mkdir()
    (production / "query.py").write_text("class QuerySet:\n    pass\n", encoding="utf-8")
    tests = tmp_path / "tests" / "cases"
    tests.mkdir(parents=True)
    (tests / "tests.py").write_text("from package.query import QuerySet\n", encoding="utf-8")
    assert locate("QuerySet has a bug", "", tmp_path, ["test_bug (cases.tests.SomeCase)"]) == []


def test_multiple_public_failures_keep_distinct_source_participants(tmp_path):
    forms = tmp_path / "django" / "forms"
    forms.mkdir(parents=True)
    (forms / "fields.py").write_text("class JSONField:\n    pass\n", encoding="utf-8")
    admin = tmp_path / "django" / "contrib" / "admin"
    admin.mkdir(parents=True)
    (admin / "utils.py").write_text("def display_for_field():\n    pass\n", encoding="utf-8")
    tests = tmp_path / "tests" / "cases"
    tests.mkdir(parents=True)
    (tests / "test_jsonfield.py").write_text("from django.forms.fields import JSONField\n", encoding="utf-8")
    (tests / "tests.py").write_text("from django.contrib.admin.utils import display_for_field\n", encoding="utf-8")
    selectors = ["test_prepare (cases.test_jsonfield.Case)",
                 "test_json_display_for_field (cases.tests.Case)"]
    found = locate("Admin JSONFields display incorrectly", "", tmp_path, selectors)
    assert [item["path"] for item in found] == ["django/forms/fields.py", "django/contrib/admin/utils.py"]
