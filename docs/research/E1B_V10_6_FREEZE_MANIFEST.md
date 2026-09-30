# E1-B v10.6 Freeze Manifest / Reproducibility Bundle

Date: 2026-09-20  
Schema: `e1b-freeze-manifest-v1`  
Status: offline protocol freeze artifact.

v10.6 adds no verifier or retrieval capability. It freezes the v10-v10.5 control-plane implementation into a deterministic content manifest before any future learned-policy or confirmatory evaluation work.

The stable content manifest hashes required implementation and specification files, component schema versions, action-set manifest, protocol-invariant report/fixture hashes, and frozen bounds. Environment metadata is deliberately separate because Python/platform fields can vary across machines without changing protocol content.

The verifier recomputes the bundle and fails closed for missing required files, file hash mismatch, bundle schema mismatch, component schema drift, bound/config drift, action-set drift, invariant-report drift, or final content-manifest mismatch.

Excluded from the bundle and from tuning evidence are the contaminated original six TEST fixtures/outcomes, replacement held-out content/outcomes, repeated DEV outcomes, and private SERBench/Test500 material.

Environment metadata is restricted to Python version/implementation, OS/system, machine architecture, byte order, and uv.lock SHA256 when present. No environment-variable values, API keys, tokens, passwords, or secrets are recorded.

This artifact supports protocol freeze and audit reproducibility only. A valid manifest does not establish patch correctness, repair success, causal benefit, model efficacy, or benchmark generalization.
