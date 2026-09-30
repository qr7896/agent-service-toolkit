# E1-C Strict-v20 frozen checkpoint — 2026-09-26

Strict-v20 is the first successor after V15 to cross the development gate: exposed DEV reached **5/6 consensus** with zero provider calls. The new success is `django__django-13233`, where an issue-noun-bounded complete-source AST assignment (`Field.self.model = cls`) provides structural evidence and an explicit issue ownership clause (`field belongs to concrete model`) provides independent semantic-localization evidence on the same production path. Focused predecessor regression is **54 passed**.

Mechanism SHA-256: `5afa2bf37fd4155a8415edf68dbbff7ca36a45fc8321d99071ffa81c5efc3383`. Development replay SHA-256: `2161e5377544ce9019549b5ddbbe6203758de2e3680814dff37c77e902b7893f`. Current prereg SHA-256 after contamination-safe boundary repair: `c3c9022e310066ed318489e8929e3f0fd70d91cdbe89d4a054197c991cf7f780`.

Before statement materialization, a contamination audit caught an incomplete exclusion boundary. The initially reserved metadata identities (`django__django-15563`, `scikit-learn__scikit-learn-25747`, `django__django-16454`) all occur in the pre-existing strict-v5 contamination ledger. That reserve is invalidated and its stale manifest was deleted. No task statement/source for those identities was materialized by V20.

The repaired boundary includes all 244 ledger identities plus prior strict canaries, yielding 256 effective exclusions. The existing 30-row metadata extension contains **0 clean identities** outside this set, so independent canary selection is blocked by metadata-pool exhaustion rather than mechanism quality or infrastructure.

V20 remains frozen. The next legal gate is metadata-only pool expansion from the frozen official task inventory, with no statement/outcome inspection, until at least three identities survive the 256-identity exclusion set. Only then may the deterministic V20 reserve run. Official image acquisition, live paired canary, C5, DEV30, and Fresh30 remain closed.

## Post-freeze continuation

The frozen Git tree contains 2,519 task identities at revision `3d07b464b7b311a0cbfb5ed5b2d8a3b96f84a33d`; subtracting 256 exclusions leaves **2,263 clean metadata-only identities**. Pool SHA-256 is `134e712449562925cd037daa7bf10f086c7f60c6fd427ae947613523a5d9c164`.

The frozen salt reserved `sympy__sympy-21586`, `pvlib__pvlib-python-1026`, and `pydata__xarray-2905` before statement materialization. Exact metadata, statements, and base sources were subsequently materialized.

Post-freeze candidate assessment is **PASS**: source/projection 3/3, executable candidate tasks 2/3, consensus tasks 1/3. SymPy has 0 executable candidates; pvlib has 4 executable and 1 consensus path; xarray has 3 executable and 0 consensus paths. Assessment SHA-256: `f7c69eb58c20779cafd29af37b176e8f7821d4f6568f3932b87576e2c7dc812a`. The preregistered `>=2/3 executable` rule therefore opens official image acquisition.

Docker Server 29.4.0 is reachable. The first official SymPy image pull downloaded multiple layers but did not finish committing within the 120-second Runner window; subsequent inspection found no completed image yet. This is **transport/acquisition incomplete**, not an experimental failure. Base-Fail/Gold-Pass is blocked until image acquisition completes; live, C5, DEV30, and Fresh30 remain closed.

### Docker storage blocker discovered on resume

On the next continuation, resuming the same frozen SymPy image failed at containerd metadata write with `meta.db: read-only file system`. `docker image ls` then exposed a content-store blob `input/output error`. A non-destructive `docker desktop restart` timed out; `wsl --shutdown` followed by starting `Docker Desktop.exe` also failed to restore the engine within 60 seconds, and the `docker-desktop` WSL distribution is currently stopped. No prune, factory reset, VHDX deletion, cache deletion, or experimental artifact mutation was performed.

This supersedes the earlier transport-only diagnosis: official image acquisition remains protocol-authorized but is now **infrastructure-blocked by Docker Desktop storage/backend I/O**. The next gate is to restore a writable Docker Desktop/containerd backend, verify `docker image ls` without I/O errors, and resume the exact same three frozen image pulls. Base-Fail/Gold-Pass, trusted-reproducer admission, live paired canary, C5, DEV30, and Fresh30 remain closed.

