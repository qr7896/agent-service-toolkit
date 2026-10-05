# E1-C 集中日志续档（2026-09-27 起）

原 [集中日志](PROGRESS_LOG_ARCHIVE.md) 含既有非 UTF-8 字节，本次不重写或覆盖历史记录；后续增量记录集中追加在本文件。这里记录事实与机器证据，不修改已封存的评估。

## 2026-09-27 — Source-contract independent canary 封板核对

旧 DEV development gate 已通过：2 个跨仓库、可重复、`--network none` 的 runtime witness。之后 metadata-first 冻结独立 primary：`django__django-12453`、`sympy__sympy-13761`、`matplotlib__matplotlib-21559`。Django 和 SymPy 的冻结盲态 preflight 均为 0 个可执行候选。因此 [原评估](../../data/e1c_strict_successor_source_contract_independent_canary_assessment.json) 的最终理论上限为 1/3，低于预注册的 2/3；`gate_status=sealed_negative_threshold_unreachable`。这不是模型修复 0/3。

原评估封存之后，Matplotlib 的官方 [Base](../../.codex/e1c/source_contract_canary/admission_results/matplotlib__matplotlib-21559/base.json) / [Gold](../../.codex/e1c/source_contract_canary/admission_results/matplotlib__matplotlib-21559/gold.json) 准入完成：Base F2P 0/1、P2P 680/680；Gold F2P 1/0、P2P 680/680；exact-base tree 与官方镜像身份有效。Matplotlib 的 source-contract preflight **未运行**；准入通过不改变 reproducer gate 不可达的结论。原评估未被覆盖，reserve 内容未查看，未在独立 canary 上做后验专用调参。

本轮零模型回归：`uv run --frozen python -X utf8 -m pytest -q tests/test_e1c_strict_v8_source_contract.py tests/test_e1c_strict_successor_gate.py tests/test_e1c_strict_successor_preflight_runner.py`，**17 passed**。新增 provider 调用 0；paired live、C5、同版 DEV30、Fresh30 仍关闭。下一合法研究步骤：只从旧 DEV/非 canary 证据构造实质不同的任务无关复现机制，零模型门槛通过后重新冻结不重叠的独立 canary；其冻结门槛通过且获得精确命令授权后才可付费。

同一工作区另跑完整非模型回归：`uv run --frozen python -X utf8 -m pytest -q` 得到 **1038 passed、4 skipped、1 failed**（177.72 秒）。唯一失败是已知的 `tests/app/test_streamlit_app.py::test_app_simple_non_streaming`，Windows 冷启动超过其 8 秒 AppTest 时限；不修改测试阈值。该单测随后独立复跑 **1 passed**（0.80 秒）。两个运行不能拼成“一次全量通过”，也都不是 benchmark repair rate。

## 2026-09-27 — 补充 DEV12 身份与下一版方法冻结（零模型）

旧 DEV30 既有显式异常契约仅 2/30 compile-ready，source-contract 的新独立 canary 又因 0/2 前两题可执行候选而封存。先只按冻结任务树元数据产生补充开发身份：`data/e1c_reproducer_dev12_identity.json`，固定 salt + 四仓库、每仓库三题，共 12 题；排除旧 cohort 与所有已记录独立 canary，YAML blob 身份 12/12 对应 frozen revision，公开 issue 在本机官方 test/dev parquet 中 12/12 存在且可经 strict-v5 投影。身份选择器在 `evals/e1c_reproducer_dev_selection.py`。参考 Issue2Test/e-Otter++/SWE-Tester 制定有限候选、执行反馈与无关失败过滤的下一版方案，详见 `E1C_REPRODUCER_DEV_NEXT_2026-09-27.md`。已实现最小反馈分类器 `evals/e1c_reproducer_dev_feedback.py`：普通导入/收集/超时等错误不算可信复现，断言或公开异常匹配也只算候选，不自动晋升 trusted。新旧专项 **8 passed**、Ruff clean。DEV12 永久排除未来独立 canary/Fresh30；目前 0 provider、0 official grade、0 真实新复现，尚不满足下一独立 canary 的 development gate。

## 2026-09-27 — evaluation_2 零模型入口与双盘处置边界

新建 [`E1C_CODING_AGENT_EVALUATION_2.md`](E1C_CODING_AGENT_EVALUATION_2.md) 作为旧 E1-C 之外的开发协议；`evals/e1c_evaluation_2.py` 将 DEV12 frozen identity SHA 与零模型 probe ledger 绑定，调用既有反馈分类器，仅汇总候选、永不自动晋升 trusted。专项 pytest **4 passed**、Ruff clean；没有运行真实 DEV12 probe、Docker 准入或 provider。双盘只读核对：旧盘 67.2 GiB、当前活动盘 60.9 GiB，当前 15 张镜像与 DEV12 0/12 重合；仓库证据、旧盘及当前盘镜像均未删除。旧盘应先外置归档，当前盘只可在核对 digest/引用后按精确镜像清理，活动 VHDX/Docker 内部目录不可手删。

## 2026-09-27 — Docker 缓存安全清理

按 [`DOCKER_E1C2_CACHE_CLEANUP_2026-09-27.md`](DOCKER_E1C2_CACHE_CLEANUP_2026-09-27.md) 的清单，精确移除 3 张 sealed source-contract canary + 7 张旧 CTI/CTI2 canary，全部 10/10 成功；保留旧 DEV 镜像 4 张及 Alpine。Docker 镜像逻辑占用 37.61→9.285 GB，Docker Engine/容器启动、bridge 本机 5 项测试、项目 E1-C 专项 21 项均通过。旧 VHDX 未改，活动 VHDX 仅由 Docker 正常更新、未手工删除或压缩；D: 主机空闲仍 4.56 GiB。因无 67.2 GiB 外置归档且无安全离线压缩条件，旧盘和活动盘均不删除/压缩。两个 tunnel-client 本地健康/就绪端点仍 200；App 私有连接清理前后均 `not connected`，不能声称 WebCodex 云端端到端验证成功。

## 2026-09-28 — 用户手动移除旧 VHDX 后复验

用户明确确认并自行删除旧 `.bak`。复验旧文件已不存在，活动 VHDX 完好，D: 空闲 **4.56→71.78 GiB**；Docker Client/Engine 29.4.0、Alpine 零下载容器启动、bridge 本机 5 项测试与 `docker_status()` 均通过。两个 tunnel-client 进程的本地 health/ready 均 200。App 侧连接仍返回清理前已有的 `not connected`；没有 WebCodex 云端端到端成功证据，也未为验证而中断 tunnel 做 Docker 冷重启。旧盘离线镜像缓存已永久失去，研究日志和代码不受影响。

## 2026-09-29 — evaluation_2 Docker 恢复、DEV12 官方准入与 issue-only 输入

