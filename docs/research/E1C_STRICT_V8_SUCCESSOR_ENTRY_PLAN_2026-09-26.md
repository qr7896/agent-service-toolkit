# E1-C Strict-v8 Successor Entry Plan — 2026-09-26

Strict-v7 is sealed at the zero-provider pre-image gate with 0/3 typed and 0/3 executable
candidate witness tasks on its independent canary. The next mechanism lineage must therefore
use strict-v7 only as development material and must not rerun the same canary as independent
evidence.

Strict-v8 starts with a selection boundary only. No v8 canary is selected in this step.
The boundary excludes the historical contamination ledger plus every strict-v6 and strict-v7
canary identity.

Development should focus on task-agnostic issue-to-observable translation rather than adding
per-task patterns. In particular, successor work should improve generic extraction of setup,
action, and observable state from public issue prose while keeping benchmark tests, Gold
patches, task IDs, grader paths, and external network out of repair-visible context.

Required order remains:

1. develop and test the successor only on synthetic fixtures and already exposed material;
2. freeze mechanism files/configuration;
3. only then select a new metadata-only three-task canary using the strict-v8 boundary;
4. require at least 2/3 executable candidates before any official image acquisition;
5. require isolated Base-Fail/Gold-Pass and at least 2/3 trusted reproducers before live;
6. only then can C5, DEV30, and eventually a brand-new Fresh30 be reconsidered.

No outcome-conditioned replacement or same-canary tuning is permitted.
