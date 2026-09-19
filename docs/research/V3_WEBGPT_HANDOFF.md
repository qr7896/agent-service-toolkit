# V3 Web GPT 续作交接

## Material Passport

- Origin skill: academic-research-suite / experiment planning
- Origin mode: handoff
- Origin date: 2026-09-19
- Verification status: VERIFIED against the local workspace
- Version label: v3-web-handoff-v1
- External model/API calls in this round: 0
- Internal sealed TEST opened/called: 0/0

## 当前事实

- 研究问题固定：在 strict-past chronological stream 中，reliability-aware experience memory 是否减少失败或检索成本，同时不增加 stale-memory harm。
- V2 已冻结；V3-0~V3-6 mechanism 已冻结，不再新增算法、阶段或阈值。
- 已实现 schema v2、execution-time provenance、strict-past replay、reliability/lifecycle、四臂 matched ablation、negative/counterfactual readiness、collection gate 与 artifact audit。
- focused V3 regression：38 passed / 0 failed / 4 dependency warnings。
- 桌面 Git preflight 已通过：真实 root/HEAD 可读，`ready_to_collect=true`、`blockers=[]`。
- 仍无真实 prospective row、paired prospective evidence 或 efficacy 结论；cohort marker 尚未创建。
- 真实评估入口尚未封口：`evals.v3_frozen_pipeline_smoke` 固定产生 `synthetic=true`，因此不能通过默认 real-only artifact audit；不得手工改标记规避。

## 下一步任务（严格顺序）

1. 确认 `git status --short` 为空，并重新运行 collection preflight；HEAD 必须是包含 frozen V3 mechanism 的提交。
2. 从现有任务中选择 5–10 条明确 non-sealed 的 development tasks，先固定 task IDs、runner、模型、prompt、token/call/time ceiling；不得使用 E1-B sealed TEST 或 Test500 private certificates。
3. 得到用户对模型与预算的明确确认后，在第一条真实任务前创建 `v3-prospective-001` cohort marker：

   ```powershell
   .venv\Scripts\python.exe -m evals.v3_collection start `
     --collection-id v3-prospective-001 `
     --trajectories .codex/trajectories/coding_agent.jsonl `
     --preflight .codex/v3/preflight.json `
     --output .codex/v3/cohort.json
   ```

4. 运行真实 Coding Agent tasks；raw trajectory JSONL 只追加、不回填旧记录。
5. 校验每条新 row 的 execution commit、retrieved IDs、adoption observation、outcome 和时间戳。
6. 运行 collection status；数据达到冻结门槛后，先补齐可验证来源的 real artifact 生成入口，再运行 frozen evaluation 与默认 real-only artifact audit。
7. 只在获得 paired prospective evidence 后分析 success、attempts、reads、tool calls、proxy/provider tokens 与 stale-memory harm。

## 当前需要用户决定的唯一事项

选择 prospective runner、模型和总预算。没有明确预算前，不发起任何真实/付费模型调用，也不提前创建 cohort marker。

## 禁止事项

- 不修改 frozen reliability、compatibility、decay、lifecycle 或 ablation arms。
- 不为历史 trajectory 回填当前 HEAD。
- 不用 synthetic smoke 冒充真实实验。
- 不把 retrieval、adoption-observed 或 counterfactual-ready 当作因果效果。
- 不打开 E1-B sealed TEST、Test500 private certificates。

## 可直接粘贴给网页版 GPT 的提示词

> 继续 `project20260827` 的 V3 prospective experiment。先阅读 `docs/research/V3_WEBGPT_HANDOFF.md`、`V3_PROTOCOL.md`、`V3_COLLECTION_RUNBOOK.md` 和 `RESULTS_V3.md`。V3 mechanism 已冻结，不再设计新算法。先确认工作树干净并重跑真实 Git preflight；然后只做 non-sealed task/runner/model/budget 冻结。未得到我的明确模型与预算确认前，不发起付费调用、不创建 cohort、不触碰 sealed TEST。出现 blocker 时 fail closed，并更新 `RESULTS_V3.md` 与 Roadmap 的当前状态，不把过程日志散落到 Roadmap。