用户重启后，Docker Desktop 4.69.0 仍在 `dockerInference` 套接字故障退出。备份设置后关闭实际生效的 `EnableInference`，只将临时 socket 目录改名留存，Engine 恢复；发现它当时指向空的 `D:\docker_related\DockerDesktopWSL`，停机后将 `CustomWslDistroDir` 指回保有镜像的 `D:\DockerDesktopData\wsl`。恢复后 12/12 image ID 与冻结导入配置摘要在线一致；原活动盘与 tunnel 配置未删除。源码身份 pilot 发现 scikit-learn-13496 和 pytest-7432 的官方 `SWE-bench` 附加提交分别改变 1168、539 个文件的权限位，但 blob 内容 0 处变化；统一守卫只允许 `100644→100755`、blob SHA 相同、base 为祖先、工作树干净。12/12 容器守卫零模型通过。

新增 `evals/e1c_evaluation_2_admission.py`，用冻结任务树 blob SHA 将官方评分材料存入 grader-only，复用锁定版本的官方日志 parser；每题每阶段独立离线容器、不可变本地 image ID、无自动重试。DEV12 一次完整准入：Base-Fail **11/12**、Gold-Pass **9/12**、两者均通过 **9/12**（scikit-learn 3/3、Marshmallow 3/3、pytest 3/3、PyVista 0/3）。PyVista-4311/3747 Gold 未过；4648 官方日志未解析，均保留在固定分母。新增 `evals/e1c_evaluation_2_issue_input.py`，从容器复制冻结 base 源码，仅下载公开 issue，按冻结 Git blob 校验；在 9 个准入任务上冻结不含测试/Gold 的生产源码窗口 **9/9**。一处普通源码窗口含 `gold` 被旧审计误挡，v2 使用任务无关的“被拦窗口跳过、补选”，未关闭审计；旧 v1 输入保留。

新增两仓库、四调用、18,000 provider-token 上限的 `evals.e1c_evaluation_2_dev_pilot`，仅执行了零调用 `preflight` 并保存 freeze，**未运行付费 `run`**，无真实 probe、trusted reproducer 或新版 official repair 成绩。专项 Ruff clean、4 passed；全量 `uv run --frozen python -X utf8 -m pytest -q` **1057 passed / 4 skipped / 33 warnings**。此数只说明代码回归。D: 空闲约 59.3 GiB。下一步必须先获得精确 `run` 命令授权，之后也只能报告 DEV probe 候选；跨仓库 trusted 与独立 canary gate 未达前不开放修复 live/Fresh30。

对 PyVista-4311 的 Gold 失败另做一次**不计正式准入、未重试原阶段**的零模型诊断：原 `eval.sh` 的 editable pip 安装在 network-none 下因 build isolation 寻找 setuptools 失败；先在新容器用本地依赖执行 `pip install --no-index --no-deps --no-build-isolation -e .` 可成功，但随后同一官方评测的 Gold 目标仍 **0/2**、P2P **1/6**。故不能仅以 pip 安装修复为由将 PyVista 晋升准入；原 9/12 统计不变。

源码守卫另做一次一次性负面容器测试：在临时容器内给 Marshmallow 生产源码追加合成内容并提交，保持工作树干净；守卫返回 **90（拒绝）**，确认权限位例外不会接受真实 blob 内容漂移。原镜像没有被修改。

## 2026-09-29 — evaluation_2 已授权 DEV probe pilot 与零调用重放

在用户对精确命令 `uv run --frozen python -X utf8 -m evals.e1c_evaluation_2_dev_pilot run` 的授权下执行一次冻结 pilot。两个已准入 DEV、每题两个输入视角，共 4 次 DeepSeek `deepseek-flash` 请求，ledger 全部完成，无重试、失败或超预算；合计 **5,606 provider tokens**，证据保存在 `.codex/e1c/evaluation_2/e1c2-dev-probe-pilot-v1/`。原运行器把四个生成候选全静态拒绝，未执行 probe，原因是本地生产包的根模块导入被窄窗口规则误挡，并把 pytest 仓库自身 `pytest` 包误判为禁止模块。原始运行结果保留，不回填改写。

修正任务无关的候选导入验证后，仅用已保存的四份响应做零 provider 调用重放：允许精确 base 工作树中可解析的生产包，继续禁止测试/危险模块和工作树漂移；执行容器改用官方 `testbed` Python，显式设置源码路径。`replay-v2` 暴露源码路径缺失，`replay-v3` 暴露误用 base Python，均保留诊断；最终 `replay-v4` 的 **3 个唯一候选全部在补丁前成功退出**，没有可重复的 prepatch failure，更没有 Gold discrimination 或 trusted reproducer。Marshmallow 候选未控制公开问题所需的 `python-dateutil` 缺失条件，pytest 候选断言了基线已经满足的行为。故当前 DEV trusted **0/12**，独立 canary、repair live、Fresh30 门槛均未开放。四次调用不是 4 个任务的修复实验，更不是 repair rate。

本轮只授权并执行上述一次付费命令；任何新 pilot/模型命令均须另行按精确命令授权。修复后的专项 Ruff **All checks passed**；全量 `uv run --frozen python -X utf8 -m pytest -q` **1058 passed / 4 skipped / 33 warnings**（47.59 秒）。这些数字仅是代码回归，不是模型修复率。

## 2026-09-29 — evaluation_2 平衡定位与下一轮反馈 pilot 零调用冻结

根据前次已保存的 DEV 失败分类，发现 `freeze_input` 将同一显式路径的前四个结构窗口全部选入，导致 issue 词法窗口被挤出。Marshmallow-1252 的旧 v2 四窗口集中在 `utils.py` 23–51 行附近；任务无关的固定交错规则（结构/词法各取候选）在新 v3 输入中保留了该文件 274–313 行的词法窗口，同时保留旧 v2 不覆盖。已在 9 个完成官方准入的 DEV 任务上生成 **9/9 v3 issue-only 输入**，未读取测试、Gold 或 grader 日志；“有窗口”仍不等于定位正确。

新增仅利用上轮原始响应及 `replay-v4` 的 `exit 0 / no_prepatch_failure` 信号的反馈提示，不向模型提供测试/Gold、grader 日志或任务 ID。冻结两题各一次调用的 `e1c2-dev-feedback-pilot-v1`：`deepseek-flash`、最多 **2 次请求 / 9,000 provider tokens**、每请求无自动重试；运行器在补丁前重复失败时仍只标候选，**不自动晋升 trusted**。零调用 `preflight` 已通过并写入 `freeze.json`，额外核对两张不可变 image ID 此刻在 Docker Engine 可查；两个被后续守卫加强取代的预检 freeze 均改名留档，未无声覆盖。provider ledger 与运行状态文件均不存在，即 **本轮新增模型调用 0**。下一次精确付费命令 `uv run --frozen python -X utf8 -m evals.e1c_evaluation_2_feedback_pilot run` 仍须用户单独授权；未运行它、独立 canary 或 Fresh30。

