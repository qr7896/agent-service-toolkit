# E1-C Source-Contract Checkpoint — 2026-09-27

- Protocol unchanged; provider/model calls: **0**.
- Frozen inventory revision and three primary task blobs: materialized and identity-verified.
- Reserve task content: **unread**.
- Official admission payload: materialized 3/3 from cached official SWE-bench test parquet (SHA256 d4f5a245c75319fa8240c540674958c4d491e82edf274b144d43836bdcbc4567), base commits matched.
- Evaluator semantics: LF-only eval.official.sh generated using frozen record_test_exit_code behavior.
- SymPy canonical image: complete; digest sha256:e2c2345aaaf6f01d6331eab8e9c3425dc314c6a544eb6907c35b31f44f9c8108; exact base and clean worktree verified.
- SymPy Base-Fail: durable run **in progress** (detached_52540dcc68373c25357fbe816780ff51280fb015ef8ce9a3850d63990c45da54), --network none; do not duplicate.
- Django canonical image pull: **in progress** (detached_d8e8336af69bc27acc02958c10bcd04586956f1d8ce9488f55bdf2586469d87d).
- Matplotlib canonical image pull: **in progress** (detached_e73e97f1d1a17ebb809f28aba8db7033552732cf5d6df213111688c740c0d2d9).
- C5 / DEV30 / Fresh30 / paired live: **CLOSED**.

## Next gate

Resume existing durable jobs only. Classify SymPy Base with the frozen parser after terminal. As Django/Matplotlib pulls finish, verify immutable image/base identity and run their Base-Fail. Gold-Pass is allowed only after clean Base admission. Continue through deterministic issue projection and frozen source-contract trusted-reproducer preflight. Reopen paired live only if the preregistered >=2/3 trusted-prepatch-reproducer gate passes.

## Continuation update

- Workspace hygiene reviewed conservatively; no destructive repository cleanup.
- SymPy first detached Base output was rejected because of a literal exit-code echo generator defect.
- Corrected evaluator-faithful exit-code echo only; protocol/test command unchanged.
- SymPy clean Base-Fail: F2P 0/1, P2P 26/0; UTF-8 raw SHA256 `a42f3a4d6e869f85fd099f830a38ec9c939d53ade3eb5efc55b0c51957c7005d`.
- Preserved pre-normalization UTF-16LE transport copy SHA256 `88564c902d2ea20d4c09109cec9e8986e069519a0ee9cde7a982ea9f3ee18944`.
- SymPy Gold-Pass: F2P 1/0, P2P 26/0, resolved=true; raw SHA256 `c082c1153377b241d873f1c7f2678ee30e8f6a17fc67156e634effec09bd47ac`.
- Django/Matplotlib canonical pulls remain running; no duplicate pulls.
- Provider/model calls remain **0**; C5 / DEV30 / Fresh30 / paired live remain **CLOSED**.

## Independent canary gate result

- Django canonical image: `sha256:a4ddc630adffc7e64d7f090bb3c486d4dac0fc2426ff5b5f73c2f6961a775c7a`; frozen base reset/clean verified.
- Django clean Base-Fail then Gold-Pass completed. Base raw SHA256 `85eef301b15be1479ca702bf2b385ee8f16fd661cec83eea1b6ce41c9fd8caf0`; Gold raw SHA256 `71d24ebe2d3dc9bea32416b24b3263a8c4db4eaa1af2fad7877ea9beeed959ca`.
- SymPy source-contract preflight: 0 candidates / 0 executable.
- Django source-contract preflight: 0 candidates / 0 executable.
- Therefore the preregistered `>=2/3` trusted-prepatch threshold is unreachable even if Matplotlib succeeds: maximum possible final count is `1/3`. This is a sealed negative gate result, not an infrastructure blocker.
- Matplotlib pull/admission may finish for audit completeness, but cannot reopen paired live / C5 / DEV30 / Fresh30 for this frozen mechanism.
- Provider/model calls remain **0**; reserves remain unread.
