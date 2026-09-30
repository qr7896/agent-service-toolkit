# E1-C Strict-v8 checkpoint — 2026-09-26

Strict-v8 successor mechanism is now frozen before independent canary selection. Focused zero-provider regression passed 12/12. The frozen mechanism SHA-256 is `129201f0512359b53a25d25f07b4eae00004947bb74253b5185792787bc041b9`; prereg SHA-256 is `b30456c21662b0fb937ef32ffe52a31042c2272edb226fa927f347b465400740`.

The new metadata-only independent canary was selected only after freeze: `django__django-14071`, `scikit-learn__scikit-learn-13536`, and `scikit-learn__scikit-learn-13641`. Its manifest SHA-256 is `0d06deb0225f3b34d81ace735718899d1109058c2cdde8485905c07f2a4f120d`. No public statement, benchmark assertion, Gold patch, provider call, or live model result influenced selection.

The earlier transport/materialization blocker was resolved without provider calls. Exact public statements and exact frozen base-source archives were materialized for all three identities. The zero-provider post-freeze assessment completed with `source_ready_count=3`, `projection_supported_count=3`, `candidate_task_count=0`, and `executable_candidate_task_count=0`. Its summary SHA-256 is `54514349049da98077256462d534f30666155473c39f908321d64c75a1dd5629`.

Strict-v8 therefore fails its frozen independent candidate gate: 0/3 executable tasks versus the preregistered minimum of 2/3. This is an independent negative canary result, not a transport failure. Official image acquisition, official Base-Fail/Gold-Pass, live canary, C5, DEV30, and Fresh30 remain closed; the three official images were confirmed absent locally and were not pulled.

Strict-v8 is now sealed against canary-conditioned tuning or canary reuse. The next legal gate is a successor mechanism iteration developed only on exposed development material. That successor must be frozen before selecting another untouched metadata-only canary, and only a new independent canary reaching at least 2/3 executable candidate tasks may reopen official image acquisition.