专项 **8 passed**、Ruff clean。全量 `uv run --frozen python -X utf8 -m pytest -q` 为 **1060 passed、4 skipped、1 failed**（171.55 秒）；唯一失败是既有 `tests/app/test_streamlit_app.py::test_app_simple_non_streaming` 在 Windows 冷启动超过 8 秒时限，未修改阈值，该单项独立复跑 **1 passed**（0.77 秒）。两次不可合并为一次全量通过，更不是修复率。

## 2026-09-29 — 获授权的 feedback pilot 一次执行及 optional-dependency 零调用判别

用户明确授权执行 `uv run --frozen python -X utf8 -m evals.e1c_evaluation_2_feedback_pilot run`，实际执行一次，退出码 **1**。Ledger 仅有 Marshmallow-1252 的 1 次 started/completed，`deepseek-flash` **2,013 provider tokens**，响应为有根据的弃答：公开 issue 限定 `python-dateutil` 未安装，而当前执行环境装有该依赖。第二题 pytest-6680 **没有发起请求**：预算守卫计算预留 4,605 tokens，高于每题 4,500 上限，在任何第二次付费调用前抛出 `ProviderBudgetExceeded`；状态封存为 `interrupted_no_auto_retry`，原命令不重跑、不抹除中断。没有 patch 或 official repair grade。

随后只用公开 issue、冻结生产窗口和前一轮已保存的模型 probe，新增任务无关的可选依赖缺失推断：只有 issue 明说依赖未安装且生产窗口出现对应 import，才在 `--network none --read-only` 容器前置只读导入阻断。Marshmallow-1252 推断 `dateutil`；零调用 DEV diagnostic-v1 得到一次 `ValidationError`，分类器保守记为 `unrelated_or_unclassified_failure`；不覆盖它，新增 diagnostic-v2 允许该类非 setup 错误重复检查，两次日志摘要一致，仍只标 `repeatable_nonsetup_failure`，不冒充可信复现。grader-only 独立 Gold 判别中，官方补丁成功应用，但同一 probe 仍因“必须有 `+00:00` 时区后缀”的更严格断言失败，`gold_discriminating=false`。该 probe **不可晋升 trusted**；Gold 内容未进入模型 prompt。当前 evaluation_2 trusted **0/12**、新版 official repair 未运行，独立 canary/Fresh30 继续关闭。

本轮新增零调用代码专项 **10 passed / 4 warnings**，Ruff clean。完整 `uv run --frozen python -X utf8 -m pytest -q` 为 **1062 passed / 4 skipped / 1 failed / 33 warnings**（184.50 秒）；唯一失败仍是 Streamlit AppTest 冷启动超过既有 8 秒时限，独立复跑 **1 passed**（0.80 秒）。未修改阈值，不能合并称一次全量通过，也不能用测试数代替 benchmark repair rate。

## 2026-09-29 — traceback DEV pilot 独立身份零调用冻结

旧 feedback-pilot-v1 状态仍为 `interrupted_no_auto_retry`，其 1 次请求与 pytest 付费前预算拒绝记录不修改、不重跑。公开 issue 显示 pytest-6680 主要请求文档更新，生产源码中的 `from_parent(config/session)` 已拒绝，旧 probe 在 base 成功退出；因此不再沿其支付另一次源码 probe。用固定的公开文本筛选（含 `Traceback:` 与明确 `*Error:` 行）扫描 9 个冻结 v3 issue-only 输入，唯一命中 Marshmallow-1359。该选择不看官方测试、Gold 或 grader 日志；官方 Base-Fail/Gold-Pass 只作为既有准入门槛核验。

新增 `evals/e1c_evaluation_2_traceback_pilot.py`，单任务、单请求、无自动重试；提示要求只断言公开 issue 的最小行为，不额外要求未声明的错误文本/格式/值。预检依照运行时预算守卫相同的提示估算公式，算出预留 **8,002 tokens**；弹性上限 `min(12,000, ceil(reserve × 1.5))`，本次为 **12,000 provider tokens**，输出上限 1,200。该上限是可花费的硬界，不是预期或已花费的额度；实际以 provider ledger 的 usage 为准。`e1c2-dev-traceback-pilot-v1/freeze.json` 已记录输入、准入、提示、runner/probe 源码与本地镜像摘要。provider ledger 与 state 均不存在，**新调用 0、trusted 0/12、official repair 0**。候选如执行仍只记重复 base 失败候选，Gold 区分需隔离的 grader-only 后处理；独立 canary/Fresh30 未开启。

验证：`uv run --frozen ruff check evals/e1c_evaluation_2_traceback_pilot.py tests/test_e1c_evaluation_2_traceback_pilot.py` 通过；相关 E1-C evaluation_2 专项 **14 passed / 4 warnings**。此轮未重跑全量代码回归；上一全量仍是 1062 passed / 4 skipped / 1 failed，单项复跑 1 passed，不能拼成一次全绿。新的付费 `run` 尚未获仓库所需的**精确命令授权**，本轮不执行。

## 2026-09-29 — 获授权 traceback pilot 与零调用 Gold 判别

用户针对上一轮列明的精确命令 `uv run --frozen python -X utf8 -m evals.e1c_evaluation_2_traceback_pilot run` 回复同意。运行前重复 preflight，冻结输入/代码/镜像身份与预算均匹配；该命令仅执行一次。`e1c2-dev-traceback-pilot-v1/provider_calls.jsonl` 记载 Marshmallow-1359 `deepseek-flash` **1 次 started/completed、3,807 provider tokens**，无自动重试、无超预算。模型生成 probe，但给出的 `issue_quote` 与公开 issue 不逐字相同，原 `state.json` 为 `candidate_rejected`；原响应和状态均不覆盖、不冒称原始成功。

后续另立零 provider 调用 `e1c2-dev-traceback-replay-v1`，只从公开 issue 自动取**唯一明确异常行**作为逐字证据引用，probe 源码仍是原响应、SHA-256 不变，不用测试源码/Gold 修补 probe。相同不可变镜像、exact-base、`--network none --pull=never --read-only` 下执行两次：两次均退出 1，日志 SHA-256 同为 `31f1b872937144ccd52250aee9ebd1f4bc4b40d3f270947d9ea07289478675ab`，末行均为 issue 原文 `AttributeError: 'List' object has no attribute 'opts'`。保守分类器仍称 `repeatable_nonsetup_failure`，不自动晋升。

隔离的 grader-only `traceback-discrimination-v1` 在同一 probe 上运行 Gold：官方 Gold 准入先前已过；本次临时容器内 `git apply --check` 和 `git apply` 成功，标记 `E1C2_GOLD_PATCH_APPLIED:PASS`，probe 退出 0、未超时，结果 `gold_discriminating=true`。Gold 材料与日志未提供给任何模型；原镜像未改变。由**公开异常逐字匹配 + 两次 base 同日志失败 + Gold 消除失败**，将 Marshmallow-1359 计为 evaluation_2 的 **1 个可信 DEV reproducer**，不是修复率，也不能与旧 source-contract 跨版本结果合并。跨仓库 ≥2 的 DEV 门槛仍缺另一仓库；后续独立 canary ≥2/3、repair live 和 Fresh30 均未开始。诊断/replay/Gold 阶段新增 provider 调用 0。

