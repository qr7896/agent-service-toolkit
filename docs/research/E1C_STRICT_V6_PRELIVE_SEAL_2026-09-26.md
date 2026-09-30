# E1-C Strict-v6 Pre-live Seal — 2026-09-26

## Decision

Strict-v6 is sealed before image acquisition and before any model/provider live run.

The frozen independent canary is:

- django__django-15569
- django__django-11734
- sphinx-doc__sphinx-8638

Post-freeze zero-provider materialization completed for all three tasks:

- public problem statement: 3/3
- exact base source: 3/3
- strict issue projection/localization: 3/3
- provider/model calls: 0
- repair-visible tests/Gold files intentionally read: 0

The preregistered candidate-reproducer threshold is at least 2/3. The observed strict-v6
candidate witness result is **0/3**; every row is no_reproducer.

Therefore:

- candidate-reproducer gate: **FAIL**
- official image pull: **CLOSED**
- Base-Fail / Gold-Pass admission: **CLOSED**
- live canary: **CLOSED**
- C5: **CLOSED**
- DEV30 strict-blind live: **CLOSED**
- Fresh30: **CLOSED**

The three large SWE-bench images are intentionally not downloaded because the earlier
zero-provider gate already fails. This is a protocol-preserving early stop, not an
infrastructure failure.

## Interpretation

The strict-v6 witness grammar remains too narrow for realistic issue descriptions. It can
only freeze witnesses from a small class of explicit, safe, literal-call behavioral
relations. The frozen canary contains three broader patterns that are not representable by
that grammar:

1. state/cache invalidation side effect;
2. ORM/subquery behavior whose failure is expressed through a multi-step query construction;
3. rendered documentation/reference behavior requiring a build-level observable.

These observations may be used for mechanism development only. They must not be used as
independent evidence for a successor mechanism.

## Required next lineage

1. Keep strict-v6 frozen and sealed. Do not redraw or replace any v6 canary task.
2. Develop a successor reproducer-focused mechanism using only already-exposed development
   material and generic synthetic/unit fixtures.
3. Freeze the successor mechanism identity before selecting or opening a new canary.
4. Select a **new independent metadata-only canary**, excluding all prior v5/v6 and other
   touched identities.
5. Run the same zero-provider post-freeze candidate gate first.
6. Only if at least 2/3 candidate executable witnesses exist may image acquisition and
   official Base-Fail/Gold-Pass admission proceed.
7. Only after admission is complete may an exact live command be frozen and separately
   authorized.

No outcome-conditioned replacement, same-canary tuning, test-assertion leakage, image-budget
relaxation, or cross-version best-of aggregation is permitted.
