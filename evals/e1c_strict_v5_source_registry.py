"""Discover metadata-only sources without reading benchmark task content."""

from __future__ import annotations

import hashlib
import json
import socket
import urllib.request
from pathlib import Path

from evals.e1c_admission import ROOT

OUT = ROOT / "data" / "e1c_strict_v5_metadata_source_registry.json"
GITHUB_TREE = "https://api.github.com/repos/SWE-bench/SWE-bench/git/trees/main?recursive=1"
GITHUB_BRANCH = "https://api.github.com/repos/SWE-bench/SWE-bench/branches/main"


def _github_json(url: str) -> object:
    request = urllib.request.Request(url, headers={"User-Agent": "e1c-strict-v5-source-discovery"})
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)


def _dns(host: str) -> dict:
    try:
        addresses = sorted({
            item[4][0]
            for item in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
        })
        return {"ready": True, "addresses": addresses[:4]}
    except OSError as exc:
        return {"ready": False, "error": f"{type(exc).__name__}: {exc}"}


def discover() -> dict:
    sources = []
    try:
        branch = _github_json(GITHUB_BRANCH)
        tree = _github_json(GITHUB_TREE)
        revision = branch["commit"]["sha"]
        paths = [
            item["path"]
            for item in tree.get("tree", [])
            if item.get("type") == "blob"
            and item["path"].startswith("swebench/resources/swebench-og/")
            and item["path"].endswith("/environment.yml")
        ]
        identities = sorted({
            "/".join(path.split("/")[3:5])
            for path in paths
            if len(path.split("/")) >= 6
        })
        sources.append({
            "name": "official_swebench_github_resource_tree",
            "url": GITHUB_TREE,
            "source_revision": revision,
            "task_content_read": False,
            "available_fields": ["instance_id", "repo"],
            "required_fields": ["instance_id", "repo", "base_commit", "image"],
            "identity_count": len(identities),
            "identity_sha256": hashlib.sha256(
                json.dumps(identities, separators=(",", ":")).encode()
            ).hexdigest(),
            "status": "safe_but_incomplete",
            "reason": "resource tree exposes instance/repo identities but not base_commit and image",
        })
    except Exception as exc:
        sources.append({
            "name": "official_swebench_github_resource_tree",
            "url": GITHUB_TREE,
            "task_content_read": False,
            "status": "unavailable",
            "reason": f"{type(exc).__name__}: {exc}",
        })

    hf_dns = _dns("huggingface.co")
    sources.append({
        "name": "huggingface_dataset_host",
        "url": "https://huggingface.co/datasets/princeton-nlp/SWE-bench",
        "task_content_read": False,
        "status": "reachable_but_forbidden_row_api" if hf_dns["ready"] else "unavailable",
        "reason": (
            "dataset row/filter APIs expose complete benchmark rows, so they are forbidden before identity freeze"
            if hf_dns["ready"]
            else hf_dns["error"]
        ),
        "dns": hf_dns,
    })
    docker_dns = _dns("registry-1.docker.io")
    sources.append({
        "name": "docker_registry_host",
        "url": "https://registry-1.docker.io",
        "task_content_read": False,
        "status": "reachable_identity_component_only" if docker_dns["ready"] else "unavailable",
        "reason": (
            "registry reachability can support later image identity checks but does not provide base_commit metadata"
            if docker_dns["ready"]
            else docker_dns["error"]
        ),
        "dns": docker_dns,
    })
    ready = any(source.get("status") == "admissible_metadata_only" for source in sources)
    return {
        "schema": "e1c-strict-v5-metadata-source-registry-v1",
        "ready": ready,
        "reason": "admissible_metadata_source_found" if ready else "no_complete_metadata_only_source_found",
        "provider_calls": 0,
        "task_content_inspected": False,
        "new_task_tree_touched": False,
        "sources": sources,
    }


def write(output: Path = OUT) -> dict:
    value = discover()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return value


if __name__ == "__main__":
    print(json.dumps(write(), ensure_ascii=False, indent=2))