代码核验：traceback pilot/replay/Gold 与相关 evaluation_2 专项共 **16 passed / 4 warnings**，Ruff clean。完整 `uv run --frozen python -X utf8 -m pytest -q` 为 **1066 passed / 4 skipped / 1 failed / 33 warnings**（158.38 秒），唯一失败仍是 `test_app_simple_non_streaming` 在 Windows 冷启动超过 8 秒；独立复跑 **1 passed**（0.78 秒），未更改阈值，不能拼成单次全绿。新的付费实验仍需新身份及精确命令授权，旧 pilot 不重跑。

## 2026-09-29 — 跨仓库 constructor DEV pilot 零调用冻结

Marshmallow-1359 的一个可信 DEV 复现尚不足跨仓库 ≥2 门槛。只用 9 个冻结 v3 公开 issue，按任务无关的“明确要求将参数暴露在构造函数中且给出默认值”文字规则唯一选中 scikit-learn-13496；官方准入只用于入场核验，不用评分输出挑题。新增 `e1c_evaluation_2_constructor_pilot.py`：模型只读 issue 与生产源码窗口，返回独立 probe 源码；逐字 issue 引用由程序直接从公开原文提取。模型生成、容器 base 重复检查与 grader-only Gold 判别分阶段，绝不把生成当成可信复现。

已两次零调用 preflight 一致并冻结 `e1c2-dev-constructor-pilot-v1/freeze.json`：本地不可变镜像、官方 Base-Fail/Gold-Pass、输入/源码 SHA 通过；按预算守卫公式估计调用预留 **8,858 tokens**，弹性及硬上限 **12,000 provider tokens**，`deepseek-flash` 最多 1 次请求、输出上限 1,200、无自动重试。新身份的 provider ledger/state 均不存在，**本轮新增付费调用 0、可信 DEV 仍 1/12**。`uv run --frozen ruff check` 通过，相关专项 **12 passed / 4 warnings**。新精确命令 `uv run --frozen python -X utf8 -m evals.e1c_evaluation_2_constructor_pilot run` 已单独请求授权，当前未执行。

## 2026-09-29 — constructor DEV 模型响应无效、独立零调用规则 Gold 区分通过

用户对上一节列明的精确 `e1c_evaluation_2_constructor_pilot run` 回复同意。该冻结命令只运行一次：DeepSeek `deepseek-flash` **1 次 started/completed、3,889 provider tokens**，无重试。原 `response.json` 返回 `{"source":"Python probe"}`，照抄了提示里的 JSON 示例占位值，不是可执行 Python；`state.json` 为 `response_saved`，表示仅保存原响应，**绝不表示 probe 有效**。原账本、输入和响应未修改或自动重试。这次模型调用没有产生可信复现；也不能据此推断 ChatGPT 客户端安全提示与 DeepSeek 响应有因果关系。

另立 `e1c2-dev-constructor-rule-v1`，只从公开 issue 的唯一明确布尔构造参数请求和公开 import 路径自动生成行为 probe，来源明确标为 `deterministic_public_boolean_constructor_rule_not_model_response`；不使用测试源码、Gold 或人工选文件。scikit-learn-13496 的不可变 exact-base 本地镜像在 `--network none --pull=never --read-only` 中两次退出 1，日志摘要相同，均为 `TypeError: __init__() got an unexpected keyword argument 'warm_start'`。分类器仅给 `repeatable_nonsetup_failure`，没有自动晋升。

grader-only `constructor-rule-discrimination-v1` 随后核对官方 Gold 准入和同一 probe SHA，在一次性容器内应用官方 Gold，Gold 标记存在、probe 退出 **0**、未超时，`gold_discriminating=true`。Gold 补丁和执行日志未进入模型输入，原镜像未修改；此零调用规则产出计为第 **2 个跨仓库可信 DEV 补丁前复现**，与 Marshmallow-1359 一起满足 DEV 数量门槛。由于规则是在已见 DEV 上开发，**不是独立 canary、不是 patch 成功或模型端到端修复**。独立三题 canary 尚未选择/冻结；其盲态 ≥2/3 未过之前，repair live 与 Fresh30 保持关闭。新增代码专项 **2 passed / 4 warnings**、Ruff clean；未运行全量回归，上一全量仍是 1066 passed / 4 skipped / 1 failed，不能称全绿。

## 2026-09-29 — DEV12 后续通用反馈对照与 canary 方案冻结

仅在已冻结 DEV 上新增五个独立付费身份；每次精确命令、模型、调用数及低于 100,000 的硬 token 上限均在运行前向用户列明；没有自动重试，原始 response/state/ledger 不回填。账本核算如下（均为 **provider tokens，不是修复率**）：

| 身份/精确命令后缀 | 模型 | 已完成请求 | 实际 tokens | 主要结论 |
|---|---|---:|---:|---|
| `evals.e1c_evaluation_2_dev_batch_v2 run` | `deepseek-flash` | 5 | 17,720 | 原候选 3 次导入审计拒绝、1 次无显式断言、1 次 JSON 格式拒绝 |
| `evals.e1c_evaluation_2_feedback_v2 run` | `deepseek-flash` thinking | 2 | 22,803 | 两次均耗尽 8,000 输出 tokens 却无可解析最终内容 |
| `evals.e1c_evaluation_2_feedback_v3 run` | `deepseek-flash` 非 thinking | 2 | 7,349 | pytest 正当弃答；scikit-learn probe 在 base 通过 |
| `evals.e1c_evaluation_2_option_v4_pilot run` | `deepseek-flash` 非 thinking | 1 | 2,140 | pytest 候选无显式行为断言，拒绝 |
| `evals.e1c_evaluation_2_option_v5_pro run` | `deepseek-v4-pro` 非 thinking | 1 | 2,245 | pytest probe 自己调用 `warnings.warn` 制造预期告警；base 通过，不可信 |

合计 **11 次请求、52,257 tokens**；五个身份各自低于预注册硬上限，未重试，未调用 sealed TEST/Fresh30。`batch-v2` 保存响应零调用重放后，Marshmallow-1164 的 base 断言两次失败，但 grader-only Gold 下同 probe 仍失败，**Gold 不区分**；pytest-7432 无断言被拒、pytest-7985 与 scikit-learn-15086 的 probe 在 base 通过。scikit-learn-26289 的外层 JSON fence 只作通用解析诊断：尽管 base 可失败，使用的数组与公开 issue 要求的输入形态不符，异常也不对题，未晋升可信。`feedback-v3` 的 pytest-7985 因源码窗口缺 `--strict` 实现而弃答，后按公开选项字符串为定位器加任务无关的精确 CLI option 加权，9/9 已准入 DEV 形成新 v4 issue-only 输入；只有该题候选窗口改变，旧 v3 不覆盖。v5 的自造告警使静态候选审计新增 `warnings.warn` 禁止规则，并补回归；旧执行结果保持 `base_pass` 不改写。

