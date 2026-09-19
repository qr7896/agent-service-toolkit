# V2 Reproducibility

Date: 2026-09-19

## Fixed dependencies

- Project working tree: `project20260827`
- Python: repository `.venv`
- SERBench URL: `https://github.com/LordTARN1SHED/SERBench.git`
- SERBench commit: `8c27a88e48dcbcd4a5745573c95937a4740f4406`
- External checkout: `.external/SERBench` (git-ignored; do not vendor)
- Frozen method: `v2_candidate_compat_v2_4_1`, ranking budget k=8
- Frozen manifest: `evals/results/serbench_v2_4_1_frozen_manifest.json`

Set `PYTHONPATH=src` before commands. Install the official SDK from the external checkout with `.venv\Scripts\python.exe -m pip install -e .external\SERBench`.

## Example integration

```powershell
.venv\Scripts\python.exe -m evals.serbench_inference_audit --split example --data-dir .external/SERBench/data --output evals/results/serbench_example_inference_audit.json
.venv\Scripts\python.exe -m evals.serbench_candidate_ranker --split example --data-dir .external/SERBench/data --output evals/results/serbench_example_lexical_predictions.jsonl -k 8
.venv\Scripts\python.exe -m serbench validate --split example --data-dir .external/SERBench/data --predictions evals/results/serbench_example_lexical_predictions.jsonl
.venv\Scripts\python.exe -m serbench score --split example --data-dir .external/SERBench/data --predictions evals/results/serbench_example_lexical_predictions.jsonl --k 5 8 --output evals/results/serbench_example_lexical_scores
```

## Cal500 frozen method

```powershell
.venv\Scripts\python.exe -m evals.serbench_v2_compatible --split cal500 --data-dir .external/SERBench/data --method v2_candidate_compat_v2_4_1 --output evals/results/serbench_cal500_v2_compat_predictions.jsonl --diagnostics evals/results/serbench_cal500_v2_compat_diagnostics.json -k 8
.venv\Scripts\python.exe -m serbench validate --split cal500 --data-dir .external/SERBench/data --predictions evals/results/serbench_cal500_v2_compat_predictions.jsonl
.venv\Scripts\python.exe -m serbench score --split cal500 --data-dir .external/SERBench/data --predictions evals/results/serbench_cal500_v2_compat_predictions.jsonl --k 5 8 --output evals/results/serbench_cal500_v2_compat_scores
.venv\Scripts\python.exe -m evals.serbench_method_freeze --prediction evals/results/serbench_cal500_v2_compat_predictions.jsonl --report evals/results/serbench_cal500_v2_compat_scores/summary.json --config evals/config/serbench_v2_4_1.json --method v2_candidate_compat_v2_4_1 --split cal500 --upstream-ref 8c27a88e48dcbcd4a5745573c95937a4740f4406 --output evals/results/serbench_v2_4_1_frozen_manifest.json
```

## Test500 boundary

`evals/results/serbench_test500_v2_compat_predictions.jsonl` is prediction-ready and officially valid. Its SHA-256 is `fafbcba882b947373f64ccf69c32fd806f4eee0d942f6d2be6ad4ab658508ed9`. Do not tune on Test500 or request private certificates. A human must submit this single frozen artifact through the upstream private evaluation queue using the required GitHub authorization; record the returned evaluation result without resubmitting variants.

## Integrity boundaries

- Model API calls for this external V2 continuation: 0.
- Internal E1-B sealed TEST opened/called: 0/0.
- Certificates/Gold are never passed into ranking or controller state.
- Upstream loader/scorer remain authoritative; local preflight is not a replacement.
