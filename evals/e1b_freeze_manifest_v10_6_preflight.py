import json

from evals.e1b_freeze_manifest_v10_6 import content_manifest, environment_metadata, verify_manifest


def report():
    manifest = content_manifest()
    verification = verify_manifest(manifest)
    return {
        "protocol": "e1b-v10-6-freeze-manifest-offline-preflight-v1",
        "content_manifest_sha256": manifest["content_manifest_sha256"],
        "required_file_count": len(manifest["files"]),
        "action_set_manifest_sha256": manifest["action_set_manifest_sha256"],
        "protocol_invariant_report_sha256": manifest["protocol_invariant_report_sha256"],
        "protocol_invariant_fixture_sha256": manifest["protocol_invariant_fixture_sha256"],
        "excluded_source_count": len(manifest["excluded_sources"]),
        "verification": verification,
        "environment": environment_metadata(),
        "provider_calls": 0,
        "live_runner_exists": False,
    }


if __name__ == "__main__":
    print(json.dumps(report(), ensure_ascii=False, indent=2))
