from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


REQUIRED_CONFIG = {
    "method",
    "action_space",
    "ranking_budget",
    "stop_rule",
    "filter_v3",
    "evidence_features",
    "prediction_protocol",
    "implementation_files",
}


def freeze(
    prediction: Path,
    report: Path,
    method: str,
    split: str,
    upstream_ref: str,
    config: Path | None = None,
) -> dict:
    config_data = json.loads(config.read_text(encoding="utf-8")) if config else {}
    missing = sorted(REQUIRED_CONFIG - set(config_data))
    checks = {
        "cal500_split": split == "cal500",
        "immutable_upstream_ref": bool(re.fullmatch(r"[0-9a-f]{40}", upstream_ref)),
        "complete_config": not missing,
        "method_matches_config": config_data.get("method") == method,
        "prediction_exists": prediction.is_file(),
        "official_report_exists": report.is_file(),
    }
    allowed = all(checks.values())
    implementation_hashes = {
        path: sha(Path(path)) for path in config_data.get("implementation_files", [])
    }
    return {
        "protocol": "serbench-method-freeze-v2",
        "split": split,
        "method": method,
        "upstream_ref": upstream_ref,
        "prediction_sha256": sha(prediction),
        "report_sha256": sha(report),
        "config_sha256": sha(config) if config else None,
        "frozen_config": config_data,
        "implementation_sha256": implementation_hashes,
        "checks": checks,
        "missing_config_fields": missing,
        "test500_allowed": allowed,
        "claim_boundary": "Hash manifest freezes artifacts only; it does not certify benchmark quality or authorize private-label access.",
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prediction", type=Path, required=True)
    ap.add_argument("--report", type=Path, required=True)
    ap.add_argument("--config", type=Path, required=True)
    ap.add_argument("--method", required=True)
    ap.add_argument("--split", required=True)
    ap.add_argument("--upstream-ref", required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    result = freeze(
        args.prediction,
        args.report,
        args.method,
        args.split,
        args.upstream_ref,
        args.config,
    )
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
