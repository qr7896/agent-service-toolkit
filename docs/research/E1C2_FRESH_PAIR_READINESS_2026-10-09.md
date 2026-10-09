# 两来源从 issue 开始的配对复现与修复链：已冻结，效果待测

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent
- Origin Mode: run（本轮仅工程与零调用预检）
- Origin Date: 2026-10-09
- Verification Status: UNVERIFIED（执行收据已核对；无独立外部重跑或新模型效果）
- Version Label: fresh_pair_readiness_v1

## 目前真实成果

前次[已授权单旧 DEV 实验](E1C2_COMPLETION_SUCCESS_2026-10-09.md)完成：Flash 一次请求、19,840 provider tokens，模型补丁独立官方 F2P 1/1、P2P 37/37、resolved=true；公开自产 21 个合成变体均完成。这是已见单题成功，不是 30/30、独立泛化或完整公开意图证书。原输入、失败、源码、结果和账本不改。

本轮完成新的[执行协议](E1C2_FRESH_PAIR_PIPELINE_PROTOCOL_2026-10-09.md)及 `evals/e1c_evaluation_2_fresh_pair_pipeline.py`：

公开 issue 自动检索/限定名补源 → 新 normal/target → 无网络容器各两次执行 → 条件执行门槛 → 新模型生产补丁 → 相同 probe 自验证 → 两题全部生成封存 → 独立官方评分。

这是 flat runner，复用现有预算、严格编译、容器与评分组件，没有增加依赖或靠全局 OUT/preflight 猴子补丁接线。使用原两个已见库来源，**从新冻结公开输入生成，不复用旧 probe 或成功补丁**。初始输入绑定既有零调用检索产物；本次模型阶段不重新拉取源码，不称两个全新任务或新抽样。

物理输入 SHA 与每个声明源码 slice/完整 base blob 核验；继承的过期 input ID 删除后重算。连续窗口保持原 5000 字符 cap、AST 窗口保持 2500。benchmark/examples 不送模型；静态 global 仍不是 runtime 值证书。首请求消息 SHA 在实际调用前再比对；实际 SDK wire 检查 Flash/enabled/high/no-tools/输出限额。预算不足不调用，未知收费或网络失败停止、不重试。

生成侧不读取现成测试断言、Gold 或官方反馈。配对稳定仅说明 `operational_pair_valid`，**不自动升为 full_issue_trusted**；自验证与官方 resolved 分开报告。没有隐藏断言进入模型，也没有自动语义完备性承诺。官方评分必须同时满足非空 F2P、P2P、源身份、有效日志和 rc；不能把脚本 rc0 当修复成功。

## 零调用验收

15 新专项覆盖 canonical 身份、常量断言/重复 probe 拒绝、实际生成反馈链、共享预算、实际 SDK MockTransport wire/推理计费、seal 缺失/缺项/越界拒绝，以及官方目标/回归/身份/日志/rc 各失败分支。使用假密钥和 MockTransport，不调用真实 provider。

Ruff 通过；预算/V3/新链重点 34 passed；合成 compact preflight ready；全量 **1766 passed、4 skipped、33 warnings，66.26 秒**。这些是工程回归，不是修复率。Docker 引擎与两张不可变镜像只读检查通过，无需下载或重启。

[脱敏收据](../../data/e1c_evaluation_2_fresh_pair_readiness.json)绑定 freeze、两个 canonical 输入与初始 prompt SHA、回归 XML。freeze SHA `2db1e3b50c0499b48382a0e14bd87440cf3f64edd74599550f22b911c20803a9`；已比对当前源码/输入/协议相等。新身份没有 started 或 provider ledger，新增付费调用 **0**。

## 唯一下一步与停止条件

按仓库 AGENTS.md 取得新精确命令授权后，本机只运行一次：

```powershell
Set-Location 'D:\codex\working\project20260827'
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_fresh_pair_pipeline run
```

模型 `deepseek-flash`，enabled/high；整批最多 **4 calls / 100,000 tokens（含推理）**，每来源最多 2 calls / 50,000。每次生成在预注册 16k–20k 范围按余量分配，HTTP300秒、retry0。`--offline`约束 uv 依赖解析；已授权模型请求仍需要网络，验证容器则明确 network none。

若 normal/target 门槛失败，跳过该题 repair；预算/JSON/弃答分别记录；SDK/容器基础设施失败停止整批，保留现场。禁止改 started 身份重跑或自动扩大预算。固定两题分别汇报 pair、自验证、official F2P/P2P/resolved 与成本，不能拼跨版最佳。

后续：按真实失败回旧 DEV 修通用方法 → 同版固定 DEV12（九准入，其他基础设施失败独列） → 公开行为义务缺证验收 → 完整方法/预算冻结 → 全历史排除的新 canary 一次 ≥2/3 → 冻结 repair 对照 → 另授权全新任务/E2。未满足门槛不抽 canary，不打开 sealed TEST/Fresh30。不能保证 30/30 或一周完美。

WebCodex 可直接跑源码单测；本机 `.codex` 来源、镜像、私有评分材料/凭证不随 Git 同步，缺材料报 INFRA_BLOCKED。本轮未扩 tunnel 白名单，未验证远程新 live 接线；不上传 Gold/raw/密钥、不开放裸 Docker、不改 IPC/VHD/注册表/代理/tunnel。逐轮过程仅记集中日志。
