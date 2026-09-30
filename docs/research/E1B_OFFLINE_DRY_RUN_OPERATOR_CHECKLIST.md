# E1-B Offline Dry-Run Operator Checklist

This checklist intentionally stops before any real provider/model command.

## Safe commands already present

1. Verify v10.6 freeze/reproducibility state:
   `\.venv\Scripts\python.exe -m evals.e1b_freeze_manifest_v10_6_preflight`
2. Exercise the v10.7 admission gate with its built-in synthetic metadata only:
   `\.venv\Scripts\python.exe -m evals.e1b_experiment_admission_v10_7_preflight`
3. Exercise v10.8 package creation/materialization in a temporary directory using the built-in synthetic configuration:
   `\.venv\Scripts\python.exe -m evals.e1b_experiment_package_v10_8_preflight`

After the independent curator supplies real content-neutral metadata and the exact experiment config is filled, run the zero-provider operator path in a fresh directory:

`\.venv\Scripts\python.exe -m evals.e1b_replacement_preflight --metadata <metadata.json> --config <config.json> --output-dir <fresh-dry-run-dir>`

This command performs admission and dry-run materialization only. It has no provider client and cannot start the experiment.

These modules are preflight entry points; `e1b_experiment_package_v10_8.py` itself exposes library functions and has no CLI main entry point.

## Before a real cohort can be admitted

- Receive only the completed content-neutral metadata object described by `templates/e1b_replacement_cohort_metadata.template.json`.
- Verify the independent curation/attestation process; do not open the hidden manifest/task fixtures.
- Freeze the exact identifiers and ceilings required by v10.7.
- Produce a fresh v10.8 dry-run package and verify its manifest chain/artifact contract while provider calls remain zero.
- Confirm the five artifacts include empty `task_outcomes.jsonl`, and freeze one `experiment_arm_id` per immutable package.
- Fill and freeze `templates/E1B_ONE_SHOT_PREREGISTRATION_TEMPLATE.md`.

## HARD STOP

Do not proceed to a command that invokes a provider/model or executes replacement held-out tasks. The exact live command must be separately shown to and explicitly authorized by the user. `ADMIT_OFFLINE_READY`, a valid dry-run package, or a generic request to continue does not cross this boundary.
