"""Fresh zero-only identity: unchanged CRLF exposure and canonical LF base blob."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from unittest.mock import patch

from evals import e1c_evaluation_2_exception_observer as base
from evals.e1c_blind_boundary import assert_agent_path
from evals.e1c_strict_v5_boundary import assert_production_relative_path

_build_driver = base.build_driver


def project_sites(workspace, sites):
    projected, proofs = [], []
    for site in sites:
        assert_production_relative_path(site["path"])
        path = assert_agent_path(workspace / site["path"], workspace=workspace)
        raw = path.read_bytes()
        original = hashlib.sha256(raw).hexdigest()
        if original != site["source_sha256"]:
            raise ValueError("exposed source changed before newline identity projection")
        effective = hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()
        projected.append({**site, "source_sha256": effective})
        proofs.append({"path": site["path"], "untouched_exposure_sha256": original,
                       "effective_LF_sha256": effective, "only_CRLF_projection": original != effective,
                       "container_bytes_and_git_blob_must_both_match": True})
    return projected, proofs


def build_driver(probe_sha, sites, nonce, hashes, keywords, base_commit):
    if not re.fullmatch(r"[0-9a-f]{40}", base_commit):
        raise ValueError("full canonical base identity required")
    source, marker = _build_driver(probe_sha, sites, nonce, hashes, keywords)
    source = source.replace("import hashlib, json, runpy, sys", "DATA['base_commit'] = " + repr(base_commit) + "\nimport hashlib, json, runpy, sys")
    source = source.replace("for site in DATA['sites']:\n", (
        "import subprocess\nfor site in DATA['sites']:\n"
        "    canonical = subprocess.check_output(['git', '-C', '/testbed', 'show', DATA['base_commit'] + ':' + site['path']])\n"
        "    if hashlib.sha256(canonical).hexdigest() != site['source_sha256']:\n"
        "        raise RuntimeError('canonical base blob differs from exposure LF projection')\n"
    ), 1)
    source = source.replace("path.removeprefix('/testbed/')", "(path[len('/testbed/'):] if path.startswith('/testbed/') else path)")
    source = source.replace("'e1c2-source-bound-exception-observation-v1'", "'e1c2-source-bound-exception-observation-v2'")
    source = source.replace("'exception_observer_module_sha256': DATA['module_sha256']", (
        "'exception_observer_module_sha256': DATA['module_sha256'], 'exception_observer_v2_sha256': "
        + repr(hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
        + ", 'canonical_git_and_effective_file_hash_required': True"
    ))
    return source, marker


def observe(candidate, probe, sites, image, base_commit, root, *, public_hashes, keywords, blocked_import_dir=None):
    def builder(probe_sha, selected, nonce, hashes, claims):
        return build_driver(probe_sha, selected, nonce, hashes, claims, base_commit)

    with patch.object(base, "build_driver", builder):
        return base.observe(candidate, probe, sites, image, base_commit, root, public_hashes=public_hashes,
                            keywords=keywords, blocked_import_dir=blocked_import_dir)
