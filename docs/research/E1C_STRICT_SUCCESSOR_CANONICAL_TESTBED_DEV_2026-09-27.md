# E1-C strict successor: Canonical Testbed Interpreter (CTI)

Status: DEVELOPMENT PREREGISTRATION; ZERO-PROVIDER; NOT FROZEN FOR CANARY.

## Preserved evidence

Setup-Closure is sealed negative. EFIL is sealed negative after its one frozen SymPy execution used the image default root interpreter and produced an environment ImportError rather than the public semantic TypeError. The EFIL result is not retried under EFIL.

Zero-provider environment diagnostics on two already-cached official old-DEV images from different repositories show the same structure: image default Python is under /opt/miniconda3/bin, while /opt/miniconda3/envs/testbed/bin/python exists as the benchmark testbed interpreter.

## Single generic mechanism

CTI changes only interpreter bootstrap. For every supported official image, the reproducer command uses the fixed path /opt/miniconda3/envs/testbed/bin/python. It never selects an interpreter based on task id, import failure text, package name, Gold, grader, or test result. If that fixed executable is absent, the environment fails closed.

EFIL contract extraction, import lifting, exact-base identity, immutable image identity, network none, timeout, and exact public exception matching remain unchanged.

## Predeclared old-DEV development gate

Before any canary:

- provider/model calls = 0;
- old DEV denominator = 30;
- task-specific rules = 0;
- leakage forbidden hits = 0;
- focused tests pass;
- EFIL compile-ready coverage remains at least 2 candidates across at least 2 repos;
- at least 2 already-known official old-DEV images across at least 2 repos expose the fixed canonical testbed interpreter;
- all such environment probes succeed without network;
- at least 1 bounded exact-base, digest-pinned, network-disabled CTI preflight yields trusted_expected_failure_reproduced;
- the sealed EFIL gate remains negative and unmodified.

The execution candidate remains the first EFIL compile-ready candidate in the previously frozen DEV30 order. A new CTI input must be frozen before execution. Exactly one CTI scenario execution is allowed for that input, with no automatic retry.

Gate failure seals CTI negative. Gate success permits freezing CTI code, gate, analysis, environment probe, and preflight hashes; only after that freeze may a new independent non-overlapping canary be selected under the existing PLAYBOOK.
