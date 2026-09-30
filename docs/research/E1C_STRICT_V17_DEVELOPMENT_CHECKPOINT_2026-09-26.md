# E1-C Strict-v17 development checkpoint — 2026-09-26

Strict-v17 remains development-only and uses no strict-v15 sealed canary material. It tests a generic relation-object type corroboration rule: a relation witness may receive independent structural corroboration only when a type token in its issue-derived object has exactly one case-insensitive production definition and that definition agrees with the witness path.

Focused regression is 40/40 PASS and executable development coverage remains 6/6. Consensus remains 4/6, replay SHA-256 `564e68f30916b74e2a8597a8ae454aabb1f0f5372a1f3cbaea8016ce26abbf4d`.

`django__django-13233` does not satisfy the new rule: the allowed localization does not provide a unique same-path `Model` definition for the relation witness. The mechanism therefore correctly fails closed rather than inventing agreement. Together with strict-v16's path disagreement diagnostic on `django__django-15995`, this shows the two remaining gaps require better task-agnostic localization evidence rather than relaxed consensus semantics.

Strict-v17 is not frozen and no new independent canary is consumed. Official image, live, C5, DEV30, and Fresh30 gates remain closed. The next legal work is generic synthetic/exposed-development localization-quality or robustness work; freeze requires >4/6 consensus without forced path agreement.
