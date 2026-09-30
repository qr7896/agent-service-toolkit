# E1-C Strict-v7 Pre-live Seal — 2026-09-26

## Frozen independent canary

- `scikit-learn__scikit-learn-13313`
- `django__django-13233`
- `django__django-15995`

The mechanism was preregistered before metadata-only canary selection. Public problem
statements were opened only after identity freeze. Exact base source materialization and
strict projection/localization completed 3/3. No benchmark test assertion, Gold/test.patch,
provider call, or live model call was used.

## Result

- exact base source ready: 3/3
- projection/localization supported: 3/3
- typed candidate witness tasks: 0/3
- executable candidate witness tasks: 0/3
- preregistered executable threshold: at least 2/3
- candidate gate: FAIL

Strict-v7 therefore stops before official image acquisition. The large SWE-bench images are
not pulled, Base-Fail/Gold-Pass is not run, and no live command is opened.

Downstream state:

- official image acquisition: CLOSED
- official Base-Fail / Gold-Pass admission: CLOSED
- live canary: CLOSED
- C5: CLOSED
- DEV30 strict-blind live: CLOSED
- Fresh30: CLOSED

This is a mechanism-coverage failure at the zero-provider pre-image gate, not an
infrastructure failure.

## Successor rule

The three strict-v7 statements are now development-only material. They may inform generic
mechanism research, but strict-v7 must not be tuned and rerun on the same canary as
independent evidence. Any successor must be frozen first and then tested on another new
metadata-only independent canary excluding all prior touched identities.

Do not outcome-condition replacements, loosen the candidate threshold, inspect grader
assertions, raise image budgets to bypass this gate, or aggregate best-of results across
versions.
