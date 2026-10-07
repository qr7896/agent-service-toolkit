"""Production windows derived from an owned generated-fixture diagnostic."""

from __future__ import annotations

import json
import posixpath
import re

from evals.e1c_evaluation_2_bounded_repro_loop import window
from evals.e1c_evaluation_2_dev_pilot import ROOT, _save, _sha
from evals.e1c_evaluation_2_production_coverage import production_path
from evals.e1c_strict_v5_boundary import assert_production_relative_path

NATIVE = ROOT / ".codex/e1c/evaluation_2/generated-skip-component-zero-v1"
OUT = ROOT / ".codex/e1c/evaluation_2/generated-runtime-location-zero-v1"


def production_locations(diagnostic):
    generated = diagnostic["generated_case"]
    if not isinstance(generated, str) or not re.fullmatch(r"/tmp/e1c2-generated-only-[A-Za-z0-9_-]+/generated_case\.py", generated):
        raise ValueError("diagnostic_not_owned_generated_fixture")
    folder, rows = posixpath.dirname(generated), []
    for label, report in diagnostic["results"].items():
        for location in report["locations"]:
            path, line = location["path"], location["line"]
            if not isinstance(path, str) or "\\" in path or type(line) is not int or not 1 <= line <= 1000000:
                raise ValueError("invalid_runtime_location")
            absolute = posixpath.normpath(posixpath.join(folder, path))
            if absolute == generated:
                continue
            if not absolute.startswith("/testbed/"):
                raise ValueError("runtime_location_outside_production")
            relative = assert_production_relative_path(absolute.removeprefix("/testbed/"))
            if not production_path(relative) or posixpath.basename(relative) in {"conftest.py", "setup.py"}:
                raise ValueError("runtime_location_not_production_source")
            rows.append({"path": relative, "line": line, "report": label, "origin": "owned_native_runtime_report"})
    return rows


def audit():
    if OUT.exists():
        raise FileExistsError("runtime location audit already started")
    from evals.e1c_evaluation_2_bounded_repro_dev import inputs

    frozen = json.loads((NATIVE / "freeze.json").read_bytes())
    if frozen["module_sha256"] != _sha(ROOT / "evals/e1c_evaluation_2_generated_skip_harness.py"):
        raise ValueError("native driver changed")
    receipt = json.loads((NATIVE / "result.json").read_bytes())
    if receipt["log_sha256"] != _sha(NATIVE / "driver.log") or frozen["driver_sha256"] != _sha(NATIVE / "controller_driver.py"):
        raise ValueError("native diagnostic source/log identity changed")
    matched = [(t, f, w) for t, f, w in inputs() if t["image_id"] == frozen["image_id"]]
    if len(matched) != 1 or matched[0][1]["base_commit"] != frozen["base_commit"]:
        raise ValueError("native diagnostic image identity differs from old DEV")
    rows = production_locations(receipt["diagnostic"])
    windows = [{**window(r["path"], matched[0][2], max(1, r["line"] - 6)), "origin": r["origin"], "reported_line": r["line"]} for r in rows]
    value = {"schema": "e1c2-owned-native-runtime-location-zero-v1", "provider_calls": 0,
             "native_result_sha256": _sha(NATIVE / "result.json"),
             "module_sha256": _sha(ROOT / "evals/e1c_evaluation_2_runtime_location_evidence.py"),
             "path_from_runtime_not_manual_selection": True, "original_tests_read": False,
             "synthetic_component_not_task_score": True, "rows": rows, "windows": windows}
    _save(OUT / "result.json", value)
    return value


if __name__ == "__main__":
    print(json.dumps(audit(), ensure_ascii=False))
