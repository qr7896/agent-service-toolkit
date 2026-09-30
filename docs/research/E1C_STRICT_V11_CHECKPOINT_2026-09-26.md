# E1-C Strict-v11 checkpoint — 2026-09-26

Strict-v11 was developed only on synthetic and already exposed v6/v7 development material. It improved exposed replay from strict-v10's 3/6 executable tasks to 4/6, with 5/6 candidate tasks and 21/21 focused tests passing. Development replay SHA-256: `4a2e71e77e69347eb070a4447af4302e0d834fffca89a906bb00bb07bb85040e`.

Before canary selection, freeze-control validation caught and repaired two metadata/control-plane issues: the prereg initially omitted imported strict-v10 mechanism dependencies, and the selection boundary initially inherited exclusions only through strict-v9. No new canary had been selected at that point. The corrected freeze includes strict-v10 dependencies and all strict-v10 sealed identities in the exclusion set. Frozen mechanism SHA-256 is `9c29fbf092ccdc8807031514404d2869a521062d90e30d435d3a2dc107df6376`; prereg SHA-256 is `41f9fc9caf928a78452c7fd57ce848bd96bb829efc8212a22f64466fbc59e0b0`.

After freeze, metadata-only selection produced `sympy__sympy-12906`, `pylint-dev__pylint-5201`, and `django__django-10914`. All three exact statements and base sources were eventually materialized; one bounded statement fetch for django initially failed and then succeeded on the same frozen identity without replacement.

The frozen zero-provider assessment completed with 3/3 source-ready, 3/3 projection-supported, 0/3 candidate tasks, and 0/3 executable candidate tasks. Assessment SHA-256: `d2d0724c6270733671f095a05fd70e0dc2cae2b97e563fcd7fe05e687d87dab5`. Strict-v11 is therefore sealed as an independent negative canary. Official images, admission, live, C5, DEV30, and Fresh30 remain closed. These canary identities must not be reused and their outcomes must not be used to tune strict-v11.

The next legal step is a successor developed only on synthetic and previously exposed development material. Given repeated 0/3 untouched-canary transfer after local replay improvements, the successor should target a more general structural/behavioral projection mechanism rather than another canary-conditioned or narrow textual rule expansion.