### Partial recovery and reproducible large-write failure

A later non-destructive recovery (`wsl --shutdown`, normal Docker Desktop start, then wait for engine readiness) restored Engine 29.4.0. Both `docker image ls` and a `hello-world` pull/inspect succeeded, proving that the content store was initially writable again. The frozen SymPy image then completed successfully with digest `sha256:453e66e1e49ac05efd634d3fd83c84093ed71da8722d41a7645b05582dd52599`.

The next frozen pvlib pull downloaded many layers but failed during content ingest with `write .../io.containerd.content.v1.content/ingest/.../data: read-only file system`. The failure therefore recurs under sustained/larger writes. Current official-image progress is **1/3 complete** (SymPy complete; pvlib incomplete; xarray not yet attempted after recurrence). No destructive Docker reset or cache deletion was performed.

The existing admission implementation was also rechecked: official image digest, exact source identity, Base-Fail and Gold-Pass are separate prerequisites, and trusted-reproducer admission requires at least two trusted rows. SymPy's V20 post-freeze row has zero executable candidates, so its completed image alone cannot satisfy the trusted-reproducer gate. The next experiment gate remains recovery of stable Docker storage, followed by the same frozen pvlib/xarray pulls and isolated Base-Fail/Gold-Pass; live remains closed.

### Host-disk root cause and cleanup

The recurrent storage failure was subsequently traced to the Windows host volume: `C:` had **0 GB free** while `docker_data.vhdx` was expanding. No contemporaneous Windows System/Lxss disk-hardware warning was found. This provides a concrete explanation for the large-write I/O/read-only transition.

Only regenerable host caches were removed: Docker Desktop installer packages in `%LOCALAPPDATA%\Temp`, stale large `.tmp` files, diagnostic/WSL crash dumps, and the pip cache. No project file, Docker image cache, Docker VHDX, frozen artifact, or sealed artifact was deleted. Host free space rose to **26.46 GB**.

After cleanup Docker Desktop frontend/backend processes could start and report `Status running`, but the `docker-desktop` WSL distribution subsequently returned to `Stopped` and `dockerDesktopLinuxEngine` was absent. Therefore the current infrastructure blocker is now **Docker Desktop Linux-engine startup stability after the disk-full event**, not remaining host disk capacity. Official image progress remains conservatively recorded as **1/3 previously completed**, pending engine restart and re-validation of the cached SymPy image. pvlib/xarray pulls, Base-Fail/Gold-Pass, trusted reproducer, live paired canary, C5, DEV30, and Fresh30 remain closed until that infrastructure gate passes.

### D-drive data-disk migration attempt

`D:` is NTFS with 64.15 GB free before migration. The active Docker data VHDX on `C:` was 10.43 GB, so a non-destructive migration was attempted while Docker/WSL were stopped. `docker_data.vhdx` was copied to `D:\DockerDesktopData\wsl\disk\docker_data.vhdx`; source and destination SHA-256 both equal `2EA6792B00B22752501E849C0D67EEE8573102F2D6047A2DABD102E1A7CE4077`.

The original `C:\Users\qq人\AppData\Local\Docker\wsl\disk` directory was renamed to `disk.pre_d_migration_20260926` and retained as rollback material. A directory junction now maps the original Docker path to `D:\DockerDesktopData\wsl\disk`, so the Docker-visible path is unchanged while VHDX writes land on `D:`. The original C-drive VHDX has **not** been deleted.

Docker Engine 29.4.0 reached readiness once using the migrated path, demonstrating that the copied VHDX is bootable. However Docker Desktop again exited/stopped shortly afterward; `docker-desktop` returned to `Stopped` and the Linux-engine pipe disappeared before cached-SymPy validation could complete. D-drive migration is therefore **copy/hash/boot validated but not yet lifecycle-stability validated**. D: retained 53.72 GB free after the copy. The next gate is stable Docker Desktop startup from the migrated VHDX, then cached SymPy verification and the same frozen pvlib/xarray pulls. The C-drive rollback copy must remain until those checks pass.

