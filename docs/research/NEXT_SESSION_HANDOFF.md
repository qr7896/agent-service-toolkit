# WebCodex 接手：E1-C evaluation_2

交接日期：2026-10-05。仓库：`qr7896/agent-service-toolkit`。先读 [AGENTS.md](../../AGENTS.md)、[当前 Roadmap](../PROGRESS_RESEARCH_ROADMAP_2.md)、[一周计划](E1C2_ONE_WEEK_PLAN_2026-09-30.md)，不要按历史文档的旧“下一步”直接运行。

## 当前状态

DEV v4 经语义审核可信复现 4/12，不是修复率；首批独立 canary 1/3，已封存负结果。canary v2 方法和三题身份已冻结，原官方直连尝试失败；用户授权后另冻基础设施修订 `e1c2-canary-v2-metadata-proxy-v1`，官方小型元数据通过 7892、镜像站直连，3/3 摘要一致。官方正文 26,333 字节 / 6 请求；本地 Docker 正常，待用户下载三张镜像，模型调用 0。新版 repair / C5 / Fresh30 / E2 main 未运行。

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

## 当前冻结路径：仅条件满足时逐关推进

使用[新传输修订/下载交接](E1C2_CANARY_V2_METADATA_PROXY_AMENDMENT_2026-10-05.md)交给本机用户完成大文件。新 seal 在 `.codex/e1c/evaluation_2/canary-v2-metadata-proxy-v1/image_transport.json`，数据 freeze 在 `data/e1c_evaluation_2_canary_v2_transport_amendment.json`。它继续同一 cohort，不是新独立样本。镜像缺失时不能自动拉取或走 VPN。确认传输与 image ID 后：

```sh
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_canary_v2_metadata_proxy admit
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_canary_v2_metadata_proxy public
```

每一步检查退出码和原位失败记录；不串成无条件执行链。修订对应的 live adapter/执行 freeze 尚待零模型准入后实现，必须绑定本修订和新产物路径，不能用原 `canary_v2_live` 读本修订产物。保持原生成方法、Flash ≤3 请求、整批42,000 tokens、每题14,000、重试0；preflight 真过并核验精确命令授权后才 run。本次文档交接不构成跳过前置条件的授权。

若可执行结果不足2/3，封存负结果，不在这三题上调方法后仍称独立。若达到2/3，先冻结新 repair 配对协议；不自动打开 Fresh30 或旧六条 TEST。

## 可立即推进的 DEV 工作

按一周计划在**新版本**实现行为合同记录与反馈约束；复用现有定位、预算、容器和 ledger。不得修改 canary v2 的14份冻结方法文件；优先新增独立 DEV 模块与针对性测试。已有 DEV12 与旧 DEV30 可用于调试；新 canary、sealed TEST、SERBench private/Test500 内容不可用于调参。

先实现合成边界测试，再在已有非保护 DEV 证据上验证。若缺原始输入/镜像，输出明确缺失路径和所需能力，不伪造真实实验。每个新付费 DEV 实验先输出精确命令、模型、最大请求数、token 上限与冻结身份；使用用户已有单实验≤100,000 tokens 的许可范围，不无限串联批次，遵守一周计划的累计预算与停止规则。

## 每次结束必须回传

- Git commit、实际命令、退出码、测试通过/失败/跳过数。
- 固定分母、各阶段人数、弃答/环境失败/模型失败分别计数。
- 请求数、provider tokens、失败扣费、自动重试次数。
- 新产物相对路径和SHA；未运行项及下一条条件式命令。
- 是否触及 protected 数据、镜像/本机设置（正常应为否）。
- 只在[集中续档](PROGRESS_LOG_ARCHIVE_2026-09-27_CONTINUATION.md)追加过程，更新 Roadmap 2 当前状态；保留旧版本和失败记录。

旧 E1-B 交接全文保留在[历史快照](NEXT_SESSION_HANDOFF_HISTORY_2026-09-30.md)。
