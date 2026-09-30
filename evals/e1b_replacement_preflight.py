import argparse
import json
from pathlib import Path

from evals.e1b_experiment_admission_v10_7 import AdmissionConfig, admit
from evals.e1b_experiment_package_v10_8 import build_package, dry_run_materialize
from evals.e1b_freeze_manifest_v10_6 import EXCLUDED_SOURCES


def run(metadata_path, config_path, output_dir):
    metadata = json.loads(Path(metadata_path).read_text(encoding="utf-8"))
    raw = json.loads(Path(config_path).read_text(encoding="utf-8"))
    config = AdmissionConfig(
        task_metadata=metadata,
        data_isolation=EXCLUDED_SOURCES,
        frozen_identifiers=raw["frozen_identifiers"],
        provider_call_ceiling=raw["provider_call_ceiling"],
        provider_token_ceiling=raw["provider_token_ceiling"],
        one_shot_frozen=raw["one_shot_frozen"],
        runtime_features=tuple(raw.get("runtime_features", ())),
    )
    admission = admit(config)
    if admission["decision"] != "ADMIT_OFFLINE_READY":
        return {
            "status": "REJECT",
            "admission": admission,
            "provider_calls": 0,
            "starts_experiment": False,
        }
    package = build_package(admission, config)
    dry_run = dry_run_materialize(package, output_dir)
    return {
        "status": "READY_FOR_DRY_RUN_AUDIT",
        "admission": admission,
        "run_id": package["run_id"],
        "package_manifest_sha256": package["package_manifest_sha256"],
        "dry_run": dry_run,
        "provider_calls": 0,
        "starts_experiment": False,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--metadata", required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    result = run(args.metadata, args.config, args.output_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["status"] == "READY_FOR_DRY_RUN_AUDIT" else 2)


if __name__ == "__main__":
    main()