### Detached launch fix and image acquisition progress

The apparent Docker Desktop "auto-exit" was isolated from Docker-engine failure. Recent Docker logs contained a prior explicit `/app/quit` but no matching Docker crash event for the migrated boot; VM logs showed a healthy Engine serving API/image requests. Launching Docker Desktop through a detached `Win32_Process.Create` process instead of a short-lived WebCodex shell kept the Desktop/backend alive. After 15 seconds it remained `running`, Engine version was 29.4.0, and the cached SymPy image revalidated as `sha256:453e66e1e49ac05efd634d3fd83c84093ed71da8722d41a7645b05582dd52599`.

With the detached launch and D-drive VHDX, the frozen pvlib image completed successfully: digest `sha256:5572429a5029e74c47fb94118af3915531dfdf991da76bafc8831bc8e9f4afe8`. Official-image acquisition is therefore **2/3 complete**. The frozen xarray image name was re-read from the frozen manifest (`swebench/sweb.eval.x86_64.pydata_1776_xarray-2905:latest`) after an initial hand-written repository-name typo was rejected before any experimental execution. Repeated bounded pull windows have downloaded/cache-populated xarray layers while Docker remains stable; the final xarray image has not yet committed. Current free space is approximately C: 34.31 GB and D: 47.97 GB.

No provider/model call, canary reselection, mechanism change, Docker prune, factory reset, or frozen/sealed artifact mutation occurred. The next gate is completion of the exact frozen xarray image, then three-image digest verification and isolated Base-Fail/Gold-Pass under the existing admission protocol.

### Continued acquisition and grader-only preparation

The pvlib image was rechecked as complete at digest `sha256:5572429a5029e74c47fb94118af3915531dfdf991da76bafc8831bc8e9f4afe8`, so official images remain **2/3 complete**. Repeated pulls of the exact frozen xarray image continued to populate/download layers, but several 120-second Runner windows ended with no final image commit. Docker Desktop remained `running` and D: retained about 47.97 GB free, with no recurrence of containerd read-only/I/O failure. The remaining xarray blocker is therefore transport progress, not storage integrity.

While xarray transport was stalled, the existing strict-v5 Base-Fail/Gold-Pass and grader-only implementation was inspected and reused as the protocol reference. V20 grader-only materialization was started only after frozen identity selection; it writes under `.codex/e1c/strict-v20/grader-only-v1` and remains `repair_visible=false`. Raw GitHub transport also stalled during this step: only `sympy__sympy-21586/gold.patch` completed before the bounded job timed out, and no materialization summary was sealed. This is recorded as a partial infrastructure artifact, not experimental evidence and not a task failure.

Current gate: resume the exact frozen xarray image and missing grader-only files when transport progresses; only after all three official image digests and grader prerequisites are complete may isolated Base-Fail/Gold-Pass run. Existing completed phases must not be silently retried. Live paired canary, C5, DEV30, and Fresh30 remain closed.

### Frozen grader blob inventory and admission preflight

Another bounded pull of the exact frozen xarray image again timed out without a final commit; Docker remained healthy and no storage error recurred. A broad recursive cache search was abandoned after its diagnostic timeout and replaced by scoped searches only; no experimental artifact was changed by that diagnostic.

The already-frozen task-repository tree `.codex/e1c_swebench_tree.json` was then used as metadata-only evidence for grader acquisition. It contains exact Git blob SHA and size metadata for all five required grader files (`tests.json`, `gold.patch`, `test.patch`, `eval.sh`, `Dockerfile`) for all three V20 identities: **15/15 blob identities are known at the frozen repository revision**. Only the previously fetched SymPy `gold.patch` content is currently materialized, so no grader-ready claim is made. This inventory provides a safe exact-blob recovery path without identity substitution or outcome-conditioned replacement.

The existing admission implementation was also exercised with its focused zero-provider regression: `tests/test_e1c_admission.py` plus `tests/test_e1c_strict_v5_admission.py` produced **5 passed in 0.18s**. Thus the admission code path is ready; the remaining prerequisites are infrastructure/materialization only. Next gate: obtain the 14 missing grader-only blobs by their frozen identities and complete the exact frozen xarray image, then verify 3/3 official image digests and run isolated Base-Fail/Gold-Pass.

