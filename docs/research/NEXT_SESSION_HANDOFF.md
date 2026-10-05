# WebCodex 接手：E1-C evaluation_2

交接日期：2026-10-05。仓库：`qr7896/agent-service-toolkit`。先读 [AGENTS.md](../../AGENTS.md)、[当前 Roadmap](../PROGRESS_RESEARCH_ROADMAP_2.md)、[一周计划](E1C2_ONE_WEEK_PLAN_2026-09-30.md)，不要按历史文档的旧“下一步”直接运行。

## 当前状态

DEV v4 经语义审核可信复现 4/12，不是修复率；首批独立 canary 1/3，已封存负结果。第二批经元数据代理修订、用户直连下载，3/3镜像及官方双准入通过；三次Flash一次执行共13,783 tokens，可信0/3，已封存。旧DEV的成功数不能补入这批分母。新版 repair / C5 / Fresh30 / E2 main 未运行。详见[第二批结果](E1C2_CANARY_V2_AMENDED_RESULT_2026-10-05.md)和[data摘要](../../data/e1c_evaluation_2_canary_v2_amended_result.json)。

canary v2 方法 SHA：`fd58671dcdb923e70b7f018362682802849c54651655e21d051828e1d6f4d14b`；identity SHA：`a22311ffc4dd41c379e839e5618bccb35164367b35b9a3797bf5f17bb3dba997`。以 [freeze JSON](../../data/e1c_evaluation_2_canary_v2_method_freeze.json) 核验方法文件，不重写摘要迁就改动。

## 第一步：可执行性检查

在仓库根目录执行；安装依赖可能需要网络，但不需要模型密钥：

```sh
git status --short
git rev-parse HEAD
uv sync --frozen --group dev
uv run --frozen python -X utf8 -m pytest -q tests/test_model_budget.py tests/test_v3_pilot_runner.py tests/test_v3_compact_pilot.py
uv run --frozen python -X utf8 -m pytest -q
```

依赖已缓存时可加 `--offline`。本机测试记录与已知 V3 preflight 编码失败见[保全记录](WORKSPACE_REORGANIZATION_2026-09-30.md)。零失败才称本次回归通过；skip 必须解释，不能通过删除断言或增加 skip 造绿。

只读确认 `docker version`、`docker image ls` 和需要的本地摘要文件是否存在。Docker 不存在时继续源码/单测工作，报告 `INFRA_BLOCKED`。GitHub 上只有可公开材料；`.codex`、镜像和本机 bridge 不会随 clone 自动出现。不要索取或上传 `.env`、Gold 正文、密钥或整块数据盘。

## 当前冻结批次已封存：不要重跑

本批完整路径为 `.codex/e1c/evaluation_2/canary-v2-metadata-proxy-v1/`，已有 acquire、grader-only、issue-only、source、live原始记录。原始响应、输入、账本、状态和Gold结果保留，不回填、不删除。云端 clone 只有公开摘要，不能假定这些本机原件存在。下列命令仅为已执行记录，不能再作为“下一步”运行：

```sh
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_canary_v2_metadata_proxy admit
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_canary_v2_metadata_proxy public
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_canary_v2_proxy_live run
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_canary_v2_proxy_gold
```

新适配器已实现，live freeze SHA `5b3c8bb508019adb2fd33f32511d9d16f3bebc8cb5979e69e2cc7f4871c1004f`。三题都有四个自动窗口；Seaborn回显到输出上限导致响应拒绝，Marshmallow无效fixture导致Gold后仍失败，pytest明确弃答。原runner把弃答统一记candidate_rejected；审计报告单列，原state不改。

实得0/3，不足2/3，本批已关闭。任何格式重放、窗口扩展或候选修订都只能作为未来开发材料，不能重报本批独立成绩。下一步回旧DEV开发通用机制；有同预算增益后再冻新方法、选择同时排除DEV及两批canary的新身份。Fresh30和旧六条TEST继续关闭。

## 可立即推进的 DEV 工作

按一周计划在**新版本**实现响应分账、行为合同、fixture正对照与自动源码窗口覆盖核验；复用现有定位、预算、容器和 ledger。先用旧DEV及合成夹具做通用回归，禁止任务ID→文件/规则表。不得修改 canary v2 的14份冻结方法文件或本批live freeze；已有 DEV12 与旧 DEV30 可用于调试，sealed TEST、SERBench private/Test500内容不可用于调参。响应协议改善与真实可信覆盖增益分别报告。

先实现合成边界测试，再在已有非保护 DEV 证据上验证。若缺原始输入/镜像，输出明确缺失路径和所需能力，不伪造真实实验。每个新付费 DEV 实验先输出精确命令、模型、最大请求数、token 上限与冻结身份；使用用户已有单实验≤100,000 tokens 的许可范围，不无限串联批次，遵守一周计划的累计预算与停止规则。

## 每次结束必须回传

- Git commit、实际命令、退出码、测试通过/失败/跳过数。
- 固定分母、各阶段人数、弃答/环境失败/模型失败分别计数。
- 请求数、provider tokens、失败扣费、自动重试次数。
- 新产物相对路径和SHA；未运行项及下一条条件式命令。
- 是否触及 protected 数据、镜像/本机设置（正常应为否）。
- 只在[集中续档](PROGRESS_LOG_ARCHIVE_2026-09-27_CONTINUATION.md)追加过程，更新 Roadmap 2 当前状态；保留旧版本和失败记录。

旧 E1-B 交接全文保留在[历史快照](NEXT_SESSION_HANDOFF_HISTORY_2026-09-30.md)。
