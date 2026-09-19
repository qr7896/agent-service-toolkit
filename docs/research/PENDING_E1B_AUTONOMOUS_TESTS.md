# E1-B Autonomous Editor 未完成测试日志

> 更新：2026-09-18；状态：R10 DEV 4/4 已调用，但原子推理结算导致预算协议失效；最终配置尚未冻结；6 条 TEST autonomous outcomes sealed。

## 已完成前置

- E1-B 10/10 Base-Fail + Gold-Pass；与原始20条形成30-task executable pool。
- prospective split 已冻结：DEV 4 / TEST 6，source-commit overlap=[]。
- Gold source/label/grader 编辑阶段不可见；strict JSON patch、写路径/测试保护、sandbox、独立 pytest grader 已实现。
- deterministic DEV plumbing 已跑通；最近 harness + async adapter：11 passed in 15.75s。
- run_dev_with_editor 已取消隐式 full-workspace evidence；runlog 已绑定 model/prompt/split/tasks/config hashes。
- DeepSeek V4 Flash DEV one-shot：随后只补跑剩余 state-version-29 一次，现 4/4 DEV 均获得模型调用；第 4 条单次 22,860 tokens，累计 31,276 tokens，sealed TEST 调用数=0。

## P0：真实模型 DEV

- [x] Provider/model=`deepseek/deepseek-v4-flash`，仅运行 DEV，sealed TEST 未调用。
- [x] 已记录 temperature=0、seed=null、prompt SHA、iterations=1、write budget 与 sandbox policy。
- [x] DEV evidence protocol=`declared-seed-read-v1`；只读取任务公开声明的 setup paths，不读取 Gold/test content。
- [x] 已记录 calls、wall time、parse/model failure、files written、F2P/P2P、resolved 与 token usage。
- [x] resume 逻辑通过 22 项测试，且确认不会覆盖前三条真实结果；只补跑第 4 条 DEV 一次。
- [x] 第 4 条 state-version-29 已调用但未修复成功、未重试；单次 22,860 tokens，累计 31,276。
- [ ] 重新定义硬预算协议：当前 provider 只能在原子调用结束后结算推理 token，固定小 ceiling 无法在调用前保证；协议修复前禁止进入 sealed TEST。

## P0：Evidence 协议冻结

E1-B 没有可直接复用的 V1 frozen retrieval trace；另行建立协议前不能声称与 V1 使用相同 retrieved evidence。

- [~] DEV 已采用受限 `declared-seed-read-v1`；尚未记录 irrelevant-read ratio，也未冻结 TEST evidence-policy hash。

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
- [x] 不沿用两个无法查询的旧后台 job；2026-09-18 明确重跑 Runtime + E1 smoke + V1 decision/policy，最新结果 75 passed。该数字只表示非模型回归，不表示 Autonomous Repair Rate 或 patch success。

## 封存清单

DEV：async-propagation-22、config-code-budget-25、cross-module-status-26、state-version-29。
SEALED TEST：async-cancel-27、hard-negative-router-28、multifile-policy-21、multifile-sandbox-cleanup-30、resume-approval-23、symbol-hard-negative-24。

## Claim Boundary

可说：R10 DEV 已完成 4 次 one-shot 原子调用；第 4 条暴露 provider 原子推理结算与固定小 token ceiling 不兼容，累计 31,276 tokens；sealed TEST 仍为 0 调用。
不可说：4 条 DEV 构成可报告的 Autonomous Repair Rate；预算协议已经有效；Autonomous Editor 已验证成功；V1 gain 已证明 autonomous patch success；6条 TEST 已验证；结果具有统计泛化性。