### Exact-blob grader completion and first admission attempt

The remaining grader-only files were fetched through the GitHub Git-blob endpoint using the exact blob SHAs already frozen in `.codex/e1c_swebench_tree.json`. Every returned payload was verified by recomputing the canonical Git blob identity (`SHA1("blob <size>\\0" + content)`). Result: **15/15 grader files materialized and 15/15 frozen blob identities verified** under `.codex/e1c/strict-v20/grader-only-v1`. No task identity was substituted and no grader content was exposed to the frozen repair mechanism.

The three V20 `task.yaml` files and their verified grader-only files were assembled into `.codex/e1c/strict-v20/admission-input-v1`; static validation passed for all three tasks. The admission-input summary is `data/e1c_strict_v20_admission_input.json` with summary SHA-256 `d1773199a19babd897338f10a9d8b87f3e2a05ce1cd29cb6da2bbdeaa0bd1a4c`.

Because pvlib is one of the two executable candidate tasks and its official image is complete, an isolated pvlib Base admission invocation was attempted without waiting for xarray. The outer WebCodex runner reached its 120-second lifetime before `probe()` created the phase artifact directory or Docker admission container. Post-timeout inspection found **no Base log/result and no admission container**, while direct pvlib image-digest inspection immediately succeeded. This is recorded as a **pre-phase infrastructure timeout**, not a Base result; the no-silent-retry rule has not been consumed because no phase artifact exists. A future pvlib Base invocation is permitted only via an execution path whose outer lifetime can exceed the admission phase.

The exact frozen xarray image still has no committed local image after another bounded pull. Docker remains healthy; official images remain **2/3**. Next gate: run pvlib Base through a sufficiently long-lived execution path and continue the exact xarray acquisition. If pvlib Base admits, run its Gold phase exactly once; after xarray commits, evaluate xarray Base/Gold and require at least two trusted reproducers before live remains eligible.

### Runner-lifetime diagnostic

A nonexperimental execution diagnostic tested whether Windows `Start-Process` could detach the pvlib Base admission and xarray pull from the 120-second WebCodex shell lifetime. Both child PIDs were reclaimed immediately when the parent runner ended, with no redirected logs/results and no admission phase artifact. Therefore this runner is using process-lifetime containment/job semantics that make ordinary Windows detachment unsuitable. This route is now recorded as unsupported and must not be repeated.

The admission parser itself was separately verified: the local SWE-bench harness is pinned at `02e7a74ffd0b707aab73d203fe87bdc7c76afc8e`, the expected parser source exists, and `_official_grader()` imports successfully under `python -X utf8`. Thus the remaining pvlib issue is execution lifetime, not parser availability or task/grader materialization. No Base/Gold experimental result was produced by these diagnostics.

Next gate: use a WebCodex-native long-running/asynchronous execution primitive, or equivalent resumable container-phase plumbing that preserves the existing admission semantics, for pvlib Base; keep xarray image acquisition independent. Frozen/sealed mechanism state and no-silent-retry semantics remain unchanged.

### Durable Job resolution and pvlib Base result

The runner-lifetime blocker is resolved without changing admission semantics: WebCodex `run_process` with a 1800-second budget promoted the original native process into a durable Job. The unmodified `e1c_admission.probe()` therefore completed normally for pvlib Base, while a second durable Job continues the exact frozen xarray pull.

Pvlib Base completed in 13.313 seconds with Docker exit code 0 and exact source identity (`source_tree_match=true`, `source_identity_valid=true`). However the official parser produced `valid_log=false`, `parsed_test_count=0`, `f2p_explicit_fail=0/1`; log SHA-256 is `0f26d75bcb19e5f061d673623bd748990e02724364943a38355c07892d785a28`. Direct log inspection explains the invalid log: pytest failed while importing `pvlib` before the target test executed because this historical pvlib source references `np.Inf`, while the official image currently contains NumPy 2.0 where that alias has been removed. This is an environment/test-collection incompatibility, not an explicit FAIL_TO_PASS result.

