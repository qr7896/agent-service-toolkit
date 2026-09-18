# E1-B Autonomous Editor 未完成测试日志

> 更新：2026-09-18；状态：Runtime R1–R9 complete，P0/R10 PAUSED；真实模型未配置；6 条 TEST autonomous outcomes sealed。

## 已完成前置

- E1-B 10/10 Base-Fail + Gold-Pass；与原始20条形成30-task executable pool。
- prospective split 已冻结：DEV 4 / TEST 6，source-commit overlap=[]。
- Gold source/label/grader 编辑阶段不可见；strict JSON patch、写路径/测试保护、sandbox、独立 pytest grader 已实现。
- deterministic DEV plumbing 已跑通；最近 harness + async adapter：11 passed in 15.75s。
- run_dev_with_editor 已取消隐式 full-workspace evidence；runlog 已绑定 model/prompt/split/tasks/config hashes；新增真实/付费模型调用=0。

## P0：真实模型 DEV

- [ ] 配置明确 Provider/model，复用 core.get_model()；仅运行4条 DEV，严禁调用6条 TEST。
- [ ] 记录 model/provider、temperature/seed、prompt SHA、iterations、write budget、sandbox policy。
- [ ] 明确 evidence access protocol；不得把整个 workspace 冒充 retrieved evidence。
- [ ] 每 task 记录 calls、wall time、parse failure、files written、F2P/P2P、resolved。
- [ ] failure 分类：retrieval_gap / editor_reasoning_gap / regression_gap / model_or_parse_failure / budget_exhaustion。

## P0：Evidence 协议冻结

E1-B 没有可直接复用的 V1 frozen retrieval trace；另行建立协议前不能声称与 V1 使用相同 retrieved evidence。

- [ ] 选择 retrieval snapshot 或受限 read/search tools；记录 files/calls/context/irrelevant-read ratio；冻结 evidence-policy hash。

## P0：最终配置冻结

- [ ] 冻结 editor/prompt/model/evidence/tool/budget/sandbox/task/split SHA 与 Gold-hidden assertion；freeze 后禁止依据 TEST outcome 修改。

## P0：6条 sealed TEST one-shot

- [ ] P0 全完成后一次性运行6条 TEST，不逐题调 prompt、不追加预算。
- [ ] 报告 Autonomous Repair Rate/pass@1、F2P/P2P、attempts、wall time、calls、files read/written、安全违规。
- [ ] Oracle 与 Autonomous 分开报告，计算 Editor/Reasoning Gap，并区分 Retrieval/Editor/Regression Gap。
- [ ] 保存 trajectory、final diff、grader result、config hash；n=6 不宣称统计泛化。

## P1：安全与回归补强（已完成）

- [x] 递归 Gold-key leakage scan；canonical root/symlink 防护；normalized-path collision；strict string-only patch content。
- [x] 保护 `.git` / `.env` / `.codex`、test path；content ceiling；完整回归 E1 smoke + E1B harness + V1 decision/policy。
- [x] 不沿用两个无法查询的旧后台 job；2026-09-18 明确重跑 Runtime + E1 smoke + V1 decision/policy，最新结果 74 passed。该数字只表示非模型回归，不表示 Autonomous Repair Rate 或 patch success。

## 封存清单

DEV：async-propagation-22、config-code-budget-25、cross-module-status-26、state-version-29。
SEALED TEST：async-cancel-27、hard-negative-router-28、multifile-policy-21、multifile-sandbox-cleanup-30、resume-approval-23、symbol-hard-negative-24。

## Claim Boundary

可说：E1-B prospective autonomous evaluation infrastructure is ready for DEV model testing。
不可说：Autonomous Editor 已修复成功；30条都是 untouched held-out；V1 gain 已证明 autonomous patch success；6条 TEST 已验证；结果具有统计泛化性。
