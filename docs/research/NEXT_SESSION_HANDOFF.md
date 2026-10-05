# WebCodex 接手：E1-C evaluation_2

交接日期：2026-10-05。仓库：`qr7896/agent-service-toolkit`。先读 [AGENTS.md](../../AGENTS.md)、[当前 Roadmap](../PROGRESS_RESEARCH_ROADMAP_2.md)、[一周计划](E1C2_ONE_WEEK_PLAN_2026-09-30.md)，不要按历史文档的旧“下一步”直接运行。

## 当前状态

**最新：独立canary v3已完成并封存为1/3；回旧DEV的新生成v3为3/12，开发门槛仍失败。当前任务是零调用证明可信正对照/fixture contract，不再下载或重跑本页历史命令。** 本轮Flash15请求/31992tokens，未自动重试，未改旧冻结依赖。完整[独立负结果](E1C2_HYBRID_CANARY_V3_RESULT_2026-10-05.md)、[DEV结果/零调用下一步](E1C2_HYBRID_DEV_V3_RESULT_2026-10-05.md)。原controller缓存4/12只是开发证据，不能补新生成分数；底层trusted仍false，结果包含人工语义审核。

接手时先核验两份公开结果JSON和其中SHA对应本机原件；云端缺原件时报INFRA_BLOCKED，不虚构复跑。旧DEV v3已运行，禁止再次`run/gold`。下一步按DEV结果文档第1–5项：证明control/target非触发参数可比、生产前置条件校验、保持issue oracle、合成负例与四条参考不退化；仅旧DEV/合成，先零调用，不读取canary调参。证明不足不新增付费试验/新canary；新增付费须新身份和冻结Flash≤100000预算先列命令，不无限连跑。新方法尚未实现，不能算已验证创新或自动可信。

本机本轮回归1118passed/4skipped/0failed/33warnings（50.55秒），工程回归非修复率。下一独立样本/Agent repair/DEV30/Fresh30/E2都未启动。未扩大权限、开放Docker远程端口、修改tunnel或清理镜像/VHD；D盘约42.2GiB。

历史封板记录：先冻新方法/预算再metadata-only选题，三题Flask-5063、PyVista-4226、SymPy-17150不与历史identity重叠。官方/镜像站摘要3/3一致；当时未读issue/未付费。freeze SHA`978a0b86ba70f7cf9c7fd9add3a123c682202afb73d401ade4cb15b3c2bc7a44`，identity SHA`62649edc20998fad8f101a488ccbb22e0dff6343bf81a0fc3398e5fed5d1500d`。现已执行，保留[协议](E1C2_HYBRID_CANARY_V3_METHOD_2026-10-05.md)、[初始传输收据](../../data/e1c_evaluation_2_hybrid_canary_v3_transport_receipt.json)与各失败原件，不改原freeze或回填初始收据。

## 已完成的用户直连下载与执行（历史命令，不重跑）

已核压缩层分别1.067/2.130/1.064GiB，总4.261GiB（磁盘安装体积不是该数字）。D:现场42.77GiB空闲，逐张`20+6×compressedGiB`空间守卫，当前最大门槛32.78GiB；后续镜像解压仍可能触发stop，不承诺空间必够。不清理原记录、活动VHD或tunnel。下载显示每层MiB、速度、ETA、断点续传与Docker导入心跳。平均1–5MiB/s，传输约15–73分钟，加校验/导入粗估总40分钟–2小时；0.2MiB/s则仅传输约6小时，网络未知不保证时长。单镜像硬超时6小时。

关闭VPN全局及TUN（仅取消全局可能仍被TUN接管），Docker保持No proxy。官方小型manifest seal已缓存，本条download不请求官方或7892；镜像与blob显式空代理直连，不能绕过系统级透明路由。失败时保留日志，通知执行者，不自动重试。