Accordingly pvlib is **not a trusted reproducer**, its Base phase is final/nonadmissible, and Gold is **not permitted**. The Base phase must not be retried. The xarray durable pull remains running with no output change yet. If xarray commits, its Base phase is the next executable admission phase and must use the same durable Job path; Gold is permitted only after a valid Base log with an explicit FAIL_TO_PASS failure.

### Post-pvlib preregistration reachability check

The frozen preregistration requires at least **2 trusted reproducers**. The frozen postfreeze assessment records SymPy as `no_executable_reproducer` with zero candidates/executable candidates, while pvlib is now final nonadmissible and cannot proceed to Gold. Xarray is therefore the only remaining executable-candidate admission path. Even if xarray eventually becomes a trusted reproducer, V20 can reach at most **1 trusted reproducer**, below the frozen minimum of 2.

This means the V20 live gate is now **unreachable under the frozen protocol**. SymPy must not be upgraded post hoc, pvlib Base must not be retried, identities must not be replaced, and the threshold must not be weakened. The already-running xarray durable pull may finish for artifact completeness, but its outcome cannot reopen live/C5/DEV30/Fresh30 for V20. After xarray reaches a terminal acquisition state, V20 should be sealed as an independent negative / insufficient-trusted-reproducer result and the PLAYBOOK should return to zero-model successor-mechanism development followed by new independent identities.

### Successor preparation while xarray acquisition remains active

The PLAYBOOK was re-read before successor work. Its loop is explicit: preserve a failed independent canary as a negative result, develop one new task-agnostic mechanism on old DEV evidence, then use a new independent/non-overlapping canary; the same three identities must not be tuned until they pass. Historical `E1C_DEV_V48`–`V50` records were also checked and are the earlier 2026-09-24 public-test/outcome-selected DEV branch, not successors of strict V20, so they are not being reused or relabeled.

The successor development baseline is V20's old-DEV replay: 6/6 executable and 5/6 consensus, with one remaining old-DEV consensus gap. Successor work is constrained to old DEV evidence only; V20 independent-canary outcomes/content are excluded from mechanism design. No task ID, repository/framework name, target path, benchmark assertion, Gold, or grader outcome may be hardcoded. The development gate is a strict improvement over V20 (>5/6 consensus) before any successor freeze or new metadata-only canary selection.

The WebCodex high-level coding workflow currently refuses to start while the xarray durable pull is a blocking active Job. The pull was deliberately left running rather than stopped/restarted, and bounded read-only/manual inspection continued instead. Xarray still has no output change or committed image at this checkpoint. Provider/model calls remain 0.

### Strict-v21 zero-model successor development started

Without stopping the xarray acquisition, successor development proceeded manually under the same old-DEV-only boundary. The sole V20 old-DEV consensus gap was diagnosed from the already-exposed DEV projection/source: an explicit issue callable and a generic role/type noun produced two individually executable witnesses on different files, leaving no consensus. A new task-agnostic hypothesis was therefore implemented in `evals/e1c_strict_v21_probe.py`: when an issue explicitly names a callable and a role/type noun, the uniquely localized production callable may contribute an independent structural corroboration only if its production AST defines or returns an identifier matching that noun. The rule contains no task ID, repository/framework name, target path, benchmark assertion, Gold, grader result, or hidden test content.

Focused generic tests for the new rule pass **2/2** (`2 passed in 0.11s`), with provider/model calls still 0. The six-task old-DEV replay is running as durable WebCodex Job `e28e90f5-e1fc-45f1-9b15-34d1e906f688`; its output artifact has not yet been written, so no development-gate result is claimed yet. The predeclared successor gate remains a strict improvement over frozen V20: **>5/6 consensus (therefore 6/6)** before V21 may be frozen/preregistered or any new independent canary identities selected. Xarray acquisition remains artifact-completeness-only and cannot reopen V20 live.

### Successor development outcome: V23 frozen

