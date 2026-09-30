# E1-C / WebCodex runner handoff — 2026-09-23

This records **the Windows local runner**, not the WebCodex cloud container. The pasted blocker list predates materialization; do not turn old claims into current results. Nothing here is a model repair result.

## Direct-call answer

WebCodex can inspect and test code only after the relevant changes are committed and pushed to the branch it checks out. It cannot inherit this machine's ignored `.codex/` cache, Docker daemon/images, source worktrees, parser checkout, or process environment. Cloud Docker availability and outbound network must be checked **inside that runner**. Do not claim that local PASS means cloud PASS.

Cloud Codex starts from a repository checkout in a new container. Its agent internet is off by default; configure network access if downloading public sources/images is required. Secrets entered as cloud environment **secrets are only available during setup**, not to the agent phase, so do not assume `DEEPSEEK_API_KEY` will be present for an agent-phase live run. Do not place the key in Git, task text, logs, or a publicly visible ordinary environment variable. Prefer a suitably secured local/self-hosted runner for paid calls if cloud secret delivery cannot satisfy that boundary. See [official Codex cloud environment documentation](https://learn.chatgpt.com/docs/environments/cloud-environment).

## Verified local state

| Check | Local result |
|---|---|
| Git / Docker CLI / Docker daemon | PASS; Docker `hello-world` and official SWE-bench container execution previously passed |
| Candidate selection | 30/30 public tasks; frozen manifest SHA-256 `16f86e20a296cc6e555038c0cbe336b6008d3b9252e8dc930a2d1c0a6cd9bca6` |
| Task files / exact source commits | 30/30 and 30/30 |
| Official image present | 23/30 original candidates (replacement images not yet pulled) |
| Base-Fail / Gold-Pass | 18/30 and 17/30 original candidates; **17/30 jointly admitted** under the separately frozen v2 source-identity protocol |
| Replacement pool | Deterministic next 10 metadata candidates selected; public task files **10/10** and exact source commits **10/10** verified; **0/10 admitted** |
| Hugging Face | NOT REQUIRED on this path; task blobs come from the pinned public GitHub tree |
| Public HTTPS reachability | Local `--network`: GitHub HTTP 200; Docker Hub auth endpoint HTTP 405; DeepSeek root HTTP 401. These prove reachability only, not image pull or authenticated inference |
| GitHub / Docker Hub network | Intermittent: first replacement source pass verified 8/10 and logged two GitHub:443 failures; one resume verified 10/10. Prior Docker Hub pull ended with auth-token `EOF`. Original candidate 24 Docker pull hit its 3600-second hard timeout, with no phase results; HTTPS reachability alone is not transfer reliability. |
| DeepSeek live request | NOT RUN; HTTP 401 without credentials is not a model/API-key PASS. Exact experiment command authorization still required by `AGENTS.md` |
| E1-C entry gate / E2 entry gate | BLOCKED / not yet assessed |

The historical first-pass Sphinx identity failure and Django pull `EOF` are preserved, but both were resolved by the separately frozen v2 admission protocol / resumed pull; see [v2 source-identity rule](./E1C_ADMISSION_V2_SOURCE_IDENTITY.md). Five later original candidates fail source identity (`astropy__astropy-13453`, `django__django-14787`, `scikit-learn__scikit-learn-25747`, `sympy__sympy-13031`, `django__django-15695`); `django__django-16454` fails an official cleanup step despite F2P/P2P passing. None are counted as admitted or as agent failures. Preserve those records. Replacements are ordered **after** the unchanged original 30, never swapped into its frozen identity.

Latest transport incident: `matplotlib__matplotlib-24026` timed out after 3600 seconds in `docker pull`; its 357-byte log remains at `.codex/e1c/admission_v2/matplotlib__matplotlib-24026.pull.log` (SHA-256 `9961d601c601d04d415fcdec3639907185a7b131a4ceafc76f37ad032f969dfc`). This is a registry transfer failure, **not** a Base-Fail/Gold-Pass or agent outcome. The batch was not retried automatically.

## Commands for the target runner

Use Python 3.12–3.14 and the committed lockfile. From the repository root:

```bash
uv sync --frozen --group dev
uv run --frozen python -X utf8 scripts/experiment_preflight.py
```

The default preflight is read-only and offline: it does not download, pull, access API keys, or call a model. Add `--network` for unauthenticated GitHub, Docker Hub token-endpoint, and DeepSeek **HTTPS reachability only**; it still does not call inference or prove an API key works. Exit `2`/`BLOCKED` is expected until all prerequisites and authorization are satisfied. It reports missing files/images/admission separately. The checked-in `data/e1c_candidate_manifest.json` preserves the selected cohort without reselection. To reconstruct ignored public task/source caches on the target runner **only if its network is allowed**:

```bash
uv run --frozen python -X utf8 -m evals.e1c_materialize --frozen
uv run --frozen python -X utf8 -m evals.e1c_materialize --source-only
```

Pin the official parser checkout; the integration test `tests/test_e1c_admission.py` also requires it:

```bash
git clone --filter=blob:none --sparse https://github.com/SWE-bench/SWE-bench.git .codex/e1c/swebench-harness
git -C .codex/e1c/swebench-harness checkout 02e7a74ffd0b707aab73d203fe87bdc7c76afc8e
git -C .codex/e1c/swebench-harness sparse-checkout set swebench
```

Re-run preflight. If the target has a usable Docker daemon and registry access, `uv run --frozen python -X utf8 -m evals.e1c_admission_batch` performs **zero-model** sequential pull + Base-Fail/Gold-Pass; it preserves existing phase artifacts and stops on a pull error. Do not delete failed artifacts just to obtain a green result.

For the deterministic replacement pool, first commit/transfer the new code and snapshot, then use `evals.e1c_cohort_prepare --allow-network --pool-size 40` to verify the frozen 30-prefix and select the next 10. `evals.e1c_materialize --replacement-pool` and `--replacement-pool --source-only` create **separate** replacement inventories; they do not rewrite the original candidate manifest. These ten currently have verified public files and source commits, but still need official images and Base-Fail/Gold-Pass before final-cohort freeze. After all original 30 have both phase records, run `uv run --frozen python -X utf8 -m evals.e1c_admission_batch --replacement-pool`; the flag refuses an incomplete original batch or unverified replacement inventories. Without that flag, the batch only processes the original 30. Both modes are zero-model.

The frozen 30-task selection is **candidate**, not yet an admitted live cohort. `evals/e1c_live_preflight.py` checks zero-call prompt reserve, and `evals/e1c_docker_grade.py` grades a patch; there is not yet a confirmed E1-C `n=30` real-model runner or exact authorized live command. Do not invent a command or treat a successful Python test as E1-C live. Resolve admission/protocol, freeze adapter and configuration, show the exact paid command for user confirmation, then run once with resumable artifacts and proceed to E2 Entry Gate only after audit.
The zero-call live preflight now reads original and replacement source inventories with duplicate-ID rejection; the original 30 remain 30/30 prompt-ready, but this is not admission. After the Docker timeout, a fresh read-only network check returned GitHub HTTP 200, Docker Hub auth HTTP 405, and unauthenticated DeepSeek root HTTP 401; these show endpoint reachability only, **not** that a large image transfer or paid inference will succeed.

## WebCodex handoff request

"Work from the pushed project branch. Run `uv run --frozen python -X utf8 scripts/experiment_preflight.py` in your own runner first and report each PASS/BLOCKED/NOT_TESTED item. Rehydrate the frozen original 30 with `evals.e1c_materialize --frozen`; use the separate replacement-pool commands only after verifying the original prefix. Never touch sealed E1-B TEST. Check Docker daemon, registry transfers, GitHub transfers, disk, and pinned parser inside your runner; local caches are not inherited. The v2 Sphinx case passed; do not repeat the stale v1 diagnosis. No DeepSeek request until I authorize the exact live command. Keep E1-C and E2 gates BLOCKED until actual admission evidence passes."
