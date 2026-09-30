import json
import tempfile
from pathlib import Path

from evals.e1b_experiment_admission_v10_7 import admit
from evals.e1b_experiment_admission_v10_7_preflight import synthetic_config
from evals.e1b_experiment_package_v10_8 import build_package, dry_run_materialize


def report():
    config = synthetic_config()
    admission = admit(config)
    package = build_package(admission, config)
    with tempfile.TemporaryDirectory() as directory:
        dry_run = dry_run_materialize(package, Path(directory))
    return {
        "protocol": "e1b-v10-8-experiment-package-offline-preflight-v1",
        "run_id": package["run_id"],
        "package_manifest_sha256": package["package_manifest_sha256"],
        "freeze_manifest_sha256": package["freeze_manifest_sha256"],
        "admission_manifest_sha256": package["admission_manifest_sha256"],
        "task_manifest_sha256": package["task_manifest_sha256"],
        "required_artifact_count": len(package["required_artifacts"]),
        "dry_run": dry_run,
        "provider_calls": 0,
        "starts_experiment": False,
        "live_runner_exists": False,
    }


if __name__ == "__main__":
    print(json.dumps(report(), ensure_ascii=False, indent=2))