V21 completed at 6/6 executable but 5/6 consensus (`293403a47f79ec8cc832f63404b9a62e320ceb34776db31588f45735e88790d7`) and is preserved as a development negative. V22 made the callable semantic/AST evidence families independent and recovered the remaining old-DEV callable case, but its aggregation omitted V20's ownership semantic special case and therefore regressed another old-DEV row; it also finished 5/6 consensus (`b1b07d49213ab5b3d74cf9d99e1890d4020fd43bcd011b584f446de32c67e7a3`) and is preserved as a development negative.

V23 is the minimal compatibility-preserving successor: it retains V20's ownership/bounded-assignment family semantics while keeping explicit issue-callable localization semantic and independently derived production-AST role/type corroboration structural. Focused V21–V23 regression is **7/7 PASS** and the six-task old-DEV replay is **6/6 executable, 6/6 consensus**, summary SHA-256 `64ec3896cab0042147db09af7667e7aef261c2f93a405be8b9bbdf0a23939356`. Provider/model calls remain 0.

The V23 mechanism is now frozen. Mechanism-chain SHA-256 is `9e0dd2d87a1c33d2e1e4f84da02eac397156ec908f9ee239ceee7053c7e83616`; prereg SHA-256 is `5a517906a52f8e482d81172782f96fe938c37c0f6ac7e6fc335fc573290b2dbc`. Deterministic metadata-only selection, before statement/source materialization and excluding prior/V20 identities, froze the new independent canary as `django__django-14291`, `django__django-16517`, and `pydata__xarray-3338`; manifest SHA-256 is `7d40c61a66fb3485ee3a36b8eda57a06644d16c0cb519b08a0cae2fab9150ba6`. V23 must not be changed using these canary outcomes. The next gate is post-freeze statement/exact-base source materialization followed by the frozen V23 candidate assessment; official image acquisition requires at least 2/3 executable candidate tasks.

### V23 independent canary result and seal

The first raw GitHub materialization attempt failed before creating the first `task.yaml` because the connection was reset; this was treated strictly as transport infrastructure and not as a canary result. The same frozen identities were retained. Their exact `task.yaml` and problem-statement blobs were then materialized through the Git blob API and verified against their frozen canonical Git blob SHA identities before use. Exact-base source materialization subsequently completed for all three tasks.

Frozen V23 post-freeze assessment completed with **3/3 source ready, 3/3 projection supported, 1/3 executable candidate tasks, and 0/3 consensus tasks**. Assessment SHA-256 is `0bb2eddd03c205ab8b95bf8b8359ee71b7eeb42fb48d6df9475e043f6bd7ea84`. The preregistered candidate gate therefore failed, official-image acquisition for the V23 canary is not allowed, and no live run is permitted. V23 is sealed as an independent negative / insufficient-executable-reproducer result; seal SHA-256 is `df194217ed370d063f3166cfc4d180bb46e65453c434422c460a71eaa95bf155`. These canary outcomes must not be used to tune V23 or reuse the same identities.

Separately, the long-running V20 xarray official-image acquisition finally completed successfully for artifact completeness: `swebench/sweb.eval.x86_64.pydata_1776_xarray-2905:latest` resolved to digest `sha256:23c72d6ce177631efc8094bf28418e3a960d96ca23e8ad727a18c644de257e9f`. This does not alter the already-closed V20 gate. The next research gate returns to zero-provider successor development on old DEV evidence only, followed—only after a predeclared development improvement—by another new non-overlapping metadata-only independent canary.

### Post-V23 successor: strict V25 reaches the candidate gate

Because V23 already reached 6/6 old-DEV consensus, the next development gate was frozen before implementation around evidence diversity rather than inventing an impossible >6/6 task count. V24's taxonomy-only attempt is preserved as a development negative. V25's predeclared gate required all 6 old-DEV tasks to retain consensus, at least two independent evidence families per task, and total consensus-family support strictly greater than 16. Its only allowed addition was a generic behavioral witness when an issue explicitly names an already-localized callable and independently contains an execution/behavior claim; the path must come from the existing frozen callable-localization witness.

V25 passed that gate with **6/6 consensus tasks, minimum family support 2, total family support 17**. Replay SHA-256 is `ad9ce7c5da2a6cdb53747e6df4c9037c7318ec9efc21081789f87c3c8de07302`. The frozen mechanism-chain SHA-256 is `4297b7ff5da4719aec80eb26a70fb8550539ac0aaa146d88a94f9fa0d9d11c29`; prereg SHA-256 is `c26ed4757dc28545d657f8bae4c9f72a59975265eac9c45a73c04b2828ecf1df`.