固定 DEV12 官方准入仍为 **Base-Fail 11/12、Gold-Pass 9/12、双门槛 9/12**。可信补丁前复现仍仅 **Marshmallow-1359 与 scikit-learn-13496，2/12、跨 2 仓库**：前者保存模型 probe，后者确定性公开构造参数规则；新 11 次付费请求没有新增 trusted。此数只是开发数量门槛，不是同一机制的泛化、自动修复或 30/30。新版 official repair 未运行。

逐项固定分母核算（Base/Gold 仅列独立 grader 的准入布尔值；失败原因不向模型回传）：

| DEV12 任务 | Base / Gold 准入 | 补丁前复现结论及原因 |
|---|---|---|
| PyVista-4311 | 过 / 未过 | Gold 目标仍 0/2，未进入可信 probe |
| PyVista-4648 | 未过 / 未过 | 官方日志两阶段均不可解析，未进入可信 probe |
| PyVista-3747 | 过 / 未过 | Gold 目标仍 0/1，未进入可信 probe |
| scikit-learn-13496 | 过 / 过 | **trusted**：公开布尔构造参数规则；base 两次同错、Gold 消除 |
| scikit-learn-26289 | 过 / 过 | 模型输出需通用 JSON fence 解析；probe 输入形态偏离公开 issue，异常不对题，拒绝晋升 |
| scikit-learn-15086 | 过 / 过 | 两轮 probe 在 base 均通过，无补丁前故障 |
| Marshmallow-1252 | 过 / 过 | 可选依赖隔离后 base 故障可重复，但 Gold 后 probe 仍因过严时区断言失败 |
| Marshmallow-1359 | 过 / 过 | **trusted**：保存模型 probe、公开异常逐字引用；base 两次同错、Gold 消除 |
| Marshmallow-1164 | 过 / 过 | base 断言两次失败，但 Gold 后仍失败，不区分 |
| pytest-7432 | 过 / 过 | 生成候选无显式行为断言，静态拒绝 |
| pytest-6680 | 过 / 过 | 公开 issue 主要为文档变更，既有生产源码 probe 在 base 通过；未继续付费 |
| pytest-7985 | 过 / 过 | 旧定位漏 `--strict` 定义，新定位补入；新候选无断言或自造预期告警，均不可信 |

只冻结[不重叠 canary 预注册方案](E1C_EVALUATION_2_CANARY_PREREG_2026-09-29.md)，文件 SHA-256 `6c7c987985cc3a532e30f4cbbaa154600f793fcc528b952af74ef4636cb21c29`：固定元数据池、旧 cohort/canary 与 DEV12 排除源、盐及三个不同仓库的选择算法、固定分母、盲态 ≥2/3 和失败停机；**未选择 ID、未读新任务内容、未运行 canary**。完整方法/模型配置尚待身份选择前另外封存，故这不是 canary 已通过或 sealed TEST/Fresh30 的入场许可。本轮停止于方案，不再开新付费实验。

最新专项 `uv run --frozen pytest -q tests/test_e1c_evaluation_2_probe.py tests/test_e1c_blind_evidence.py` **13 passed**；`uv run --frozen ruff check evals/e1c_evaluation_2_probe.py tests/test_e1c_evaluation_2_probe.py` 通过。最终完整 `uv run --frozen python -X utf8 -m pytest -q` **1079 passed / 4 skipped / 33 warnings**（50.63 秒），此次为单次全量通过；这是代码回归，不是 benchmark 修复率。

## 2026-09-29 — 统一 DEV 公开 issue 生成与离线 Gold 判别（本轮停在 DEV）

本轮沿用冻结 DEV12 与 9 条双门槛准入任务，不改变旧 trial 身份。新增统一 `e1c_evaluation_2_unified_dev_v1`：固定公开 issue + exact-base 生产源码窗口，按统一提示生成行为 probe；明确的布尔构造参数走任务无关确定性规则，其余 8 条各最多一次模型请求。生成器不读取官方测试断言、Gold 补丁或 grader 日志；执行仅用已验本地镜像，`--network none --pull=never`，base 失败重复两次，不把单纯异常算成可信。v1 在用户后来提出 Flash-only 要求**之前**执行，`deepseek-v4-pro` 非 thinking 8 次、**24,699 provider tokens**；运行前列出的弹性硬上限 **79,285**，未重试。v1 主要是严格提示导致弃答/静态拒绝，未新增 trusted；原账本、响应与状态封存于 `.codex/e1c/evaluation_2/e1c2-unified-dev-v1/`，不覆盖。

仅在已见 DEV 上把提示改为允许补齐缺失的最小合成合法 fixture，但期望行为仍须来自公开 issue；候选静态审计只新增允许无害标准库 `datetime`。另立冻结身份 `e1c2-unified-dev-v2-flash`，模型按用户新偏好改为 `deepseek-flash`，命令 `uv run --frozen python -X utf8 -m evals.e1c_evaluation_2_unified_dev_v2 run` 在运行前列明：最多 **8 请求**、估计预留 **65,476**、弹性硬上限 **81,845 provider tokens**（配置绝对上限 90,000）、无自动重试。实际 **8 请求、25,645 tokens**，无超预算；源、输入、镜像、提示与预算冻结于 `.codex/e1c/evaluation_2/e1c2-unified-dev-v2-flash/freeze.json`。两版本轮合计 **16 请求、50,344 provider tokens**，不得与上一节五轮的 11 请求/52,257 tokens 混成单一身份。

v2 有 **7 个两次同日志 base 失败信号**（其中 1 个确定性规则、6 个模型 probe），1 个 base 通过、1 个静态拒绝。`evals.e1c_evaluation_2_unified_dev_v2_gold run` 在隔离的 grader-only 目录，对全部 7 个信号在同一 probe 上应用官方 Gold；补丁应用标记 7/7，Gold 消除失败 **3/7**，其余 **4/7** 不能晋升。该判别没有模型请求，结果在 `.codex/e1c/evaluation_2/grader-only/unified-dev-v2-discrimination/`，Gold 内容和运行日志没有回流生成器。逐项核算如下，固定 DEV12 分母不改变：

