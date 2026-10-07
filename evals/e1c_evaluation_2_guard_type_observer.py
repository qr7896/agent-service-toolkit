"""Controller-owned, values-free type observation for an already validated probe.

No model trace tool or safe_static_check for the driver. Original source bytes
are mounted separately; instrumentation/filename may affect execution timing.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path
from uuid import uuid4

from evals.e1c_evaluation_2_container_health import (
    ContainerInfrastructureUnavailable,
    require_engine,
)
from evals.e1c_evaluation_2_dev_pilot import _save, _sha
from evals.e1c_evaluation_2_probe import docker_command
from evals.e1c_strict_v5_boundary import assert_production_relative_path

DRIVER = '''import hashlib, json, runpy, sys
if hashlib.sha256(open('/e1c2_model_probe.py', 'rb').read()).hexdigest() != DATA['probe_sha256']:
    raise RuntimeError('model probe source changed')
for site in DATA['sites']:
    if hashlib.sha256(open('/testbed/' + site['path'], 'rb').read()).hexdigest() != site['source_sha256']:
        raise RuntimeError('observed production source changed')
try:
    import numpy
    numpy_array_type = numpy.ndarray
except ImportError:
    numpy_array_type = None
builtin_types = [(list, 'builtins.list'), (tuple, 'builtins.tuple'), (dict, 'builtins.dict'),
    (str, 'builtins.str'), (int, 'builtins.int'), (float, 'builtins.float'),
    (bool, 'builtins.bool'), (type(None), 'builtins.NoneType')]
records = []
def trace(frame, event, arg):
    if event == 'line' and len(records) < 8:
        for site in DATA['sites']:
            if frame.f_code.co_filename == '/testbed/' + site['path'] and frame.f_lineno == site['line']:
                present = site['variable'] in frame.f_locals
                cls = type(frame.f_locals[site['variable']]) if present else None
                tag = next((name for known, name in builtin_types if cls is known), None)
                if tag is None and numpy_array_type is not None and cls is numpy_array_type:
                    tag = 'numpy.ndarray'
                records.append({'path': site['path'], 'line': site['line'], 'variable': site['variable'],
                    'observed_type': tag or 'other_unclassified_type', 'local_present': present})
    return trace
sys.settrace(trace)
try:
    runpy.run_path('/e1c2_model_probe.py', run_name='__main__')
finally:
    sys.settrace(None)
    print(DATA['marker'] + json.dumps({'records': records, 'argument_values_emitted': False}))
'''


def build_driver(probe_sha, sites, nonce):
    if not re.fullmatch(r"[0-9a-f]{64}", probe_sha) or not re.fullmatch(r"[0-9a-f]{32}", nonce) or not 1 <= len(sites) <= 2:
        raise ValueError("bounded observer identity required")
    for site in sites:
        if set(site) != {"path", "line", "variable", "source_sha256"}:
            raise ValueError("unexpected observation capability")
        assert_production_relative_path(site["path"])
        if (type(site["line"]) is not int or not 1 <= site["line"] <= 200000
                or not re.fullmatch(r"[A-Za-z_]\w{0,99}", site["variable"]) or site["variable"].startswith("__")
                or not re.fullmatch(r"[0-9a-f]{64}", site["source_sha256"])):
            raise ValueError("invalid bounded observation site")
    marker = "E1C2_GUARD_TYPES_" + nonce + "="
    data = json.dumps({"probe_sha256": probe_sha, "sites": sites, "marker": marker})
    return "import json\nDATA = json.loads(" + repr(data) + ")\n" + DRIVER, marker


def observe(candidate, probe_path, sites, image, base_commit, root):
    if root.exists():
        raise FileExistsError("type observation already started")
    if candidate.get("safe_static_check") is not True or _sha(probe_path) != candidate["probe_sha256"]:
        raise ValueError("original model probe must already be statically validated and bound")
    require_engine((image,))
    driver, marker = build_driver(candidate["probe_sha256"], sites, uuid4().hex)
    driver_sha = hashlib.sha256(driver.encode()).hexdigest()
    _save(root / "freeze.json", {"original_candidate": candidate, "sites": sites, "driver_sha256": driver_sha,
                                "observer_module_sha256": _sha(Path(__file__)), "image": image, "base_commit": base_commit,
                                "provider_calls": 0, "controller_owned_driver": True})
    path = root / "driver.py"
    path.write_bytes(driver.encode())
    descriptor = {"probe_sha256": driver_sha, "input_sha256": candidate["input_sha256"]}
    command = docker_command(descriptor, image, base_commit, path)
    image_index = command.index(image)
    command[image_index:image_index] = ["--mount", f"type=bind,source={probe_path.resolve()},target=/e1c2_model_probe.py,readonly"]
    log_path = root / "observer.log"
    with log_path.open("xb") as log:
        try:
            completed = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=90, check=False)
        except subprocess.TimeoutExpired:
            subprocess.run(["docker", "rm", "-f", command[command.index("--name") + 1]], capture_output=True, timeout=30, check=False)
            raise ContainerInfrastructureUnavailable("type observer timeout; no retry") from None
    raw = log_path.read_text(encoding="utf-8", errors="replace")
    if completed.returncode in {90, 125, 126, 127}:
        raise ContainerInfrastructureUnavailable("type observer transport/source identity failure")
    lines = [line[len(marker):] for line in raw.splitlines() if line.startswith(marker)]
    if len(lines) != 1:
        raise ValueError("controller type observation marker missing or ambiguous")
    report = json.loads(lines[0])
    value = {"schema": "e1c2-source-bound-guard-type-observation-v1", "provider_calls": 0,
             "original_probe_sha256": candidate["probe_sha256"], "observer_driver_sha256": driver_sha,
             "source_freeze_sha256": _sha(root / "freeze.json"), "log_sha256": _sha(log_path),
             "returncode": completed.returncode, "network_none": True, "read_only": True, "pull_never": True,
             "program_source_bytes_changed": False, "instrumented_same_semantics_claimed": False,
             "machine_trusted": False, **report}
    _save(root / "result.json", value)
    return value