Before any new task content was inspected, deterministic metadata-only selection froze `sympy__sympy-16637`, `django__django-12830`, and `django__django-12125`, excluding the V20/V23 and earlier contaminated identities. Identity manifest SHA-256 is `e1190a072e1437a1bc925a09ed8f177dc2b9c818ef14f7fd8c31b36d57d32503`. Exact task/statement Git blobs were then materialized and canonical blob identities verified; exact-base source materialization completed for all three. Frozen V25 post-freeze assessment is **3/3 source ready, 3/3 projection supported, 2/3 executable candidate tasks, 2/3 consensus tasks**. Assessment SHA-256 is `1ad542f2f718615afc525b28c9dbe73911249a603fae482022873b4de3ebe1e5`, so the preregistered candidate gate passes and official-image acquisition is authorized.

None of the three V25 official images were already cached. Durable exact-tag pulls are now running as jobs `718274f1-494d-4880-8186-0818f986b0c9` (SymPy 16637), `bc1a8966-0b35-4654-bf8c-326211357882` (Django 12830), and `94686995-12e5-4cab-88df-33f0e262dd66` (Django 12125). Provider/model calls remain 0. The next gate is exact image commitment plus isolated Base-Fail/Gold-Pass admission; Gold remains prohibited unless the corresponding Base phase has a valid official log with an explicit FAIL_TO_PASS failure, and at least two trusted reproducers are required before any live V25 run can be considered.

V25 grader-side preparation has now completed independently of image transport. All 15 required grader blobs (`Dockerfile`, `eval.sh`, `gold.patch`, `test.patch`, `tests.json` for each of the three frozen identities) were materialized from the frozen task tree and verified against canonical Git blob SHA-1 identities. The repair-visible boundary remains false for these grader artifacts. Admission input summary SHA-256 is `c88f66110edf02b5d3575782f4b463412fd49383d90e92e68ccf2b2d1c044e90`.

The first SymPy image pull terminated before image commitment with a Docker Hub manifest transport `EOF`; this is recorded as infrastructure acquisition evidence, not an experimental task failure. Because no Base/Gold phase or image identity had been produced, one exact-tag acquisition retry was started as durable job `1da9af11-a45d-4aa2-a22c-f21a8b3f6ba4`. The original Django jobs remain running and were not duplicated. At the latest inspection all three exact tags were still uncommitted locally, Docker remained responsive, and D: retained 44,078,460,928 free bytes. No Base phase has therefore been started yet, and provider/model calls remain 0.

## 2026-09-26 V25 resume checkpoint
- Reused frozen V25 artifacts; no frozen/sealed mechanism or protocol changed. Provider/model calls: **0**.
- Confirmed all three V25 official images remain uncommitted; Base 0/3, Gold 0/3, live CLOSED.
- Frozen postfreeze assessment confirms `django__django-12125` is `no_executable_reproducer` (0 candidate / 0 executable / 0 consensus). Do not spend scarce acquisition bandwidth on it for the two-trusted-reproducer path.
- The two executable-candidate admission path remains SymPy-16637 + Django-12830.
- SymPy-16637 registry manifest metadata succeeded through explicit `127.0.0.1:7892`: 13 compressed layers, total 1,142,011,407 bytes (~1.064 GiB); largest layers 420,169,440 / 276,288,606 / 210,072,575 / 205,917,499 bytes.
- Started exactly one serial SymPy acquisition resume as durable job `79514b3d-aaa6-430d-90cb-7f155281b53b`; no parallel image pull started. Job currently stalls with no stdout/stderr and image remains uncommitted. Concurrent registry probe through 7892 returned HTTP 401 in ~1.08 s and Docker Engine 29.4.0 remained healthy, isolating blocker to Engine/Desktop pull path rather than general proxy reachability.
- Focused validation command timed out at runner budget without assertion failure; treat as validation-timeout evidence only, not an experimental result.
- Current gate: official-image acquisition. Base may begin only after the corresponding exact frozen image commits; Gold only after valid Base with explicit FAIL_TO_PASS failure; V25 live remains closed until >=2 trusted reproducers.

