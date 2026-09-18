# V2 Contextual Policy — 启动记录

## Material Passport

- Document type: experiment protocol/status
- Verification status: `STARTED_PROTOCOL_ONLY`
- Date: 2026-09-18
- External model calls for V2: 0
- Result claim: none

## 当前状态

V2 已启动到 V2-0：新增候选动作 `propensity`、`policy_score`、选择动作与 pre-action state 的记录契约，并冻结第一版 reward 公式：

`evidence_gain - λ_token × tokens - λ_call × tool_calls - λ_risk × risk`

当前没有训练 LinUCB、Thompson Sampling 或其它 contextual policy，也没有执行付费模型调用。V2-1 要求的 200–500 个跨问题簇、跨 commit 任务尚未建立，因此不得报告 V2 相对 V1 的收益。

## 下一门槛

1. 先完成 R10 的第 4 条 DEV，判断 E1 是否存在端到端传导信号。
2. 冻结 V2 logging schema、reward 权重与 safe-exploration action space。
3. 建立至少 200 条、包含 propensity 的 decision records 后，才运行离线 policy replay。