| DEV 任务 | v2 公开 issue probe 与离线判别 | 可信复现审计 |
|---|---|---|
| PyVista-4311、4648、3747 | 官方双门槛未过，均不生成 | 0/3，保留原分母与原因 |
| scikit-learn-13496 | 确定性布尔构造规则；两次相同 `warm_start` TypeError，Gold 退出 0 | **可信**；旧 DEV 项在统一流程重复确认，不是新的模型产物 |
| scikit-learn-26289 | 两次失败，但 Gold 仍退出 1 | 不可信：异常来自输入类型约束，偏离公开 issue 所述故障 |
| scikit-learn-15086 | base 退出 0 | 不可信：没有补丁前失败 |
| Marshmallow-1252 | 模型 probe；只按公开 issue 所写“未安装 `python-dateutil`”隔离可选导入；两次相同 `ValidationError: Not a valid datetime`，Gold 退出 0 | **新可信 DEV 复现**：公开问题正是结尾 `Z` 的有效 ISO8601 字符串被拒。probe 还断言一个具体 naive datetime 值，比问题陈述更细；它没有导致 base 失败且 Gold 下也通过，后续泛化时应避免这种附加断言 |
| Marshmallow-1359 | 模型 probe；两次相同公开 issue 中的 `List.opts` AttributeError，Gold 退出 0 | **可信**；旧 DEV 项在统一流程重复确认 |
| Marshmallow-1164 | 两次断言失败，Gold 仍退出 1 | 不可信：probe 把返回包装对象直接与字典比较 |
| pytest-7432 | 候选无显式行为断言，静态拒绝 | 不可信：未执行 probe |
| pytest-6680 | 两次 fixture AttributeError，Gold 仍退出 1 | 不可信：自造父对象缺 `.session`，是 fixture 错误 |
| pytest-7985 | 两次 `DID NOT WARN`，Gold 仍退出 1 | 不可信：该断言不是 Gold 能消除的 issue witness |

当前**唯一可信 DEV 补丁前复现为 3/12、跨 2 仓库**，其中 2 个模型生成、1 个确定性规则；它们只证明在见过的开发任务上有可区分的复现，**不证明统一机制在新任务泛化，更不是 Agent 修复率或 30/30**。v2 原 `state.json` 的 `trusted_reproducer_count=0` 是生成阶段的保守字段；本节的 3 个结论来自事后独立 Gold 与公开 issue 语义审计，不回填原始模型运行状态。没有运行新版 official repair。专项 10 passed、Ruff clean；单次全量 `uv run --frozen python -X utf8 -m pytest -q` 为 **1080 passed / 4 skipped / 33 warnings**（48.44 秒），只代表代码回归。

本轮按用户最新边界到此停止：**不选、不读、不运行预注册 canary**，也不打开 sealed TEST/Fresh30、不测试漏洞利用、不访问生产系统。下一轮如要推进 canary，先锁定从本轮 DEV 反馈修订后的完整定位、生成、分类、预算及停机协议，再按已写的非重叠预注册方案一次盲态运行；若失败则封存、回 DEV 修改，不能在见过的 canary 上补规则后仍称它独立。

## 2026-09-29 — canary 方法先冻结、元数据选题与直连镜像交接

在任何新任务正文被读取前，固定[方法协议](E1C2_CANARY_METHOD_FREEZE_2026-09-29.md)及代码/提示摘要；`data/e1c_evaluation_2_canary_method_freeze.json` SHA-256 为 `e78f9670cf009596ef9f31f9aba5f04685be5c133c9cc3558a2f0e3598847013`。统一 DEV v2 的公开 issue + 生产源码提示、确定性布尔构造规则、静态审计、重复 base 故障与 grader-only Gold 区分沿用，不按 canary 结果补规则。`deepseek-flash` 非 thinking，最多三题各一次请求，单题上限 14,000、整批硬上限 **42,000 provider tokens**，输出单次最多 2,600，无自动重试；截至本节真实 canary 调用 **0**。

随后对固定元数据池、污染账本和 DEV12 身份核对原预注册 SHA，另扫描已有 `data/` 与 `.codex/e1c/` cohort/canary 身份文件并记录每份摘要，不读取候选正文或结果。按固定盐先排序仓库、再排序实例，固定独立三题：`scikit-learn__scikit-learn-10581`、`marshmallow-code__marshmallow-1702`、`sphinx-doc__sphinx-10320`。`data/e1c_evaluation_2_canary_identity.json` SHA-256 `d078af8c0ba6da3c2a8945db4ab0461fd729bb2658c418eb8576be334d4f9551`；本批固定分母 3，不因环境/结果替换。官方冻结 `task.yaml` 元数据 3/3 核对；Docker Hub 官方 manifest 仅小型元数据经本机 7892 获取，与显式空代理的 `docker.1panel.live` 直连 manifest 3/3 顶层及 linux/amd64 摘要一致。传输记录 SHA-256 `9f891c05723ceb6b6e7cb0d33a096d1fe8ea0ccb6d09d3e98423c3de6d5a60`。三张压缩层标称 **1.42 + 0.93 + 1.02 ≈ 3.37 GiB**；这不是实际磁盘增量或下载时间保证。

镜像获取代码只对已核官方摘要下载直连镜像站 blob，显式 `ProxyHandler({})` 不使用系统 HTTP 代理；逐层核验 size/SHA-256、解压 diff-id 与导入后 image ID。最初由本机启动第一张，但用户选择自己在终端下载，已发 Ctrl+C 并确认无本机下载进程；只留下第一张一个 **4,194,304 字节 `.partial`**，完整层可复用，当前 0/3 镜像导入完成。该直连代码不能排除 OS 级 VPN/TUN 路由；现场 `Test-NetConnection docker.1panel.live -Port 443` 显示 `InterfaceAlias: WLAN`，用户应在下载时自行再查。镜像下载、exact-base、官方 Base/Gold 准入、公开 issue 投影、付费 canary 与修复实验均未完成；sealed TEST/Fresh30 未打开。直连下载器专项 **6 passed**、Ruff clean；全量回归仍以上节 1080 passed / 4 skipped 为准，本节未重跑全量。

## 2026-09-29 — 独立 canary v1 盲态执行与负结果封存

用户终端完成三张镜像下载后，本机核对 3/3 官方不可变 image ID，零模型官方 Base/Gold 双准入 2/3。Sphinx-10320 的官方镜像 `/testbed` 存在未提交 `tox.ini` 修改，固定源码身份守卫返回 90；保留在三题分母中，不改变守卫或替换任务。另两题完成 exact-base 干净生产源码物化与公开 issue-only v4 输入，每题四个自动源码窗口；未将官方测试/Gold/评分日志输入模型。为适配官方 GitHub raw 文件传输中断，仅将 grader-only blob 获取改为官方 Contents API 且仍核验 Git blob SHA，不修改冻结模型方法。专项 2 passed；全量回归 **1083 passed / 4 skipped**。

