"""Reproducer v4: issue-derived behavioral witnesses for zero-call development."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from evals.e1c_blind_boundary import AgentView, assert_agent_payload, audit_serialized_agent_trace
from evals.e1c_blind_reproducer_v2 import infrastructure_failure, repair_probe_context, run_probe
from evals.e1c_blind_reproducer_v3 import exact_test_candidates

_MODEL = re.compile(r"^class\s+(\w+)\(([A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*)\):\s*$")
_TEST = re.compile(r"^def\s+(test_\w+)\(self\):\s*$")


def _django_settings_prefix() -> str:
    return (
        "from django.conf import settings\n"
        "if not settings.configured:\n"
        "    settings.configure(INSTALLED_APPS=[], DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}, SECRET_KEY='blind', DEFAULT_AUTO_FIELD='django.db.models.AutoField')\n"
        "import django\n"
        "django.setup()\n"
    )


def _extract_model_blocks(statement: str) -> list[tuple[str, list[str]]]:
    lines = statement.replace("\t", "    ").splitlines()
    blocks: list[tuple[str, list[str]]] = []
    index = 0
    while index < len(lines):
        match = _MODEL.match(lines[index].strip())
        if not match:
            index += 1
            continue
        name = match.group(1)
        block = [lines[index].strip()]
        index += 1
        while index < len(lines):
            line = lines[index]
            if _MODEL.match(line.strip()) or _TEST.match(line.strip()):
                break
            if line.strip() and not line.startswith((" ", "\t")):
                break
            block.append(line.rstrip())
            index += 1
        blocks.append((name, block))
    return blocks


def _with_app_label(block: list[str]) -> list[str]:
    if any(line.strip() == "class Meta:" for line in block):
        result: list[str] = []
        inserted = False
        for line in block:
            result.append(line)
            if line.strip() == "class Meta:":
                result.append("        app_label = 'blind_repro'")
                inserted = True
        return result if inserted else block
    return [*block, "    class Meta:", "        app_label = 'blind_repro'"]


def _extract_test_block(statement: str) -> tuple[str, list[str]] | None:
    lines = statement.replace("\t", "    ").splitlines()
    for index, line in enumerate(lines):
        match = _TEST.match(line.strip())
        if not match:
            continue
        body: list[str] = []
        index += 1
        while index < len(lines):
            current = lines[index]
            if current.strip() and not current.startswith((" ", "\t")):
                break
            body.append(current.rstrip())
            index += 1
        if body:
            return match.group(1), body
    return None


def django_inline_test_witness_candidates(statement: str, repo: str) -> list[dict]:
    if repo != "django/django":
        return []
    models = _extract_model_blocks(statement)
    test = _extract_test_block(statement)
    if len(models) < 1 or test is None:
        return []
    test_name, body = test
    model_source = "\n".join(
        line for _, block in models for line in [*_with_app_label(block), ""]
    )
    model_names = [name for name, _ in models]
    create_models = "\n".join(f"    editor.create_model({name})" for name in model_names)
    indented = "\n".join("    " + line[1:] if line.startswith(" ") else "    " + line for line in body)
    source = (
        _django_settings_prefix()
        + "from contextlib import contextmanager\n"
        + "from django.db import connection, models\n"
        + ("from django.db.models import Prefetch\n" if "Prefetch(" in statement else "")
        + "from django.test.utils import CaptureQueriesContext\n"
        + model_source
        + "\nwith connection.schema_editor() as editor:\n"
        + create_models
        + "\nclass _BlindAssertions:\n"
        + "    @contextmanager\n"
        + "    def assertNumQueries(self, expected):\n"
        + "        with CaptureQueriesContext(connection) as captured:\n"
        + "            yield\n"
        + "        assert len(captured) == expected, (expected, len(captured), list(captured.captured_queries))\n"
        + "    def assertEqual(self, left, right):\n"
        + "        assert left == right, (left, right)\n"
        + f"def _blind_{test_name}(self):\n"
        + indented
        + f"\n_blind_{test_name}(_BlindAssertions())\n"
    )
    try:
        compile(source, "<django-inline-test-witness>", "exec")
    except SyntaxError:
        return []
    return [{
        "kind": "issue_snippet",
        "content": source,
        "content_sha256": hashlib.sha256(source.encode()).hexdigest(),
        "origin": "django_inline_issue_test_witness",
        "repair_sensitive": True,
        "semantic_contract": "issue_assertions_must_hold",
        "contract_witness": True,
    }]


def django_reverse_prefetch_slice_witness_candidates(statement: str, repo: str) -> list[dict]:
    if repo != "django/django" or "Prefetch(" not in statement or "[:" not in statement:
        return []
    owner_match = re.search(r"([A-Z]\w*)\.objects\.prefetch_related\s*\(\s*Prefetch", statement)
    lookup_match = re.search(r"Prefetch\s*\(\s*['\"](\w+)_set['\"]", statement)
    child_match = re.search(r"queryset\s*=\s*([A-Z]\w*)\.objects\.all\(\)\s*\[:(\d+)\]", statement)
    attr_match = re.search(r"to_attr\s*=\s*['\"](\w+)['\"]", statement)
    if not owner_match or not lookup_match or not child_match:
        return []
    owner, reverse_name = owner_match.group(1), lookup_match.group(1)
    child, count = child_match.group(1), int(child_match.group(2))
    if child.lower() != reverse_name.lower():
        return []
    to_attr = attr_match.group(1) if attr_match else "blind_items"
    source = (
        _django_settings_prefix()
        + "from django.db import connection, models\n"
        + "from django.db.models import Prefetch\n"
        + f"class {owner}(models.Model):\n"
        + "    class Meta:\n        app_label = 'blind_repro'\n"
        + f"class {child}(models.Model):\n"
        + f"    {owner.lower()} = models.ForeignKey({owner}, on_delete=models.CASCADE)\n"
        + "    class Meta:\n        app_label = 'blind_repro'\n"
        + "with connection.schema_editor() as editor:\n"
        + f"    editor.create_model({owner})\n"
        + f"    editor.create_model({child})\n"
        + f"parent = {owner}.objects.create()\n"
        + f"for _ in range({count + 1}):\n    {child}.objects.create({owner.lower()}=parent)\n"
        + f"queryset = {owner}.objects.prefetch_related(Prefetch('{child.lower()}_set', queryset={child}.objects.all()[:{count}], to_attr='{to_attr}'))\n"
        + "rows = list(queryset)\n"
        + f"assert len(rows[0].{to_attr}) == {count}, len(rows[0].{to_attr})\n"
    )
    try:
        compile(source, "<django-prefetch-slice-witness>", "exec")
    except SyntaxError:
        return []
    failure_fragment_match = re.search(r"(?:AssertionError|TypeError):\s*([^\n]+)", statement)
    return [{
        "kind": "issue_snippet",
        "content": source,
        "content_sha256": hashlib.sha256(source.encode()).hexdigest(),
        "origin": "django_reverse_prefetch_slice_witness",
        "repair_sensitive": True,
        "semantic_contract": "sliced_prefetch_must_evaluate_without_error",
        "contract_witness": True,
        "expected_failure_fragment": failure_fragment_match.group(1).strip().rstrip(":") if failure_fragment_match else None,
    }]


def django_migration_order_witness_candidates(statement: str, repo: str) -> list[dict]:
    if repo != "django/django" or "auto-detector" not in statement.lower():
        return []
    before, marker, after = statement.partition("And change to this:")
    if not marker:
        return []
    before_models = _extract_model_blocks(before)
    after_models = _extract_model_blocks(after)
    if len(before_models) != 1 or len(after_models) < 2:
        return []
    base = before_models[0][0]
    child = next((name for name, block in after_models if any(f"class {name}({base}):" in line for line in block)), None)
    field_match = re.search(r"^\s*(\w+)\s*=\s*models\.CharField\(max_length\s*=\s*(\d+)\)", before, re.MULTILINE)
    if child is None or field_match is None:
        return []
    field, max_length = field_match.group(1), int(field_match.group(2))
    base_key = base.lower()
    source = (
        _django_settings_prefix()
        + "from django.db import models\n"
        + "from django.db.migrations.autodetector import MigrationAutodetector\n"
        + "from django.db.migrations.state import ModelState, ProjectState\n"
        + "before = ProjectState()\n"
        + f"before.add_model(ModelState('blind_repro', '{base}', fields=[('id', models.AutoField(primary_key=True)), ('{field}', models.CharField(max_length={max_length}))]))\n"
        + "after = ProjectState()\n"
        + f"after.add_model(ModelState('blind_repro', '{base}', fields=[('id', models.AutoField(primary_key=True))]))\n"
        + f"after.add_model(ModelState('blind_repro', '{child}', fields=[('{base_key}_ptr', models.OneToOneField(auto_created=True, on_delete=models.CASCADE, parent_link=True, primary_key=True, serialize=False, to='blind_repro.{base_key}')), ('{field}', models.CharField(max_length={max_length}))], bases=('blind_repro.{base_key}',)))\n"
        + "changes = MigrationAutodetector(before, after)._detect_changes()\n"
        + "operations = changes['blind_repro'][0].operations\n"
        + "names = [type(operation).__name__ for operation in operations]\n"
        + f"remove_index = next(i for i, operation in enumerate(operations) if type(operation).__name__ == 'RemoveField' and getattr(operation, 'model_name', '') == '{base_key}' and getattr(operation, 'name', '') == '{field}')\n"
        + f"create_index = next(i for i, operation in enumerate(operations) if type(operation).__name__ == 'CreateModel' and getattr(operation, 'name', '') == '{child}')\n"
        + "assert remove_index < create_index, names\n"
    )
    try:
        compile(source, "<django-migration-order-witness>", "exec")
    except SyntaxError:
        return []
    return [{
        "kind": "issue_snippet",
        "content": source,
        "content_sha256": hashlib.sha256(source.encode()).hexdigest(),
        "origin": "django_migration_order_witness",
        "repair_sensitive": True,
        "semantic_contract": "autodetector_remove_field_before_create_subclass",
        "contract_witness": True,
    }]


def issue_witness_candidates(statement: str, repo: str, *, limit: int = 6) -> list[dict]:
    from evals.e1c_blind_reproducer_v3 import issue_probe_candidates as v3_candidates

    raw = [
        *django_inline_test_witness_candidates(statement, repo),
        *django_reverse_prefetch_slice_witness_candidates(statement, repo),
        *django_migration_order_witness_candidates(statement, repo),
        *v3_candidates(statement, repo, limit=limit),
    ]
    result: list[dict] = []
    seen: set[str] = set()
    for item in raw:
        digest = item["content_sha256"]
        if digest in seen:
            continue
        seen.add(digest)
        result.append(item)
        if len(result) == limit:
            break
    return result


def freeze_probe_plan_v4(row: dict, view: AgentView) -> dict:
    probes: list[dict] = []
    for candidate in issue_witness_candidates(view.problem_statement, row["repo"], limit=6):
        probes.append({**candidate, "role": f"candidate_{len(probes)}", "purpose": "reproducer_candidate"})
    for candidate in exact_test_candidates(view.problem_statement, view.workspace, row["repo"], limit=3):
        probes.append({**candidate, "role": f"candidate_{len(probes)}", "purpose": "reproducer_candidate"})
    value = {
        "schema": "e1c-blind-reproducer-plan-v4",
        "instance_id": row["instance_id"],
        "base_commit": row["base_commit"],
        "repo": row["repo"],
        "image": row["image"],
        "probes": probes,
        "status": "planned" if probes else "no_candidates",
    }
    assert_agent_payload(value)
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    audit_serialized_agent_trace(encoded)
    return {**value, "plan_sha256": hashlib.sha256(encoded.encode()).hexdigest()}


def _matched_v4(result: dict, probe: dict) -> bool:
    if result.get("passed") or result.get("timed_out") or result.get("exit_code") in {None, 0}:
        return False
    if infrastructure_failure(result) or probe.get("repair_sensitive") is False:
        return False
    if probe.get("contract_witness"):
        tail = str(result.get("tail", ""))
        fragment = probe.get("expected_failure_fragment")
        if fragment:
            return str(fragment).lower() in tail.lower()
        return "AssertionError" in tail
    return False


def run_prepatch_probes_v4(row: dict, view: AgentView, artifact_dir: Path) -> dict:
    from evals.e1c_blind_reproducer_v3 import _matches

    plan = freeze_probe_plan_v4(row, view)
    results: list[dict] = []
    executed_probes: list[dict] = []
    diagnoses: list[dict] = []
    selected_role = None
    for probe in plan["probes"]:
        result = run_probe(row, probe, artifact_dir, timeout=90)
        executed_probes.append(probe)
        results.append(result)
        if result.get("timed_out"):
            reason = "timeout"
        elif infrastructure_failure(result):
            reason = "infrastructure_failure"
        elif result.get("passed"):
            reason = "candidate_passed"
        elif _matched_v4(result, probe) or _matches(view.problem_statement, result, probe):
            reason = "issue_matched_failure"
            selected_role = result["role"]
        else:
            reason = "semantic_mismatch"
        diagnoses.append({"role": result["role"], "reason": reason, "origin": probe.get("origin")})
        if selected_role:
            break
    if selected_role:
        status, no_reproducer_reason = "reproduced_failure", None
    else:
        reasons = {item["reason"] for item in diagnoses}
        if not diagnoses:
            no_reproducer_reason = "no_candidates"
        elif reasons == {"candidate_passed"}:
            no_reproducer_reason = "all_candidates_passed"
        elif "semantic_mismatch" in reasons:
            no_reproducer_reason = "semantic_mismatch"
        elif "infrastructure_failure" in reasons:
            no_reproducer_reason = "infrastructure_failure"
        elif "timeout" in reasons:
            no_reproducer_reason = "timeout"
        else:
            no_reproducer_reason = sorted(reasons)[0]
        status = "no_reproducer"
    value = {
        "schema": "e1c-blind-prepatch-probes-v4",
        "plan": plan,
        "executed_probes": executed_probes,
        "results": results,
        "reproducer_status": status,
        "selected_reproducer_role": selected_role,
        "no_reproducer_reason": no_reproducer_reason,
        "diagnoses": diagnoses,
    }
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    audit_serialized_agent_trace(encoded)
    return {**value, "freeze_sha256": hashlib.sha256(encoded.encode()).hexdigest()}


def repair_probe_context_v4(prepatch: dict) -> dict:
    return repair_probe_context(prepatch)
