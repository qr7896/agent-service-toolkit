# E1-C Strict-v10 development checkpoint — 2026-09-26

Strict-v9 remains sealed as an independent negative canary. Its three sealed canary statements and sources were not used to tune strict-v10.

Strict-v10 adds task-agnostic observable patterns for inline failures, relation clauses, negative-link behavior, and permissive/non-failure behavior. The focused synthetic/backward regression is 19/19 PASS with zero provider calls.

After task-agnostic structural binding was added, the exposed v6/v7 development replay improved to 4/6 candidate tasks and 3/6 executable-candidate tasks, SHA-256 `972bb43b353d6d2d99f5e16332dd087814489644e9a7aec8573e1d29d5b1358b`. This materially exceeds strict-v9's 2/6 executable development coverage while focused regression remains 19/19 PASS.

Strict-v10 was then frozen before any new canary statement was opened. Mechanism SHA-256 is `e77f16030df7d992fa9ec1af981dd55a67be23784e6a2ef2392bf11e27b639f4`; prereg SHA-256 is `d85267fa0ee0e42bbb437c7fea4a7b833fccc0cbb10dc95807509b284a711718`. The metadata-only independent canary selected after freeze is `pydata__xarray-5731`, `django__django-16411`, and `django__django-12912`; manifest file SHA-256 is `c220589d8948a423795004e1746f8ec4702b164aff4a3ad76e2c805ffff8b6fb`.

The first monolithic post-freeze materialization attempt timed out at 120 seconds before any statement/source artifact was emitted. This is a transport blocker, not a candidate-gate result. Do not repeat development, freeze, or selection. Next, materialize these same three frozen identities one at a time with bounded transport, then run the frozen zero-provider candidate assessment. Official image acquisition remains closed until at least 2/3 executable candidate tasks are measured with all three source/projection rows ready.

The transport blocker was subsequently resolved by bounded per-task materialization. All three frozen identities reached exact statement + exact base source, and the frozen zero-provider assessment completed with 3/3 source-ready, 3/3 projection-supported, 0/3 candidate tasks, and 0/3 executable candidate tasks. Assessment SHA-256 is `9308975aae252b0bbba85a81099a1e78afcb1a00f0fb112172488ef9e2f69a7f`.

Strict-v10 therefore fails the preregistered candidate gate and is sealed as an independent negative canary. Official images, Base-Fail/Gold-Pass, live execution, C5, DEV30, and Fresh30 remain closed. The three strict-v10 canary identities must not be reused, and strict-v10 must not be tuned against their outcomes. The next legal gate is successor development on synthetic and already exposed development material only, followed by freeze before another untouched metadata-only canary selection.
