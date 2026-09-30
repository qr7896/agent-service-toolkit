"""Single zero-provider entry point to advance strict-v5 admission safely."""

from __future__ import annotations

import json
import os
from contextlib import contextmanager

from evals.e1c_strict_v5_blob_preflight import run as run_blob_preflight
from evals.e1c_strict_v5_equivalent_mirror_acquire import (
    acquire as acquire_equivalent_mirror,
)
from evals.e1c_strict_v5_image_identity import build as build_image_identity
from evals.e1c_strict_v5_official_image_acquire import acquire
from evals.e1c_strict_v5_resume_admission import (
    inspect_local_images,
)
from evals.e1c_strict_v5_resume_admission import (
    run as resume_admission,
)


@contextmanager
def _proxy_environment(proxy: str | None):
    if not proxy:
        yield
        return
    keys = ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy")
    previous = {key: os.environ.get(key) for key in keys}
    try:
        for key in keys:
            os.environ[key] = proxy
        yield
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def _run(pull_timeout: int, proxy: str | None) -> dict:
    local = inspect_local_images()
    if local.get("ready"):
        admission = resume_admission()
        return {
            "schema": "e1c-strict-v5-advance-admission-v1",
            "ready": bool(admission.get("ready")),
            "stage": "admission_seal",
            "reason": admission.get("reason"),
            "provider_calls": 0,
            "live_model_run": False,
        }

    transport = run_blob_preflight(
        proxy=proxy,
        max_estimated_seconds=pull_timeout,
    )
    if not transport.get("ready"):
        return {
            "schema": "e1c-strict-v5-advance-admission-v1",
            "ready": False,
            "stage": "blob_transport_preflight",
            "reason": transport.get("reason"),
            "checked_count": transport.get("checked_count", 0),
            "required_count": transport.get("required_count", 0),
            "missing_instance_ids": local.get("missing_instance_ids", []),
            "provider_calls": 0,
            "live_model_run": False,
        }

    image = acquire(pull_timeout=pull_timeout)
    if not image.get("ready"):
        identity = build_image_identity(proxy=proxy)
        if not identity.get("mirror_transport_ready"):
            return {
                "schema": "e1c-strict-v5-advance-admission-v1",
                "ready": False,
                "stage": "image_identity",
                "reason": "authoritative_image_digest_unavailable_or_mirror_mismatch",
                "official_acquisition_reason": image.get("reason"),
                "authoritative_ready_count": identity.get("authoritative_ready_count", 0),
                "mirror_equivalent_count": identity.get("mirror_equivalent_count", 0),
                "mirror_mismatch_count": identity.get("mirror_mismatch_count", 0),
                "mirror_route_conclusively_closed": identity.get(
                    "mirror_route_conclusively_closed",
                    False,
                ),
                "provider_calls": 0,
                "live_model_run": False,
            }
        image = acquire_equivalent_mirror(identity, pull_timeout=pull_timeout)
        if not image.get("ready"):
            return {
                "schema": "e1c-strict-v5-advance-admission-v1",
                "ready": False,
                "stage": "equivalent_mirror_acquisition",
                "reason": image.get("reason"),
                "provider_calls": 0,
                "live_model_run": False,
            }
    admission = resume_admission()
    return {
        "schema": "e1c-strict-v5-advance-admission-v1",
        "ready": bool(admission.get("ready")),
        "stage": "admission_seal",
        "reason": admission.get("reason"),
        "provider_calls": 0,
        "live_model_run": False,
    }


def run(pull_timeout: int = 900, proxy: str | None = None) -> dict:
    with _proxy_environment(proxy):
        result = _run(pull_timeout, proxy)
    result["network_exit"] = {
        "explicit_proxy": bool(proxy),
        "proxy_value_recorded": False,
    }
    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--pull-timeout", type=int, default=900)
    parser.add_argument("--proxy")
    args = parser.parse_args()
    print(
        json.dumps(
            run(pull_timeout=args.pull_timeout, proxy=args.proxy),
            indent=2,
        )
    )
