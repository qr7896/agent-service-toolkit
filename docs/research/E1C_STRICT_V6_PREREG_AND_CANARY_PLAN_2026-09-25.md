# E1-C Strict-v6 Reproducer Preregistration and Canary Plan — 2026-09-25

## Why v6 exists

Strict-v5 reached a decisive pre-live stop on its frozen independent canary. The three frozen tasks passed identity/projection/source/leakage checks, but the frozen v5 repair-visible runtime produced no_reproducer for **3/3** tasks. The playbook requires at least **2/3 trusted pre-patch reproducers** before any paired live canary.

Therefore v5 is sealed without a live model run. The v5 canary cannot be reused after mechanism tuning and no outcome-conditioned replacement is allowed.

## Frozen v5 decision

- provider/model calls: 0
- live model run: false
- frozen canary size: 3
- v5 pre-patch no_reproducer: 3/3
- trusted reproducer: 0/3
- minimum required: 2/3
- live allowed: false
- same-canary tuning/retest: forbidden
- C5/DEV30: closed
- Fresh30: closed

The image/grader network failures observed later are secondary infrastructure failures; they do not change the earlier decisive reproducer-admission failure.

## Strict-v6 mechanism

Strict-v6 keeps the strict-v5 assertion-blind boundary and production-only localization but expands the generic natural-language behavioral witness grammar. It recognizes only safe, task-agnostic relations such as function returns expected literal, returns X instead of expected Y, equality expressions, contains/not-contains, expected exception type, and actual exception type instead of expected type.

Only simple module-level calls with literal arguments are accepted. Dynamic calls, methods/attribute calls, unsupported prose, test-derived assertions and evaluator artifacts fail closed to no_reproducer. Witness execution remains isolated with Docker --network none; a witness is not trusted merely because it can be generated.

## Mechanism freeze

The mechanism was preregistered before selecting a v6 canary in data/e1c_strict_v6_prereg.json.

- mechanism SHA: a01920faae6e92a9b0efc0e5ca4cb14b2e769c9c0e0471b672ba251c8238baa2
- prereg SHA: f0636f02d031d8bd27705ded26340a85c63e5ef5534dd409c3f736d80dcc6aef
- selection salt: e1c-strict-v6-independent-canary
- canary size: 3
- trusted reproducer minimum: 2
- live before admission: forbidden

Synthetic/boundary tests for the v6 mechanism are green; these tests are engineering evidence only and are not repair-efficacy evidence.

## Independent identity policy

The contamination union was expanded from 232 to **244 identities** before v6 canary selection. It now includes the 12 metadata rows touched during v5 candidate selection, including the final three v5 canary tasks.

A v6 canary must be selected from official SWE-bench task metadata after applying this 244-identity denylist. Identity selection must happen before any statement materialization.

Because GitHub API tree access is rate-limited, the allowed fallback is: download the fixed-revision SWE-bench/SWE-bench source archive; inspect ZIP filenames only; derive task identities from swebench/resources/swebench-og/*/*/environment.yml; never extract those resource files for candidate selection; rank untouched identities using the frozen v6 salt; fetch only selected candidates' task.yaml from SWE-bench/swe-bench-tasks at fixed revision 3d07b464b7b311a0cbfb5ed5b2d8a3b96f84a33d; then freeze exactly three identities before reading statements.

The fixed inventory archive inspection produced 500 identity names and no benchmark task content was opened.

## Next gate

After the v6 metadata-only freeze: certify the three-task freeze; materialize only those three public statements; run strict projection and v6 production-only localization; generate v6 witness plans. If fewer than 2/3 have candidate executable witnesses, seal v6 pre-live immediately. Otherwise continue source/image/Base-Fail/Gold-Pass and Docker-isolated witness execution. Only if admission reaches at least 2/3 trusted reproducers with every safety/identity gate clean may a live command be frozen for explicit authorization.

No live command is authorized by this document.
