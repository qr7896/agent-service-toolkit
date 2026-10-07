"""Controller-owned, generated-only unconditional-skip diagnostic component.

Not a live Agent tool or a replacement for the frozen native-fixture guard.
The model never supplies shell commands, paths, plugins, or this driver source.
"""

from __future__ import annotations

import ast
import hashlib
import json
import subprocess

from evals.e1c_evaluation_2_container_health import require_engine
from evals.e1c_evaluation_2_dev_pilot import ROOT, _save, _sha
from evals.e1c_evaluation_2_probe import docker_command
from evals.e1c_strict_v5_boundary import audit_repair_visible_payload

OUT = ROOT / ".codex/e1c/evaluation_2/generated-skip-component-zero-v1"
DRIVER = '''import json, os, sys, tempfile, subprocess, re
from pathlib import Path
import pytest
try:
    Path(pytest.__file__).resolve().relative_to(Path('/testbed'))
except ValueError:
    raise RuntimeError('pytest production import identity differs')
folder = Path(tempfile.mkdtemp(prefix='e1c2-generated-only-'))
case = folder / 'generated_case.py'
case.write_text(DATA['source'], encoding='utf-8')
config = folder / 'isolated.ini'
config.write_text('[pytest]\\naddopts =\\n', encoding='utf-8')
env = dict(os.environ)
env['PYTEST_DISABLE_PLUGIN_AUTOLOAD'] = '1'
env.pop('PYTEST_ADDOPTS', None)
results = {}
for label in ('control', 'target'):
    command = [sys.executable, '-X', 'utf8', '-m', 'pytest', *DATA[label],
        '-p', 'no:cacheprovider', '--noconftest', '--confcutdir=' + str(folder),
        '-c', str(config), str(case)]
    completed = subprocess.run(command, cwd=folder, env=env, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, text=True, encoding='utf-8', timeout=20, check=False)
    locations = [{'path': m[1], 'line': int(m[2])} for m in
        re.finditer(r'^SKIPPED \\[\\d+\\] (.*?):(\\d+):', completed.stdout, re.M)]
    results[label] = {'returncode': completed.returncode, 'locations': locations,
        'output_tail': completed.stdout[-4000:]}
print('E1C2_NATIVE_DIAGNOSTIC=' + json.dumps({'results': results,
    'generated_case': str(case), 'original_tests_requested': False,
    'conftest_disabled': True, 'plugin_autoload_disabled': True}))
'''


def validate_fixture(source):
    if not isinstance(source, str) or not 1 <= len(source) <= 3000:
        raise ValueError("generated_fixture_size")
    audit_repair_visible_payload(source)
    tree = ast.parse(source)
    if len(tree.body) != 2 or not isinstance(tree.body[0], ast.Import) or ast.unparse(tree.body[0]) != "import pytest":
        raise ValueError("only_pytest_import_and_one_skip_case_supported")
    node = tree.body[1]
    if (not isinstance(node, ast.FunctionDef) or not node.name.startswith("test_")
            or node.args.posonlyargs or node.args.args or node.args.kwonlyargs or node.args.vararg or node.args.kwarg
            or node.returns or getattr(node, "type_params", []) or len(node.body) != 1 or not isinstance(node.body[0], ast.Pass)
            or len(node.decorator_list) != 1 or ast.unparse(node.decorator_list[0]) != "pytest.mark.skip"):
        raise ValueError("only_generated_unconditional_skip_without_injected_fixtures_supported")
    return hashlib.sha256(source.encode()).hexdigest()


def build_driver(source, control, target):
    validate_fixture(source)
    for flags in (control, target):
        if (not isinstance(flags, list) or not 1 <= len(flags) <= 2 or any(not isinstance(f, str) for f in flags)
                or len(set(flags)) != len(flags) or any(f not in {"-rs", "--runxfail"} for f in flags)):
            raise ValueError("unsupported_native_flags_or_paths")
    data = json.dumps({"source": source, "control": control, "target": target})
    # Driver capabilities are constant controller code; case data cannot escape repr/JSON.
    return "import json\nDATA = json.loads(" + repr(data) + ")\n" + DRIVER


def smoke():
    if OUT.exists():
        raise FileExistsError("component already started; preserve it")
    from evals.e1c_evaluation_2_bounded_repro_dev import inputs

    rows = [(t, f) for t, f, _ in inputs() if t["instance_id"].split("__", 1)[0] == "pytest-dev"]
    if len(rows) != 1:
        raise ValueError("one old DEV pytest image required for component verification")
    task, frozen = rows[0]
    require_engine((task["image_id"],))
    source = "import pytest\n\n@pytest.mark.skip\ndef test_generated_case():\n    pass\n"
    driver = build_driver(source, ["-rs"], ["-rs", "--runxfail"])
    digest = hashlib.sha256(driver.encode()).hexdigest()
    _save(OUT / "freeze.json", {"schema": "e1c2-generated-skip-component-freeze-v1", "provider_calls": 0,
                               "synthetic_component_not_task_score": True, "model_fixture_source": False,
                               "module_sha256": _sha(ROOT / "evals/e1c_evaluation_2_generated_skip_harness.py"),
                               "driver_sha256": digest, "generated_fixture_sha256": validate_fixture(source),
                               "image_id": task["image_id"], "base_commit": frozen["base_commit"]})
    path = OUT / "controller_driver.py"
    path.write_bytes(driver.encode())
    # Deliberately use only the command builder, not forge a model safe_static_check.
    descriptor = {"probe_sha256": digest, "input_sha256": frozen["input_sha256"]}
    command = docker_command(descriptor, task["image_id"], frozen["base_commit"], path)
    log_path = OUT / "driver.log"
    with log_path.open("xb") as log:
        try:
            completed = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=60, check=False)
        except subprocess.TimeoutExpired:
            subprocess.run(["docker", "rm", "-f", command[command.index("--name") + 1]], capture_output=True, timeout=30, check=False)
            raise
    raw = log_path.read_text(encoding="utf-8", errors="replace")
    marker = next((line for line in raw.splitlines() if line.startswith("E1C2_NATIVE_DIAGNOSTIC=")), None)
    if completed.returncode or marker is None:
        raise RuntimeError("native component execution failed; inspect preserved log, no automatic retry")
    diagnostic = json.loads(marker.split("=", 1)[1])
    if not all(row["returncode"] == 0 and row["locations"] for row in diagnostic["results"].values()):
        raise ValueError("native collection/reporting component not verified")
    value = {"schema": "e1c2-generated-skip-component-result-v1", "provider_calls": 0,
             "synthetic_component_not_task_score": True, "network_none": True, "pull_never": True,
             "fixture_is_only_generated_unconditional_skip": True, "driver_is_controller_owned": True,
             "diagnostic": diagnostic, "log_sha256": _sha(log_path), "trusted_reproducer": False}
    _save(OUT / "result.json", value)
    return value


if __name__ == "__main__":
    print(json.dumps(smoke(), ensure_ascii=False))