```powershell
Set-Location 'D:\codex\working\project20260827'
Start-Transcript -Path '.codex\e1c\evaluation_2\hybrid-canary-v3\download.log' -Append
try {
    uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_hybrid_canary_v3 download --timeout-per-image 21600
    if ($LASTEXITCODE -ne 0) { throw '下载未完成：保留缓存和日志，不进入模型实验。' }
} finally {
    Stop-Transcript
}
```

返回`verified_loaded=3`后，先核对loaded/transport/image ID，再执行以下**零模型**命令，任一步非0即停、不自行跳过：

```powershell
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_hybrid_canary_v3 admit --timeout 900
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_hybrid_canary_v3 public
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_hybrid_canary_v3 preflight
```

所有阶段位于`.codex/e1c/evaluation_2/hybrid-canary-v3/`，保持live/public/source与grader-only分区。未双准入仍占固定分母，不替换题；预算预检须给出可执行候选数及reserve。仅在这些条件满足后，先报告以下精确付费命令：

```powershell
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_hybrid_canary_v3 run
```

Flash非thinking、temperature0、最多6请求、单题20,000/整批60,000provider tokens、单请求输出3,000，SDK零重试。在用户已授权单实验≤100,000范围内，但不得无限串批或放宽此freeze。run完成才执行`uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_hybrid_canary_v3 gold`，独立零模型判别。记录provider返回alias而非不可变版本；可信≥2/3（机器与人工语义审核分开）才另冻Agent repair小实验。失败封存回DEV，不能在v3修规则后仍称独立；sealed TEST/C5/Fresh30继续关闭。

**云端限制**：新代码和身份在Git；小型metadata/transport seal仍在本机`.codex`。用户用本机终端完成下载；WebCodex须经已验证本机执行器读取这些摘要/调用限定入口，缺执行器、Docker、缓存或原件时报INFRA_BLOCKED。不能把云端clone误当本机、不打开Docker远程裸端口、不上传密钥；tunnel在线能力仍需独立检查。本次没有改Docker/tunnel设置。

封板时工程回归：1115 passed、4 skipped、33warnings、0failed（50.61秒）；最新1118见页首。skip与原套件一致，非修复率。指定重点18passed/Ruff通过/V3规定原preflight退出0。

## 已封存 v2 背景（不要按旧建议重建下一批）

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

## 已完成的 DEV 开发计划（历史要求保留）

以下开发已完成并保留多轮结果，当前按页首v3执行，不重复计费：按一周计划在**新版本**实现响应分账、行为合同、fixture正对照与自动源码窗口覆盖核验；复用现有定位、预算、容器和 ledger。先用旧DEV及合成夹具做通用回归，禁止任务ID→文件/规则表。不得修改 canary v2 的14份冻结方法文件或本批live freeze；已有 DEV12 与旧 DEV30 可用于调试，sealed TEST、SERBench private/Test500内容不可用于调参。响应协议改善与真实可信覆盖增益分别报告。

先实现合成边界测试，再在已有非保护 DEV 证据上验证。若缺原始输入/镜像，输出明确缺失路径和所需能力，不伪造真实实验。每个新付费 DEV 实验先输出精确命令、模型、最大请求数、token 上限与冻结身份；使用用户已有单实验≤100,000 tokens 的许可范围，不无限串联批次，遵守一周计划的累计预算与停止规则。

## 每次结束必须回传

- Git commit、实际命令、退出码、测试通过/失败/跳过数。
- 固定分母、各阶段人数、弃答/环境失败/模型失败分别计数。
- 请求数、provider tokens、失败扣费、自动重试次数。
- 新产物相对路径和SHA；未运行项及下一条条件式命令。
- 是否触及 protected 数据、镜像/本机设置（正常应为否）。
- 只在[集中续档](PROGRESS_LOG_ARCHIVE_2026-09-27_CONTINUATION.md)追加过程，更新 Roadmap 2 当前状态；保留旧版本和失败记录。

旧 E1-B 交接全文保留在[历史快照](NEXT_SESSION_HANDOFF_HISTORY_2026-09-30.md)。