### V25 resume continuation
- SymPy-16637 official image acquisition **completed successfully**. Durable job `79514b3d-aaa6-430d-90cb-7f155281b53b` exit 0; RepoDigest `sha256:e9f3c11aec668ecba061657a380848ce3dd7f90c3b4cccebddcdb856c7347e4b`.
- Django-12830 manifest: 13 compressed layers, 1,275,705,758 bytes (~1.188 GiB). Serial acquisition job `852943e1-cd98-4174-b3fe-d3d0edebbed5` is running; not yet committed.
- SymPy Base is now image-unblocked but has **not started**. Admission runner requires frozen task files under `.codex/e1c/tasks/sympy__sympy-16637`; `task.yaml` has been fetched from immutable task-tree revision and verified as Git blob `ff1166b2e735ad4e6d4efcbe1309d4e832899964`. Remaining immutable files are pending raw-GitHub transport. No experimental phase artifact exists yet, so no retry semantics have been consumed.
- Current gate: finish immutable task-layout materialization -> SymPy Base exactly once -> Gold only if Base has valid official log + explicit FAIL_TO_PASS failure. Provider/model calls remain 0.

### V25 Base admission and seal
- `sympy__sympy-16637` Base executed exactly once with the committed official image. Source identity and source tree matched exactly; container exit code was 0.
- Official grading was nonadmissible: `valid_log=false`, parsed tests `0`, explicit FAIL_TO_PASS failures `0`, phase pass `false`; Base log SHA-256 `8dc1191f1d3be090586d56427bbe513d9a56b2484a5adda98f37dcc472761a29`. Log evidence includes Python initialization failure (`init_fs_encoding`, `ValueError: source code string cannot contain null bytes`). No Base retry is permitted and Gold is prohibited.
- V25 preregistration requires 2 trusted reproducers and the frozen postfreeze assessment has exactly 2 candidate reproducer tasks. With SymPy permanently nontrusted, maximum possible trusted count is 1. Therefore the V25 live gate is mathematically unreachable and V25 is **SEALED NEGATIVE**.
- Seal artifact: `data/e1c_strict_v25_seal.json`, SHA-256 `25fbdbfb741623bc582529e871dd156037688d597d362682b5652ef5acb76916`.
- Django-12830 acquisition was stopped with cache preserved; completing it cannot reopen V25 and is no longer required under this sealed version.
- Gold / V25 live / C5 / DEV30 / Fresh30 remain closed. Provider/model calls remain 0.
- Next gate: develop a new strict successor using permitted old DEV evidence only, freeze mechanism first, then select a new independent/non-overlapping canary. V25 canary content/outcomes must not be used to tune the successor.

### V25 final seal and two-round stop rule
- SymPy-16637 admission task layout reached 7/7 immutable files with raw Git-blob identity verification. Base then ran exactly once. Official image/source identity was valid, but the image Python runtime failed before parseable test output (`ValueError: source code string cannot contain null bytes`); official parser returned `valid_log=false`, `parsed_test_count=0`, `f2p_explicit_fail=0`, `phase_pass=false`. Base is nonadmissible; no retry and no Gold.
- With Django-12125 already frozen non-executable, only Django-12830 could possibly become trusted. Maximum possible trusted reproducers is therefore 1, below the preregistered minimum 2. V25 live gate is mathematically unreachable; Django-12830 acquisition was stopped with cache preserved because further acquisition cannot change the gate.
- Canonical V25 seal: `data/e1c_strict_v25_seal.json`, SHA-256 `25fbdbfb741623bc582529e871dd156037688d597d362682b5652ef5acb76916`. Supplementary dated seal is retained, not substituted for the canonical artifact.
- V23 and V25 are two different independent negative rounds without a net-new live gain. Per PLAYBOOK section 8, paid expansion is paused. C5/DEV30/Fresh30 remain closed. Next allowed gate is zero-provider successor research on old DEV/non-canary evidence only; any later canary requires a new mechanism plus new non-overlapping metadata-first identities.