冻结 live 命令 `uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_canary_live run`，`deepseek-flash` 最多两请求、预留 15,161、整批硬上限 42,000 provider tokens、SDK 零重试。实际两请求共 **5,755 provider tokens**，无超限。scikit-learn-10581 的 probe 与公开 issue 的 `ElasticNet` 输入复制行为一致，补丁前两次同日志断言失败；评分侧同一 probe 在 Gold 成功应用后退出 0，语义核对后计 1 个可信复现。Marshmallow-1702 对公开 RFC 缺少明确断言行为选择弃答，未运行 probe。Gold 判别 1/1 可执行候选成功，但不得写成总成绩；Sphinx 未进入生成。

固定分母可信 **1/3 < 预注册 2/3**，独立 canary v1 标记 `sealed_negative_below_preregistered_threshold`。本批不得按失败反馈调规则、重跑后仍称独立；新版 official repair、sealed TEST/C5、Fresh30 保持关闭。完整任务表、账本与摘要见[单独结果页](E1C2_INDEPENDENT_CANARY_V1_RESULT_2026-09-29.md)。下一步只能在旧 DEV 或其他非本批材料上改进通用方法，另冻结并选择不重叠的新盲态 canary。

## 2026-09-30 — 旧 DEV 通用方法 v3/v4 对照与第二批 canary 冻结

不改写首批独立 canary。旧 DEV12 的 9 条官方双准入任务中，另立 v3 Flash 身份 `e1c2-unified-dev-v3-flash`，全部原位运行，最多 8 请求、弹性上限 82,577、配置硬上限 90,000 provider tokens，实际 **8 请求／27,696 tokens**，无重试。3 个重复补丁前失败在 grader-only Gold 下消失，但两个模型 probe 引入了公开 issue 未要求的返回值／内部属性断言；因此只记候选，不把 v3 宣称为高质量新方法。原账本、候选和判别记录保留，不覆盖。

针对旧 DEV 上的通用“API 应成功却抛异常”表达缺陷，新 v4 提示区别公开 issue 明确给出的返回值与只要求调用完成的行为：后者仅在真实 API 调用之后设置到达标记并断言，不编造额外属性、结果或错误。全部 9 条双准入 DEV 再按同一流程运行，命令 `uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_unified_dev_v4 run`；模型 `deepseek-flash`、最多 8 请求、预留 66,268、弹性上限 82,835、配置硬上限 90,000 provider tokens、无重试。实际 **8 请求／25,424 tokens**，5 个重复 base 失败候选中 4 个 grader-only Gold 消除；公开 issue 审核后分别为 scikit-learn-13496、scikit-learn-26289、Marshmallow-1252、Marshmallow-1359，**DEV 可信 4/12、跨 2 仓库**。scikit-learn-26289 的 NumPy 数组 `feature_names` 与公开输入类型一致，Gold 消除原异常；Marshmallow 两题均不再附加未陈述的值断言。这仍是已见 DEV 的方法选择证据，不是独立泛化或自动修复。v3/v4 合计 16 请求／53,120 provider tokens，为两个身份之和，不能当作单轮成绩。

在读取任何第二批任务正文前，冻结[完整方法与预算](E1C2_CANARY_V2_METHOD_FREEZE_2026-09-30.md)，方法文件 SHA-256 `fd58671dcdb923e70b7f018362682802849c54651655e21d051828e1d6f4d14b`；再按固定盐和全部历史排除源只用元数据选出 Seaborn-2846、Marshmallow-1343、pytest-8861，身份 SHA-256 `a22311ffc4dd41c379e839e5618bccb35164367b35b9a3797bf5f17bb3dba997`。3/3 官方 `task.yaml` 小型元数据直连核对，DEV12 和首批 canary 重叠均为 0。新方法保持三题固定分母、≥2/3、`deepseek-flash`、每题一次／14,000、整批 42,000 provider tokens、零重试。

新传输代码对 urllib 显式禁用代理；官方 Docker Hub 认证端点直连在 TLS 握手被重置，Docker Hub 另一个官方 Hub API 域名直连也超时。**官方/镜像站摘要比较尚未完成，未生成 transport seal、镜像 0/3、新 issue/Gold 未读、第二批模型调用 0。** 直连镜像站单独显示三张压缩层约 2.93 GiB，只供容量/时间估算，不充当权威镜像身份。用户要求自己下载且不走 VPN/代理，已准备[含前置摘要门槛、逐层速度/ETA、导入心跳、日志与续传的终端命令](E1C2_CANARY_V2_DIRECT_DOWNLOAD_HANDOFF_2026-09-30.md)；前置直连失败将停在下载前。D: 当前约 42.9 GiB 空闲。新增专项 **3 passed**、Ruff clean；完整回归 **1083 passed／4 skipped／1 failed**，失败是已知 Streamlit 冷启动 8 秒超时，单项独立复跑 **1 passed**，不可合并成一次全绿。sealed TEST/C5、Fresh30 与新版 repair live 均未运行。

## 2026-09-30 — 文档入口重整与安全发布

按用户请求，先保存907个待提交文件的哈希清单，再逐字节复制两份roadmap、研究README和旧交接；四份历史快照均核对SHA。新入口分别负责项目总览、当前执行路线、导航与WebCodex交接；逐轮过程继续只追加本续档。新增一周计划，以行为合同保真和受限反馈为待验证假设，保留30/30目标但不承诺未知实验必然成功。

核对DEV v4的4/12口径：4个Gold可区分结果还叠加了人工issue语义审核；机器trusted字段没有回填。canary v1负结果1/3保持封存，v2的14份方法文件SHA匹配，当前仍阻塞官方摘要直连reset/timeout，0新模型调用；无repair/C5/Fresh30运行。

本次零模型验证：指定Ruff通过；专项18 passed；完整pytest一次1084 passed / 4 skipped / 33 warnings / 0 failed（53.96秒）。独立V3 compact preflight暴露Windows非UTF-8子进程输出的解码错误及后续stdout=None错误，保留失败。全仓Ruff另检发现2225条既有风格/导入问题，未批量改写冻结源码来造绿。不能宣称全部CI检查已通过。

发布采用精确路径清单、敏感格式/原始任务字段扫描与字节身份保护；sealed spec和含原题面的旧DEV输入保留本地，不发布密钥或原始容器材料。GitHub直连超时后，仅对Git命令使用现有本地代理；Docker、WSL、数据盘和tunnel设置不变。完整保全和验证说明见[重整记录](WORKSPACE_REORGANIZATION_2026-09-30.md)，下一工作见[当前Roadmap](../PROGRESS_RESEARCH_ROADMAP_2.md)与[一周计划](E1C2_ONE_WEEK_PLAN_2026-09-30.md)。

## 2026-10-05 — 旧 DEV 结构审计、回归与 canary v2 基础设施复核

本轮未修改第二批 canary 的 14 个冻结方法文件，逐文件 SHA-256 再核均匹配。沿用用户此前给出的精确零模型 `evals.e1c_evaluation_2_canary_v2_stage transport` 命令复试：`auth.docker.io` TLS 握手仍报 `WinError 10054`；未产生 `image_transport.json`，未下载第二批大文件，模型调用 0。Docker Linux engine 管道不存在；只尝试启动已安装的 Docker Desktop，服务仍停止；当前会话 `Start-Service com.docker.service` 因无权限失败。没有调整代理/VPN、镜像、WSL、VHDX 或 tunnel。

