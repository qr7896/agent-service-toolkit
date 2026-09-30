# E1-C Strict-v15 development checkpoint — 2026-09-26

Strict-v14 was first fully sealed at 1/3 independent executable using resumable aggregation; its bookkeeping blocker is closed. Strict-v15 then began without using any strict-v14 canary statement, source, or outcome for tuning.

V15 introduces an evidence-family consensus diagnostic: structural, semantic-localization, and behavioral witnesses are grouped independently, and agreement on the same production path is recorded. The inherited executable behavior remains unchanged during development so the diagnostic can be evaluated without silently weakening prior semantics.

The successor added a task-agnostic unique-localized-symbol corroboration signal with duplicate-symbol and path-disagreement fail-closed checks. Focused regression is 31/31 PASS. Exposed development remains 6/6 executable and consensus improved from 2/6 to 4/6, replay SHA-256 `fbd5e3183e617cca9bd84a42a23808cb24d7c34a476ab72a8229c351b6550127`.

After that development gate passed, strict-v15 was frozen before canary selection. Mechanism SHA-256 is `29a12081b5ce44a3fdb021aaad503530d2087b5d9139caa8e902c3c26085626d`; prereg SHA-256 is `3154d3f29ba58041c87e1a32d1aa3848f3639dd318a11169472f18129e1f87af`. The metadata-only untouched canary is `django__django-13512`, `astropy__astropy-7671`, `pytest-dev__pytest-5631`, frozen before statement inspection.

All three statements and exact base sources materialized successfully. Frozen assessment produced 0 executable for django, 2 executable with one consensus path for astropy, and 0 executable for pytest. Aggregate independent result is 1/3 executable, below the preregistered >=2/3 candidate gate; aggregate SHA-256 `00fa45160f510b2786fc3653c0338eee81505142fc80bad844e6078c01905ff8`.

Strict-v15 is therefore sealed as an independent negative canary with partial transfer, not an infrastructure failure. Official images, Base-Fail/Gold-Pass, live, C5, DEV30, and Fresh30 remain closed. Strict-v15 canary content and outcomes are forbidden for successor tuning.