只在旧 DEV 的已保存 v4 公共 issue 输入与候选源码上新增独立零调用形态审计 `evals.e1c_evaluation_2_contract_dev`：核对输入/源码摘要与逐字 issue span，并用 AST 区分真实调用后到达标记、值比较、吞异常及不受支持断言。9 条固定 DEV 记录为 3 个调用后标记、1 个值比较、1 个吞异常、2 个不受支持断言、2 个无候选；这些类别只说明代码结构，**9/9 的语义状态均为未验证**，不替换原人工语义审核或 Gold 判别，不提升 4/12 可信数，也不宣称自动修复。模块不读取官方测试或 Gold，不触碰现有冻结身份。相关专项 12 passed，新增文件 Ruff clean。

规定的 V3 重点 Ruff 通过、18 项重点 pytest 通过、`evals.v3_compact_pilot preflight` 返回 `ready=true`。全仓 `uv run --frozen --offline pytest -q` 首轮为 **1085 passed / 4 skipped / 1 failed**：Windows 缺 `-X utf8`，既有 admission 测试在调用 Docker 前按原守卫拒绝。按该环境条件完整重跑 `uv run --frozen --offline python -X utf8 -m pytest -q`，单次 **1086 passed / 4 skipped / 33 warnings / 0 failed**（49.94 秒）。这是工程回归而非复现、补丁或 official resolved 成绩。下一门槛仍是官方摘要直连、用户终端镜像下载、本机 Docker 正常运行，再原协议零模型准入；不能跨过阻塞直接付费或打开 sealed TEST/C5/Fresh30。

## 2026-10-05 — Docker 本机运行时恢复，官方摘要直连仍阻塞

用户终端 `docker version` 显示 Linux engine 管道不存在，随后手工继续执行 `transport` 命令，官方 Docker Hub 认证在 TLS 握手处 `WinError 10054`；手工再输入 `download` 不会绕过前置传输 seal。现场没有 `image_transport.json` 或第二批 `acquire/`，无大文件下载。

本机诊断定位 Docker backend 无法移除旧 AF_UNIX `dockerInference` socket（Windows 错误 1920）。完全停止 Docker 后，单文件改名同样被系统拒绝。核对两个运行时目录只含旧零字节 reparse-point socket，再将 `%LOCALAPPDATA%\Docker\run` 和 `%LOCALAPPDATA%\docker-secrets-engine` 分别改名为带日期的同目录备份；原文件保留、未删除。一次启动又留下新 socket，随后用 `docker desktop stop` 正常退出，将两个新运行时目录在同一次重启前再次备份，再用 `docker desktop start` 启动。没有改 WSL/VHDX、镜像或 tunnel 配置。此恢复方式与 [Docker 公开问题报告](https://github.com/docker/desktop-feedback/issues/460)描述的相同故障形态一致，但本机原因仍以自己的 backend 日志为证。

恢复核验：`docker desktop status=running`，`docker version` 服务端 **29.4.0**，Linux/overlay2，原 DEV12 获取账本的 **12/12 不可变 image ID** 均可 `docker image inspect`。本机另有 20 张镜像记录；未做全局清理。恢复后只再次运行用户指定的零模型 `transport`，官方 `auth.docker.io` 直连仍 `WinError 10054`，因此第二批 canary 保持 **0/3 镜像、0 模型调用**。下一步需用户在无 VPN/TUN 的可达网络上完成官方小型摘要核验，成功后才由用户终端按既有直连命令下载大文件；Docker/tunnel 端到端联通仍需单独验证。

## 2026-10-05 — 官方小型元数据代理修订冻结，三张镜像摘要门槛通过

用户换网仍直连超时后，明确允许仅小型官方元数据使用本机 7892。新增独立基础设施入口 `evals.e1c_evaluation_2_canary_v2_metadata_proxy`，新执行身份 `e1c2-canary-v2-metadata-proxy-v1`；原 14 份方法文件、选择身份和 direct-only 失败目录全部保留。此为选题后、读取新题正文/源码/Gold/结果前的基础设施修订，继续原三题固定分母；不宣称重抽了一批独立样本。修订文件 `data/e1c_evaluation_2_canary_v2_transport_amendment.json` SHA-256 **7afba65fcddc8d94f0b576e901f770daec77d5303f77397777ccad4246a38b85**，在任何代理元数据请求前写入并封存新源码/协议及镜像导入依赖摘要。

代理客户端只允许 HTTPS 官方 token/manifest 地址，最多 9 请求、每响应 200,000 字节、累计正文 2,000,000 字节，禁止跳转/自动重试和 blob URL，令牌仅存在内存。镜像站 manifest 仍空代理直连。冻结后执行 `uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_canary_v2_metadata_proxy transport`，**3/3 顶层/linux-amd64 摘要、层数量和压缩字节完全一致**；官方实际 **6 请求、26,333 正文字节**，镜像站正文 9,528 字节，blob/image pull/provider call 均 0。新 seal 位于 `.codex/e1c/evaluation_2/canary-v2-metadata-proxy-v1/image_transport.json`，SHA-256 **9634eacb4e893cac0131c6f167b3b341ba83cb8b6b768dec42bed6e58bdb002e**。三张已核官方压缩层总量 **3,148,086,127 字节 / 2.932 GiB**；D: 约42.9 GiB空闲，解压和归档占用仍须逐张守卫。

大文件未运行，用户关闭 VPN 全局/TUN 后在终端运行新模块 `download --timeout-per-image 21600`。下载只消费缓存 seal，不再请求官方 registry；复用直连镜像站的逐层进度、Range 续传、SHA/大小/diff-id/image-ID校验、磁盘守卫和导入心跳。新入口先检查 Docker engine。后续 `admit/public` 共用新产物目录；修订绑定的 live adapter/执行 freeze 尚待准入后实现，不能直接套原 `canary_v2_live`。新题面、评分文件、模型、sealed TEST/C5/Fresh30 均未打开。

验证：新传输与既有隔离/镜像专项 **14 passed**，规定重点 **18 passed**，指定 Ruff 全过。V3 preflight 带 `-X utf8` 的额外调用出现既有 Windows 子进程 UTF-8 解码/`stdout=None` 错误；按仓库规定 `uv run --frozen --offline python -m evals.v3_compact_pilot preflight` 完整运行返回 `ready=true`，分别保留两条命令结论。全仓 `uv run --frozen --offline python -X utf8 -m pytest -q` 单次 **1091 passed / 4 skipped / 33 warnings / 0 failed**（52.00 秒），只算工程回归。最新状态、下载命令和 WebCodex 交接已同步更新。
