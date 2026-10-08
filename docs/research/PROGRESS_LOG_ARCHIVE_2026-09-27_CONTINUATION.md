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

## 2026-10-05 — 第二批镜像/官方准入完成，Flash三题一次执行可信0/3封存

用户终端返回 `verified_loaded=3` 后，本机用原transport/loaded链核对不可变image ID 3/3；执行新修订入口 `admit --timeout 900`，六项离线官方Base/Gold全部通过，固定三题均双准入。Seaborn FAIL_TO_PASS 3个base明确失败/Gold全部过，原47测试保持；Marshmallow目标1个、原24；pytest目标1个、原127。随后 `public` 按原v4自动物化三条公开issue与exact-base干净生产源码，各四个窗口。模型输入与grader路径隔离，未人工选文件或读取Gold正文。

新增live/Gold桥接适配器只绑定原v4方法和新基础设施目录，原14份方法文件摘要保持。初始专项暴露导入时共享runner覆盖v1提示的副作用，改为延迟加载后同项8 passed；没改旧提示或削弱断言。指定Ruff、18重点tests、V3原命令preflight均通过；全仓单次 **1093 passed / 4 skipped / 33 warnings**（70.29秒）。导入Gold适配器后计算的preflight与独立live原freeze完全相同，避免模块导入顺序漂移。

新身份 `e1c2-independent-canary-v2-metadata-proxy-v1-flash` 的live freeze SHA **5b3c8bb508019adb2fd33f32511d9d16f3bebc8cb5979e69e2cc7f4871c1004f**，预留27,760、最多3请求/42,000 tokens、单题14,000、单次输出2,600、Flash非thinking、temperature0、SDK零重试。按用户此前每个≤100,000tokens实验先列精确命令无需再确认的明确授权，源码先提交 `272f841`，再执行 `uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_canary_v2_proxy_live run` 一次；真实完成3请求，共 **13,783 provider tokens**。没有失败请求或重试。只保存请求模型alias和response/usage，返回具体模型版本没有完整记录，不补写版本声明。

固定逐题：Seaborn-2846 7,010tokens，回显输入/源码耗尽2,600输出，未形成可解析source JSON，原解析器拒绝；Marshmallow-1343 3,678tokens，唯一执行候选base两次同错，独立Gold成功应用后仍退出1，原因是构造validator引用不存在字段，不能晋升；pytest-8861 3,095tokens，明确因相关生产窗口不足而abstain，原runner统一记candidate_rejected，审计报告另列弃答，原state不回填。独立Gold命令 `uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_canary_v2_proxy_gold`，attempted1、gold_discriminating0，零模型调用。

固定分母可信 **0/3 < 2/3**，新增终结摘要/data结果/报告标记 `sealed_negative_below_preregistered_threshold`。ledger SHA **4fab3c9a61671094b3e0d71bea298fd2f50d3bcd2788457f3b66f00f3c047c94**，原state SHA **5c79a826d72c533619d73593269f6acef20721af3761cd22895dbc0b98e30124**，Gold结果SHA **bb4fb3eb46021c819a85d559d49f501a122152a8133a6eb7adc01fcf14f96241**；原response/ledger/state/输入/日志和历史metadata-only摘要全部保留。新版Agent repair、sealed TEST/C5/Fresh30未运行。详细结果见[E1C2_CANARY_V2_AMENDED_RESULT_2026-10-05.md](E1C2_CANARY_V2_AMENDED_RESULT_2026-10-05.md)。下一步回旧DEV做响应分账、固定行为合同/fixture正对照和自动窗口覆盖核验；不在本三题重跑后重称独立，取得同预算增益再冻新方法和不重叠canary。

## 2026-10-05 — 旧DEV合同A/B、source-contract与评分前控制器研究

按用户已有“单实验≤100,000tokens先列命令/模型/次数/预算无需重确认”权限，仅在旧DEV、Flash非thinking下运行新身份；未重试旧失败或使用canary调参。源码先提交7192071、c23f702、0a58b9c。A/B v1 A九请求19,256tokens、Gold3/12；B第8请求SDK `LengthFinishReasonError`处理失败，中断保留（七完成16,344、错误携带4,281usage），第9未调用。部分Gold零调用只评分已完成prefix1/12，不伪装公平完整对照。v2统一生产覆盖/raw JSON计量，A/B各九请求17,545/19,253tokens、各Gold1/12，未优于基线。生产文件真实import/AST构造重分期的零调用source-contract回放A/B各2/12；回放与后验策略开发不算新模型或独立成绩。

新prospective hybrid-v1优先B正对照，按评分前base失败锁定，最多一次A回退，15请求29,864tokens；Gold3/12，日期基线缺失，原preservation gate失败原样留存。controller v2将原call_completes合同贯穿A回退，严格AST结构证明时取消未经合同支持的额外返回值oracle（value_relation不弱化）；全部九条旧DEV缓存重放、零调用，Gold4/12，人工语义审查四条跨2仓库，机器trusted保持false。历史v4也4/12，不称超过基线或因果增益。开发gate另立数据SHA，无原件覆盖。累计本组102,262完成tokens+错误4,281可见usage=106,543，50开始/49完成/1SDK处理失败，零自动重试；加本日旧canary13,783=120,326，非账单核验。

实现最小复用：原冻结14文件不改，新source-contract/预算/controller外围适配；newmethod先冻结，再选独立canary。完整[结果与限制](E1C2_DEV_CONTRACT_STUDIES_2026-10-05.md)。审计更正：旧canary ledger实际记录`response_model=deepseek-flash` alias，缺的是不可变版本snapshot；旧公开JSON字段过宽，在新报告追加更正，不改sealed原件/0/3分数。

## 2026-10-05 — 新hybrid canary v3方法/身份/小型传输门槛封板

提交de55874后`freeze-method`，methodSHA **978a0b86ba70f7cf9c7fd9add3a123c682202afb73d401ade4cb15b3c2bc7a44**，包含完整controller/source合同/行为oracle/预算/生成评分链文件SHA。随后metadata-only盐选Flask-5063、PyVista-4226、SymPy-17150，排除DEV/旧canary/历史身份，固定3、无替补；identitySHA **62649edc20998fad8f101a488ccbb22e0dff6343bf81a0fc3398e5fed5d1500d**。历史身份扫描耗时；一次重复启动的零模型selector在写入前终止，最终只一份身份，无重抽、无题面/评分读取。过早metadata命令因identity不存在退出，稍后正确读取官方task.yaml，失败无模型/镜像调用。

新`transport`官方token/manifest按许可7892，7请求/26,299正文bytes，镜像站直连，三题官方/mirror顶层/amd64摘要3/3完全一致。transportSHA **a3c28931a11f26d6e3d09ae7e18f9652d072749a99ae363bc53e9977a76adfa9**，压缩层总4,575,379,722bytes≈4.261GiB，blob/image pull/provider均0；大文件由用户终端下载。新批整批60000、每题20000、≤6请求/每题2、输出3000、Flash非thinking，SDK零重试。下一步下载→离线官方双准入→公开输入→preflight→报告精确run→独立Gold/语义审核；≥2/3才另冻Agent repair，否则负结果封存。

Docker现场Server29.4.0/Dfree42.77GiB，未改配置、清镜像或操作VHD/tunnel。全仓单次1115passed/4skipped/33warnings/0failed（50.61秒），指定重点18passed/Ruff全过/V3规定原preflight退出0；是工程回归不是修复率。两份roadmap/接手入口改为新canary下载，过程仅在此集中追加。所有旧失败、账本、原响应和冻结身份保留；新canary正文、sealed TEST/C5/Fresh30尚未打开。

## 2026-10-05 — 独立hybrid canary v3一次完成，可信1/3封存

用户续做时发现三份loaded.json均已就绪，验证全部official-bound不可变image ID，不重新下载。执行冻结入口`admit --timeout 900`六项离线评分：Flask/SymPy双通过，PyVista Base有效官方日志但25目标无明确fail/pass，Gold过仍不双准入；保留固定分母3、不换题。`public`仅两题按原规则生产窗口物化；`preflight`冻现场4请求/60000tokens，首轮reserve15031。原36文件/方法/身份SHA不变。

按用户已有授权先列精确`hybrid_canary_v3 run`/Flash/4请求/60000，再执行一次：3请求7280tokens（Flask5366，SymPy1914），完成无失败/重试。Flask B弃答，A无关subdomain匹配失败；SymPy B按issue log值关系稳定base失败。独立`gold`一真一假，人工语义审核可信1/3<2/3，机器trusted保持0/false。新增公共结果e234a14封存，原ledger/state/响应与transport收据不回填；不启动repair/TEST/C5/Fresh30。完整[报告](E1C2_HYBRID_CANARY_V3_RESULT_2026-10-05.md)。PyVista issue未物化、未调用；不把基础设施失败说成模型失败。

## 2026-10-05 — 弃答STOP/路径锚点旧DEV v3，一次新生成3/12，开发门槛未达

另立旧DEV版本，不修改canary：显式B弃答停止task、不触发A；公开issue准确生产路径/行号优先窗口，无taskID表。合成专项首次暴露测试路径拒绝异常冒泡，修复只catch边界异常先拒绝后跳过，未读测试、未弱化断言。专项7passed，源码/protocol先提交e234a14。preflight9题固定12、最多18请求/80000tokens、单题20000/输出3000/零重试，reserve61231，freezeSHA87926c7d86e59b9d2b4a509d4986772de36d596a4cecb87d34dde35fe0cade66。

先展示精确`hybrid_dev_v3 run`/Flash/18/80000，再一次执行9题、12请求24712tokens，无provider失败/重试；3明确弃答均不调用A。零调用独立`gold`评5候选，3区分（ctor/date/inner DateTime），dtype fixture与generator两候选Gold仍失败。经issue语义审核可信3/12，机器trusted不回填，缺四条参考中的dtype，开发gate失败。与原fresh hybrid-v1同3/12但任务不同，少3请求/5152tokens，只作描述、不称因果或新SOTA，不能拼接缓存4/12。

本輪共15请求/31992tokens；加此前120326可见usage为152318（含旧SDK错误4281，非核账单）。无新增镜像下载/宿主配置改动/删除，Dfree42.2GiB。完整回归1118passed/4skipped/33warnings/0failed（50.55秒），重点21passed/Ruff通过/V3规定preflight ready=true。所有进程已完成，旧失败和原件保留。

下一门槛先零调用证明counterfactual fixture contract：同API非触发参数可比、生产前置条件验证、oracle不改、允许待支持参数的负例、四条DEV参考不退化。尚未实现/验证，不算成果；未达不得再抽新canary/repair。本次gate失败按预注册封存，不放宽标准以继续计费。具体接手步骤见[DEV v3结果](E1C2_HYBRID_DEV_V3_RESULT_2026-10-05.md)，两roadmap/交接首部已改成此状态；历史命令保留并标不重跑。

## 2026-10-05 — literal counterfactual零调用证明与新生成4/12

复核DEV v3 B响应发现上一归因应更正：control并未省略feature_names，而是一个标签list对照六标签array，同时改类型和值/长度。追加勘误，旧结果不回填。新通用AST compiler识别相同callee/参数结构、未遮蔽numpy导入/未重赋值literal、仅一个容器变化，生成保持target元素/顺序/长度的list对照；target/setup/assertion/oracle不改，不eval/setup取值，未知计算/mutation/dtype/新参数支持保留unproven。

旧DEV九条B零调用audit：1 supported、5 unproven、3 abstain；派生相同六标签对照在原base两次触发生产长度约束，在target/Gold前拒绝错误fixture。生产guard自动来源/SHA保留，不称完整静态语义证明。完整hybrid-v1缓存新目录replay，五个target probe SHA与原oracle replay相同，四条参考Gold区分、generator仍失败；0provider，开发证据不是新生成。提交37c84c8与零调用gate保全，原canary不动。

原counterfactual慢入口反复重建同一源码索引，新增独立fast adapter提交8b503e7：读取旧DEV v3冻结输入，逐次查Git/base/窗口生产SHA/image身份，task records逐字相同；保留慢入口零调用freeze，无第二份付费trial。fast freeze SHA394b8c08da35f52e49257912546162513ce1df5adc6f3d58a976cfc1fb3e3234，reserve62980、18/80000上限、单题2/20000、输出3000、Flash非thinking/零重试。

先列精确`uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_counterfactual_fast_dev run`后，按用户已有授权一次完成9题/13请求26762tokens，无失败/重试；随后同入口gold独立评分5候选四真一假。四参考（warm_start/array兼容/ISO-Z/内嵌DateTime）经人工可观察行为核对4/12，机器trusted仍0。array是单标签合法shape触发参数校验不支持ndarray，Gold后完成；非原报告多标签truth-value原栈，限制明示。比DEV v3增2050tokens（8.3%）、恢复一条参考，不称省费/SOTA/因果增益；与历史v4同4/12，不称超过基线。stateSHA f7350efed623c0571ddd55df5b18d65110b7343e08f47a0e82418f1db251697d，ledgerSHA c36d61560f2c32927a899477007ca7af277e2d2f5e7ffbc84bb80dd8d4e64aed。

工程最初与重负载replay并发全仓1123passed/1failed/4skipped，唯一Streamlit8秒超时；重负载结束原测试0.76秒过，无修改断言/timeout。串行全仓1124过，fast后1126过，新增独立canary适配后完整单次1127passed/4skipped/33warnings/0failed（142.85秒）。指定重点含新helper22passed、Ruff通过、V3规定preflight ready=true。不是repair rate，不拼接测试结果。

新生成开发参考门槛通过，源码/独立完整协议先提交b42aa2e，再冻结counterfactual canary v4方法SHA88df1067d0770a74ebe6d72d7eee74b78c3135defd1659b97c7b444c5fbd21ea，Flash≤6/60000、每题2/20000、输出3000、零重试、分母3，无替补。此后只metadata-only排除旧DEV/三批canary/历史identity选新三题；不读新正文/Gold/模型、不下载大文件。下一步身份/官方小摘要→用户直连下载→准入/公开输入/预检→独立盲态；≥2/3才另冻repair。旧三批负结果、TEST/C5/Fresh30及Docker/tunnel均不改。累计本日可见usage179080（含旧SDK错误4281，非核账单），系列非无限预算。结果与局限见[E1C2_COUNTERFACTUAL_DEV_RESULT_2026-10-05.md](E1C2_COUNTERFACTUAL_DEV_RESULT_2026-10-05.md)。

本次选题完成：排除301历史身份，盐选PVLib-1048、SymPy-20131、scikit-15535；identitySHA06d55d996a2f6786d8718340d24c8debd5e8c2a566897cf55c3b24e114f3a337。选择时只读metadata，耗时单列不计模型，未重抽。官方task.yaml来源核验后，transport官方经授权7892共7请求/26342正文bytes，direct mirror manifest完全相同3/3；transportSHA da5c553c3765f64e83fa01a8751aa732da2fd697a0cfa0a63893f7e3b199ae71。压缩层总4345861461bytes≈4.047GiB；blob/pull/model0。Dfree42.2GiB，逐张下载空间守卫最大约29.52GiB；大文件交用户终端关闭VPN全局/TUN、Docker No proxy，新模块download --timeout-per-image21600显示进度/ETA/导入心跳。下载记录和原始小型metadata seal在本机.codex；Git只提交public receipt/hash/identity/method，不上传评分或密钥。新题issue/Gold未读，未来盲态尚未执行；当前外部等待为用户完成直连下载。

## 2026-10-06 — 第4批完整独立实验0/3，模型3请求5596tokens

用户下载后，三份loaded/official manifest/image ID核验通过；admit六项离线官方评分，PVLib Base/Gold因NumPy2不兼容旧np.Inf导入失败，另两题双准入，固定3不换题。public只物化SymPy/scikit生产输入。live freezea8a9057a03c09905ef5397f12bc8051e08b2aa682cb9980cb91388216a6b43aa，最多4现场请求/60000、reserve13472。按已列精确命令/Flash/预算一次run，3请求5596tokens、无provider失败/重试，SymPy缺Point.vel窗口弃答，scikit两probe base通过，无锁定失败；独立gold attempted0/区分0。0/3<2/3封存，source原件/result/身份/方法不回填，repair/TEST/C5/Fresh30关闭。source stateac81f7a55ed3c884397ff4d759eb0c6100be06242345c6512dd75614fdb285b2，ledger22cbe8bbf72dff98c0ba7823ef8466fa386d808feb09cb3de6262d48fdf99bd7。

仅事后DEV诊断确认旧围栏投影删掉scikit公示输入.astype(object)，不是模型真的没获得足够原始issue；不得补本批后重称独立。回旧DEV用AST facts保留dtype/shape/seed/切片/声明fixture与末端调用，断言/测试/答案变量/输出行/能力块fail-closed，不执行；import/reexport/inheritance绑定生产API，源SHA/关系/depth/origin seed追踪，合成验证不导入包。old DEV九题/固定12最终3题4safe块，6无块/拒绝；Lasso原X/y/n/d恢复，自动找到继承fit（depth2）。中间audit-v1–v4原件保留，final-v5绑定模块/SHA/官方public blob metadata，无Gold输入。源码协议先提交b676837，newinput freeze00ab5ba6ccb4a3755b014191ddcb2c6aee5d989dd13b67d4825390b68b457581，18/80000上限、reserve67335、单题20000/输出3000/SDK0。

## 2026-10-06 — Faithful输出已生成但Docker未运行，验证INFRA_INVALID

先列精确faithful_dev run/Flash/18/80000，已授权一次生成9题16请求37593tokens，无provider失败/重试。然而原快输入只核磁盘身份未核真实daemon，Docker LinuxEngine管道不存在，control/target退出1被旧frozen executor误判重复nonsetup故障；七项Gold未应用patch。立即停止新增付费，原验证无效，**不报0/12能力成绩**。原response/state516721755853e07629e02d0980ca405b3df5d2483f576802b29e5837e399888e、ledgerb590d99136bfa8a78201bbfec41b631fc4f501030631fd46929d824f1af91307和全部日志保留，新invalid摘要另立。

ordinary docker desktop start一次失败；backend日志明确旧dockerInference IPC socket无法移除（系统无法访问/语法错误），引擎退出。没有删除socket目录、改registry/WSL/VHD/镜像/代理/tunnel；已请求仅正常停止Docker、备份改名C:\Users\qq人\AppData\Local\Docker\run目录再普通启动的确认。启动/status查询可能后台挂起，不继续叠加启动/付费。当前等待系统修复范围确认，不宣称已恢复。

新增未污染原freeze的container-health guard与cache-only replay适配器：require realengine/images，transportfailure立即拒绝为软件证据；同source preflight相等/绑定全部response SHA，真实API钥匙不用、新provider0，missingrole明确controller缓存缺失、不补调用。代码已实现、专项4passed，当前engine未恢复因此replay未执行，不声称模型效果。新frozen源码不改，新恢复目录单独留存。

工程记录：v4 run前首全仓1126passed/1coldTimeout/4skipped，原项0.81秒独立通过后完整1127passed/4skipped/0failed（83.42秒）；新事实/locator/faithful重点35passed/Ruff/V3 ready=true；新全仓1143passed/1coldTimeout/4skipped，原项0.94秒过后完整1144passed/4skipped/0failed（181.75秒）；加health/replay后完整1148passed/4skipped/33warnings/0failed（49.54秒）。未加timeout/skip或弱化断言，首次失败保留，不拼接、不是repair rate。

自10月5日可见usage179080+canary5596+Faithful37593=222269（含旧SDK错误4281，非账单核验）。没有新模型授权请求/新增付费循环，缓存可0调用恢复；Docker/镜像/本机/tunnel安全边界保留。两份roadmap与WebCodex当前首部已更新为engine恢复+零付费cache，不再按旧下载/旧run执行。

收尾运行新零付费恢复preflight：ContainerInfrastructureUnavailable，真实Docker Linux Engine仍不可用；守卫在新freeze/state与任何模型调用前停止，未继续run/gold。证明当前不可运行，不产生新的复现成绩。IPC修复范围仍待用户确认。

## 2026-10-06 — 授权IPC联合恢复，完整零付费回放Gold5/12

用户授权正常停止/IPC run备份改名；09:07单独改名run并启动后发现另一个Secrets Engine旧engine.sock，启动失败。获准Secrets目录备份改名并启动一次，前次启动留下新dockerInference而再次失败。用户再授权最后一次联合操作；确认Docker正常停止，在同一停机内将两个已获准IPC目录分别备份改名（09:12:11），启动成功。四份备份原件保留，不删除、不读密钥、不改镜像/VHD/注册表/WSL/代理/tunnel。前两次CLI等待超时与GBK读取警告保留；最后启动退出0有stdout GBK解码警告，真实engine/9个image ID和后续成功离线容器作健康证据。没有宣称tunnel端到端重验。Dfree约38.64GiB，无blob下载。

faithful-input-dev-v1-infra-replay-v1 preflight同原method/input逐项相等、绑定16response SHA，依次run/gold完成。9题/固定12，六个base稳定失败，独立Gold5真1假，机器trusted仍false；五个可观察行为人工审查范围单列，原四参考保留、新Lasso fifth候选。generator Gold仍失败，两pytest无稳定失败、一个明确弃答，历史三个准入失败仍在分母12。不写逐题特例、不重测旧canary、不把新缓存回放计为0生成成本。新provider0/tokens0/缺缓存0；源生成16/37593保持，原无效state/log/Gold不回填。

新回放freeze94cc5432566ea7d6b5d443c59963c567edcda1225a7810716851e5a01abb4b08，statebb4d1e05344681004e577fc336835596c999d87c812aa79128672442ee46b0b2，cache_statusd1771e68b40963ae343782bdbb052b85c30313fb7405cbdfe33491cf4fcdafa9。六个Gold result SHA与逐题边界绑定公开DEV gate，原模型freeze/state/ledger保持。5/12不是Agent修复或独立泛化，不是已控制消融因果收益；37593比26762贵约40.5%，不宣称省费。结果/下一阶段协议与代码先提交b794f3a。

复用框架新增独立Faithful canary v5适配器，保留输入facts/末端定位、counterfactual/STOP/正对照；关键新engine check在每个provider请求之前，而非仅验证前。新3项专项与既有19项共22passed，规定预算/V3重点18passed/Ruff通过。全仓第一次未用Python UTF8模式：1150passed/1fail/4skipped，失败为Windows official grader要求UTF8的运行环境守卫；正确python -X utf8 -m pytest单次1151passed/4skipped/33warnings/0failed（54.23秒），XML保存在新engineering目录，未加skip/timeout或改断言。V3 preflight附加-X utf8导致旧子进程CP936/UTF8解码异常，按AGENTS原python命令ready=true，未改冻结源码。

52份完整方法文件先冻结，method7fe8bf6c1fa9c0acbe82915ba43410b0f95db65615bb3def949dc5b1801feab3，提交03ef71a，Flash≤6/60000/每题20000/输出3000/重试0。随后metadata-only按新预定盐选不重叠三题；选择仍在扫描时提前调用metadata因identity尚不存在退出，未访问网络/写metadata，后续必须等identity真正完成再推进。这是命令时序失误，不是网络阻塞/模型失败。尚未读新题issue/Gold、未新付费、未下载大文件；后续大镜像仍交用户直连终端。累计可见usage222269不增，TEST/C5/Fresh30/repair/E2关闭。

选题完成：排除304历史身份，SymPy-22080/Sphinx-9180/pytest-7749，identity baa5abda0f8151dba915a13975ab014ca4b5315080a1c7b39426d17ab96d294b；官方task.yaml metadata f2bcc7b91f6260f01dbe7e8c536561e38ede072cfbbf37bd5539313c7191c93a。随后transport官方授权7892小认证/manifest、mirror空代理直连，3/3描述一致，7官方请求/25899正文bytes，transport3b1892690e3b70edbbf6a356ee349b1382a434e6562addbf2126432d1be6090d。压缩3162964124bytes≈2.946GiB，最大单张守卫26.123GiB，Dfree38.64GiB；三本地official tag都不存在。没有大blob/pull/provider或新issue/Gold读取；终端直连命令/ETA/进度页已准备，大文件继续交用户。身份和方法不再重冻，未来仅成功下载后进入准入；旧缓存回放和旧canary命令不再执行。现以用户下载为明确外部依赖，不追加付费。

## 2026-10-06 — 第5批真实盲态完成0/3，回旧DEV做零调用机制修订

用户后续下载已齐，三张loaded/official manifest/image ID与engine逐项现场核验，52份方法文件未变。零调用admit六项：SymPy/pytest Base与Gold均phase_pass=true；Sphinx source_identity_pass=false、两项exit90、无valid official log，不替补不送模型，分母仍3。public只物化两准入题、各四个自动窗口。live freezec70b66df87be7d91cf62a64245baa78412100b3984c90184805a479ad346739e，现场最多4请求/批60000/每题20000/输出3000/SDK retry0，primary reserve15726。先展示精确run命令/Flash/次数与预算，再按用户单实验≤100000既有许可一次运行。

实际3started/3completed/0failed、9642tokens：SymPy B明确弃答1602，pytest B4169/A3871均base通过、无repeatable witness。随后gold一次attempted0/discriminating0。固定3最终0/3<2/3封存，无Agent repair、TEST/C5/Fresh30/E2。SymPy public块unsupported_statement整块拒绝，terminal0、词法选四个同名symbols，缺Mod/lambdify/printing；pytest B调用不足格式化路径，A只定义test函数，直接Python脚本不执行函数体；Sphinx为环境/source门槛失败，不称模型能力失败。LangChain提示系统代理检测与自定义transport，未变更任何网络/代理设置。读取usage的首个本地诊断脚本把jsonl字符串误当Path导致AttributeError；只纠正读取诊断，不重跑模型/Gold。原state33f161a4e884fd7d11bfc6c4eca03bcc2ac2604c4ee9433f6f0b1818240cf5f9、ledger8af85abe23708ec1cab1344bcaba405d9a6e9d9a3d354e6dd1b50d04f0dbd3e3与原method/identity/probe/所有日志保留。

回旧DEV实现import_prefix审计原型，leading from-import只读声明，非import即停止，不遍历assert/函数体/输出值，源码AST/reexport归属/歧义拒绝，最多4窗2500。v1零调用九题：3题4新定义窗、provider0、模型输入未改、修复/复现分数null。原模块SHA3d70e6eda76269f9d0b2d2b0301edd3a3cbd519dc99fe570302412d6fa185ebf，提交3cb7bf9保留执行代码；v1 freezec2ab1e727db575c2ef76318f7f8aba94db1015dccfe858dfb61b403a0202a1d1。Ruff最初I001仅import排序，原型先留版本后机械格式化，再新增保守invocation分类，测试decorator/default/注解/type-parameter等侧效未知不得当inert。旧DEV8缓存候选1份函数-only未调用；v5 A亦命中，仅事后说明不改独立成绩。

后加固答案型名称/别名/模块根拒绝，另立import-prefix-old-dev-audit-v2，不覆盖v1。v2 modulea28a157a7592272b2aa5e3006d390e1c14b860092b4dabc89c4ee7409552bbd5、freeze1553c9abb285192c77b2d58c22218a117d3fef670e7c6dc452ec24b3257dd5e1，v1/v2 result SHA均4791dba8a4f6ec21743d999a70f879c06543f10e7e11ba0f967b3a93bc3ed4a2。6项新专项，规定预算/V3重点连初4项共22passed、Ruff最终通过；V3 preflight原命令ready=true。最终完整单次1157passed/4skipped/33warnings/0failed（49.04秒），XML在v2工程目录；中间完整同1157的51.96秒、48.65秒记录保留，不拼接结果、不改timeout/skip/断言。这些只是工程/结构审计，不是新生成提升或自动语义证明。

五批独立1/3、0/3、1/3、0/3、0/3全部保留。本批新增9642，10月5日起可见usage222269+9642=231911（含旧SDK错误4281，非账单核验）。没有继续扩大付费或选第6批；当前先在旧DEV接import fallback同预算消融与明确execution manifest，证明函数确实执行/非法入口拒绝后才另冻新付费DEV计划。两份roadmap和WebCodex入口从头更新为此下一步，旧v5下载/run命令仅历史；Docker/镜像/VHD/代理/tunnel及IPC备份未动、无新增删除或大文件下载。

## 2026-10-06 — DEV接线与15个封板canary镜像缓存清理；新付费0

用户要求继续并允许清理以后不再用的task。核实五批全部封存，15个canary ID与DEV12不重叠、各唯一精确e1c2/tag/image ID、无任何容器引用；仅非强制docker image rm这15tag，全部返回成功。源码/响应/账本/所有manifest/seal/loaded历史收据不删，保留12个DEV12（含未准入3）、两旧DEV30以及alpine；不prune/动volume/VHD/registry/代理/tunnel/密钥。清理后全12 immutable images与engine真实核验通过。标称虚拟总44540771302bytes含共享层，非实际回收量；Dfree观察前38.31/后38.19GiB，未作VHD压缩。旧canary未来如需复核要按原digest重获镜像、upstream不能保证永久可得，不能假称loaded收据代表现场镜像仍在。用户授权及15项准确ID记录在公开cleanup JSON。

新增execution_contract/executable_dev v1，terminal→import→lexical同4窗/23000预算；manifest A/B解析strip字段后保留旧oracle锁定，B不能自选入口，A仅明确无参同步函数、无注解/装饰/顶层副效，append一次调用，不猜fixture、不自动discover。每provider与候选前真实engine/image；transport不算软件故障。18项专题过/Ruff修正1import排序。零调用预检先产生v1 freeze2624309d728393b4acde03a4cd2f9a84b0aee3b9d5ffd64f0ff988b0b2ae8b92：九题固定12、Flash≤18/80000/每题20000/输出3000、primary reserve70048；provider0，没有模型state/ledger。

合成离线smoke首次命令quoting SyntaxError未执行；第二次已成功运行入口并打印marker，但校验脚本错误期望passing probe内部也执行两次，原execute_candidate正常成功短路一次。旧输出保留、不改执行器；另立zero-contract-smoke-v2，pass两次独立执行[0,0]，fail一次executor重复[1,1]、均观察EXECUTION_BODY_REACHED、network none/pull never、无provider且不作SWE/repair分数。result99000946acf88b3e014c310106d92018d0c9f96fa65150240f2d10840e04707a。指定重点18passed/V3 preflight作为全仓前置成功执行；全仓持久XML1171tests/0fail/0error/4skips/50.579秒，即1167passed，源代码及协议/原型收据提交f7d57d3。未动旧冻结代码/断言/skip/timeout。长终端session在用户继续消息后查询返回Unknown process id，改核持久XML与进程，不重跑stateful实验。

随后现有bridge docker_status返回docker_ready=false、报告脚本假设成功字段docker_version而KeyError；读取失败分支与CLI复核确认LinuxEngine管道不存在、Desktop/backend当时未运行。未知何时/为何停止，不能推断image rm造成。普通启动一次（不读/改目录）又在13:29本地日志报旧Docker/run/dockerInference socket不可移除，启动失败；已向用户请求正常stop＋同次停机备份两个IPC目录＋普通start一次的确认，没有擅自移动/删除或强关WSL、factory reset。bridge代码/密钥/服务未改、未发新的provider调用，engine不可用时工具不能称健康。此为当前外部阻塞。

安全复核补齐fixture边界：fixture_source声明不代表可调用默认native test suite；新增guard拒绝pytest.main/_pytest.config.main、runpytest/makepyfile/makeconftest及import alias/函数引用/native模块赋值别名，B所有code字段与A同样检查，不启用native harness权限。因此v1零调用原型和f7d源码完整归档、不重用其freeze，新v2目录/协议另立，仍固定12/候选≤18/80000，但engine恢复后必须重新preflight/算reserve/冻配置。v2目前无freeze、无state/ledger/provider，未在五批canary补规则重测。

v2重点26passed/Ruff通过；首次native guard全仓1172passed/4skipped/0fail（72.30秒）保留，加别名/ref负例后的最后完整1175passed/4skipped/33warnings/0fail（65.46秒；XML1179tests/0errors/65.136秒）。未拼接或弱化断言。两份roadmap与WebCodex首部更新为授权恢复engine→v2新预检→展示精确Flash run/预算后一次旧DEV；native fixture hydration仍不支持，静态可达/语义非普遍证明。新增付费本轮0，累计可见usage231911保持（含旧SDK错误4281，非账单核验），TEST/C5/Fresh30/repair/E2关闭；无新增镜像下载或重要文件删除。

## 2026-10-06 — 授权IPC恢复，V2与V4两次真实DEV均未达门槛

用户确认仅正常停止Docker、两个IPC目录备份改名再启动一次。确认backend/Desktop已停止、校验精确源/目标路径无junction/冲突；同次停机备份run与docker-secrets-engine，后缀20261006-135813，普通start成功。真实server29.4.0、DEV12全12 config ID可inspect、现有bridge docker_status docker_ready=true；不改VHD/registry/代理/tunnel/key，没有重下已删除15旧镜像，Web端到端未验。

V2方法0cebf87已提交，现场新freeze c56411f586fbfcb59891f82fef1da7bc5aa81c8d308bb276ee694bdee5c75737，固定12/九eligible，Flash最多18/批80000/每题20000/输出3000、primary70519、temp0/nonthinking/retry0。先列精确executable_dev run/模型/预算后使用既有≤100000单实验授权一次执行。12started/12completed、36689tokens、无provider失败/重试，4base候选Gold3真1假，四参考未保不抽新canary。warm_start/Lasso/ISO-Z区分，generatorGold仍失败；array与List(DateTime) A缺execution有效field而协议拒绝。后只读这些响应JSON字段发现其实只有issue/windows输入echo，没有source，不能拼造候选。原stateeb24a0a458108748705f592d37afb19ab7f513920f9ffb4f9fdb9b63f6a0538c、ledger8e7baaa6f42d7d6b889e0403a91f37e11d4d1ae584f8e85cffce7f8d821d7c58、全部源码/响应/控制/评分一字不改。机器trusted0，未逐项封板语义审核，不称可信3/12或修复率。

零费controller-owned grammar兼容回放：新两模块/12缓存raw SHA、source method/input逐项同一，cache-only不使用真实key/HTTP、新provider0，9题完整/缺缓存0。manifest只忽略唯一execution元数据，input echo和其他额外字段仍拒绝、未知fixture/native API/无参入口等边界保留。controller-manifest-cache-dev-v3最终同样Gold3/12，无提升也非新生成；freeze0a9848173943b16d924fa1d7a55dbf12ef4c79a6aea9d6d1218bf6385162a75c，state081863ba6517544ac9d4a1952f175c5ee60069ad1e8a71f617bee657a371146c。24专题passed，后代码/协议/原结果先提交f7693b7。旧A只有Human prompt、指令/大JSON上下文混合且后置facts，识别为待验证输出请求风险，不假称因果证明。

另立真新生成V4：可信A指令System、公开issue/windows/facts Human、最后明确生成请求和source/七字段schema；原窗口/输入/预算及native/fixture/source边界保留，不把公开数据升为system。现场freeze40cd232e56945628f8c1f6e0946d3b1f659bb574081c252e1aaa51029c3ef2fb、最多18/80000/每题20000/输出3000、primary70238、0重试。重点6passed/Ruff、指定预算/V3重点18passed、原V3 preflight ready=true，全仓完整1181passed/4skipped/33warnings/0failed（68.70秒），未弱化断言/timeout/skip。先列精确controller_generation_dev run与Flash预算后一次执行，14started/14completed/35889tokens、无provider失败/重试。

V4 A5/5均生成source无输入echo，五个base候选Gold2真3假；ISO-Z/List(DateTime)消除失败，array/generator/pytest候选Gold仍失败，warm_start弃答、Lasso无稳定失败。机器trusted0、语义审核未完整，不称全自动可信或修复。state14ad5c4f45a553c0f48a716cd6a59cbf9977dfe8e416308737724ece0393e796、ledger41f25f5d82b5f4fca1aeea682ac77b6ee57364bb981e276b5666b872a1886fd0。仅生成源码/生产依据诊断：X一列却给3个feature_names；pytest FakeConfig/FakeItem且assert True，不是原真实行为；generator未建立返回形态/重复调用关系。不能用Gold答案补输入或断言，不能合并V2/V4最好结果。

本轮真实新增12+14=26请求/36689+35889=72578tokens，缓存0；10月5日起可见usage304489（含旧SDK错误4281，非账单核验）。两版质量均未保四参考，停止继续付费提示微调/扩批，不抽第6批；下一步先零调用生产precondition/guard/返回结构与正对照、A同样的fixture约束、可信generated/native执行覆盖及docs/特性请求路由。未知关系保留unknown，不手填维度/对象/断言，不让仅稳定失败算可信。五批canary负结果原样、TEST/C5/Fresh30/Agent repair/E2关闭。两份roadmap、当前交接从头更新为此步骤；无额外镜像下载/文件删除，IPC备份全部保留。

## 2026-10-06 — A fallback 零调用对照拒错机制

使用academic-research-suite的实验执行/证据分离与ponytail最小复用：新fallback_control从普通顶层A候选提取最后真实调用，复用既有literal counterfactual compiler，同值/顺序/长度，仅派生一个numpy→list控制；多因素/变异/逃逸/调用重绑定/函数或未知fixture保留unknown，常量Assert通用拒绝。source SHA、exact-base/输入/immutable镜像现场检查；不改任何旧source或oracle，尚未接入live runner，不宣称语义等价。

首次专项2failed/18passed是新合成fixture没有初始化Git，原validator正确拒绝；修测试fixture为真实clean Git，不弱化guard。第一次审计预检错误把canonical input SHA和冻结文件SHA混比，执行前停止、未建OUT/运行容器或调用provider。修正file绑定并新增单测；Ruff首次import顺序错误也修正。以上异常如实保留，非模型重试、非被测软件失败。

新一次零模型审计fallback-control-zero-dev-v1完成：固定12/原九准入/五A，compiled1、控制失败1、常量断言拒绝1、unknown3。array三项labels对一列X，自动派生同literal list后两次独立离线执行[1,1]，生产guard报feature_names must contain 1 elements, got 3；logSHA af45a7cfa213bba0f73a7dcd3c739389d9f683e710809ded16829af3b765dc99一致。pytest assertTrue在静态阶段拒绝未执行。没有修维度/数值、读取Gold/test、重算原V4 Gold2/12，也未计新可信分数。

freeze9d78aafbcd3a6eae3686fe48023031cb580861708edc660a5a3e931f0e89afb2，result7a74c894f10b6592de09f5aaebc048afc0e18b4994249c9c8a3e22c223d3ba28。原V4 freeze/state/ledger三个SHA仍相同；本轮provider0/tokens0/Goldreads0，累计可见usage304489不增。九immutable镜像运行前健康、DockerServer29.4.0。没有新增下载/删除/重启，IPC备份/VHD/registry/代理/tunnel/key不动。

最终专项24passed、规定重点18passed、Ruff通过、原V3 compact preflight ready=true；完整单次1201passed/4skipped/33warnings/0failed（79.82秒），持久XML1205tests。不削弱旧断言/skip/timeout，工程数不是修复率。两份Roadmap与交接最新入口已补局部证据/接线未完成/跨仓库正对照待办；独立第6批/repair/TEST/C5/Fresh30/E2仍关。公开摘要绑定本机完整记录，未上传原评分/密钥。下一步先补跨仓库合法控制及返回结构/消费关系，再另立版本接A校验；不凭两项拒绝启动新的付费提示微调。

## 2026-10-07 — 新受限运行反馈主干、授权IPC恢复与真实零调用门槛

用户确认按新方法推进。用研究执行技能/ponytail复用边界、执行器、原B七字段合同和预算账本；新bounded_repro_loop及bounded_repro_dev支持production-only AST retrieve、已暴露path read、合同probe、弃答，最多4轮。两次正控制通过才target，自生成日志反馈修fixture/API，首次有效oracle锁定，禁用native fixture/任意shell/test/Gold反馈。没有安装完整mini/ReProAgent/SWE-Doctor，未宣称论文成绩迁移，也未实现完整debugger或Agent patch。三题按旧V4manifest首个准入task/repo预选，不看成绩：SK13496/MM1252/pytest7432；screen3/原DEV分母12，计划Flash≤12/80000/每题26000/输出2200/retry0，准备时未freeze。

现场engine初始缺管道，普通启动一次仍失败，20秒健康探测timeout。诊断CLI原未设timeout挂起，仅中止自己该诊断，不杀backend。日志starting services/Inference manager报Docker/run/dockerInference旧socket，未factory reset/删IPC。专项首次1failed/16passed源于新合成Git fixture把生成artifact放进未忽略workspace，原clean guard正确拒绝；修fixture.gitignore，不弱化guard。Ruffimport/unused修正。新专项21+原规定重点18=39passed，Ruff通过，原V3 preflight ready=true；完整单次1222passed/4skipped/33warnings/0failed（64.86秒；XML1226tests/0errors/64.778秒）。工程数不是repair/repro率。

随后用户本轮明确允许仅正常stop→两个IPC目录备份改名→start一次。docker desktop stop --timeout30后确认Desktop/backend均退出；源/目标/父目录无reparse/conflict，精确备份run与docker-secrets-engine，后缀ipc-backup-20261007-081928，再hidden普通启动一次。真实engine与DEV12全12 config IDs核验成功。旧备份/VHD/registry/代理/tunnel/key/镜像全不动，无大下载/删除。

列明零模型smoke精确命令后一次完成：scikit-learn与marshmallow生产普通API合成输入，先retrieve，再control两次+target，通过target不算bug、反馈后明确弃答；两个repository均3步fake invoke，真实无网络/只读/pull-never执行。provider0，真实smoke gate通过；人工编写合成fixtures只说明控制器执行有效，不能报实际任务全自动正确。旧V4freeze/state/ledgerSHA不变，原所有负结果保留。准备收据先记录blocked，再追加授权恢复与smoke，不回填旧实验结果。两新method源码和协议将先提交，再freeze精确live；本节截至此处真实新增付费0，TEST/C5/Fresh30/repair/E2不变。

源码/协议先提交b14e29e，新v1 preflight冻结bde797eab1bcb4fac78a52bfd751b5090bd4311a0b3e979494e964257796ffc5，列精确bounded_repro_dev run、Flash≤12/80000/每题26000/输出2200/retry0后按用户既有≤100000预算授权一次执行。12started/12completed/24976tokens、无provider失败/重试；三题都turn_limit，schema one_action_object_required，没有合法候选。generation seal2d2a83b5899e4de94002420d34e4bcf0215a95dc35c166272663dadaea0848a9，state884327c8610e15c1a1c90b6c623ff22e6d4cb47a995271348a2a8ce0574d0e92，ledgerb8dd9229991d3240968a6723ac09e6e79f47a0fb7b80b8cf0823fae6a3d4b333。独立grade入口核seal后attempted0/区分0，未执行Gold容器。不能解释成三个任务的软件复现失败。

只读raw JSON shape初见(type,retrieve)9份、(type,七字段)3份，最初误判type为动作枚举；另立typed codec v2及零调用smoke（两仓库真control2/2、无付费run/freeze）。12缓存格式审计全部typed_fields_mismatch；一个后续诊断脚本只读response外封装而非raw，输出None，随即改正确两层解码。确证type固定值json_object，是格式元数据而非动作名。原v1/v2源码与smoke不改，v2协议追加修正说明，另立v3只剥离该固定tag，再严格canonical/完整B字段检查，额外echo/execution/shell/未知type仍拒绝。12缓存零调用解码全通过（9retrieve/3probe），不是重放成绩。v3真合成smoke两仓库通过，新预算60000/每题20000/输出2000，≤12/nonthinking/retry0，未改旧输入/prompt/quote/source/oracle，不据Gold调参，三题身份与原分母不换。

v2相关/预算/V3重点49passed，完整1232passed/4skipped/33warnings/0failed（57.33秒）；v3相关39passed/Ruff通过，追加完整回归结果随后记录。所有旧freeze/state/ledger/负结果保留，无模型重试、镜像下载/删除、VHD/registry/代理/tunnel/key变动。10月5日起累计可见usage暂329465=304489+24976（含旧SDK错误4281，非账单核验）；v2paid0。下一步只有v3另冻新method/真实预算再列精确命令一次screen，不修改旧run或直接开canary/repair/TEST/Fresh30。

v3方法/协议与v1负结果先提交61b81c6；完整单次1240passed/4skipped/33warnings/0failed（56.90秒）。新freeze571ace3fba55708f194c4823d9d43c544ce67364cc0c708703fc904bf25798f9，列唯一v3 run命令/Flash≤12/60000/20000/输出2000/retry0后一次新生成。6started/6completed/13341tokens，无provider失败/重试；每题第二步重复同query而retrieval_no_information_gain停止：IsolationForest.__init__和DateTime._deserialize均找到1生产定义，Skipping.pytest_runtest_makereport错误owner限定找不到。格式正常但无probe，generation seal2c7ce740dbab9df5c01479b6534dded9d6e3ed178250524525ab4a26bb1dea8a，state1d8568b656095afe97b207526367b354096698dd0ade2e4a93bb461a4286eed9，ledgerc46ea4583918b97e0cc42ca161fbd336bb0e7a1d466ed3b7120607861285ead5；独立grade attempted0/区分0，没有Gold执行或score反馈。

进一步接线审查：v1/v3每次主要重构Human JSON，只嵌last_feedback，没有真实上一Assistant action及明确turn/next action请求。这只是受限反馈原型，不能夸为已完整实现成熟Agent线性历史。另立v4，真实新run上一response/feedback原件接Assistant/Human观察，最后明确turnN/4、检索已完成和下一行动；unknown qualified symbol允许plain symbol的通用提示，不按task补文件或断言。source/旧三题/decoder/两control/oracle锁定边界不变，completeconversation≤36000，Flash≤12/60000/20000/输出2000/retry0。前两付费共38317，本新batch上限60000，当前轮三批总上限98317，不跨批借额度；v4若仍无候选则停止本轮付费扩批，保留负结果。

v4新专项/原codec与预算V3重点50passed，Ruff通过；单测读取自己上一真实action/feedback，不制造模型响应，也证明资料/体积拒绝在provider前。新真实两仓库smoke与完整回归下一步，原所有methods/freezes不修改。自10月5日起可见usage暂342806=329465+13341，非账单核验；TEST/C5/Fresh30/repair/E2仍关闭。

v4真实新namespace两仓库smoke均完成，方法/协议/历史接线测试先提交0f2d227；完整单次1243passed/4skipped/33warnings/0failed（56.86秒），重点50passed/Ruff，原V3 preflight ready=true。新freezeab09fc427cb29b9d867aa1801dcea9763f5c9ad10fd70ce09231fed2527d480a，列唯一v4 run命令/Flash≤12/60000/20000/输出2000/retry0后一次执行。11started/11completed/32660tokens，provider失败0/重试0；SK3calls预算stop，MM4calls控制失败，pytest4calls最后生成语法错误，无selected candidate，机器trusted0。statea6d7b84ef22a5ff692aac24ae5bd9cfb5ca4d49badadd779937dc072ab78c7dc，ledger8b6cc8c3b1e98f0e96066d7f867815a506bd2afd030e865d905a92d055e876de，generation sealf4873fa7b12ee2090e6581cdfe04c3345e6604a7463e6233c9a64363b09a2522；独立grade attempted0/区分0，未执行Gold容器或反馈Gold。

零调用原因审查：SK retrieve IsolationForest.fit找到了定义→read→probe被一comparison assert格式拒绝，上一invalid payload没有进入previous字段；正确重建下一conversation后已消费9913/剩10087、下一reserve10700，guard发请求前停，不是余额/API故障。首次诊断误带invalid payload为previous造成11137，原工具输出保留，公开只用正确10700。MM probe→read→两次probe，control共同程序的Z load先失败，未分离valid setup/bug trigger；pytest错误owner限定query0→plain Skipped1→read→probe语法失败。真实观察让模型走出了重复query，但无可信候选质量收益，不能扩批或按题手改输入/断言。

本轮遵守停止付费扩批承诺：v1/v3/v4共29calls/70977tokens（24976+13341+32660），v2paid0，无自动重试/跨batch借token；原三题与DEV12分母不换。自10月5日起可见usage375466（含旧SDK错误4281、非账单核验）。最新结果/data与两份roadmap/接手首部更新为已完成negative→零调用trace/AST故障前沿、冗余预算压缩与受限generated fixture，禁止所有已开始入口重跑。全旧DEV/四参考、独立canary、Agent repair/TEST/C5/Fresh30/E2未达门槛。Docker全12已核、IPC备份均保留，VHD/registry/代理/tunnel/key不改、无新镜像下载/删除；Web端到端仍未核。源码与安全摘要最终同步Git，原完整日志/响应/评分留本机.codex。

## 2026-10-07 — 零调用first-probe合同恢复、生产正常格式对照、生成式native定位

本轮继续用户新方法，按ARS实验证据边界和ponytail复用，不重跑已seal paid或开未见样本。本轮新增provider/tokens0，累计可见usage375466不增。原件核对纠正假设：SK assertion是n2==20表达式而非Assert，已有production signature前沿能识别不支持warm_start；MM第一控制+00:00失败位置在control_action，不是setup，不盲目移动或手改日期。三个first-probe issue/expected quote后来均核验在投影issue中，pytest问题为English CLI动作非Python，撤回“无效quote”推断。

新contract_recovery只给单Compare加Assert语法wrapper，predicate AST/数值/quote不变，不宣称原无Assert程序等价；再复用source-frontier并证明canonical setup+完整target_action AST恒等，control/oracle不改。trace审计绑定自己probeSHA/顶层帧，未知留unknown。15专项/source原tests通过。zero v1固定旧三题首probe、不按成绩挑响应，实际SK两control成功/target两次TypeError，producer完成seal后独立Gold1通过；MM控制失败、pytest语法不支持。freeze5b283068dea98694456462f0e49a15a402480f32d8e189fb9959def6c74746fd/stateada82aa500893c1e70b1d911228ce60110e0d2a8887e86cc848b4cec282cd19a/seal96272fec1a8d1285314eeb3c04f10c1a8822e0604a9d805491e5aa5f83644ba7。

从自动selected production source AST发现stdlib strptime静态格式，新source_format_control不含repo/task ID/手选文件：仅call_completes/单一ISO literal，未知/多值/动态格式/不可信receiver拒绝；按source path/line首个完整日期时间格式生成正常control，target与期望不改，时区/表示与target binding未证，明确不是same-literal或语义等价证明。23相关专项通过。新zero v2相同三题首probe，SK与MM两次control成功、target稳定失败；seal后独立Gold2通过，pytestEnglish动作仍拒。freeze5354720eed89761df3a37f0b0cbc929201a350b13b8aae6ce5575156fc166341/state7b3fdee99477526263b30de66ce70b8022bfdb8076e9f19158218723fff8d18f/seal385acf10cfb84ec6b98e0753b4f3bda54142ab62ec1ec272ebbdf647c0cb28b6。2/3是cache开发结果，不是fresh/独立canary/repair；machine trusted0。前沿proof控制不变只属该子阶段，v2实际控制替换由nested source-format proof明确记录，不回填原JSON。

lossless_context重叠源窗编码正向/往返JSON完全一致、SHA/metadata/文字全保、gap不读，4单测过；原实际SK budgetstop点原reserve10700编码10694（仅6节约），仍不够余额10087，不解瓶颈不接live，不减少保守reserve。原型/negative保留，也未证明模型理解新wire索引格式。实际字段非法、native伪命令仍严格拒，不以green tests包装质量。

新增controller-owned generated_skip_harness有限组件，not Agent tool/非通用fixture，旧native guard不改、不伪造model safe_static_check；只允许import pytest、@mark.skip单无参Pass函数，固定显式自生成/tmp文件、空ini，noconftest/confcutdir、禁止plugin autoload，flags只-rs/runxfail，无任意shell/path/config/插件/注入。11专项过（driver兼容Path.relative_to避免旧Python API问题）。一次真实组件smoke readonly/network-none/pull-never，两个CLI均collected1/rc0：control生成文件:3，target生产../../testbed/src/_pytest/skipping.py:239。开发者synthetic fixture不计SWE任务成绩。native freeze1b7df2bb489b7accef53cc625218c675a927d97158679b4ddb63b6496fbd9e83/resultcfb57cf36de68f3ac1add7626a173c1acd527610b30982a36778a78bddc0885a。

runtime_location_evidence绑定自己native driver/module/log/image/base，把report path按owned fixture cwd归一，拒绝伪tmp根、原test/docs/hidden/conftest/host/越界、不把自己生成文件当生产窗。13专项过；一次source-only审计自动得src/_pytest/skipping.py:239及233起窗口，无人工选文件，result a594cb66a2355187977ada7ae5ac913f826d10846a6d3a7dd152d908cc2e0cf6。没有读原测试、没有生成patch或native Agent评分。

中间全仓1268passed/4skipped（57.85秒），追加native后1279/4（56.27秒），最终location guard单次1292passed/4skipped/33warnings/0failed（61.87秒；XML1296tests/0errors/61.815秒）；规定预算V3重点18passed/Ruff和原V3 preflight ready=true。无旧断言/skip/timeout削弱。所有old paid/zero seals与source保持；本轮无付费、Docker重启/IPC改名/删除/下载或VHD/registry/代理/tunnel/key变动，原备份仍在。两份roadmap、结果机器摘要与Web接手更新为统一新DEV编译器/typed native接口与独立评分身份待接，再同版四参考/完整DEV、独立canary≥2/3、Agent repair；不跳gate或承诺30/30。新组件/缓存解码/工程counts都不是任务成功率。所有已经开始zero/gold/component/audit不再重跑，安全源码/摘要同步Git，原raw/评分仅本机.codex。

## 2026-10-07：统一编译 / 原文引用两轮完整旧DEV与零调用诊断

按用户继续请求与既有每批≤100000的Flash授权，使用academic-research-suite的实验分账/不retry规范与ponytail最小改动复用旧机制。新compiled_runtime_dev独立文件/身份，raw→canonical→锁oracle、源码前沿与strptime正常控制接旧运行反馈，完整旧九准入而非每仓库首题；初始reserve60707、早题动态ceiling扣未跑题首调用reserve，保守1.4不降。真实两仓库合成smoke每control2通过、passing target非bug；47专项/规定重点/Ruff过，完整1300passed/4skipped/33warnings（58.97秒），规定compact V3 preflight无UTF8 ready=true。方法先提交d06caba，freeze73d2423924d9d87898e93e7280fd7a320ef0b841938dee166db95c0673cf2439后列精确compiled_runtime_dev run/Flash≤36/100000/20000/输出2000/retry0，一次run26started/completed/74336，候选3。seal3972629239627db3f60bfe754b48da0b260db553c6f34d86edb8e59b82703455后独立grader3/3区分，固定3/12、四参考2/4、机器trusted0。SK参数构造、MM ISO Z与generator谓词是开发证据，不是完整warm-start证明或修复率。

9次quote拒绝根因只读原response/input确认：误转述原文、将生产错误消息当issue期待等，不手工补quote。新issue_quote_refs无损行/offset/SHA目录、整数ID严格解码，target/数值/期待不改，不按task排序/模糊匹配；另立referenced_runtime_dev，保留旧精确字符串兼容。12项新单测/重点38/Ruff、真实合成smoke与完整1312passed/4skipped/33warnings（57.27秒）过，方法提交0f4818b，新freeze4ca872c62fe075194b9a692e0497933075537feaa1671e584275f24fadcd96db，先列精确referenced_runtime_dev run/Flash≤36/100000/20000/输出2000/retry0后一次完整九题。26started/completed/89923，2候选，sealf71727ada3a028b4f0948f379112aae633bf55b4538ab544fe6415b8bfc9d708后独立Gold1/2，固定1/12、四参考1/4、machine0。引用拒绝9→0、11真实ref证明，但context开销/新包装与fixture错误总体退化，不以3与1best-of拼分；无provider失败/SDKretry，不回填或重跑任一命名空间。

停止本轮paid扩批，零调用新增contract_feedback_diagnostics：严格一层已知json_object/content dict包装、extra/string/递归拒；四份SK raw均strict解出原probe+有效ref，没有执行/修control/改score。candidate/execution source SHA与generated module帧绑定，MM generator在旧统一版是Assert predicate AssertionError，在引用版是Assert内部tuple索引TypeError，Gold仍失败，分类oracle_evaluation_error而非预期谓词false。constructor/API处TypeError留unknown，trace不可信、不是语义证书，helper未接live。8新专项加引用/编译重点28passed；初次Ruff仅新test import排序失败、最小格式修复后pass，不动旧测试/断言/skip/timeout。零审计result33a4516ec062a2550da73c0d328ee0d9e5ea065da767674e7ad150d32915b6e6，源码SHA/两批freeze/state/ledger/seal/Gold结果SHA在公开data receipt绑定，原件仅本机.codex不上传。

最终完整1320passed/4skipped/33warnings/0failed（56.44秒，XML1324tests/0errors/0failures/56.423秒）；Ruff/预算V3重点/原compact preflight通过。两批新增52请求/164259tokens，各自≤100000，自10月5日可见539725（非账单核验、含历史SDK错误4281），不称项目总量。没有新下载/删除、Docker restart/IPC改名、VHD/registry/proxy/tunnel/key变动，Dfree约34.22GiB，全部旧备份/记录保留。当前六步落地接手在最新结果第4节，唯一round日志本续档，两份Roadmap页首/Web handoff指向；先DTO/control/readiness/成本零调用实证，另冻新完整DEV，开发有收益才新canary≥2/3，再repair/官方评分/同版DEV/全新任务。TEST/C5/Fresh30/private Test500/E2未打开，不承诺一周100%。小型安全源码/文档/脱敏receipt计划同步Git；原bridge strict-v5白名单未扩，不假称Web已能paid端到端调用。

## 2026-10-07：readiness四参考新生成 / 执行绑定setup前沿 / Docker恢复待授权

用户先问退化原因再允许继续实现，按研究执行/最小改动技能先旧cache零调用，不改已冻root。新增ready_runtime_dev单文件适配：统一五strings/two refs、已知一层JSON content包装、lossless紧凑pairs与只去全等重复Assistant/observation、Assert求值错误回feedback而非terminal候选、两次相同invalid/control失败/目标通过第三调用前停止。52旧response原accepted全部保留、51格式可解码、4包装恢复、一份空type仍拒绝；不把decoder acceptance当真实候选。37专项/预算V3重点/Ruff过；初次Ruff仅unused_sha import、最小移除后pass。两仓库真实synthetic control2通过/pass target非bug，完整1331passed/4skipped/33warnings（58.33秒）、规定compact preflight ready=true。只读原feedback更正上轮SK26289引用版“控制失败”为控制通过、target_not_repeatable_failure，table修正加说明，不改任何原实验/机器收据。

ready方法提交ca9ef29，freeze01f0a4e9819abed193798fbf789fe0fba23bc929f7f999baa80ea25e7c85de37，screen4/原12与九准入分开；展示唯一ready_runtime_dev run/Flash≤16/50000/每题20000/输出2000/reserve1.4/retry0后一次真实新生成。10started/completed/32826tokens，无provider失败/重试，SK13496与MM1252两个control过/target重复失败、独立Gold2/2；SK26289先control缺导入、后target仍通过/预算stop，MM1359 shared setup先MySchema实例绑定fault，导致normal DateTime行动未执行即fail后弃答。本批Gold2/4、machine0、四参考gate未过，不扩批，不将screen换算完整DEV12或best-of。累计可见572551非账单核验，原件seal与精确SHA在新公开receipt。

为shared setup根因新增runtime_frontier_zero：两failed controls sourceSHA/executionSHA/同生成顶层Assign(Call)故障位置→setup suffix移target；完整target AST恒等、control/quote/oracle不改，normal control读取moved binding则拒；静态free-name disjoint不证明alias/global独立性，trace不可信非证书。13新专项（含非call/frame/timeout/infra/SHA拒绝）+readiness24/Ruff通过，完整1344passed/4skipped/33warnings/0failed（66.47秒，XML1348/0errors/0failures/66.458秒），方法/zero协议提交4d2b2b3。cache只原turn顺序、不按Gold选、缺cache不补provider，prod input须与源cached input完全相同；不是对新feedback重新采样的因果model回放。helper尚未接新live，所有oldfreezes保留。

随后zero run在preflight真实Docker health失败，Desktop/backend不运行/LinuxEngine管道缺失，OUT/freeze尚未创建，provider0/新研究容器0。执行普通docker desktop start --timeout30仅一次，启动超时；最新2026-10-07T06:32:01UTC日志明确“initializing Inference manager...Docker/run/dockerInference...file cannot be accessed”，backend取消后退出，06:33 GUI Quit记录保留，不推断停机由代码造成。只读现场/日志，没有强杀/WSL reset/移动VHD/删image/改registry/proxy/tunnel/key/IPC改名；向用户另请求本轮仅两个IPC正常停机备份并启动一次，旧一次授权不复用，当前待确认。

等待时继续offline遍历本批全部3份failed controls，2份（同MM1359两turn）满足AST前沿证明，provider0/新容器0、未做真实normal控制/target验证，不能报恢复一题。offline proof与源码SHA/旧paid seal、52decoder审计、工程XML在data/e1c_evaluation_2_ready_runtime_dev_result.json绑定，完整结果/两Roadmap/Web handoff更新为Docker gate→一次未开始zero run/seal/gold→再新live四参考与质量gate，旧所有smoke/preflight/run/gold不重跑。研究未完成、独立gate未过、TEST/C5/Fresh30/private Test500/repair/E2关闭，raw/Gold/test/key不上传。无新大下载/删除，所有历史备份/源码保留；old bridge whitelist不扩，不假称云端端到端已验。

## 2026-10-07：明确授权IPC恢复、zero前沿3/4、新生成2/4、源码guard覆盖审计

用户本轮明确允许正常停机仅两指定IPC备份改名再启动一次。docker desktop stop --timeout30返回“不运行”，确认Desktop/backend/proxy/secrets无进程；两个精确绝对路径普通Dir/无reparse、backup sibling同parent/不冲突全检查后Rename-Item，后缀20261007-144329，全旧备份保留不读内容。ordinary start --timeout30仅一次成功，真实Server健康，九准入及原DEV12全12 immutable/config ID可inspect。未删/下载镜像、改VHD/registry/proxy/tunnel/key、强杀/WSL reset；旧授权/普通启动失败和本轮授权恢复分开，不推断反复IPC的长期根因已解决。

已有源/protocol先提交，runtime-frontier-zero-reference-v1恢复后首次freeze/run，source ready seal/state/ledger/响应完整SHA核对，当前input与cache input完全相等，动作按原turn顺序、首次base符合即选、不按Gold挑；SK26289第四cache不存在保留分母/不上模型。SK13496turn2、MM1252turn1复现，MM1359turn2搬setup后仍control失败/turn3normal DateTime两过、完整target两次同AttributeError。完整AST/control/quote/expected不改，free-name不证alias/global独立，trace不可信不机器升格；producer seal后独立Gold3/3区分，screen3/4，provider/tokens0。freezecd04766a9831c51b578b60d42c70510bb999ba6d5428a3a82e163a38db0ae122/state18b67d5307e7df25414c15c1b24dcd53b038bf4a069860b00b874b7c7c18aca9/seal14a67d73c7d23cbd326c7990db74258ed97b4870d1f220ec5213e54c2c314c01，公开zero receipt绑定独立Gold SHA。旧blocked/离线AST proof不改，cache不是新feedback-conditioned generation，所有已开始入口不重跑。

新增frontier_live_dev最小单文件wrapper，复用runtime-frontier/ready，不编辑旧冻结方法。新预算全批50000不变、task24000（上轮spent11447+reserve9747超过旧20k；原旧cap不改），output2000/≤16/题4/reserve1.4/保护未跑首reserve/retry0，source/method/protocol/预算明示新namespace，不声称单因素实验。两repo真实synthetic smoke正常control2过/通过target非bug，相关45/Ruff、完整1347passed/4skipped/33warnings（85.63秒）过，原compact preflight ready=true；source先提交aa0d282，freezee50cd41de432567ea065f7d1ce5c4ea531eb8c32732df0afe944ad5f23e8d223，列唯一frontier_live_dev run/Flash16/50000/24000/输出2000后一次新生成。12started/completed/40135tokens，无provider失败/自动retry，MM1252turn3与MM1359turn2重复候选，SK13496target属性赋值已工作后弃答、SK26289list输入通过后错误判断源码已修好而弃答。seal5493c5daa758257e3d497d6101c0c14dc1d39b757f5e38ceec978af8395d1110/statee09603fdeee3659551387821237b2096ccc49489cb21542b2507f1727c654865/ledger82a97e3e556dbaba7f2055723f93b10ed49003ab51b1e825399f2211be3fb25e；独立Gold2/2，screen2/4、machine0、四参考gate未过。不能和zero3/4/旧SK成功拼4/4，不扩九题/新canary/repair/E2。

停止paid扩批，新增guard_evidence_audit，仅根据public quoted/imported API与public失败条件→selected/SHA-bound production AST If（nested也覆盖、depth真实AST距离）→自动窗口，不含task IDs/手选源/Gold/原test输入。真实四题第一合同都审，不按Gold筛：SK26289十四guard，public失败predicate feature_names→_export.py:1040，already_visible=true。先前“可能缺源码”推测不成立，模型实际忽略已在窗口里的bool guard，不能继续盲堆source/semantic服务；源码已修好结论没有完整源支持。其它三题此规则guard0不是所有源/接口不存在，API绑定/期待语义unknown，prototype未接live/不加score。新3专项/negative源保护与24预算V3重点/Ruff过，最终单次1350passed/4skipped/33warnings/0failed（89.21秒，XML1354/0errors/0failures/88.361秒）。未弱化测试/timeout/skip；source/seal/private raw保持，公开JSON绑定zero/paid/guard audit hash。

本轮新付费40135、zero0，10月5日起可见612686非账单核验（含旧SDK错误4281，不作项目总账）；Dfree恢复时约33.89GiB，未新下载/删除。两Roadmap/Web handoff/current结果更新为API可执行义务/入口参数绑定与输入类型hypothesis、模型source结论核对的零费门槛；原所有“Docker等待授权/zero未开始”明确历史，当前engine已恢复/12镜像保留。本轮IPC一次授权已消费，未来同故障另问，不扩大old strict-v5 bridge白名单或声称Web新paid入口端到端已验，keys/proxy/VHD/registry/tunnel不改。TEST/C5/Fresh30/private Test500/repair/E2未开、研究未完成不承诺30/30；只小型安全源码/协议/测试/脱敏摘要同步Git，raw/Gold/test/key留本机。

## 2026-10-07：API义务真实3/4、受限类型观测真实2/4，停止本轮paid扩批

用户继续请求；主代理完整读research/ponytail技能，复用production resolve_symbol/resolve_method与assertion-free表达式，不起subagent/新dependency。新增api_obligation有限明确expose/accept/support param in/on/via Owner.__init__ grammar，参数/类/位置取public全文、无task规则，未知不伪证；production import/alias/source signature/SHA绑定，只顶层无条件普通stmt直接constructor keyword满足语法，拒attribute绕过/影子/dead/dynamic mapping/错qualified模块，语法fulfillment不证明runtime已执行或语义trusted。参数来源public expression exact vsmodel hypothesis/unknown、runtime type永不由static提升。两旧batch四题第一contract零费全部审（无Gold/容器/provider），新frontier的working属性赋值拒，ready正确constructor保留；另三题grammar不适用。10helper专项+3wrapper/相关budget V3共34/Ruff通过，初次新imports Ruff仅排序问题最小格式修正，旧method/断言/skip/timeout不动。

api gate在oracle lock前，拒未履行/未证入口不锁错误子目标；target通过才附≤2个matched public failure guards（source SHA/line/still present）与argument provenance，不堆14window、不Controller转换类型/值。新两repo真实synthetic smoke control2过/pass target非bug，完整1363passed/4skipped/33warnings（96.23秒）、规定compact preflight ready=true。先提交87f9e4d，新freeze17136deaa489e5eefd3dc709be4e8998c5cfcd60d3e3c8b8cee1701300212a95，列唯一obligation_dev run/Flash≤16/50000/24000/output2000/reserve1.4/retry0后一次新生成。8started/completed/28363，SK13496首call直接constructor、MM1252首call、MM1359turn2三候选；SK26289仍list→错误array假设→弃答。seal ee17275a77c313f683c4ec60bba7912c57c25e2faffbfdcc155516ade73560e0后独立Gold3/3，screen3/4、machine0，不完整DEV/独立/repair、四参考gate未过。

对余一题做zero受限类型观测：新可信constant driver SHA/nonce唯一marker、只自己/e1c2_model_probe.py/≤2个selected production Name-guard sites，container内probe/source SHA、base identity核对，net-none/read-only/pull-never/限pids/mem/cpu。sys.settrace精确sourcefile/line/local名，最多8记录，builtin身份+启动前numpy.ndarray type，no bool/len/repr/getattr/参数值/原test/Gold；driver没有model safe_static_check伪证，也不是开放trace工具。源字节相同，filename/instrumentation/timing影响不宣称等价，失败不采用、infra/timeout停、不retry、optional blocker环境不支持则skip。新7负例保护专项过。首次Ruff仅新helper import排序，修复；在实际运行前修正_sha(__file__ string)为Path，zero入口尚未开始不重跑。遍历四题第一target通过+matched guard（非task-ID挑），零provider真实观测_export.py1040 feature_names是builtins.list/rc0，值未输出，模型数组判断错误；原语义/source型未知不machine升格。

新observed_type_dev只传自己input运行态事实，源/sourceguard/input关联保持，不Controller改array/expected。新smoke/相关30/Ruff、完整1372passed/4skipped/33warnings（92.73秒、XML1376/0errors/0failures/92.702秒）、规定compact preflight过。先提交42c15a3，再freeze6c8e3d23dd2f2b306728f35338bb94a1b4ef294bff25418c78cdd1ed41f301de，列唯一observed_type_dev run/Flash≤16/50000/24000/output2000/retry0，说明此前28363+新批上限50000≤78363。8started/completed/28428、SK13496与MM1252两候选，SK26289纠正list后因原报dtype不确定而弃答，MM1359同故障normal control失败后弃答；seal851d9ffa5806d662b6fc195b06dfebf0801c023347823a813c673241d3147a34后独立Gold2/2，screen2/4、machine0。不得拼3/4+2/4=4/4，不继续本轮paid重采样/加预算/扩九题/选第6canary。准确类型事实不自动提升复现；observed全局提示与新生成不同，不能硬称observer造成MM退化。

本轮总16请求/56791tokens、SDK/provider失败/自动retry0，10月5日起可见669477非账单核验（含历史SDK错误4281，不作项目总账）。新公开data receipt绑定两个freeze/state/ledger/seal/Gold、zero API审计/类型组件/工程XML，raw/Gold/test/key仅.codex。开发比较基线保留API obligation3/4，2/4observer只diagnostic，下一步单一hypothesis政策：缺expected不可捏造，缺类型可明确source-consistent假设但不能原报化/当report-exact；先零费跨repocontrol/拒错/target保真，完整新freeze后小screen，全部quality gate后完整DEV/native/独立canary/repair/official/new任务。研究未完，TEST/C5/Fresh30/private Test500/E2不打开，不承诺完美。本轮无Docker restart/IPC rename/镜像下载删除/改VHD/registry/proxy/tunnel/key，原12镜像/备份保留，old bridge whitelist不扩大、Cloud缺本机material/runtime明确INFRA_BLOCKED，不假称Web新paid端到端可用。两Roadmap/current结果/handoff指向本新结果，下方旧“下一步”只历史；新源码与脱敏摘要安全同步Git，工作区重要内容不删。


## 2026-10-07：单一政策与DTO兼容修订，Gold2/4；零费诊断与当前入口归并

本轮新生成两批共15 Flash请求43,966 tokens：单一政策9/25,928，DTO形状不兼容、候选0/Gold attempted0；新兼容版本6/18,038，SK13496/MM1252独立Gold区分、SK26289弃答、MM1359control_failed，screen2/4、machine0。版本与负结果分账，不best-of。原9响应零调用解码且五个code/oracle字符串逐字段不改，新canonical示例与codec同改不称单因素因果；新source先commit f06fda7/86dbefc再freeze/live，两个generation seal/独立评分完成。新contrast审计六响应发现两份同动作control；bare Name guard隐式协议诊断不执行代码、类型未知、不修改输入、未接live、不授语义证书。完整1388 passed/4 skipped/33 warnings（93.81秒）、Ruff/预算V3/compact preflight ready=true，断言/timeout/skip不弱化。本轮总43,966，自10月5日起可见713,443非账单核验。公开data/e1c_evaluation_2_unified_policy_codec_results.json绑定freeze/state/ledger/seal/Gold/zero audit/XML，raw/Gold/test/key不上Git。

下一步先正常控制/状态与输入假设的可执行契约及跨仓库零调用反例，再另冻一次四参考/完整DEV；五批旧canary负结果不改、不新抽canary，TEST/C5/Fresh30/private Test500/Agent repair/E2关闭。无新下载/删除/Docker启动或IPC/VHD/registry/proxy/tunnel/key更改，所有旧记录和备份保留。当前两Roadmap/交接单一入口更新；旧快照如下逐字保全（仅换行规范化），并保留Git历史，归档内容不是当前执行指令。

### 保全快照：Roadmap 1旧开头快照

**最新：public API入口门槛版真实Gold3/4；类型观测接线版2/4，四参考开发gate未过。** 16Flash请求/56791tokens、无retry，source-bound类型事实纠正了numpy/list误判，但不等于复现收益，machine trusted0、非完整DEV/独立成绩/patch score。[最新分账结果与零费止损方案](research/E1C2_API_OBLIGATION_RESULTS_2026-10-07.md)。保留3/4方法作比较基线、不best-of、不paid扩批；下一步统一事实/假设/未知及正常control政策，不层层加提示或改输入答案。工程1372passed/4skipped/0failed不能冒充修复率，TEST/Fresh30/独立canary/repair/E2关闭；本轮Docker/VHD/IPC/proxy/tunnel/key/镜像不动，原所有记录保留。下方旧“最新/下一步”均历史。

**最新：Docker按明确IPC备份授权恢复、DEV12全12核验；执行前沿零费cache Gold3/4，新生成Gold2/4，质量门槛仍未过。** 12Flash请求40135tokens/retry0，恢复MM1359但两个SK弃答，机器trusted0，不best-of、不等于Agent修复。guard AST审计自动定位`_export.py:1040`且已在模型窗口，进一步把瓶颈缩到API请求与实际目标绑定/类型假设，不继续无效检索或paid扩批。[本轮逐项结果/落地顺序](research/E1C2_FRONTIER_LIVE_DEV_RESULTS_2026-10-07.md)。工程1350passed/4skipped/0failed不是质量gate；旧数据/所有备份保留、VHD/registry/proxy/tunnel/key不改，TEST/Fresh30/canary/repair/E2关闭。以下旧“等待IPC授权/未开始zero”只是历史，不按旧命令重跑。

**最新：readiness四参考真实screen完成，Gold区分2/4、machine0，尚未达开发gate。** 10Flash请求/32826tokens、无retry；52旧响应codec审计/重复无效停止/Assert求值错误反馈已接线。执行绑定setup前沿保持完整target AST/期望不改，离线证明2份同task程序，真实零调用研究却被Docker挡在freeze前；普通启动一次失败、旧run/dockerInference IPC，现等待本轮有限IPC备份授权，不强修数据盘。[最新结果/接手门槛](research/E1C2_READY_RUNTIME_DEV_RESULTS_2026-10-07.md)。工程1344passed/4skipped/0failed不是修复率，TEST/Fresh30/canary/repair/E2不开放，旧记录/备份不删除；前一段SK26289摘要误写已纠正，原得分/原件不变。

**当前主线：统一编译与原文引用接口已做两轮完整旧DEV真新生成，质量仍未达标。** 两轮各原固定12/九准入：统一版26Flash请求/74336tokens、Gold区分3/12；引用版26/89923、Gold1/12，四参考2/4与1/4，机器trusted均0，不能best-of合并或当Agent修复。源码/输入/预算/响应/seal分开封存；引用错误减少但成本/质量变差，停止付费扩批先DTO/正常控制与返回消费关系/oracle就绪反馈的零调用验证。[最新逐题结果与落地待办](research/E1C2_UNIFIED_RUNTIME_DEV_RESULTS_2026-10-07.md)。工程1320passed/4skipped/0failed（56.44秒）不是repair rate；TEST/C5/Fresh30/repair/E2仍关闭，无本轮新下载/删除/IPC/VHD/tunnel/密钥变动。

10月7日早轮封存：三次旧DEV三仓库screen共29次Flash请求/70977tokens、无provider重试；v1格式拒绝、v3重复检索停、v4进入真实probe/反馈但无合格候选，grader均attempted0。[早轮结果](research/E1C2_BOUNDED_RUNTIME_RESULTS_2026-10-07.md)。Docker当时按明确授权仅备份两个IPC目录恢复，DEV12全12核验；原负结果不回填。

最新零调用推进：[合同恢复与runtime定位结果](research/E1C2_CONTRACT_RECOVERY_RESULTS_2026-10-07.md)。同三题第一份旧响应，比较语法/构造前沿＋生产格式正常对照恢复2个候选/Gold区分2，**是缓存开发证据，不是新生成或独立2/3**。生成-only pytest组件实际观察到报告位置差异，并自动取得生产源码窗口，无人工选文件；组件fixture是人工写的合成用例、尚未接Agent，不计第三条成绩。新增provider/tokens0，旧所有negative不改，下一步另版统一编译/typed fixture接口，再真实同版旧DEV验证。

10月6日及之前封存：五批独立canary为**1/3、0/3、1/3、0/3、0/3**，负结果不改；旧DEV新生成V2 Gold3/12、零付费兼容回放3/12、再新生成V4 Gold2/12，共26请求72578tokens、未保四参考。V4 A5/5返回source修复了输出回显，但未证明复现质量提升。15个历史canary镜像缓存已按允许移除，全部记录/源码保留。没有同版DEV30全过、Fresh30或新版Agent修复结果，历史本机bridge健康不等于Web端到端已验证。

最新增量：[A fallback 零调用有效性审计](research/E1C2_FALLBACK_CONTROL_ZERO_DEV_RESULT_2026-10-06.md)完成：原五份 A 中拦住一份无效维度对照、一份常量断言，三份仍 unknown；模型/Gold读取均0，未改 V4 得分。已证明局部拒错机制，尚未证明跨仓库正对照或接入新 live；下一步先完成这些验收，不立即抽新 canary。

### 保全快照：Roadmap 2旧页面全文

# Roadmap 2：E1-C evaluation_2 当前状态与执行顺序

状态日期：2026-10-07。本页是当前执行入口；背景见 [Roadmap 1](PROGRESS_RESEARCH_ROADMAP.md)，逐轮过程见[集中续档](research/PROGRESS_LOG_ARCHIVE_2026-09-27_CONTINUATION.md)。本页不再堆叠历史“最新快照”。

## 0. 当前执行状态与唯一待办

**最新：API obligation新生成Gold3/4，类型观测接线新生成2/4；四参考gate仍未通过。** 两批各8请求、28363/28428tokens，本轮合计16/56791，provider失败/retry0、machine trusted0。同四旧DEV/原12九准入分账，不best-of，不算完整DEV/修复。[最新结果/止损顺序](research/E1C2_API_OBLIGATION_RESULTS_2026-10-07.md)、[哈希收据](../data/e1c_evaluation_2_api_obligation_results.json)。结构入口门槛恢复SK13496，source-bound zero observer证实实际list（非numpy）而不输出值；准确观测没有自动提高复现率。

唯一下一步：保留API obligation版3/4作为开发比较基线，类型组件只作diagnostic；先零费统一“缺期待不可捏造/缺类型可显式source-consistent hypothesis”的单一政策与facts/hypothesis/unknown三层，以及跨repo有效normal control/target保真证据。不得把假设叫原报事实，不手修array/date/expected、不层层追加提示或增加budget；零费/完整freeze后才小DEV一次新生成。四参考/忠实性/cross-repo gate未过不扩九题/第6canary，后续native DTO/确定性证书与独立评分仍待做，TEST/C5/Fresh30/private Test500/repair/E2不打开。

最终工程1372passed/4skipped/33warnings/0failed（92.73秒），Ruff/规定budget V3重点/compact preflight ready=true；可见累计669477非账单核验，旧任何freeze/state/ledger/response/audit不修改或重跑。本轮无Docker重启/IPC/镜像下载删除/改VHD/registry/proxy/tunnel/key。以下“当前最新/下一步”均本日更早封存阶段，以本段为准。

**当前最新：Docker已恢复；执行前沿cache3/4，但新生成仍Gold2/4，独立质量gate未过。** 本轮按明确授权仅两个IPC备份（20261007-144329）并启动一次，原DEV12全12现场核验。zero-frontier run/seal/gold已完成，模型新增0/缺cache不补；另冻同四参考Flash新生成12请求40135tokens，MM1359恢复，两个SK弃答、机器trusted0，不best-of。[当前完整结果/下一步](research/E1C2_FRONTIER_LIVE_DEV_RESULTS_2026-10-07.md)、[新生成收据](../data/e1c_evaluation_2_frontier_live_dev_result.json)、[zero收据](../data/e1c_evaluation_2_runtime_frontier_zero_result.json)。

唯一下一步转为**public API义务→实际入口/调用方式绑定、原文事实与输入类型假设分账、模型“已修复/无法复现”结论的源谓词核对**，先旧cache/跨repo合成零费，不继续paid扩批/提示微调。源码guard审计自动匹配SK26289的`_export.py:1040`且已可见，不能再误说缺源码或源码已修好，也不盲目接14重复windows。新method/预算/输入/代码freeze后才一次四参考，全部reference/忠实性/cross-repo gate后完整DEV，再新独立canary≥2/3/Agent patch/official评分/新任务；TEST/C5/Fresh30/private Test500/E2仍关闭。

最终1350passed/4skipped/33warnings/0failed（89.21秒），Ruff/规定预算V3重点/compact preflight ready=true；可见累计612686非账单核验。本轮paid≤50000、task新cap24000（原20000不改）、输出2000、16calls/retry0，不声称单因素实验；记录/备份不删，未动VHD/registry/proxy/tunnel/key。下面所有“Docker阻塞/零费未开始/等待授权”均历史，旧已started入口禁止重跑，当前不需要新下载。

**当前最新：readiness四参考screen已完成，Gold2/4；零费运行前沿仍被Docker挡在freeze前。** 10请求/32826tokens、provider失败/重试0，机器trusted0，四参考gate未通过，不扩九题/抽canary。全52旧响应codec审计保留原accepted、恢复4包装；Assert求值错误反馈与重复无效停止已接线。共享setup故障前沿离线AST证明2份（同一task两turn），但新容器执行0，不能当恢复一题。[最新结果与接手步骤](research/E1C2_READY_RUNTIME_DEV_RESULTS_2026-10-07.md)、[机器收据](../data/e1c_evaluation_2_ready_runtime_dev_result.json)。

下一步先恢复实际Docker：普通start一次失败，最新run/dockerInference旧IPC阻塞，已询问本轮仅两IPC目录正常停机备份/普通启动一次，尚待确认；不强杀/重置/动VHD/registry/proxy/tunnel/key/镜像。恢复并核验Server/image后，尚未开始的runtime-frontier-zero-reference-v1一次run/seal/gold验证，不把缓存回放叫新反馈生成。之后才另冻live同四参考；四参考/忠实性/跨仓库gate未过不扩批，TEST/C5/Fresh30/private Test500/repair/E2仍关闭。旧所有已started入口不重跑。

最终工程1344passed/4skipped/33warnings/0failed（66.47秒），Ruff/规定预算V3重点和compact preflight ready=true，无测试弱化；可见累计572551非账单核验。前次SK26289引用版“控制失败”摘要已按原feedback更正为control通过、target未复现，原件/得分/机器收据不改。以下段落是本日更早封存阶段，不覆盖本段。

**完整旧DEV两轮真实新生成与独立Gold判别已完成，尚未过开发质量门槛。** 统一编译运行版26请求/74336tokens、Gold3/12；无损原文引用版26请求/89923tokens、Gold1/12。固定12/九准入，四参考分别2/4、1/4，机器trusted都0；版本分账，不能best-of拼成绩。引用错误9→0但总体变差，停止付费扩批，先零调用DTO/fixture消费与oracle就绪反馈。具体每题、哈希、接手步骤见[本轮完整结果](research/E1C2_UNIFIED_RUNTIME_DEV_RESULTS_2026-10-07.md)，[机器收据](../data/e1c_evaluation_2_unified_runtime_dev_result.json)。

下一步按结果文档第4节：①统一action DTO与精确单层包装、重复invalid停止；②源码普通构造/返回消费关系与跨仓库有效control证据；③Assert求值错误回反馈而非terminal candidate；④无损冗余与实际reserve核算，再另冻同版四参考/完整九准入DEV一次；⑤有限generated native DTO/确定性证书和独立评分，开发有收益才新不重叠canary一次≥2/3；⑥同方法Agent patch/official grade→同版DEV→新任务。没有30/30、一周完美、独立gate或E2完成承诺。

本轮新增52calls/164259tokens（两批各≤100000）、provider失败/重试0；自10月5日可见539725非账单核验。最新工程1320passed/4skipped/33warnings/0failed（56.44秒），Ruff/预算V3重点/规定compact preflight ready=true；工程数不是修复。零费新诊断已识别四份合法action包装与Assert内tuple TypeError，但未接live、没有缓存回填分数。无需下载/删除，Docker/VHD/IPC/registry/proxy/tunnel/key/所有旧记录不动；TEST/C5/Fresh30/private Test500/repair/E2仍关闭。

以下本日早轮快照及各节旧“当前/下一步”均为封存历史，不覆盖本节；已started的smoke/preflight/run/gold/zero audit均禁止重跑。

**当前唯一下一步：闭环真实negative之后的零调用根因验证，不再付费扩批。** 新v1/v3/v4旧DEV三仓库screen均完成并seal，共29请求70977tokens、无provider失败/重试；v1格式拒绝，v3重复query停，v4已消费真实执行反馈但未产合格候选。v2仅零调用未paid。grader均attempted0、无Gold执行，机器trusted0，不是Agent修复失败率。本轮先验证trace→生成AST的setup/故障前沿、不丢issue义务的预算压缩及受限生成fixture能力；详见[逐项结果/验收待办](research/E1C2_BOUNDED_RUNTIME_RESULTS_2026-10-07.md)。所有已开始smoke/preflight/run/gold禁止重跑；完整旧DEV/四参考、独立canary/repair/TEST/Fresh30/E2门槛不开放。

**上述零调用根因验证已有实际结果：** 旧三题第一probe合同恢复v1 Gold1，增加production strptime正常对照v2 Gold2/3（缓存screen，不是新生成/独立score），machine trusted0；pytest旧English CLI仍拒绝。另立生成-only skip组件＋自有report定位器，实际自动到skipping.py:239生产窗口，fixture为synthetic不计研究score；旧native guard不解除、尚未接Agent。重叠窗口无损压缩实际reserve只省6，未解budget、不接live。[最新已做/未做清单](research/E1C2_CONTRACT_RECOVERY_RESULTS_2026-10-07.md)。下一步统一新DEV编译/typed generated-fixture接口后再冻真实旧DEV方法与预算；不直接抽canary或付费重跑旧入口。

本次零调用后的最终工程单次1292passed/4skipped/33warnings/0failed（61.87秒），Ruff/规定预算V3重点18/原V3 preflight均通过；旧paid SHA不变，累计可见usage375466不增。source-format正常对照不证明时区语义等价；native实际组件只支持一类生成skip用例，不能包装成第三条研究成绩或通用harness。

环境与工程：授权正常stop确认后台退出，仅两个IPC目录备份（20261007-081928），普通start成功；engine/全12immutable镜像核验。各namespace真实合成smoke两仓库controls2/2通过、反馈消费、通过target不计bug，不能当任务score。最新完整1243passed/4skipped/33warnings/0failed（56.86秒）、重点50passed/Ruff、规定V3 preflight ready=true。准备时blocked→恢复→冻结/运行的全过程在集中日志；[v1](../data/e1c_evaluation_2_bounded_runtime_v1_result.json)/[v3](../data/e1c_evaluation_2_bounded_runtime_v3_result.json)/[v4](../data/e1c_evaluation_2_bounded_runtime_v4_result.json)绑定原SHA。旧“待启动/未冻结”收据均历史，不当作命令许可。

## 1. 完成情况

| 环节 | 证据 | 状态 |
|---|---|---|
| DEV12 身份、镜像 | 12 张官方等价镜像曾完成本地核对 | 已完成准入；每次运行仍须核验现场 |
| DEV12 官方双准入 | Base-Fail 11/12；Gold-Pass 9/12；同时满足 9/12 | 异常题保留在固定分母 |
| 自动定位 | 9 个准入任务的公开 issue / exact-base 生产窗口冻结 | 无人工选文件；有窗口不等于定位正确 |
| DEV v4 复现 | 8 次 Flash 请求 / 25,424 tokens；5 个重复失败候选、4 个 Gold 区分 | 人工语义审核后可信 4/12，跨 2 仓库 |
| 旧 DEV 零调用形态审计 | v4 的 9 条记录：3 个调用后标记、1 个值比较、1 个吞异常、2 个不支持结构、2 个无候选 | 只做结构筛查；9/9 语义状态仍未验证，不增加可信数 |
| 独立 canary v1 | 2 请求 / 5,755 tokens；可信 1/3 | 未达 ≥2/3；负结果封存 |
| 独立 canary v2（传输修订） | 3/3 镜像/双准入；3 次 Flash、13,783 tokens；1 个重复失败候选、Gold 区分 0 | 可信 0/3，未达 ≥2/3；负结果封存 |
| 旧DEV合同A/B v1/v2 | v1 B因SDK处理截断中止、不重试；v2两臂各9题完成，Gold各1/12 | 无证据直接取代基线；[分账报告](research/E1C2_DEV_CONTRACT_STUDIES_2026-10-05.md) |
| source-contract hybrid | 新生成15请求/29,864 tokens，Gold3/12；controller v2缓存回放4/12、零新增调用 | 仅DEV开发证据，含人工语义审核；不是独立成绩 |
| 独立hybrid canary v3 | 镜像3/3、双准入2/3；3Flash请求/7280tokens | 可信1/3，固定分母3，负结果封存 |
| 最新旧DEV hybrid v3 | 弃答STOP/路径锚点；9题新生成、12请求/24712tokens | 可信3/12（含人工审核），未保留四条参考，开发门槛失败 |
| Counterfactual零调用 | 九条B审计：1 supported/5 unproven/3 abstain；同元素对照两次拒错fixture，缓存回放4/12 | 仅局部开发证明，target/oracle不改，非独立/非新生成成绩 |
| Counterfactual新生成 | 原九题/固定12，13Flash请求26762tokens，Gold4 | 经人工可观察行为审查4/12，array不是原报告同一报错位置；四参考保留 |
| 第4批独立canary | 镜像3/3、双准入2/3；3请求5596tokens | 0/3负结果封存，不换题/重算 |
| 输入事实保真/导入归属定位 | 公开fixture AST无assert/输出答案，3题4safe块；自动找到继承fit，关系/深度/seed/SHA可追踪 | 零调用审计与新协议已冻，不手选文件 |
| Faithful DEV原生成 | 原九题16请求37593tokens，无provider失败/重试 | 原验证INFRA_INVALID保留，不回填、不报0/12 |
| 运行态恢复/完整0付费回放 | engine/9个image健康；9题执行、6候选Gold5/12，无缺缓存角色 | 原四参考保留、新Lasso候选；人工行为审查5/12，机器trusted仍0 |
| 第5批独立canary v5 | 三镜像核验、双准入2/3；实际3Flash请求9642tokens，无重试 | 0/3负结果封存，不再重测；Sphinx source identity失败不送模型 |
| 新DEV import/执行形态原型 | 旧9题零调用审计，3题4个新增定义窗；8份旧缓存候选中1份未调用函数体 | 6项新专项通过；未接入新生成/未证明复现效果，不抽第6批 |
| 新版DEV执行接线 | terminal→import→lexical，同预算；显式direct_script/无参数call_entrypoint、解析兼容原B oracle；每请求engine检查 | 18项专项、隔离合成成功/失败入口验证；旧DEV预检9题、≤18/80000，新付费0 |
| 资源清理与当前engine阻塞 | 15个封板canary本地镜像移除，DEV12全12与源码/记录保留 | 清理后engine曾核验健康；后发现已停止，普通重启旧IPC失败，不推断清理造成停机 |
| 新版 Agent 补丁 + official grade | 尚无结果 | 未运行 |
| 受限运行反馈闭环 | 两仓库真合成smoke/格式/实际历史接线；三次screen共29请求70977tokens，v4实际执行控制反馈 | 0选定候选、grader attempted0；negative封存，停本轮paid扩批，继续零调用根因验证 |
| 零调用合同恢复/定位 | 同三题第一probe：v1候选/Gold1，source-format v2候选/Gold2；生成-only skip组件与report→生产window实际运行 | cached screen2/3、非新生成/非独立/非repair；原pytest合同仍invalid，native Agent接口尚未完成 |
| 统一编译 / 引用编号真实完整DEV | 两轮各九准入、固定12；26/74336→Gold3/12，26/89923→Gold1/12；四参考2/4→1/4 | 机器trusted0，后者质量未提高，不best-of；原件分别封存，先DTO/control/readiness零调用修复 |
| A fallback 前置有效性零调用审计 | 原九题/五A：一份同元素对照两次失败、一份constant assert拒绝、三份unknown；模型/Gold读取0 | 局部拒错实证，未接live/不产生新可信数；[结果](research/E1C2_FALLBACK_CONTROL_ZERO_DEV_RESULT_2026-10-06.md) |
| 严格同版 DEV30 / Fresh30 / E2 main | 尚无结果 | 保持门槛关闭 |

**现存人工环节：** Gold 区分不能自动证明 probe 忠实表达 issue。最新5/12包含人工可观察行为审查，底层`trusted_reproducer=false`保持原样。后续分别报告自动准入和人工审核后结果，不合称“全自动可信”。

## 2. 当前瓶颈与最新入口

**最新完成：A fallback 的任务无关拒错原型与旧DEV离线审计。** 自动保持literal/长度/API其余参数，三项labels对一列X的派生list对照仍两次失败；常量assert拒绝。原五A中三份unknown，模型0/Gold读取0、V4成绩不改。下一步须补跨仓库有效正对照与返回结构/消费关系，再另立runner把A校验接在target/Gold前；本次尚未接live，不能视为完整fixture质量gate，更不能凭两项拒绝启动第6批。[验收清单与收据](research/E1C2_FALLBACK_CONTROL_ZERO_DEV_RESULT_2026-10-06.md)。

当前工程验收：专项24passed、指定重点18passed、Ruff通过，原V3 preflight ready=true；完整单次1201passed/4skipped/33warnings/0failed（79.82秒）。工程数与复现/修复指标分开。

**当前不再付费重复提示微调，先在旧DEV做fixture前置条件/正对照机制。** Docker授权联合IPC备份后恢复，DEV12全12和本机bridge状态健康。V2一次真新生成12请求36689tokens、Gold3/12；controller-owned缓存兼容0调用回放仍3/12；V4另冻提示/语法后14请求35889tokens、Gold2/12。全部原件/负结果封存，四参考未保、不能best-of合并或抽第6批。V4把可信A指令System/数据Human/最后明确生成，A5/5返回source不再echo，但不代表复现质量提升。第一瓶颈已转fixture有效性/grounded oracle/有限执行覆盖；[V4结果](research/E1C2_CONTROLLER_GENERATION_V4_RESULT_2026-10-06.md)、[V2/缓存诊断](research/E1C2_EXECUTABLE_DEV_V2_RESULT_2026-10-06.md)。

IPC恢复已按用户确认完成，备份后缀20261006-135813，未触碰VHD/代理/tunnel/密钥。没有新下载需求。V2/V3-cache/V4的preflight/run/gold均已完成，**禁止再运行这些已开始的入口**；旧准备收据只历史，不按engine阻塞旧状态重跑。五批独立结果不变，旧DEV5/12不补进本次分数；TEST/C5/Fresh30/Agent repair/E2关闭。本轮实际新增72578，10月5日起累计可见usage304489（含旧SDK错误4281，非账单核验）。

此前零调用原型与v1/v2审计仍保留，见[摘要](../data/e1c_evaluation_2_import_prefix_dev_audit_result.json)，本版已正式接线但尚无新生成效果。完整回归持久XML1171tests/0failures/0errors/4skipped，即1167passed/4skipped（50.579秒）；必须区分工程/合成与研究得分。按用户允许仅清理15个旧封板canary镜像缓存，非强制精确tag，无container引用且与DEV12不重叠；12张DEV12、两旧DEV30镜像及alpine保留、源码/响应/账本/所有seal不删，清理后真实engine与全12曾现场复核。D空闲前约38.31/后38.19GiB，不能把44.54GB标称镜像量当实际主机释放；未收缩/移动VHD、改registry/代理/tunnel或读密钥。历史若需重执行须按旧digest重新取得镜像，不能假称缓存还在；[完整清理收据](../data/e1c_evaluation_2_closed_canary_cache_cleanup.json)。后来Docker停机原因未确认。

v2新增guard与别名/ref负例后最新完整单次**1175passed/4skipped/0failed**，33warnings、65.46秒（XML1179tests/0errors/65.136秒），重点26passed/Ruff通过。未修改旧freeze、断言、timeout或skip；首次加固中间1172passed完整记录保留，不拼接结果。v2没有配置freeze/模型调用/新修复得分；不能把这次工程增量说成8个任务修复。

上述1175是当时工程状态；后新增controller grammar/数据-指令隔离与回显负例，完整单次**1181passed/4skipped/33warnings/0failed（68.70秒）**，规定V3 preflight ready=true。这只是工程回归。V4 ndarray probe训练X一列却给三项feature_names，pytest probe造FakeItem且assert True，Gold后仍失败；不能把稳定失败当可信。下一版先把生产guard/输入维度/返回结构/已执行行为检查变为可验证的前置关系与正对照，未知不自动修数值或放松native fixture边界。

第4批method/identity/transport原件与最早0调用receipt保持，当前由[封存结果](research/E1C2_COUNTERFACTUAL_CANARY_V4_RESULT_2026-10-06.md)补充执行状态：PVLib环境兼容失败，SymPy缺关键窗口而弃答，scikit两个probe base通过。方法/样本不重抽，不能在本批补规则重报独立。下载/admit/public/run/gold旧命令不再运行，TEST/C5/Fresh30继续关闭。

canary v3保留身份Flask-5063、PyVista-4226、SymPy-17150，方法SHA`978a0b86ba70f7cf9c7fd9add3a123c682202afb73d401ade4cb15b3c2bc7a44`未变。用户完成下载；Flask/SymPy双准入、PyVista Base没有明确目标失败记录，保留分母。两题模型共3请求7280tokens；Flask候选行为偏离且Gold不区分，SymPy经审核可信，最终1/3。见[完整结果](research/E1C2_HYBRID_CANARY_V3_RESULT_2026-10-05.md)。不得换题/在已看身份调参后重称独立；repair、sealed TEST/C5/Fresh30继续关闭，冻结协议和下载收据作为历史保留。

下面是旧v2基础设施与负结果背景，不作当前执行命令：

2026-10-05 用户允许仅小型官方元数据使用本机 7892。新增并封存传输修订 `e1c2-canary-v2-metadata-proxy-v1`，保持原选择身份和 14 份方法文件。官方认证及 manifest 经代理，镜像站 manifest 直连，三张镜像摘要 **3/3 一致**；官方响应正文仅 **26,333 字节 / 6 请求**。新 seal 位于 `.codex/e1c/evaluation_2/canary-v2-metadata-proxy-v1/image_transport.json`；原 direct-only 路径仍无 seal，历史失败保留。这是同一三题 cohort 的基础设施修订，不是新抽样。

用户已下载 **3/3 镜像**，本机image ID/源码身份及六项官方Base/Gold全部通过；公开issue/生产窗口3/3物化，各四个窗口。冻结新live身份后一次调用Flash三题，实际13,783 provider tokens（硬上限42,000、无重试）。可信复现 **0/3**，该批关闭。环境已可运行，主瓶颈转为生成与定位质量。

- 元数据代理限官方 token/manifest，最多 9 请求、200,000 字节/响应、2,000,000 字节累计正文；无跳转/重试，拒绝 blob URL。
- 下载只读取缓存 seal，镜像层通过空 ProxyHandler 直连；用户关闭 VPN 全局/TUN，Docker 保持 No proxy，再用新入口下载。
- 本批 `admit/public/live/Gold` 已执行并封存，不再重复。Seaborn输出回显/不可解析；Marshmallow构造fixture错误，Gold后仍失败；pytest因相关生产窗口不足而明确弃答。

完整结果与账本摘要见[第二批负结果](research/E1C2_CANARY_V2_AMENDED_RESULT_2026-10-05.md)。[传输协议](research/E1C2_CANARY_V2_METADATA_PROXY_AMENDMENT_2026-10-05.md)、[live协议](research/E1C2_CANARY_V2_PROXY_LIVE_PROTOCOL_2026-10-05.md)和原[直连尝试](research/E1C2_CANARY_V2_DIRECT_DOWNLOAD_HANDOFF_2026-09-30.md)保留，命令只作历史证据。

## 3. 严格验收定义

1. **非公开断言输入**：生成侧只使用公开 issue 的允许自然语言投影与 exact-base 生产源码；不读测试断言正文、题面可执行断言、Gold、官方测试/评分日志。新生成的行为检查须有 issue 依据。
2. **非人工定位**：同一规则自动选择文件/符号/窗口，记录来源、排名、预算；无任务 ID→文件表、人工挑文件、逐题特例。
3. **可信复现**：无网络、不可变镜像，同一 probe 两次稳定 base 失败；独立 grader 中 Gold 消除失败；环境异常和语义不符不晋升。
4. **真实修复**：Agent 生成补丁，经盲态验证后由独立官方评分判 resolved。Gold-Pass 不算 Agent 修复成功。
5. **全通过**：代码回归零失败、同版 DEV30 30/30 resolved、Fresh30 30/30 是三个不同指标。固定分母、不合并版本最好结果、不把未运行算通过。

## 4. 待办与放行条件

| 顺序 | 工作 | 完成证据 | 失败分支 |
|---|---|---|---|
| 0 | v2 负结果与当前入口保全 | 原response/state/ledger不回填，公共摘要/结果页已写 | 不拼接旧DEV成功数 |
| 1 | 响应分类/行为合同已开发 | v1 SDK失败保留，v2 raw JSON两臂完整；issue oracle固定 | 无完整A/B优势，不包装增益 |
| 2 | 正对照/生产覆盖已开发 | API/类/traceback统一选择、生产AST/真实import证明，合成与旧DEV回归 | 定位覆盖不等于语义正确 |
| 3 | DEV研究与完整回归已记录 | Faithful回放Gold5/12；全仓1151passed/4skipped/0failed | 语义包含人工审查，工程通过不算repair |
| 4 | Counterfactual局部机制已实现 | 1case literal类型对照、生产guard来源、两次控制验证；四参考保持 | 5条unproven保留，未宣称通用语义证明 |
| 4b | Docker恢复＋0付费DEV回放已完成 | 同输入/代码/响应SHA，新provider0、无缺缓存，Gold5/12 | 不重跑、不把原错误验证回填成有效 |
| 4c | 第5批独立确认已完成但失败 | 固定3，3请求9642tokens，0/3完整封存 | 不回填/重测，不晋升repair |
| 4d | import fallback接线已完成，效果待实证 | terminal→import→lexical，去重同4窗/23000，审计源/statement/source SHA绑定 | 不从断言提API；结构窗口增加不等于效果 |
| 4e | 受限执行契约已接线/合成验收 | manifest合法无参数入口确运行；参数/注解/装饰/重复入口拒绝；direct函数-only拒绝；base/Gold同source | 不猜testdir/pytester、不支持未知native harness；非普遍可达/语义证明 |
| 4f | V2/V4真实新生成与V3缓存已完成，均失败 | V2 Gold3/12、缓存3/12、V4 Gold2/12；26新请求72578tokens、retry0 | 原响应/输入/方法/state/ledger冻结，不再执行，不合并最好结果 |
| 4f-2 | 零调用fixture前置关系与正对照 | 从生产签名/guard/返回结构验证合法fixture；A fallback也需要充分控制，避免1列X/3名误触发失败 | unknown保留；不手填输入/断言，不再扩大付费或马上抽第6批 |
| 4g | 新独立确认与修复小对照 | 完整新method先冻后选历史全排除的三题；≥2/3且行为审查一致才冻repair | 负结果永久保留，TEST/Fresh30继续关闭 |
| 5 | 新修复配对小实验 | 同模型/预算 baseline/treatment，独立 official grade | 无净收益不扩批 |
| 6 | 同版旧 DEV30 | 单一冻结身份、30 行，目标 30/30 resolved | 保留失败分布，Fresh30 关闭 |
| 7 | Fresh30 one-shot | 门槛真过后先选新身份、再读内容、一次运行 | 如实报告，不回调规则 |
| 8 | E2 / E3 | 新预注册、样本、预算、提前停止条件 | operational PASS 不代表已完成 |

已封存 canary v2：`deepseek-flash`、non-thinking、temperature 0；每题≤1请求 / 14,000 provider tokens；整批≤3请求 / 42,000；单请求输出≤2,600；retry=0。实用13,783 tokens。后续“弹性预算”不改写这一冻结身份。

## 5. 一周交付

[10 月 1–7 日详细计划](research/E1C2_ONE_WEEK_PLAN_2026-09-30.md)保留原逐日安排与停止条件。截至10月6日五批独立均未达门槛，最新0/3，当前回DEV做import fallback/执行契约；源DEV5/12仍不等于独立或修复成功。本批新增9642tokens，10月5日起累计可见usage231911（含旧SDK错误4281，非核账单）。新增两个零调用原型尚需集成/效果验收；后续新DEV预算与repair都需另冻，不承诺10月7日必达30/30，不继续盲抽样本或增加模型上限掩盖机制问题。

可控交付是输入隔离和自动定位检查、一个通用复现改进、同预算 DEV 消融、冻结记录、独立结果或明确阻塞报告、可接手的状态包。**30/30 保留为目标；当前证据不足以承诺一周必达。**

重点改进：固定 issue 行为合同，限定执行反馈可修改的部分，保留明确弃答。它针对“失败候选不一定忠实于 issue”的瓶颈。已有 canary v2 方法不改；新 DEV 方法另立版本，再先冻结不重叠 canary。

## 6. WebCodex 接手

- 云端可以接源码、单测、文档和公开摘要，使用提交的 `uv.lock`。
- 本机镜像、`.codex` 原始证据、WSL 盘和 tunnel 凭证不会随 Git 同步。桥接端到端未验证，不假定云端可访问本机 Docker。
- 大文件仍由用户终端直连；长任务先确认执行器不会受已有 120 秒通道限制。
- 缺原始材料时明确报告，不虚构复跑。直接使用[交接说明](research/NEXT_SESSION_HANDOFF.md)。

## 7. 更新纪律

当前状态仅更新本页；逐轮日志只写[集中续档](research/PROGRESS_LOG_ARCHIVE_2026-09-27_CONTINUATION.md)。旧协议和结果保持原样。原全文见[完整历史快照](PROGRESS_RESEARCH_ROADMAP_2_HISTORY_2026-09-30.md)，其中“当前/下一步”只指其原日期。

### 保全快照：WebCodex旧交接全文

# WebCodex 接手：E1-C evaluation_2

交接日期：2026-10-07。仓库：`qr7896/agent-service-toolkit`。先读 [AGENTS.md](../../AGENTS.md)、[当前 Roadmap](../PROGRESS_RESEARCH_ROADMAP_2.md)、[新闭环真实结果与待办](E1C2_BOUNDED_RUNTIME_RESULTS_2026-10-07.md)，不要按历史文档的旧“下一步”直接运行。

## 当前唯一接手：API obligation真实3/4、类型观测真实2/4；先一致hypothesis政策零费，不再paid扩批

先读[最新完整结果/第4节止损](E1C2_API_OBLIGATION_RESULTS_2026-10-07.md)、[机器收据](../../data/e1c_evaluation_2_api_obligation_results.json)。两个新namespace obligation-runtime-reference-dev-v1与observed-type-reference-dev-v1均smoke/freeze/run/seal/gold完成：各8calls28363/28428，Gold3/4与2/4、machine0，不能拼4/4或当完整DEV/独立/repair；本轮56791，累计可见669477非账单核验。所有已开始入口/方法/预算/响应/state/ledger/audit不重跑或改写。

有限明确constructor参数prose→production alias/class/signature/源SHA→直接keyword目标，拒绝属性赋值/workaround/影子/死函数/动态kwargs/错qualified模块，保留旧正确目标；它是grammar-limited syntactic门槛，不是通用语义证书。真实恢复SK13496首call正确constructor，另MM两题也过（3/4）。input provenance分public AST expression vsmodel hypothesis，runtime type不自动证明。可信Controller sys.settrace/nonce/源SHA仅运行自己probe，生产guard类型不值观测，readonly/net-none/pull-never/resource limits、无model safe_static_check伪证，真正观测builtins.list；source字节不变但trace/filename/timing非等价证明，optional blocker明确skip。类型组件第二版纠正事实却SK因缺原报告dtype而弃答，MM1359不合法control弃答，2/4负结果不覆盖3/4。

当前保留3/4版作开发比较基线，observer diagnostic保留、不当默认全面升级。先统一缺expected→不能捏造与缺inputtype→明确source-consistent hypothesis的单一可执行政策，facts/hypothesis/unknown分层，不把synthetic原报化、不手修某题dtype/date/value/oracle，也不再层层append提示或加budget。再跨repo正常control、目标API/失败point/源谓词保真零费，完整method/input/budget/codefreeze后一次小screen，四参考/忠实性/cross-repo gate后完整DEV/native DTO/确定性证书/独立评分，才新不重叠canary≥2/3/Agent patch/official/new任务。当前不扩九题/第6canary，不开TEST/C5/Fresh30/private Test500/E2。

最新工程单次1372passed/4skipped/33warnings/0failed（92.73秒，XML1376/0errors/0failures/92.702秒），Ruff/规定budget V3重点/compact preflight ready=true，未弱化旧assertions/skip/timeout。本轮无Docker重启/IPC/镜像下载删除/改VHD/registry/proxy/tunnel/key，原12DEV镜像和全部备份保留；旧strict-v5 bridge whitelist不扩，不假称Web新paid入口已验。Cloud可接本节source/zero测试；local source/private artifact/image/runtime缺失即INFRA_BLOCKED，不索key/开裸daemon。以下旧“当前/下一步”只历史，不覆盖本节。

## 当前唯一入口：Docker已恢复，cache3/4／新生成2/4；先API义务与类型假设零费，不再paid扩批

先读[最新完整结果及第5节待办](E1C2_FRONTIER_LIVE_DEV_RESULTS_2026-10-07.md)。本轮新授权仅两IPC普通stop确认→备份后缀20261007-144329→start一次成功，原DEV12全12核验，不动VHD/registry/proxy/tunnel/key/镜像，全部备份保留，该次授权已消费。原blocked receipt保持，不再按以下旧“等待授权/尚未开始zero”操作。

runtime-frontier-zero-reference-v1已run/seal/gold：cache3/4、provider0，SK26289上游无第四response缺cache不补；不是新feedback-conditioned生成，不重跑。frontier-runtime-reference-dev-v1另freeze/source/预算，代码提交aa0d282，真实12calls40135/Gold2/4，MM两题区分、两个SK弃答；机器trusted0/四参考gate不通过，不best-of/不扩九题、不抽新canary。新cap task24000/全批50000/output2000/≤16/reserve1.4/retry0，旧cap不改，不宣称单因素因果。

新guard_evidence_audit只零诊断，public API/condition→SHA-bound AST guards→自动window：SK26289十四guard，failure条件准确命中_export.py:1040且already_visible=true，不是缺检索window。模型忽略实际bool分支、用普通list目标通过后误称“源码已修好”；SK13496用属性赋值绕过public请求的constructor入口，把已经可工作的行为当预期而弃答。下一步只零费typed API obligation/入口与参数调用方式绑定、明确public事实vs未知类型hypothesis、源谓词与观测类型的对齐；未知不硬证，禁止SK/task-ID专属规则、手修array/date/expected或看Gold生成策略。保留所有raw与negative，先跨repo合成/旧cache拒绕过目标验收，新live必须另身份完整freeze再列命令；四参考/忠实性/cross-repo后完整DEV、native DTO/确定性证书/独立评分，再不重叠canary≥2/3/repair/official/new任务。

最终工程1350passed/4skipped/33warnings/0failed（89.21秒，XML1354/0errors/0failures/88.361秒），Ruff/规定budget V3重点/compact preflight ready=true，不改旧断言/skip/timeout。可见usage612686非账单核验；本轮新增paid40135、zero0，无新大下载/删除。旧bridge strict-v5 whitelist未扩，Cloud可接本节source/单测，缺local private artifacts/source/image/runtime明确INFRA_BLOCKED，不声称新模块paid端到端可用/不索key/开daemon。TEST/C5/Fresh30/private Test500/E2关闭，研究尚未完成；现所有开始过的smoke/preflight/run/gold/audit不重跑或修改其method/budget/state/response。

## 当前唯一入口：readiness新screen2/4；runtime-frontier零费研究尚未开始，Docker IPC阻塞

先读[当前结果/逐题/恢复顺序](E1C2_READY_RUNTIME_DEV_RESULTS_2026-10-07.md)、[哈希收据](../../data/e1c_evaluation_2_ready_runtime_dev_result.json)。ready-runtime-reference-dev-v1四参考已run/seal/gold：10请求32826，Gold2/4、机器trusted0；不是完整DEV12、独立canary或repair，四参考gate未过不扩批，所有该paid/smoke/preflight入口不能重跑或修改已冻method/budget/response/state/ledger。

单一DTO/精确包装/紧凑lossless quote pairs、Assert求值错误回反馈、重复无效行动第三调用前停已接线。52旧response零调用审计原accepted保留/4包装恢复，51格式解码不当51任务成功。最新runtime_frontier_zero新增13专项，控制source/execution SHA与顶层Assign(Call)故障绑定→setup后缀移到target、完整target AST相同/normal control与期望不改；free-name检查不是alias/global独立性证明。离线全部3失败control中2份同task可编译，运行0、不能报cache新增可信数。

Docker已停止、普通start一次失败，日志旧run/dockerInference IPC不可访问；没有新的IPC改名、VHD/registry/proxy/tunnel/key/镜像删除或重置，旧备份保留。已请求本轮仅Docker/run与docker-secrets-engine正常停机备份改名/普通启动一次，等待人类明确确认，不复用旧“一次”授权。若允许并恢复，确认Server/四immutable images，再按zero协议一次run，完成seal才gold。runtime-frontier-zero-reference-v1此时freeze/目录未创建；后续如已存在须以新状态为准，不能照此旧“未开始”重跑。新反馈改变后缓存动作没有重新生成，不能称因果闭环新模型成绩。

最新1344passed/4skipped/33warnings/0failed（66.47秒，XML1348/0errors/0failures），Ruff/预算V3重点/compact preflight ready=true；累计可见572551非账单核验。SK26289上轮摘要“控制失败”为误写，已纠正为control过/target未复现，原件/得分不回填。无需新大下载；Cloud可读源码/单测，缺本机source/private artifacts/image/runtime即INFRA_BLOCKED，old strict-v5 bridge whitelist未扩大，不假称Web可paid端到端调用、不索取key/开daemon端口。开发gate后才新live同四参考→完整DEV→新不重叠canary≥2/3→Agent patch/official评分→同版DEV→新任务；TEST/C5/Fresh30/private Test500/E2关闭。下面所有旧“当前/下一步”仅历史。

## 当前唯一接手入口：统一DEV两轮已封存，先零调用，不再paid扩批

先读[最新完整每题结果/六步落地待办](E1C2_UNIFIED_RUNTIME_DEV_RESULTS_2026-10-07.md)与[机器收据](../../data/e1c_evaluation_2_unified_runtime_dev_result.json)。compiled-runtime-old-dev-v1与referenced-runtime-old-dev-v1均九准入/固定12、完整新生成和Gold判别seal完毕：26calls74336→Gold3/12、26calls89923→1/12；四参考2/4与1/4，机器trusted0，不best-of。新增52/164259分属两批各≤100000，不使用Pro、不自动retry；累计可见539725非账单核验。所有smoke/preflight/run/gold已开始，不再执行或修改已冻源/响应/预算/账本，旧历史完全保留。

引用编号使原文quote错误9→0、真实11份ref证明，但格式content包装、控制/返回消费错误与额外上下文造成退化，不能“再试一次”掩盖。新contract_feedback_diagnostics仅零调用：四份精确json_object/content字典包装可strict解码，尚未执行；Assert内tuple索引TypeError被分出oracle求值错误，不混同谓词false/构造失败，诊断不是信任证书。helper尚未接live、没有新增缓存成绩，现有候选/负结果不回填。

按结果第4节先一个一致DTO→源码有效control/返回消费关系跨仓库验证→oracle求值错误回反馈/重复invalid停止→保真冗余与reserve核算。完成零调用门槛/四参考/完整回归后才另立统一新runner、method/budget freeze并展示唯一Flash命令。开发有收益才有限generated-native DTO/确定性证书/独立评分、再新不重叠canary一次≥2/3且忠实性过→Agent patch/official score→同版DEV→全新任务；目前不选第6批、不打开TEST/C5/Fresh30/private Test500/repair/E2，不保证30/30。

最新工程单次1320passed/4skipped/33warnings/0failed（56.44秒，XML1324/0errors/0failures），Ruff/规定预算V3重点与compact preflight ready=true，无断言/timeout/skip削弱。无新下载/删除/重启/IPC改名，Dfree约34.22GiB；Docker/VHD/registry/proxy/tunnel/key与所有备份不动。旧bridge白名单未扩展，Cloud可接本节源码/单测，缺本机private artifact/source/image/runtime明确INFRA_BLOCKED，不宣称Web端到端已验、不索要key或暴露daemon。下列旧“当前/下一步”仅历史，不覆盖本节。

## 最新接手增量：零费恢复2条缓存、生成式runtime定位组件已验

先读[本轮新结果/接口待办](E1C2_CONTRACT_RECOVERY_RESULTS_2026-10-07.md)。`contract_recovery`统一Compare字段语法＋已有源码构造前沿，`source_format_control`从selected production strptime静态格式导出正常control，不手修target/日期/预期；同三个旧任务第一probe、无best-of，zero v1 Gold1、zero v2 Gold2/3，provider0，机器trusted仍0。这是缓存开发结果，绝不当新生成或独立canary。

`generated_skip_harness`可信driver仅运行自生成/tmp一个unconditional skip/Pass，禁止外路径/插件/config/注入fixture、noconftest+禁止autoload；没有解除旧native guard、没有model safe_static_check伪证。真实base CLI正常定位生成文件:3、runxfail定位生产skipping:239，`runtime_location_evidence`按受绑定自有report自动归一化并取得源窗，不人工选择文件。fixture是开发者synthetic，不计第三题模型成功。原pytest两个quote已核验均来自投影issue，但自然语言CLI尚无machine-readable执行协议，不能回填为新native研究合同。组件还未接Agent/tunnel，能力有限不是通用pytester。

下一步：另立统一DEV runner接编译器/provenance；native动作必须明示machine-readable case_source/flags和有效issue/expected quote，不自动翻译旧English CLI、不允许默认收集原tests/conftest；接口与独立评分身份必须先冻、未知/注入拒绝。零调用门槛过后另冻新Flash同版旧DEV方法/预算，先列精确命令，再验证四参考与完整旧DEV；开发有收益才不重叠canary≥2/3，再Agent repair。2/3缓存和合成不能跳这些gate。原所有付费/zero/smoke/gold已开始入口不重跑或回填。

`lossless_context`重叠source往返无损，但实际10700→10694只省6、仍不够10087，保留negative不接live。新增模型/tokens0、累计可见375466不增；Docker/VHD/registry/代理/tunnel/key/IPC备份不动、无新下载/删除。以下之前negative与当时“下一步”作为历史保留，当前以本节顺序为准。

## 现在的接手任务：受限运行反馈闭环，不再继续静态提示微调

生产retrieve/read→七字段正控制→两次control后target→自生成trace反馈→4轮修订、oracle锁定和真实上一action/observation接线已实际运行。v1 12请求24976tokens格式拒绝；v2仅零调用；v3 6请求13341tokens重复query停止；v4 11请求32660tokens进入probe反馈但无合格候选。三批共29请求70977tokens、无provider失败/重试，独立grader均attempted0、机器trusted0。所有smoke/preflight/run/gold已开始入口禁止重跑，绝不补旧账本或改method/response/state/freeze。只借鉴成熟Agent思想，未安装原框架/完整debugger/Agent patch。

Docker初始IPC失败已在本轮明确授权后恢复：正常stop、只备份run与docker-secrets-engine，后缀20261007-081928，普通start一次成功；全12immutable images核验，全部旧备份保留。不动VHD/registry/代理/tunnel/key，没有新下载/删除。Cloud可做零调用分析/单测；缺本机source/image/runtime明确INFRA_BLOCKED；原tunnel旧strict-v5白名单未扩大，不默认能调用新paid入口，不开放裸daemon或索要key。

下一步仅零调用：①自己trace→生成AST的setup/故障前沿，证明target完整程序/预期不改，不人工修维度/日期；②源码/上一probe冗余压缩保持来源和issue义务，先验证reserve节约，别降低guard或借旧budget；③合同行语法/受限生成临时fixture适配器，只运行自己生成文件，不读原tests/conftest/默认收集，原native guard不解除。跨仓库与四参考证据后另冻新版完整旧DEV，开发有收益才新的独立canary≥2/3，再另冻Agent repair，最后同版对照与全新任务。停止本轮付费扩批，不把3题screen/合成/工程tests当修复率，TEST/C5/Fresh30/private Test500/E2不打开。

最新完整单次1243passed/4skipped/33warnings/0failed（56.86秒），重点50/Ruff和原V3 preflight ready=true。可见usage自10月5日起375466（含旧SDK错误4281、非账单核验），本轮70977单列。所有最新公开JSON绑定本机freeze/state/ledger/generation seal；原响应/Gold/日志不上传，初始schema接线失败与误诊修正均在集中日志。

以下为10月6日封存历史，旧“健康/下一步”不得覆盖本节。

## 当前状态

**最新：Docker/DEV12/本机bridge已恢复；两版付费DEV已完成但均未达质量门槛。** V2新生成12请求36689tokens、Gold3/12；V3缓存新增0/缺缓存0、仍3/12；V4真新生成14请求35889tokens、Gold2/12。原所有结果封存，不拼接best-of。[最新V4结果](E1C2_CONTROLLER_GENERATION_V4_RESULT_2026-10-06.md)、[V2/零费诊断](E1C2_EXECUTABLE_DEV_V2_RESULT_2026-10-06.md)。V4 A5/5返回source不再输入echo，但fixture/语义质量未提升。当前停止付费扩批/提示微调，先零调用生产前置关系与正对照机制。五批独立1/3、0/3、1/3、0/3、0/3全部保留，TEST/C5/Fresh30/repair/E2关闭。

## 当前唯一下一步：零调用fixture有效性/正对照与受限执行覆盖

已新增[A fallback零调用审计](E1C2_FALLBACK_CONTROL_ZERO_DEV_RESULT_2026-10-06.md)：原九题五A，一项control两次失败、一项constant oracle拒绝、三unknown。新增provider/Gold读取0，原V4 SHA未变。`fallback-control-zero-dev-v1`目录已经完成，不能再次运行其audit或修改已冻两模块；本次仅诊断原型，尚未接live。接手先补跨仓库合法正对照和production返回/消费关系，另立runner接A guard，再验证四参考与成本。没有新下载需要，不能直接付费或选第6批。

最新工程单次1201passed/4skipped/33warnings/0failed（79.82秒），专项24/指定重点18/Ruff均过，规定V3 preflight ready=true；原件/评分口径不变。这不是1201个task修复。下方旧工程数字和命令均属历史。

禁止重跑任何V2/V3-cache/V4/canary已有preflight/run/gold、改旧source/response/state/ledger/freeze，不能从issue/windows输入回显拼造代码。所有已开始的命令都只历史，下面旧engine阻塞/等待run记录不作当前指令。

1. 使用合成与旧DEV，源码API signature/guard/返回结构验证fixture。现有具体负例：X一列与三项feature_names不符、FakeItem与assert True无法表达原行为、generator返回形态/重复调用关系未知。先做任务无关的可验证前置关系或已知有效正对照，未知不猜；不手填字段/维度/断言，不读取Gold/test生成。A fallback同样不能只因JSON合法就绕过控制。
2. 对可证明表示/类型差异，保持literal/长度/API调用不变，派生正对照失败即停。尚不能证明的关系留unknown，不强行“修到过”。需要native/generated fixture harness则明确来源/执行模式，当前guard保持禁用未知pytest.main/runpytest/fixtures，不重新运行五批已看样本称独立。
3. 明确docs/特性请求与行为bug的任务无关路由及覆盖限制；缺行为期待不能制造异常。完成零调用验收、四参考/两仓库的机制证据后再另冻完整旧DEV方法/提示/预算/源码，一次新生成比较效果与成本；无收益不抽第6批，不继续付费提示微调。最后独立方法仍须先冻、再metadata-only全历史排除，≥2/3才另冻Agent repair。

本轮真实新增26请求/72578tokens，SDK/provider重试0；10月5日起可见usage304489（含旧SDK错误4281，非账单核验）。最后工程1181passed/4skipped/33warnings/0failed（68.70秒）、规定V3 preflight ready=true；不是修复率。IPC已授权正常stop/两目录备份后普通start一次成功，备份后缀20261006-135813；Docker29.4.0，DEV12全12与现有bridge Docker status现场正常，不等于Web私有连接端到端已验。无新的大下载/删除、VHD/registry/代理/tunnel/密钥不动，原15旧镜像清理收据不回填。

Cloud可以接源码/单测/文档/上述零调用设计，但缺本机source/cache/image/执行器时明确INFRA_BLOCKED，当前bridge仍旧strict-v5工具，不默认允许新paid模块。不要复制旧研究命令或索取密钥，不要开放裸Docker端口。所有新结果SHA绑定公开JSON，真实评分/Gold/test和原完整日志留本机.codex。

## 以下为已完成IPC恢复与V2准备（历史，不再执行）

已按用户允许移除15个已封板canary镜像缓存：与DEV12 disjoint、无容器引用、精确tag/non-force，全部源码/响应/账本/manifest/所有旧freeze保留。[清理收据](../../data/e1c_evaluation_2_closed_canary_cache_cleanup.json)。DEV12全12、两旧DEV30和alpine保留，清理后全12与engine曾真实核验；Dfree约38.19GiB，未收缩/移动VHD、删文件、改registry/代理/tunnel/密钥。旧canary如需历史复核必须重新获得原digest镜像，不能假称本机镜像仍存在，不建议再跑旧研究入口。

后来桥接docker_status返回docker_ready=false，CLI同样缺LinuxEngine管道，Desktop/backend进程当时未运行。普通start一次失败，日志再报Docker/run/dockerInference旧socket；没有证明停机由image rm引起，不擅自删IPC。已向用户询问：仅正常停止→同次停机备份改名`C:\Users\qq人\AppData\Local\Docker\run`与`C:\Users\qq人\AppData\Local\docker-secrets-engine`→普通启动一次。没有确认不可强杀WSL、factory reset、动VHD/registry/代理或tunnel。桥接文件/密钥未改，但engine不可用时桥接Docker工具也不可用，不能称端到端健康。

获准恢复后：确认真实server与DEV12全12 image ID→当前模块preflight→核源码/输入/budget freeze，重新计算reserve→展示唯一精确run命令、Flash/最多18/实际80000/每题20000/输出3000、0重试，再用既有≤100000授权一次run→同模块gold独立评分。此时仍固定12/九双准入，不从五批canary补样本，不立即选第6批；四参考/两仓库/新机制/成本必须实证。没有新镜像下载需求。v2尚未冻live配置，v1原型freeze不可重跑或改写。

现在代码入口：`evals/e1c_evaluation_2_executable_dev.py`与`execution_contract.py`，两模式direct_script和A call_entrypoint；唯一普通无参同步函数，append一次调用，非法入口拒绝。B spec剥离后仍原合同；原fallback解析器同时接新schema，避免manifest让oracle锁定意外跳过。保留已有静态安全+无网络容器。v2显式拒绝native runner/生成文件工具及其直接引用/常见别名，不作普遍Python语义证明，不猜testdir/pytester、不隐式发现官方test。合法入口合成在真实隔离容器中曾观察到函数体；这不是SWE score或Agent repair。

v2工程最后26重点passed、全仓1175passed/4skipped/0failures/0errors（65.46秒），未削弱任何旧断言/timeout/skip。当前收据[data](../../data/e1c_evaluation_2_executable_dev_v2_preparation.json)明确新provider0/无budget freeze。新增付费累计本轮0，10月5日起可见usage仍231911，不继续亏预算试跑没有engine的任务。桥接`docker_status`实际因engine不可用返回false；隧道/密钥/服务文件未改，未验证Web端到端新DEV工具权限，不默认现有strict-v5 bridge允许新paid模块。云端可以接源码/单测/文档；缺本机缓存/镜像/执行器就报告INFRA_BLOCKED，不改身份、伪造评分、索取密钥或开放裸daemon端口。

## 以下为上一轮DEV原型规划（历史，接线已完成；未完成的native harness仍保留）

禁止再执行v5的select/download/admit/public/preflight/run/gold或任何旧canary/cache回放。原方法/身份/输入/响应/账本/Gold日志不回填；v5的新method/identity/source/state/ledger SHA见公开结果。它已看过，不在该三题补规则后仍称独立。

已有新`evals/e1c_evaluation_2_import_seed_audit.py`原型与6项专项：公开示例开头import-only→生产AST/reexport定义，遇非import即停，不从断言/函数体/输出值提名字；明确拒绝测试/答案型名字、能力根、wildcard、歧义。旧DEV九题零调用v1（代码3cb7bf9）与加固v2结果分别保留，当前只是结构覆盖审计，**不是新复现成绩**。`invocation_status`保守识别direct-script未调用函数体，旧DEV8候选中1份命中；对已封存v5的诊断只作事后解释。

直接接手实现下面三个阶段，先本地合成单测/旧DEV零调用，不要立刻付费：

1. 把import fallback接入另立新版DEV的证据构造：terminal API窗口优先，之后生产归属import定义，再旧词法；同4窗/23000字符预算、源SHA/depth/seed，未知或溢出不猜，不按task ID指定文件。断言值/函数名改变不得改变import来源；证明新窗口对目标API有实质作用，不能只数窗口。
2. 明确probe manifest的执行模式、入口、fixture来源与可观察检查。函数-only明确拒绝，不把Python退出0当测试执行；不能自动猜testdir/pytester参数。先证明合法入口真的运行、非法/未知入口拒绝。若需要可信临时fixture/native harness，全部隔离/无网络/不读仓库官方test或Gold，协议另冻；未做到不能写“执行契约已完成”。
3. 上述零调用门槛与完整回归通过后，另冻旧DEV方法/配置/预算/源码，展示精确Flash命令。候选计划最多18请求/批80000/每题20000/输出3000/重试0，**尚未冻结或运行**；实际reserve不够即停。完整固定12、九题准入，四参考保持、跨两仓库、效果/成本分别报。无实证提升不抽第6批；有提升才完整新method先冻后metadata-only排除所有历史（含v5）选一次三题，≥2/3且行为审查一致才另冻Agent repair。

截至本次累计10月5日起可见usage231911（含旧SDK错误4281，非账单核验），本批新增9642。完整代码回归通过，最新实测数见Roadmap 2/集中日志；规定V3 preflight ready=true，未改已冻结预算/V1/V2/V3代码、断言、skip或timeout。小型安全摘要/代码可同步Git，原件仍在本机.codex；云端缺源/镜像/执行器即INFRA_BLOCKED，不伪造重跑、索取密钥或开裸daemon端口。Docker/VHD/代理/tunnel和IPC备份不动。

## 以下为v5准备记录（历史，已完成，不再执行）

下方“未读/未下载/尚未调用”只表示当时准备时状态；以页首0/3封存为准。

开发gate通过，已先提交方法代码/协议b794f3a，再封存52份方法文件03ef71a；method SHA7fe8bf6c1fa9c0acbe82915ba43410b0f95db65615bb3def949dc5b1801feab3。新模块`evals.e1c_evaluation_2_faithful_canary_v5`，新目录`.codex/e1c/evaluation_2/faithful-canary-v5`。按既有metadata-only盐序排除所有历史/四批canary，选固定三题无替补；本次截至此处未读新issue/Gold、未调用provider或下载blob。完整[选题前协议](E1C2_FAITHFUL_CANARY_V5_METHOD_2026-10-06.md)。不要重复freeze-method/select；不要运行任何旧v4/v3/cached replay入口。

顺序：identity完成→仅官方task.yaml metadata/授权7892小官方manifest→用户关闭VPN全局/TUN且Docker No proxy直连下载→本机admit/public/preflight→列精确run命令/Flash/最多6请求/60000tokens→一次run/gold。每请求之前真实engine/image检查，不以磁盘loaded.json代替。任何失败保留现场，不自动provider重试、不调当前canary后继续称独立；≥2/3且人工行为审查通过才另冻repair，机器/人工结果分开报。Agent repair/TEST/C5/Fresh30/E2仍未开放。

identity和小型transport现已完成：排除304身份，SymPy-22080/Sphinx-9180/pytest-7749，identity SHAbaa5abda0f8151dba915a13975ab014ca4b5315080a1c7b39426d17ab96d294b；transport SHA3b1892690e3b70edbbf6a356ee349b1382a434e6562addbf2126432d1be6090d。官方摘要3/3一致，7官方Docker小metadata请求/25899正文bytes，blob/provider0。三镜像本地tag均不存在，压缩2.946GiB；大文件交用户，直接复制[本次终端命令](E1C2_FAITHFUL_CANARY_V5_DOWNLOAD_2026-10-06.md)。新题issue/Gold仍未读，不再调用select或重抽。下载后才按上述顺序零调用准入，未准入题保留分母3。

工程完整单次1151passed/4skipped/33warnings/0failed（54.23秒），专项22passed、指定预算/V3重点18passed/Ruff通过，原V3 preflight ready=true。首次测试漏UTF8参数/另一次V3强制UTF8导致子进程编码异常都保留为命令环境异常，不修改冻结代码/断言。所有原记录和IPC备份留存；不动VHD/镜像/tunnel，不假称tunnel端到端已验证。自10月5日可见usage仍222269，本轮新增付费0。云端缺本机.codex/source/image/执行器即INFRA_BLOCKED，不索取密钥或开放裸daemon端口。

## 已完成的缓存恢复准备（历史命令，不再执行）

以下保留当时Docker不可用的接手记录；其preflight/run/gold现已完成，结果见页首。不按旧“当前/未执行”继续运行。

普通Docker Desktop启动未恢复；日志明确旧`Docker\\run\\dockerInference` IPC socket不可访问，backend退出。用户确认尚待：仅正常停止Docker、备份改名`C:\Users\qq人\AppData\Local\Docker\run`目录、再普通启动。未触碰该目录/注册表/WSL/镜像/VHD/代理/tunnel。没有确认不可factory reset/global prune/强关全部WSL。Docker start/status查询可能后台挂起，勿再叠加启动或付费run。

确认并恢复后必须先真实`docker version`含Server及九个immutable image ID全部可inspect，再在本机执行以下**零模型**命令，任一步非0即停，不自动重试provider：

```powershell
foreach ($stage in @('preflight', 'run', 'gold')) {
    uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_faithful_infra_replay $stage
    if ($LASTEXITCODE -ne 0) { throw "零付费回放停止于 $stage；保留原件，不自动重试。" }
}
```

新目录faithful-input-dev-v1-infra-replay-v1；cache-only model不使用真实钥匙、不发HTTP，原usage标upstream、新provider0。原方法/输入/preflight须与源freeze相等，绑定原全部response SHA；环境transport失败立即中断，不当软件证据。没有收集的缓存角色记controller缺失、不补模型调用、不假称模型弃答。独立[协议](E1C2_FAITHFUL_INFRA_REPLAY_2026-10-06.md)。截至交接回放未执行、无有效新分数。

新faithful_dev run/gold已执行（评分无效），严禁再次运行；三张v4镜像已下载、canary模型已结束，下方旧download/admit/public/run/gold均为历史。旧code/state不回填，新结果另立。原source freeze00ab5ba6ccb4a3755b014191ddcb2c6aee5d989dd13b67d4825390b68b457581，state516721755853e07629e02d0980ca405b3df5d2483f576802b29e5837e399888e，ledgerb590d99136bfa8a78201bbfec41b631fc4f501030631fd46929d824f1af91307。云端clone缺本机.codex/cache/执行器即INFRA_BLOCKED，不索取密钥、不伪造复跑或开放裸Docker端口。

有效DEV改进证据与独立≥2/3仍未达，不选新canary、不启动repair/TEST/C5/Fresh30/E2。自10月5日以来可见usage222269（含旧SDK错误4281，非账单核验），当前不续付费。最后工程单次1148passed/4skipped/33warnings/0failed（49.54秒），只表示代码回归，不保证Docker健康。所有原件及四批负结果保留，集中日志唯一入口。

## 以下为旧counterfactual/v4执行交接（历史，不按其“当前”操作）

历史counterfactual新生成4/12、13请求26762tokens，包含人工行为审核、非原报告同一错误栈，不是修复率；当时进入第4批准备。该批现已0/3结束，不能用旧DEV成功数补入分母。

新的入口为`evals.e1c_evaluation_2_counterfactual_canary_v4`；完整方法SHA`88df1067d0770a74ebe6d72d7eee74b78c3135defd1659b97c7b444c5fbd21ea`先冻，metadata-only排除301历史身份后选PVLib-1048/SymPy-20131/scikit-15535。identity SHA`06d55d996a2f6786d8718340d24c8debd5e8c2a566897cf55c3b24e114f3a337`；三张官方/mirror摘要一致，官方小metadata7请求/26342bytes，模型/blob0。公开[下载收据](../../data/e1c_evaluation_2_counterfactual_canary_v4_transport_receipt.json)。尚无该批泛化或修复结果，不能重选或改冻结依赖。

## 当前需要用户终端：直连下载新三张

压缩层PVLib1.587/SymPy1.064/scikit1.396GiB，总4.047GiB；实际安装体积更大，逐张磁盘守卫最大约29.52GiB。D现场约42.2GiB，不承诺最终空间必够，触发守卫即停、不自行prune。平均1–5MiB/s传输约14–70分钟，加校验/导入粗估40分钟–2小时；0.2MiB/s仅传输约5.8小时，单镜像硬超时6小时。逐层进度/速度/ETA、Range续传、SHA校验和导入心跳沿用原实现。

官方元数据seal已缓存，这条download不走7892/官方blob。先关闭VPN全局和TUN、Docker No proxy；显式空代理不能绕过系统级透明路由。只使用**新模块**：

```powershell
Set-Location 'D:\codex\working\project20260827'
Start-Transcript -Path '.codex\e1c\evaluation_2\counterfactual-canary-v4\download.log' -Append
try {
    uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_counterfactual_canary_v4 download --timeout-per-image 21600
    if ($LASTEXITCODE -ne 0) { throw '下载中断，保留缓存/日志，不进入模型实验。' }
} finally {
    Stop-Transcript
}
```

返回verified_loaded=3后核验loaded/transport与Docker ID，再按同一新模块依次`admit --timeout 900`、`public`、`preflight`；每步非0即停，infra失败保留固定分母3、不换题。完成live freeze才列精确`uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_counterfactual_canary_v4 run`：Flash≤6请求/60000tokens、单题2/20000、输出3000、重试0，沿用用户≤100000许可。结束后同模块`gold`独立评分/语义审核；一次可信≥2/3才另冻repair，不打开TEST/C5/Fresh30。下方所有v3历史命令不重跑。

原counterfactual_fast_dev已经run/gold完成，不重跑；原counterfactual_dev慢入口只有零调用freeze，不再另开付费trial。快输入适配逐次重查Git/base/生产SHA/image身份，上游九条输入与慢入口逐字一致，不是手选文件。云端无本机原件/执行器则报INFRA_BLOCKED，不复制密钥/公开评分答案或开放Docker裸端口。

最新工程全仓1127passed/4skipped/0failed/33warnings（142.85秒）。首次并发重负载导致原Streamlit8秒超时，已记录；失败项原样单独通过，再串行完整通过，未改超时或断言。所有旧模型试验/record/镜像/VHD/tunnel设置保留，累计本日可见usage179080（含旧SDK错误4281，非账单）。第4批至多60000，不无限扩批。

以下为上一轮DEV v3的历史要求，counterfactual机制现已完成；未支持的五条pair仍保留unproven，不能把局部证明扩大为普遍语义证明：

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

## 2026-10-07：执行器重入覆盖根因、真实链修复与同版四参考Gold4/4

完整读研究执行/监控与ponytail技能，无subagent/新依赖。v1 execution-plan将control_failed和source-bound裸Name条件/自己的类型观察转为有限next-evidence计划，不改输入/期待，不升可信；六新单测/重点30/Ruff、两repo真实synthetic正常control、完整1394passed/4skipped（62.78秒）、规定compact preflight过。全部六旧响应零费审计有2normal配置plan、source-bound hypothesis0，追查实际根因而非直接付费：outer loop hook为true，compiled runner内部再次配置后为false。旧obligation/observed/codec目录有executed候选但API义务/类型观测产物0；此前组件已在paid链生效的解释不成立，原3/4、2/4、2/4成绩/文件/协议不回填。v1 zero源码/smoke/audit保留、provider0，未重跑原namespace。

另立v2 namespace，compiled executor所有者也绑定捕获delegate完整链，内部重入与异常恢复有3新回归，不编辑任何已用v1/旧source。两repo真实synthetic smoke与重点27/Ruff、完整1397passed/4skipped（73.78秒）过；五份旧probe按全部原响应顺序零模型离线执行（不按Gold选、不是新反馈生成），API/uncertainty/plan5/5、适用1个runtime type观测与source-bound implicit-operation计划、2normal配置计划，Gold读取0。源码先commit0c986a5，freeze e676d9f37075c54fd8f47d9f16dae28ea21346a777a67e649a19af65b6dfe43e；列精确execution_plan_dev_v2 run、Flash only/nonthinking/温度0/16calls/批50000/题24000/output2000/reserve1.4/待跑首reserve保护/retry0后执行一次。

真实新生成四题各首call候选，4started/completed/11,909provider tokens、无provider失败/retry，producer completed/seal完整核对；paid API/uncertainty/plan产物4/4。独立Gold attempted4/区分4，四参考数值gate首次同版通过，但原固定12/九准入/screen4分账，不是完整DEV/独立/repair/30题成绩。类型observer paid未触发（四目标直接失败），不能声称其造成4/4；模型新生成/接线/计划提示并改，不声称单因素因果。既有compiler派生control或移动setup前沿仍存在，plan组件不改不等于全部Controller绝不转换程序。

新增witness_grounding_audit仅零执行审全部4候选，不Gold挑：1项期待引用是File traceback，实际array在参数校验失败，公开guard未在两次trace中观察到；其它3期待仅未分类待语义证据，不授可信。not_observed不是全局不可达或故障无关证书，matching site/Gold也不证语义。5新正负单测、Ruff通过，最终单次1402passed/4skipped/33warnings/0failed（60.81秒）、XML持久，无assertion/timeout/skip削弱。machine trusted0、语义gate未过，按协议停止本轮付费扩批，不开第6canary/TEST/C5/Fresh30/private Test500/Agent repair/E2。

公开data/e1c_evaluation_2_execution_plan_results.json绑定freeze/state/ledger/seal/Gold/实际hook产物/zero chain与诊断/工程XML；本轮11,909，自10月5日起可见725,352非账单核验，不作整个项目总账。两旧结果页追加接线更正、原正文与分数保留；两Roadmap/Web handoff单一当前入口更新为期待角色在oracle lock前接线、失败位置/接口义务双标签与跨仓库反例，再新冻结四参考/完整DEV/native/独立确认/repair路线，不继续叠提示或无机制采样。

本轮无下载删除/重启Docker/IPC/VHD/registry/proxy/tunnel/key改动，全部旧记录和备份保留；Cloud只接source/zero tests/脱敏摘要，缺本机材料明确INFRA_BLOCKED，旧bridge白名单不扩，不假称Web paid新入口端到端已验。raw/probe源码/Gold/test/key不上传，仅安全源码/协议/单测/分账摘要同步Git。研究未封板、不保证完美或30/30。


## 2026-10-07：期待在lock前筛查、公开API对照源绑定，新生成3/4与零费normal诊断

本轮继续普通软件缺陷评测，完整读research/ponytail执行与监控规范，无subagent/依赖新增。新增expectation_dev复用quote catalogue/解析、source resolver/guard、inner完整delegate链。trace/mixed trace/code/literal/不完整guard/empty期待在oracle lock前拒，unknown prose不自动可信；明确works/succeeds for/with→but not for/with单一两qualified-call语法提取公共A/B，复杂/多义不猜。若识别，模型必须normal A/target B，未影射from-import与已暴露production source SHA、共享简单argument AST与公共literal不改；public alias scope/实际共享值/语义不证。Controller不替模型改输入或期待；执行后grounding记API对照语法/公开guard实际trace，machine不晋升。14新专项+预算V3共32/Ruff、两repo真实synthetic controls、完整1416passed/4skipped（112.01秒）、规定V3 compact preflight ready=true。旧四响应零模型全审1拒/3未知保留，四公开Human输入逐字不改；zero provider/Gold读取0，不更改旧4/4。

源码先commit9648a4f，freeze0f04c414602c65c89362e419c061ba16abfc9774a93a6ccc54ab83431b1df543；列精确expectation_dev run/Flash only/≤16/批50000/题24000/output2000/reserve1.4/保护未跑首reserve/retry0，按用户≤100000授权执行一次。实际9started/completed/30,477tokens，无provider失败/retry；SK13496turn2、MM1252turn1、MM1359turn3三候选；SK26289两份code-only期待被拒，turn3以缺desired behavior弃答。producer completed/seal核对后独立Gold attempted3/区分3，screen3/4、machine0，固定12/九准入/screen4分账。未保前版4/4，成本也高于11,909，不能宣称效果改善、不能best-of或追加paid采样。三成功的prose只是unclassified语义待证，不当可信。所有原4/4及历史freeze/source/预算/state/ledger/响应/负结果保留。

零模型反馈审计发现同一比较报告3turn，其中两份probe拒绝反馈contrast=null；原完整公共文本始终可见，不叫原文丢失，也不确定加反馈能恢复。为检验normal可行性，新增public_normal_diagnostic：仅zero诊断，从公共A/B和缓存target from-import源绑定自动派生normal A，原自有argument表达式复制、公共A专有literal补入，unknown额外参数/影射/source不绑定不派生。派生setup/control是Controller程序，非model_generated、未接live，原target/oracle/response不改；不将诊断当Agent输出。真实同immutable base/net-none/read-only/资源限额，全部两份相关缓存派生normal各两次完成，但是同一task、同一唯一program（4次normal执行），不是2task或新修复，不3+1拼4/4；provider/Gold读取0、语义仍unknown。

新helper3正负专项/Ruff过，最终单次1419passed/4skipped/33warnings/0failed（113.65秒），XML持久，无assertions/timeout/skip弱化，工程数不当repair。公开data/e1c_evaluation_2_expectation_results.json绑定新freeze/state/ledger/seal/Gold/角色binding/zero inputs-feedback-normal/代码hash/XML；本轮30,477，自10月5日起可见755,829非账单核验、非整个项目总账。raw/probe/Gold/test/key不上Git。下一步先零费明确请求/公开回归/公开比较/unknown，比较推断期待标inferred_from_public_comparative_report并先定准入与反例，不能暗改本轮口径追回4/4；将已识别关系与prose锚附回反馈、仍让模型生成A/B，派生normal仅feasibility。再跨repo验收/新冻结四参考/完整DEV/native/新独立确认≥2/3/Agent修复official/最后新任务。当前停止paid扩批，不抽第6canary，不开TEST/C5/Fresh30/private Test500/repair/E2，不保证一周/30题完美。

两Roadmap/交接更新单一当前入口，不堆叠最新快照；旧所有结果/记录/备份保留。本轮未下载删除/重启Docker/IPC/VHD/registry/proxy/tunnel/key更改，当前无下载需求；Cloud可接源码与zero tests，缺本机private material/source/images/runtime明确INFRA_BLOCKED，不扩old bridge白名单、不假称新paid模块Web端到端已验。仅安全源码/协议/单测/脱敏摘要同步Git。


## 2026-10-07：公共报告锚新生成4/4、零费真实异常对应3/4与双source身份

完整读research/ponytail执行/监控规范，无subagent/新依赖。report_anchor_dev复用catalogue/API请求/公开比较语法，有限previous/earlier/used-to/before/<=和work/without-raising共现作回归prose锚；unknown/trace/code不获锚，explicit request仅公开请求，比较/回归标completion_hypothesis_from_public_report，不冒充原报告保证或report-exact，不造literal期待。初始Human新增锚但原字段/原文保持，拒绝反馈保留比较关系；System和下一turn同步去冲突，原七字段DTO/bad quote在lock前拒/source/normal-target/预算不改，完整hook仍在inner runner。旧九响应与四输入零调用全审、各一锚/字段不变；新8专项/26重点/Ruff/两repo真实synthetic normal控制、完整1427passed/4skipped（105.72秒）、规定compact preflight ready=true过。源码先commite220a87，新free ce751cec630abc95601048a30a522cfc13daf0f9898c9b753cdd7c28860d7b51，列精确report_anchor_dev run/Flash only/nonthinking/温度0/16calls/批50000/题24000/output2000/reserve1.4/待跑首reserve保护/retry0后执行一次。

实际6started/completed/21,400 provider tokens、无失败/retry，SK13496turn2、SK26289turn1、MM1252turn1、MM1359turn2四候选，真实比较case选quote_ref1公共prose、normal export_graphviz/target export_text两端source SHA和共享feature_names/max_depth表达式履行。producer completed/seal完整核对后独立Gold attempted4/区分4，原固定12/九准入/screen4分账，不是完整DEV/独立/repair/30题。不回填前版严格3/4；本版新假设准入/data/policy并改，不声称单因素因果，不best-of，machine0/语义未认证。

为突破只看日志，新增zero-only exception_observer固定controller driver，复用validated probe/image/base/nonce/source/timeout的原type observer传输；监听真实Python exception event，只精确四builtin类型及单str参数，公共消息hash/公开声明缺keyword匹配、两selected production文件/八条记录，不输出raw消息/arg值，未知自定义类型不调用repr/getattr/字符串化；无driver safe_static_check伪证，不接paid，不授trust。6专项/Ruff过，v1新namespace首题在source SHA前置中断，尚未执行model probe，freeze/driver/log完整保存、没有重试。只读Docker/git核对iforest/bagging live均等Git canonical base，host CRLF与runtime LF；原host SHA0ffc5.../28199...，LF投影1e339.../891861...恰等实际/canonical，不是生产源被改，不修改原副本或放过hash。

另立exception_observer_v2新源/namespace（不是v1重跑）：验证原暴露SHA、仅CRLF→LF投影，并在container同时查live及git show exact-base blob SHA，实际非换行变化仍拒，兼容旧Python不用str.removeprefix。3新专项/Ruff、最终完整1436passed/4skipped/33warnings/0failed（104.66秒），XML持久，assertion/timeout/skip不弱化。四原候选全自动zero base观察/不Gold挑，保持原缺dateutil blocker。SK13496真实TypeError缺声明keyword1记录；SK26289自定义参数校验不匹配公共机制0；MM1252公共parser builtinValueError2记录；MM1359公共AttributeError5记录。四仪器run rc1是原故障候选，不infra失败；3/4异常/关键词对应但2/5传播帧不当额外task成功，不作可信3/4。filename/instrumentation/timing不证全语义等价，nonce不是对抗任意恶意Python的attestation，wrong fixture可能同异常，实际共享值/intent仍unknown。

公开data/e1c_evaluation_2_report_anchor_results.json绑定producer/Gold/真实锚-binding-grounding/zero-v1失败/zero-v2各观察与identity projection/两observer源/readonly byte audit/XML；本轮21,400，自10月5日起可见777,229非账单核验/非整项目总账。raw/probe/Gold/test/key不上传。下一步停止paid调提示，先零费合并公开输入约束/production call及alias/期待来源/真实异常，定义支持证书scope与unknown，校准wrong fixture/alias shadow/生产对象改写/shape参数偏离/只API兼容未达原机制/源码环境变化跨repo反例，再完整method含observer双身份冻结/同版四参考九准入native/全历史排除独立canary≥2/3/Agent patch official/旧DEV30/最后新任务。语义未认证，不抽第6canary、不开TEST/C5/Fresh30/private Test500/repair/E2，不保证完美/一周30题。

两Roadmap/Web handoff当前入口更新为新结果、旧负记录和备份全保留，日志只集中续档。本轮未下载删除/启动重启Docker/IPC/VHD/registry/proxy/tunnel/key改变；readonly诊断及普通隔离containers不等于修系统/改源。当前无下载需求，Cloud可接source/zero tests，缺本机private evidence/source/images/runtime报INFRA_BLOCKED，不扩old bridge白名单或假称新paid云端端到端已验。只安全源码/协议/测试/脱敏摘要同步Git。


## 2026-10-07：零付费受限资格校准、反例与未暴露依赖authority

本轮完整读research/ponytail执行/监控规范，无subagent/依赖新增、provider/tokens0/0、Gold读取0，不重跑任何paid/smoke/observer。新增qualification组合assertion-free公共fixture绑定/class结构、from-import规范化、alias/生产对象修改、dynamic能力、生产依赖source SHA、精确公开锚、observer与原probe绑定、normal/target重复门槛。known bool/int严格JSON类型不混同；遗漏public import不推断成完整namespace、不错误当改值；实例/容器修改、custom行为/控制流、缺constraints/来源皆unknown。所有结果semantic/trusted false，受限候选不包装通用证书/独立/repair，已知约束库存不等于全部公共约束。

13专项及预算V3重点/Ruff过，两旧完整回归分别1449passed/4skipped（114.42秒）、规定compact preflight ready=true；对报告锚四候选原seal/input/observer sourceFreeze与candidate核对，全四零费缓存审计，不Gold挑。v1两机制候选、两因辅助production source未在暴露窗口误拒，原freeze/module/result留存；四样本各做一个内存alias-shadow信息包反例均拒，不称四新runtime故障。新增v2另source/namespace，缺暴露依赖source证据分unknown而非sha变化，真正已暴露source变更仍拒，增量赋值/删除/NamedExpr等不宣称公共binding保存。四新专项/全部17资格单测/Ruff过，最终完整1453passed/4skipped/33warnings/0failed（102.31秒），无assertion/timeout/skip弱化。

v2实际四缓存：SK13496、MM1359为mechanism_supported_candidate；SK26289 unknown unexposed DecisionTreeClassifier(_classes.py)，MM1252 unknown unexposed Schema(schema.py)+public Foo/Schema/DateTime没有import范围。没有rejected、machine0，不叫可信2/4。原Gold4/4、异常对应3/4、所有负记录均不变。依赖源可由同一public from-import解析器自动找到，但未暴露不等于corruption；不手选文件/造期待/改输入。

进一步zero readonly authority：先核对两个原host未改副本LF投影与exact-base Git blob，随后同immutable image net-none/read-only/pull-never、Git safe.directory仅container env的普通诊断查询runtime文件与canonical blob，两处均匹配。第一条本机Python命令因引号SyntaxError在任何Docker执行/输出产物之前失败，修正调用转义后只执行一次有效诊断，不provider retry/不篡改实验记录。authority两个独立namespace留存，model inputs/window/资格结果不改，authority尚未接v2，不把unknown回填成PASS。

公开data/e1c_evaluation_2_qualification_results.json绑定v1/v2、反例、authority、两资格源码、XML、原producer seal；private raw/probe/Gold/test/key不上Git。下一步另版接已核验authority并验wrong base/digest/path，定义public import省略的有限范围推断/unknown，再跨repo反例、method含资格/observer/双source身份完整freeze、同版四参考/九准入native；可信gate真过才全历史排除独立canary≥2/3、Agent patch/official、旧DEV30及最后新任务。当前不paid调提示、不抽第6批、不打开TEST/C5/Fresh30/private Test500/repair/E2、不承诺一周完美或30题全过。

两Roadmap/Web handoff维护唯一当前入口，所有旧source/预算/response/state/ledger/seal/备份保留；日志只集中续档。无新下载删除/启动重启Docker/IPC/VHD/registry/proxy/tunnel/key更改，当前无下载需求；普通只读诊断containers不是机器修复或本机配置修改。Cloud可接source/zero tests，缺本机private material/source/images/runtime报INFRA_BLOCKED，旧bridge白名单不扩，不假称新paid已云端端到端验证，仅安全源码/测试/脱敏摘要同步Git。

## 2026-10-07：authority接入v3与根目录快照竞态修复

资格v3已接入辅助生产源码authority：四缓存2机制支持候选、1行为候选（原机制未证明）、1unknown，machine trusted仍0，E1-C未封板。本轮provider/tokens0/0、Gold读取0；旧Gold4/4、异常对应3/4不改。audit overlay不改原模型输入；public import省略范围推断仅为未接受方案。最终1462 passed/4 skipped/33 warnings（89.41秒），预算/V3重点19项、Ruff与合成preflight通过，不是修复率。初次preflight的SQLite sidecar复制竞态失败保留；只排除根目录运行态数据库快照复制，不删除数据库。不打开新canary/TEST/C5/Fresh30/private Test500/repair/E2，无下载需求。

新增8项身份单测，receipt SHA/task/base/image/host/LF/Git/runtime均严格核验。初次完整回归1461passed，最终1462；原失败与XML保留。公开收据data/e1c_evaluation_2_authority_integration_results.json和结果文档绑定证据。下一步范围/unknown协议及行为/机制分账、完整method冻结，再同版DEV；未达门槛不抽canary、不repair/E2。无新下载删除/Docker重启/IPC/VHD/registry/proxy/tunnel/key修改，原source/state/ledger/seal/负结果保留。下附更新前文档快照，最新待办只按当前Roadmap接手。

### 更新前快照：docs/PROGRESS_RESEARCH_ROADMAP.md

<details><summary>原文保全</summary>

# Coding Agent 研究总览：成果、证据与边界

更新：2026-10-07。本文是项目总览；当前可执行待办只维护在 [Roadmap 2](PROGRESS_RESEARCH_ROADMAP_2.md)。

本项目基于 [JoshuaC215/agent-service-toolkit](https://github.com/JoshuaC215/agent-service-toolkit)，在 LangGraph、FastAPI、Streamlit 服务骨架上研究：**如何以受控成本获取代码证据，并让自动生成的故障复现真正支持软件修复？**

**当前：零模型资格校准完成一轮，2项机制支持候选、2项unknown，尚不认证语义可信。** 本轮provider/tokens0/0，旧Gold4/4与异常对应3/4不改。已拒公共约束改写/import影射/对象修改等反例，区分缺来源与真实SHA变化；两个缺口辅助依赖已只读核验host LF/Git base/runtime一致，但未回填资格。[最新校准与接手步骤](research/E1C2_QUALIFICATION_RESULTS_2026-10-07.md)、[收据](../data/e1c_evaluation_2_qualification_results.json)。下一步把authority接入新身份并处理省略public import的有限范围/unknown，再完整方法冻结；不加模型预算采样。工程1453 passed/4 skipped不是修复率，TEST/C5/Fresh30/private Test500/repair/E2未开，本机配置/旧记录不动。

所有旧分数、输入、源码、观察与失败保留；不将“候选”叫可信2/4，不best-of或改旧namespace。日志只在[集中续档](research/PROGRESS_LOG_ARCHIVE_2026-09-27_CONTINUATION.md)，下表保留历史版本。

## 1. 阅读入口

| 读者目的 | 入口 |
|---|---|
| HR / 工程师 / AI 快速了解项目 | 本页第 3、4 节 |
| 接手下一步开发与实验 | [Roadmap 2](PROGRESS_RESEARCH_ROADMAP_2.md) → [WebCodex 交接](research/NEXT_SESSION_HANDOFF.md) |
| 查看一周交付和验收 | [一周实验计划](research/E1C2_ONE_WEEK_PLAN_2026-09-30.md) |
| 查原始过程、失败与演变 | [历史索引与保全记录](research/WORKSPACE_REORGANIZATION_2026-09-30.md) |
| 查看最新实验与下一步 | [统一运行反馈两轮结果](research/E1C2_UNIFIED_RUNTIME_DEV_RESULTS_2026-10-07.md)、[哈希收据](../data/e1c_evaluation_2_unified_runtime_dev_result.json)；旧V4/V2及所有协议/负结果保留 |

## 2. 从启动到现在的主线

| 阶段 | 做了什么 | 现在如何理解 |
|---|---|---|
| 8 月末—9 月上旬：工程基线 | 服务；本地 BGE-M3；代码搜索、读写、测试；Planning、Reviewer、HITL；轨迹与经验；配置和工作流 | 已有实现和分项验收，不能等同于研究全部完成 |
| V0：规则证据获取 | 受控检索任务、Utility Gate 与静态策略比较 | 检索层原型收尾，不是自动修复率 |
| V1：学习排序与停止 | Decision Episode、LogReg ranker/stopper、冻结划分、动作消融 | 已冻结，小样本检索效率改善，未证明修复增益 |
| V2：扩展检索评估 | adaptive acquisition、SERBench Cal500 与 Test500 prediction-ready | 已冻结；Cal500 未优于词法基线，Test500 未获私有评分 |
| V3：经验复用 | 时间顺序隔离、6 条真实轨迹、3 组 OFF/ON 对照 | pilot 关闭；未观察到修复收益 |
| 9 月 20–23 日：Formal E1 / E1-C | 外部任务准入、预算账本、容器评分、完整实验封存 | Formal E1 0/30；原 E1-C 最终 1/30 |
| 9 月 24–27 日：DEV30 与严格复现 | 同版开发、盲态配对试验、source-contract、失败归因 | best-of 不作系统成绩；独立门槛失败暴露复现覆盖不足 |
| 9 月 28–30 日：evaluation_2 | DEV12 镜像、双准入、自动源码窗口、离线判别、独立 canary | 当前活动主线，详见 Roadmap 2 |

原文中“全部阶段已完成”只适用于当时的基础工程验收。E1-C 质量目标、E2 main、E3 并未完成。

## 3. 本分支的实质工作

上游提供 Agent 服务、客户端、UI 和基础框架。以下是本分支的研究与工程扩展；不将整个上游项目算作原创。

| 能力 | 实现 / 结果入口 | 可以支持的陈述 |
|---|---|---|
| 受控代码工具 | [code_tools.py](../src/agents/code_tools.py)、[test_tools.py](../src/agents/test_tools.py) | 路径、读取量、执行超时等边界 |
| 规划、审查与轨迹 | [coding_planner.py](../src/agents/coding_planner.py)、[reviewer.py](../src/agents/reviewer.py)、[trajectory.py](../src/agents/trajectory.py) | 可记录决策和失败轨迹 |
| 经验存储与复用 | [experience.py](../src/agents/experience.py)、[V3 结果](research/RESULTS_V3.md) | 已实现并做过真实小型对照；效果未获支持 |
| 统一证据接口 | [evidence_runtime.py](../evals/evidence_runtime.py)、[evidence_controller.py](../evals/evidence_controller.py)、[codegraph_adapter.py](../evals/codegraph_adapter.py) | lexical / semantic / structural、预算与 STOP 可追踪 |
| 学习型检索策略 | [V1](research/RESULTS_V1.md)、[V2](research/RESULTS_V2.md) | 冻结划分、检索成本指标、消融 |
| 请求预算与账本 | [model_budget.py](../src/agents/model_budget.py) | token 预留、硬上限、失败记账与中断边界 |
| 离线缺陷评测 | [evaluation_2](research/E1C_CODING_AGENT_EVALUATION_2.md)、[冻结清单](../data/e1c_evaluation_2_canary_v2_method_freeze.json) | 生成侧/grader 隔离、镜像/源码身份、固定分母、失败留档 |

研究假设：**固定 issue 的可观测行为约束，并限制执行反馈只能修正环境或构造过程，能否减少“测试失败但与 issue 无关”的假阳性？** 现有失败记录支持这个研究动机；效果与新颖性仍须通过消融和独立验证，不能提前称为已验证的新算法。

## 4. 已有结果与统计口径

| 实验 | 结果 | 限制 / 证据 |
|---|---|---|
| V1 frozen test，4 tasks | Recall 0.7812；tokens 122.5 → 87.0；tool calls 2 → 1.25 | 小型检索实验；[报告](research/RESULTS_V1.md) |
| V2 SERBench Cal500 | MSS@8 0.078；BM25 0.104；lexical 0.118 | 未胜出；[报告](research/RESULTS_V2.md) |
| V3 exploratory pilot | 6 trajectories；3 组 OFF/ON 结果相同；ON 多 369 tokens | 未观察增益；[报告](research/RESULTS_V3.md) |
| Formal E1 | 0/30 resolved；23 provider 基础设施失败 | 不能归因成纯模型能力；[汇总](../data/formal_e1_n30_summary.json) |
| 原 E1-C | 最终 1/30；49 requests；65,801 provider tokens | 含 selective salvage；[报告](research/E2_ENTRY_GATE_STATUS_2026-09-23.md) |
| 旧 DEV30 | 一次同版完整运行 4/30；跨版 best-of 13/30 | 不可相互替代；[历史](PROGRESS_RESEARCH_ROADMAP_2_HISTORY_2026-09-30.md) |
| B4 / C4 | B4 1/4 对 1/4；C4 0/6 对 0/6 | 没有 treatment 净新增修复；[历史](PROGRESS_RESEARCH_ROADMAP_HISTORY_2026-09-30.md) |
| evaluation_2 DEV12 | 双准入 9/12；v4 经审核可信复现 4/12 | 8 请求 / 25,424 tokens；含确定性路由；不是修复率 |
| canary v1 | 可信复现 1/3，低于 ≥2/3 | 独立负结果封存；[结果](research/E1C2_INDEPENDENT_CANARY_V1_RESULT_2026-09-29.md) |
| canary v2（传输修订） | 官方双准入3/3；可信复现0/3 | Flash三请求/13,783 tokens；输出回显、fixture错误和弃答；[负结果](research/E1C2_CANARY_V2_AMENDED_RESULT_2026-10-05.md) |
| DEV合同/控制器改进 | 新生成hybrid 3/12；修订控制器缓存4/12 | 开发证据，含语义审核；A/B、失败、成本分开报告；[结果](research/E1C2_DEV_CONTRACT_STUDIES_2026-10-05.md) |
| 独立hybrid canary v3 | 双准入2/3；可信1/3，未达门槛 | 3Flash请求/7280tokens，负结果封存；[报告](research/E1C2_HYBRID_CANARY_V3_RESULT_2026-10-05.md) |
| 最新旧DEV hybrid v3 | 新生成可信3/12，门槛失败 | 12Flash请求/24712tokens，未保留四条参考；[报告与下一步](research/E1C2_HYBRID_DEV_V3_RESULT_2026-10-05.md) |
| counterfactual旧DEV新生成 | 13Flash请求/26762tokens，Gold及人工行为审查4/12 | 保持四条参考，零调用先拒错误fixture；不是SOTA或修复率；[报告](research/E1C2_COUNTERFACTUAL_DEV_RESULT_2026-10-05.md) |
| 第4批独立canary | 双准入2/3，3Flash请求5596tokens，可信0/3 | 环境失败/窗口缺失/输入dtype丢失；[封存结果](research/E1C2_COUNTERFACTUAL_CANARY_V4_RESULT_2026-10-06.md) |
| Faithful input旧DEV | 源生成16Flash请求37593tokens；原验证INFRA_INVALID保留 | 不把环境故障记0/12；[原结果](research/E1C2_FAITHFUL_INPUT_DEV_RESULT_2026-10-06.md) |
| Faithful完整缓存回放 | 新provider0；9题执行、6候选、Gold5/12，四参考保留 | 人工行为审查5/12、机器trusted0，不是独立/修复；[结果](research/E1C2_FAITHFUL_REPLAY_RESULT_2026-10-06.md) |
| 第5批独立canary | 双准入2/3；3Flash请求9642tokens，可信0/3 | import/API窗口遗漏、未调用函数、源码身份失败；[封存结果](research/E1C2_FAITHFUL_CANARY_V5_RESULT_2026-10-06.md) |
| 旧DEV import/调用形态审计 | 新provider0；3题4个新增定义窗口，8份缓存候选中1份函数体未调用 | 结构诊断原型，不是新的复现分数；下一版DEV尚未付费 |
| 新版executable-import旧DEV | v1零调用原型保留；v2能力边界加固后真实试验3/12 | 不代表净提升；[协议/历史](research/E1C2_EXECUTABLE_IMPORT_DEV_V2_PROTOCOL_2026-10-06.md) |
| Executable新生成V2 | 12请求36689tokens；4候选Gold3/12 | 未保四参考；[真实结果](research/E1C2_EXECUTABLE_DEV_V2_RESULT_2026-10-06.md) |
| Controller-owned缓存V3 | 新provider0/无缺缓存；仍Gold3/12 | 输入echo仍拒绝，没有新模型收益 |
| Controller generation V4 | 14请求35889tokens；A源码格式5/5，5候选Gold2/12 | 格式改善、质量未提升；[真实负结果](research/E1C2_CONTROLLER_GENERATION_V4_RESULT_2026-10-06.md) |

DEV v4 底层 Gold 判别 JSON 中，4 份 `gold_discriminating=true`，而 `trusted_reproducer` 仍为 false。4/12 叠加了文档中的人工 issue 语义审核，不能说机器自动判可信，也不应回填旧 JSON。自动定位不等于完全自动语义验收。

工程测试结果见[验证记录](research/WORKSPACE_REORGANIZATION_2026-09-30.md)。pytest passed 数不代表 repair success。

## 5. E1、E2、E3

| 研究线 | 状态 | 下一条件 |
|---|---|---|
| E1 / E1-B | 正式结果封存；旧六条 TEST 未执行但保密性受损 | 旧六条不再作干净确认集 |
| E1-C evaluation_2 | 活动中，尚无新版 Agent 修复结果 | 独立 canary ≥2/3，再冻结修复对照 |
| E2 | operational Entry Gate 曾 PASS；main n=100 未启动 | 先满足新质量门槛；运行完整不代表质量达标 |
| E3 | 路线规划，未启动 | E2 后另立 30 → 100 → 300+ 与提前停止协议 |

## 6. 历史保全与维护

完整旧正文保存在同目录，原相对链接继续有效：

- [旧 Roadmap 全文](PROGRESS_RESEARCH_ROADMAP_HISTORY_2026-09-30.md)
- [旧 Roadmap 2 全文](PROGRESS_RESEARCH_ROADMAP_2_HISTORY_2026-09-30.md)
- [集中日志](research/PROGRESS_LOG_ARCHIVE.md)与[9 月 27 日续档](research/PROGRESS_LOG_ARCHIVE_2026-09-27_CONTINUATION.md)

以后只更新本页项目结论、Roadmap 2 当前状态；逐轮过程写集中日志。旧 freeze/result、失败记录、源码保持原路径。本地密钥、原始任务/评分材料和大文件缓存不作为公共展示材料。本轮整理不触碰 Docker 数据盘或 tunnel 配置。

</details>

### 更新前快照：docs/PROGRESS_RESEARCH_ROADMAP_2.md

<details><summary>原文保全</summary>

# Roadmap 2：E1-C evaluation_2 当前状态与执行顺序

状态日期：2026-10-07。当前唯一执行入口；背景见[Roadmap 1](PROGRESS_RESEARCH_ROADMAP.md)，历史过程与旧页面原文见[集中续档](research/PROGRESS_LOG_ARCHIVE_2026-09-27_CONTINUATION.md)。

## 0. 最新结论

**受限资格v2：2项mechanism_supported_candidate、2项unknown，machine trusted0，E1-C未封板。** 本轮模型调用/tokens0/0，Gold读取0；旧Gold4/4、异常对应3/4不改，不是新生成/独立/修复成绩。[本轮校准与严格scope](research/E1C2_QUALIFICATION_RESULTS_2026-10-07.md)、[公开收据](../data/e1c_evaluation_2_qualification_results.json)。

四缓存逐项审及四个内存alias反例完成，17单测覆盖错误输入/shape、影射、对象改写、未知状态、源码/另一probe等。v1将辅助依赖未暴露误当源码变化，原误拒保留；v2正确标unknown，真SHA不一致仍拒。两个辅助依赖已只读确认host LF/Git base/runtime同摘要，但尚未并入资格、未改变模型输入或结果。最终1453 passed/4 skipped/33warnings（102.31秒），Ruff/预算V3/compact preflight过，非repair rate。无下载需求。

## 1. 已完成与尚未完成

| 环节 | 实际证据 | 边界 |
|---|---|---|
| DEV12基础设施 | 12镜像身份曾现场核验；双准入9/12 | 每次核验现场，异常留固定12分母 |
| 自动源码窗口/入口/guard | 公开issue与exact-base生产源、来源与SHA | 非人工选文件不等于语义正确 |
| 五批历史独立canary | 1/3、0/3、1/3、0/3、0/3封存 | 未达≥2/3；不再称独立调参 |
| 历史API/类型/codec版本 | Gold3/4、2/4、2/4保持 | 内部配置覆盖hook，效果归因不成立 |
| v1执行计划零费 | outer=true/inner=false；smoke/audit封存、付费0 | 原型负证据，不覆盖旧源 |
| v2真实完整执行链 | 五份旧probe零费5/5产物、1自身类型观测；新paid4/4产物 | 不将回放叫新生成；类型组件paid未触发 |
| v2四参考新生成 | 4请求11,909tokens；正常control与重复base失败、Gold4/4 | 固定12/九准入/screen4分账，不是完整DEV或独立成绩 |
| 前版witness grounding零费审计 | 全4审计，1项trace期待/公开guard未在失败trace观察到 | 其余也未获语义证书；组件未接live |
| 前版严格期待门槛 | 期待在lock前筛查、公开A/B/共享输入源绑定；Gold3/4 | 错误期待被拒，但新生成覆盖未保；unknown不trusted |
| 公开normal零费feasibility | 自动派生1程序、4次normal通过、Gold读取0 | 不是模型输出，未接live，不拼分 |
| 公共报告锚新版本 | 新假设口径下Gold4/4，真实A/B输入表达式/source绑定 | 前版3/4不回填，不是严格前版过关 |
| 真实异常观察与双source身份 | v1失败保留，v2观察3/4对应；CRLF/LF原副本/有效文件/Git blob核对 | 不等于语义证书或抵抗恶意程序的attestation |
| 新受限资格校准 | v2两机制支持候选/两unknown；四静态alias反例拒绝 | 非新运行时实验，不自动认证 |
| 辅助依赖authority | 两处host LF/base blob/runtime一致，只读核验 | 未并入资格，不回填unknown |
| 机器可信/Agent修复/E2 | machine0、新repair/official resolved未做 | 不报30/30，不开Fresh30 |

## 2. 当前瓶颈

检查器现在能组合已知公共fixture结构、production依赖、期待锚和异常证据，并拒绝明确改值/影射/对象改写。它只支持有限结构；状态/控制流/自定义行为、遗漏公共范围不认证。

两项unknown已定位：DecisionTreeClassifier与Schema的辅助源不在原model窗口；DateTime/Foo/Schema公共示例还省略import来源。额外生产源的host/Git/runtime字节身份已核验，下一版须显式接入authority，不假称原模型看过；省略public import的范围推断或unknown须另定协议，不能凭同名类推断原文承诺。

## 3. 严格验收定义

1. 生成侧只用公开issue允许投影与exact-base生产源，不输入原测试断言/题面可执行答案/Gold/官方评分日志。
2. 定位规则无task-ID→文件表、无人工挑文件；保留来源、rank、窗口预算与SHA。
3. 两次有效normal control和两次稳定非setup目标失败；独立Gold消除不自动授予行为忠实性证书。
4. 新probe须对齐公开行为义务，unknown保持unknown；自动语义门槛尚未完成。
5. Agent补丁由独立官方评分判resolved。代码回归、可信复现和30/30 resolved是三个不同目标，不best-of合并。

## 4. 当前唯一执行顺序

| 顺序 | 下一步 | 放行证据 | 未过时 |
|---|---|---|---|
| 1 | authority接入另版辅助源校验 | 原host摘要/LF/base Git/runtime均绑定，wrong base/digest/path反例 | 不改旧model窗口或结果 |
| 2 | public import省略的范围协议 | 有限显式推断或unknown，不凭同名认完整namespace | 不自动trusted |
| 3 | 跨repo正负例→完整method freeze | 资格scope/classifier/observer/双source身份与输入/预算先冻 | 不继续paid调提示 |
| 4 | 同版四参考/九准入DEV/native | Gold/受限候选/语义/原机制分别计，固定12 | screen不报全12 |
| 5 | 新不重叠canary一次 | 全历史排除，可信≥2/3且行为一致 | 负结果封存回DEV |
| 6 | Agent patch/独立official grade | 同预算小baseline/treatment修复证据 | 无收益不扩批 |
| 7 | 旧DEV30→另授权Fresh30→E2 | 单一冻结身份逐题resolved | 不保证30/30，不回调Fresh30 |

下一轮paid前先列精确命令/Flash/次数/≤100,000tokens，retry0不Pro。本轮provider0；资格v1/v2与authority各namespace以及所有已started的run/smoke/Gold/audit禁止重跑或改源/预算/账本。当前无新live/canary命令，不抽第6批，不开TEST/Fresh30/repair/E2。

## 5. 时间与停止条件

[原一周计划](research/E1C2_ONE_WEEK_PLAN_2026-09-30.md)保留预注册。本轮新假设口径Gold恢复4/4且成本较前版30,477下降至21,400，但不能称隔离因果收益、严格原口径达标或一周/30题保证。可控交付是有边界的行为资格校准、完整freeze和一次同版DEV实证；未过不抽新独立任务。

## 6. WebCodex与本机安全

云端可接源码、无模型单测和脱敏摘要，使用uv.lock；exact-base源码/镜像/私有.codex/凭证不会随Git同步。缺材料明确INFRA_BLOCKED；[接手说明](research/NEXT_SESSION_HANDOFF.md)给出安全检查命令。旧bridge白名单未扩，不假称新paid入口云端端到端已验证，不开裸Docker daemon。

本轮未下载/删除镜像或重启Docker，未改IPC/VHD/registry/proxy/tunnel/密钥。全部实验负结果和备份保留。sealed TEST/C5/Fresh30/SERBench私有Test500/Agent repair/E2仍关闭。

## 7. 更新纪律

本页只维护最新状态和可执行待办，逐轮日志只追加集中续档。此前本页及交接页的多份“当前/最新”快照已原文移入2026-10-07集中归档，Git历史也保留；不要按归档旧命令操作。原协议、结果、预算、response/state/ledger/seal均不回填。

</details>

### 更新前快照：docs/research/NEXT_SESSION_HANDOFF.md

<details><summary>原文保全</summary>

# WebCodex 接手：E1-C evaluation_2

日期：2026-10-07。先读[AGENTS.md](../../AGENTS.md)、[Roadmap 2](../PROGRESS_RESEARCH_ROADMAP_2.md)、[最新资格校准](E1C2_QUALIFICATION_RESULTS_2026-10-07.md)。

## 1. 当前状态与禁止重跑

资格v2四缓存：2机制支持候选/2unknown，machine0，本轮provider/tokens0/0、Gold读取0。旧report-anchor版Gold4/4与异常对应3/4不改，不能将缓存审计当新模型/修复成绩，不能叫可信2/4。

资格器检查已知fixture结构、alias/对象修改、production源绑定、期待锚、原probe观察、normal/target。17单测与四内存alias反例通过，静态反例不是四个新runtime故障。v1未暴露依赖被误拒留档，v2缺证unknown、已暴露真正SHA变化仍拒；增量赋值/删除等未知。

DecisionTreeClassifier(_classes.py)与Schema(schema.py)额外源已只读核验host LF/Git canonical/runtime同摘要，authority单独记录，未并入v2资格/未改变model输入。Foo/DateTime/Schema公共示例import范围仍不明，不能默认推断。

最终1453 passed/4 skipped/33warnings（102.31秒）、Ruff/预算V3/compact preflight过；[公开收据](../../data/e1c_evaluation_2_qualification_results.json)绑定SHA，raw/probe/Gold/test/key留本机。所有已started audit/run/smoke/Gold禁止重跑、回填或修改旧source。无下载需求。

## 2. 当前唯一下一步

另版接入已核验authority到辅助依赖检查，验原暴露摘要/LF/base Git/runtime与错误base/digest/path反例，不假称原model已看到这些文件。为省略public import定义有限显式范围推断或unknown，不凭同名认原文namespace，未知不认证。

跨repo正负例通过后完整method含资格/observer/双source身份先冻，再同版四参考/九准入DEV/native，Gold/受限候选/语义/原机制分账。可信gate真正达成才历史全排除新canary一次≥2/3、Agent patch/official、小DEV30及最后另授权Fresh30。当前无新paid/canary命令，不抽第6批、不开始repair/E2，不保证完美。

## 3. Cloud可先执行的无模型检查

```bash
uv sync --frozen --group dev
uv run --frozen python -m ruff check evals/e1c_evaluation_2_qualification.py evals/e1c_evaluation_2_qualification_v2.py tests/test_e1c_evaluation_2_qualification.py tests/test_e1c_evaluation_2_qualification_v2.py
uv run --frozen python -m pytest -q tests/test_e1c_evaluation_2_qualification.py tests/test_e1c_evaluation_2_qualification_v2.py tests/test_model_budget.py tests/test_v3_pilot_runner.py tests/test_v3_compact_pilot.py
uv run --frozen python -m evals.v3_compact_pilot preflight
uv run --frozen python -m pytest -q
```

无需DeepSeek/tunnel密钥，合成preflight不是sealed TEST实验。依赖安装失败报环境阻塞，不降低断言/timeout/skip；源码与uv.lock可云端运行，本机exact-base/private .codex/镜像/runtime不随Git同步，缺材料报INFRA_BLOCKED。旧bridge白名单未扩、不假称新paid端到端已验、不开放裸Docker daemon、不上传key/raw/Gold。

## 4. 付费、安全与回传

未来新实验先列精确命令、Flash、次数与≤100,000 tokens，新未开始namespace，retry0、输入隔离、producer seal后独立Gold；原v2/expectation-v1/report-anchor-v1和两个observer namespace都不能“再试”。不使用Pro，不开sealed TEST/C5/Fresh30/SERBench私有Test500，当前没有新canary/repair/E2命令待执行。

本轮无下载删除/重启Docker/IPC/VHD/registry/proxy/tunnel/key更改，备份与负结果全保留。旧IPC授权已消费，任何新修改需明确限定授权；大文件交用户终端直连、不走VPN，当前无下载需求。

回传diff、实际hook证据与源SHA、工程数、paid ledger、Gold/语义/各固定分母、未过gate和下一步；不承诺完美/30题全过，不把Gold/回归称repair。日志只写[集中续档](PROGRESS_LOG_ARCHIVE_2026-09-27_CONTINUATION.md)，两Roadmap保持单一当前入口。旧快照/Git历史保留，不按历史“下一步”操作。

</details>

## 2026-10-07：有限引用范围与静态export链零调用审计

已实现条件引用范围检查与静态重导出链审计：四缓存3显式结构支持/1条件结构支持；两个条件引用链均有静态身份支持，但原资格v3仍2机制候选/1行为候选/1unknown，machine trusted0。新增provider/tokens0/0、Gold读取0，旧Gold4/4及异常对应3/4不改。新增23单测，最终1485 passed/4 skipped/33warnings（84.67秒），Ruff、重点38项与合成preflight过；工程数不是修复率。未完成运行时对象/公开意图对应或完整live方法冻结，不开canary/TEST/C5/Fresh30/private Test500/repair/E2。

范围协议预注册后审计四缓存，原producer seal和生产侧产物hash全部验证；完整引用路径与唯一生产定义/host SHA/LF/base Git条件绑定，不改原public facts/model输入。MM1252仅条件结构支持，明确public import不显式、export/runtime/intent不推断证书。后续export-chain协议预注册，以范围输出自动派生Schema→schema.Schema及fields.DateTime来源，两链静态身份支持，旧资格/Gold结果均不改。范围11、export12新增单测；两合成库正例不是两个真实repo实验。

初次范围单测1failed/9passed因fixture把同一alpha.fields.DateTime直接import当不同对象，改为alpha.DateTime负例且增加同对象正例，未弱化拒绝断言。首轮Ruff I001未过而scope审计已开始，原source全文snapshot保存于该私有namespace，SHA等原freeze；公开source仅交换argparse/ast import顺序，另记SHA和可重建差异，不修改原freeze/result、不重跑。export源码在Ruff/专项过后冻结，之后不改。重点38passed、最终1485passed/4skipped/33warnings84.67秒，XML SHA与原source/currentsource/public result SHA收据绑定；synthetic preflight ready=true。

本轮未付费、未读Gold、未运行新容器故障，无下载删除/Docker重启/IPC/VHD/registry/proxy/tunnel/key改变。安全公开同步限源码/单测/协议/脱敏收据，private raw/probe/Gold/test/key不上Git；旧source/state/ledger/seal/失败备份全保留。后续runtime对象与公开行为资格仍未过，完整live方法未freeze，不抽新canary/不开TEST/C5/Fresh30/privateTest500/repair/E2，不承诺完美或30/30。当前三入口更新待办，本轮日志只集中归档。

## 2026-10-07：构造器运行时关系零付费诊断，v1未知保全与v2真实观察

已补充真实构造器关系证据：原四缓存中1项具有两个条件引用，离线容器观察到DateTime exact type与Foo→Schema MRO关系；其余3项not applicable。v1直接构造器未知结果保留，v2新namespace一次诊断，新增provider/tokens0/0、Gold读取0，原probe未改。旧资格仍2机制候选/1行为候选/1unknown，machine trusted0，旧Gold4/4及异常对应3/4不改。尚未完成行为资格和完整live方法冻结，不开canary/TEST/C5/Fresh30/privateTest500/repair/E2。

完整读ARS执行/监控规范与ponytail，本轮无subagent/新依赖。v1/新协议/新namespace限定direct self构造器，10专项及Ruff过后审计四参考；Schema公开class无直接__init__，整体unknown，未执行容器、不重跑v1。只读AST诊断确认一般metaclass helper形态，未按task/helper名补继承规则。v2另源码/协议/namespace，以export末端同模块全部有界constructor行观察实际class identity/MRO，不解释with_metaclass。7新专项加v1共17passed，预算V3重点36、Ruff过后一次新离线诊断。

复用现有只读transport，原probe/source/seal/optional dateutil blocker不变；全部三export文件runtime原字节等exact-base Git blob及host LF摘要。一次net-none/read-only/pull-never容器、90秒硬超时，无restart/download/provider/Gold。DateTime __init__与Field __init__处self exact对应声明DateTime，BaseSchema __init__处self非exact Schema但MRO包含Schema。原fault rc1不是infra失败；5记录含2early非对应调用全保留，3positive记录不是3任务。四缓存3N/A、1项两个关系出现，固定DEV12分母保留；不把关系证据当public namespace意图/行为可信、任意Pythonattestation或全语义等价。

最初v1/v2 Ruff unused import只在对应freeze前修正，已冻结方法源与结果未改；原scope/export/qualification/Gold/预算/state/ledger/seal/负记录/备份均保持。最终合成compact preflight ready=true、完整1502passed/4skipped/33warnings81.24秒，XML及两observer source/v1/v2freeze/result SHA绑定data/e1c_evaluation_2_object_relationship_results.json。下一步paired API实际共享输入/类型对应与有限行为义务校准，再完整method freeze/同版DEV；不是付费调提示，不开新canary/TEST/C5/Fresh30/privateTest500/repair/E2，不保证完美或30/30。

两Roadmap/Web handoff唯一当前入口更新，日志只本集中续档；源码/单测/协议/脱敏收据公开，raw/probe/Gold/test/key本机保留。无镜像删除/系统Docker修复/IPC/VHD/registry/代理/tunnel/密钥更改；Docker健康只读检查，普通隔离诊断不修改机器配置，当前无下载需求。

## 2026-10-07：paired caller输入诊断与Parameters规格支持缺口

公共API对照的调用前诊断完成：normal rc0/target rc1，feature_names(ndarray)与max_depth(int)两路typed摘要一致，但分类器对象unknown，all_inputs_match=false。生产参数文档两API均仅明确写list of str，因此ndarray期待存在规格支持缺口，不等于输入非法或任务不是bug。新增provider/tokens0/0、Gold读取0，原probe与旧Gold4/4/资格2机制候选+1行为候选+1unknown保持，machine trusted0。

完整读ARS执行/监控规范及ponytail，复用原guard transport，不新增依赖/subagent。caller-input协议预注册，新namespace验证原producer seal/全部生产侧SHA、normal/target各原脚本；源码API两role均host LF/runtime/base Git匹配。参数装饰器可阻止进函数体，故从冻结AST单一顶层调用行捕获local Name或frozen Constant，无副作用参数；不eval/repr/getattr/custom属性。builtin有界typed表示、ndarray精确类型biufcSU≤64KiB按dtype/shape/C-bytes SHA，object/subclass/custom/cycle/预算未知，官方NumPy文档仅核验bytes/kind语义。normal0/target1各一次新隔离容器快照，feature_names ndarray和max_depth int摘要匹配；positional_0分类器unknown，all_inputs_match=false，不证明API体执行/public完整fixture/语义/抵抗恶意probe。

另版Parameters文档协议/新namespace，6专项过后只读审计；自动从pair binding选择API source，原host SHA/LF/base匹配，提取Parameters四声明行，不序列化Returns/Examples/断言/答案。冻结两个API均feature_names list of str，实际ndarray未明确在文档支持域；max_depth声明int与观察一致。报告documentation_scope_gap而不是非法输入或task不是bug，文档可能过时、明确公共变更请求可覆盖旧文档；normal接受不能单独推target承诺，旧报告completion假设仍分账。当前优先规格/意图分支，不扩任意对象序列化或付费碰运气。

新增caller11+contract6共17单测，预算V3重点36/Ruff/合成compact preflight过；先前1513passed/4skipped107.76秒保留，最终完整1519passed/4skipped/33warnings105.28秒/XML SHA绑定公开data/e1c_evaluation_2_pair_input_contract_results.json。unused imports与测试排序仅在各audit freeze前修正，已冻结source/result/预算不改、不重跑原namespace。provider/tokens0/0、Gold读取0、machine0，原资格/Gold/exception/source/state/ledger/seal/负记录/备份保持。两新普通隔离容器不等于旧模型或评分重跑；不改model输入，不输入Gold，raw/probe/Gold/test/key不上Git。

两Roadmap/Web handoff更新为有限行为资格分支/正负例、最小观测义务，再完整method freeze/同版DEV；可信gate未过不抽新canary、不打开TEST/C5/Fresh30/privateTest500/repair/E2，不保证30/30或一周完美。无下载删除/Docker重启/IPC/VHD/registry/proxy/tunnel/密钥修改，当前无下载需求。日志只集中本续档，仅安全源码/单测/协议/脱敏收据同步Git。

## 2026-10-08：行为子义务校准与公开旧版本生产源准备，Docker准入前阻断

有限行为分支已校准：四缓存1显式bool keyword子义务支持、1比较假设、2回归假设，机器可信仍0（不是可信1/4）。旧版本对照已准备MM1359公开3.0.0rc8的11生产文件/152,704bytes，但Docker engine管道不存在、Desktop/backend未运行，准入前INFRA_BLOCKED，driver与probe均未执行。本轮provider/tokens0/0、Gold读取0，旧资格与Gold4/4/异常对应3/4不变。

本轮跨2026-10-07/08，完整读ARS执行/监控与ponytail，无subagent/依赖新增。behavior-gate另版协议/source/namespace，在16专项/Ruff后核验原producer/qualification-v3/exception-v2/pair/doc收据，对全部四缓存一次只读分类。显式BooleanCtor请求确认qualifiedAPI/公开bool域/目标literal/normal仅差请求keyword/闭合签名缺参数且无kwargs/host LF/base/原编译AST/该行TypeError同keyword；1子义务支持，default/增量/其他issue义务仍不覆盖。另1比较、2回归保持假设，全issue trusted0，无Gold读/新provider/旧评分重写。

为核实regression旧版，新增本地版本source对照协议10月8日：只取publicquote单一==/<=旧版，自动包根，既有tag或80条init祖先历史，限90秒；不fetch/下载/读旧tests/Gold。只archive生产.py，路径/symlink/预算检查，每文件原始byte等canonical Git blob。首次加canonical检查1failed/40passed，Windows archive换行影响，修复仅单次core.autocrlf=false/core.eol=lf并保留相等断言；后重点41passed，缺失历史blob按metadata不可用，不当probe失败。

version-witness-zero-v1 source/protocol已冻，MM1359 3.0.0rc8的11文件152704bytes在新私有目录保存。随后require_engine在driver生成/task freeze/容器启动之前抛ContainerInfrastructureUnavailable。另只读docker context=desktop-linux，version报dockerDesktopLinuxEngine named pipe不存在，Get-Process未见Desktop/backend。没有probe执行/版本批次完整result；failure.json单独INFRA_BLOCKED，并只读重新核对已存11文件等该tagcommit Git blob。没有重试旧namespace，没有Docker启动/重启/IPC/registry/VHD/代理/tunnel/key变更。先前一个测试session在用户消息切换后不可收集，Unknown process id记录，不能据此称crash；之后源canonical增强后的重点测试明确收集。

最终新增22专项、Ruff/预算V3重点41/合成compact preflight ready=true，完整1541passed/4skipped/33warnings104.58秒，XML/两个冻结source/behavior freeze-result/version freeze-failure/source manifest绑定data/e1c_evaluation_2_behavior_version_results.json。工程passed不等于旧版已验证或修复率。原input/source/ledger/state/seal/Gold/失败与备份全保留，raw/probe/Gold/test/key不上Git；旧源码快照仅约149KiB，不是新镜像，0下载0新provider0Gold。

两Roadmap/Web handoff当前入口更新，日志只本续档；用户先打开Docker确认Engine running后，另freeze resume-only身份只推进未执行版本probe，不再运行version v1，不复用旧IPC授权。再完整义务/方法/预算freeze、同版DEV gate；未过不开新canary/TEST/C5/Fresh30/privateTest500/repair/E2，不保证完美或30/30。仅安全源码/单测/协议/脱敏收据同步Git。

交付状态补记：本轮源码/结果已本地提交3adc771；两次小型Git推送均被GitHub remote Internal Server Error拒绝（非实验retry），只读ls-remote确认main仍1fe2feb。远端同步未完成，Cloud当前main尚无本轮behavior/version新增模块；恢复后仅同步本地commits，不重跑研究namespace。工作与私有证据已本机保全，不做force push或其他历史改写。

## 2026-10-08：旧版本准备项安全续接成功，Docker/GitHub恢复

Docker与GitHub阻塞均恢复。resume-only身份已一次完成MM1359旧版3.0.0rc8同一原probe，实际版本/path核验通过、rc0；原当前base封存两次rc1未重跑。原11文件直接readonly复用，旧v1失败保持，新provider/tokens0/0、Gold读取0。只是一份DEV缓存的一个版本点，旧资格/Gold4/4/exception3/4不改，机器可信仍0，完整live方法尚未冻结。

只读require_engine恢复ready，未启动/修复Docker系统；GitHub小型push一次成功同步先前3adc771/aaae7fd，前500负记录不改。完整读ARS/ponytail，新增resume-only源码/协议/namespace，9专项+预算V3重点28/Ruff过后执行一次精确零调用run。failure receipt绑定public hash，phase/status/真实int0/driver和taskfreeze False、实际runtime文件不存在，prepared11文件SHA/inventory全核对；原producer seal/全部产物/原probe校验，原image/base/旧3.0.0rc8/原dependency条件不变，无重选版本/重新archive/下载。

新freeze/started/driver/log/result留存，oldsource/probe两个readonly mount、net-none/read-only/pull-never90s。actual__version__3.0.0rc8与__file__历史mount检查通过，原target program rc0。原current sealed execution两次rc1/probeSHA对应，只读对比、不重跑。只有一个DEV缓存/一个旧版本点实际支持，不报全更早版本、fullIssueTrusted、独立canary/repair；machine0和原资格/Gold4/4/exception3/4全保持。原v1freeze/failure/source不变，resume namespace已started不得再跑。

最终完整1550passed/4skipped/33warnings106.43秒、合成compact preflight ready=true，XML/新method/source/started/resume结果/原中断/原当前execution SHA绑定data/e1c_evaluation_2_version_resume_results.json。provider/tokens0/0、Gold读0、新probe0、新普通诊断container1、0镜像下载，旧代码与raw/private记录不删除，系统IPC/VHD/registry/proxy/tunnel/key不变。仅source/专项/协议/脱敏收据公开；private source/probe/driver/log/Gold/test/key不上Git。

两Roadmap/Web handoff更新唯一当前入口：停止重复收collector，下一步已有规则统一Controller接线、scope/剩余义务与adapter正负例/零调用真实接线，然后完整方法/预算freeze、同版DEV新生成；可信gate真达标才历史排除新canary≥2/3/Agentpatch official/DEV30/Fresh30/E2。MM1252无本轮旧版执行证据，不把MM1359结果移植，不打开TEST/C5/Fresh30/privateTest500/repair/E2，不承诺完美/30题全过。日志只本续档。

## 2026-10-08：统一Controller有限接线、真实正常正例与adapter冻结

ARS执行/冻结边界与ponytail最小改动规范指导本轮；未新增依赖/subagent/独立collector。新qualified-controller直接复用原report-anchor编译/锁定/控制/目标链，Verified input以base_commit绑定workspace，不猜taskID→文件；内层compiled.execute_probe与loop hook均接新Controller，异常退出恢复。生成只补≤8组生产Parameters声明，单文件≤1MB，host SHA与LF/base blob核验，排除Examples/答案；≤30000上下文cap不变，明确变更请求可覆盖旧文档。

policy在delegate前检查已知fixture/alias/对象变更与唯一公开期待锚，仅completion+空assertion；未知仍未知。原candidate成立才调用已有exception-v2观察、qualification-v2与behavior gate，最多两生产文件、原probe与双source身份绑定，结果进入下一轮feedback；line1为文件身份边界不是失败guard定位。fullIssueTrusted始终false，不把正常API接受域推target承诺，不把bool子义务推全issue。paired/object/version尚未自动接入，不假称已完成全方法。

前置mock chain1failed/9passed原因是Behavior.git_blob未mock，而Controller已mock；补同一合成source canonical mock、不改断言，后10passed再补synthetic issue隔离专项11passed，重点30passed/Ruff。synthetic issue清除原real fixture义务并更新issueSHA，两个新regression合成公开文本，复用sklearn/Marshmallow正常API，retrieve→probe→abstain。精确零调用smoke一次通过，normal每组两次rc0、target每组一次rc0、实际inner admission和post-verdict存在、feedback已消费、未选作bug；通过target无需第二次失败确认。2/2是正常管道正例，不是两task成功；真实selected-candidate观察分支未触发，仅mock覆盖，必须下一步真实反例验证。

新smoke/source/protocol先冻，freeze精确零调用一次成功，固定12/九准入/screen4分账，Flash候选≤16calls/batch50000/task24000/output2000/retry0、首轮保留36101。CLI只smoke/freeze、real_provider_run_enabled=false；这是有限adapter身份，不是完整producer或付费放行，不得从底层run绕过禁用。两namespace已started，不重跑/改source。完整1561passed/4skipped/33warnings118.45秒，合成compact preflight六合成任务ready=true，XML SHA及freeze/协议/源/结果在data/e1c_evaluation_2_qualified_controller_results.json；工程计数不是repair。

原producer sealSHA5997675327f8f246b179413f0c2df5efd2b66fd2edacc2f6db430796588ea86f及201产物全部匹配，新所有methodSHA无变。provider/tokens0/0、E1-C Gold0、新镜像0；旧Gold4/4、exception3/4/资格与MM1359单点旧版实证不改，machine0。无Docker重启/IPC/VHD/registry/proxy/tunnel/key修改、无删除；原raw/probe/Gold/test/key/失败/备份本机保留，不上Git。V3 mandatory synthetic grader与本轮E1-C材料分账。

两Roadmap/交接仅更新当前入口，日志本续档；协议/结果报告/安全source/专项/脱敏收据同步Git。下一步新零调用反例身份引用v1 SHA验证selected异常链，再scope/剩余义务/unknown动作gate、按需证据、完整producer freeze/旧DEV同版新生成。当前无新paid命令/不抽第6批、不打开canary/TEST/C5/Fresh30/privateTest500/repair/E2，不保证30/30或一周完美，无下载需求。

同轮进一步推进：追加controller-failure-smoke独立零调用验证协议/source/namespace，引用已冻Controller v1所有method SHA而不改v1。6专项/Ruff后一次精确命令执行；复用现有sklearn库synthetic fixture，新公开文本请求支持_e1c2_requested_flag bool，normal与target仅差该keyword。retrieve自动定位构造方法，不挑task文件；原issue fixture义务清空，参数名不是real task策略/调参规则。normal×2 rc0、target×2 rc1、实际observer rc1，qualification mechanism_supported_candidate无unknown，synthetic bool子义务支持，full issue trustedfalse/machine0，解除了真实selected分支只mock覆盖的管道缺口。不是benchmark新生成或三个任务成绩、不回填正常smoke，provider/tokens0/0/Gold0。新freeze/result/driver/protocol/verdict/observation SHA补同轮公开收据，三namespace完成后不重跑。重点36passed；当前下一步改为scope/剩余义务/unknown动作gate，不再扩同类smoke/collector。最终full suite另补最终XML，不复写先前1561计数。

最终收尾验证：1567passed/4skipped/33warnings102.02秒，XML SHA7fcb322061bb842d6b0513333712ce042e619d90c3ae5341754e5a71159f06e6。先前1561/118.45秒XML保留，收据另加final_regression。全部新method、failure driver/protocol、原201producer文件SHA再次匹配；源/协议冻结后未改。两Roadmap/交接唯一当前入口一致，source/专项/协议/结果/脱敏收据安全同步，私有raw/probe/Gold/key/历史负记录不动。

代码范围限制补记：参数声明读取v1在window缺owner时按函数名匹配已核验文件内定义，可能多同名，不是唯一targetAPI绑定。已在收据/结果/交接声明；冻结v1不改，下一producer按窗口行号与AST所属类证明唯一范围，再scope/缺证动作gate，unknown不进入repair。

## 2026-10-08：Scoped定义与补证gate，三次真实Flash后边界中断，零调用投影修复

完整读ARS执行/监控/output与ponytail，inline无subagent/依赖新建。新scope模块复用frozen qualified v1，精确start_line+直接AST owner唯一函数定义，缺/错/Boolean行号/错owner无声明保持unknown；class/guard/nested helper不作函数参数证书，host SHA/LF/base Git仍核验，不宣称targetAPI意图获证。scope action gate接内层Controller，q/behavior拒绝或unknown不terminal select，raw/lockedOracle保持；至多两production缺证symbol请求或abstain。已支持子义务/conditional hypothesis仅independent DEV grade，repair/canary/fullissue false。

15专项首次全过，Ruff1 UP012仅synthetic bytes literal机械修正在任何freeze前，不改断言。重点51/Ruff通过后新两真实正常正例smoke/freeze一次、failure smoke一次normal×2=0/target×2=1/observer1及scope grade-only过；shadow四缓存按已发布q-v3/behavior SHA核对后3grade-only/1补证/0repair，旧分类/Gold/原probe不改，不是新模型样本。四新namespace started不重跑。scope source/protocol先冻，budget继承四参考50000/task24000/max16/retry0，adapter live仍禁用。

新增单独scoped_dev_trial identity与预注册协议，parent全method SHA/positive freeze-result/negative Controller-freeze-driver/protocol/实际scope gate绑定；6专项+旧scope15共21/Ruff通过，freeze精确命令0call成功。真实paid命令会话预列model deepseek-flash/最多16calls/50000tokens（既有≤100k免二次确认授权），首请求保护37737；只OLD DEV screen4，非canary、repair false。旧adapter禁用不改；新producer目的scope calibration，inner hook/preflight/budget恢复单测证实。

实际run一次完成3calls/13706tokens，ledger3started+3completed：SK13496一次3908tokens，normal两0/target两1/observer/qualification/typeerror同keyword，有限Boolean子义务候选，default/增量/完整issue不证明、未Gold；SK26289两次9798tokens，原controller新gate缺DecisionTreeClassifier未暴露生产依赖，返ACQUIRE_EVIDENCE_OR_ABSTAIN使候选不terminal，下一第三provider调用之前messages拒绝。报BlindBoundaryViolation因qualification/behavior本地Gold_used:false字段名中marker；不是实际Gold泄漏、Docker/网络/API余额错误。HTTP proxy/socket选项warning只是提示，3请求均completed；无APIretry。MM两题未开始。state interrupted_no_auto_retry仅1完成row，无generation seal/new Gold/整批率，不能报1/4或0/4 repaired。旧Gold4/4/异常3/4等保持，machine0。停止paid、不重试旧run或换身份暗补。

新feedback_projection零调用修复，不改frozen scope/trial/boundary源。只已知q-v2/behavior-v1严格False诊断flag可从复制的agent反馈去掉；true/null/0/字符串/未知schema/其他位置marker拒绝，实际评分字串继续原边界拒，不全字符串清洗。10专项过后预列精确零调用audit一次；先freeze旧state/ledger/唯一nonterminal feedback SHA，实际production routes与所有messages层roundtrip，最终Human JSON14857字符过原audit，nested新hook存在，unknown/scope/补证条件保持。只证明安全反馈回路，不是原trial已恢复；新provider/containers/Gold0。旧中断state/ledger原样，raw诊断keys留私有源。

最终新增31专项，Ruff/预算V3重点50/合成compact preflight六合成ready=true；完整1598passed/4skipped/33warnings82.09秒，XML SHA72c22bd06eac2c4901383ee3137677b6d96c79b7901e08bd2274791701d83330。前1588/117.56秒XML与结果保留，source/namespace/prefix SHA及partial真实tokens绑定data/e1c_evaluation_2_scoped_dev_results.json，所有原201产物和qualified/scoped/trial三个method SHA最终匹配。工程计数非repair、cached shadow非新生成，partial paid不可报完整成绩。无下载/删除/Docker重启/IPC/VHD/registry/代理/tunnel/key修改；raw/probe/Gold/密钥/负记录/备份留本机。

两Roadmap/交接只更新当前入口，日志本续档。下一步先中断后resume-only决定与新冻结prefix/投影/预算身份，再仅未调用步骤（当前题最多2轮/14202tokens、两个MM各≤4call/24000，总新增最多10请求/36294tokens，累计≤50000），不重置run_id额度、不再执行原3请求/probe。现无resume CLI，不造命令、不直接run/gold旧trial；新完整seal才独立评分。之后按真实缺证接production/paired/object/version并单版九准入DEV质量gate，真正过关才新canary≥2/3/Agentpatch official/DEV30/Fresh30/E2。全部sealed TEST/C5/Fresh30/privateTest500继续关闭，不保证一周完美/30题全过；只安全source/专项/协议/脱敏收据同步Git。

## 2026-10-08：获准resume-only完成与评分，发现预算/缺证路由瓶颈

用户明确允许新身份只续未调用步骤、新增≤36294tokens、不重做旧3请求。完整读ARS执行/监控/output与ponytail，inline无subagent/新依赖。新增scoped_resume源/协议、13专项/Ruff首次全过；freeze前增强“cached prefix不完整不得新probe/provider”硬错误守卫，原断言保留重点32passed。原receipt freeze/state/ledger及整个109文件inventory核验，必须3已完成call/13706tokens、1完成row/当前2已完成轮次，无ambiguous/started未结事件。旧source/namespace不改，不读取Gold。

resume-zero新namespace先source/protocol/prefix freeze，实际loop缓存AIMessage回放两原response（0新usage），旧两个probe被cache execute硬拦并返回已存反馈/锁定Oracle/执行，payload/input/Oracle/顺序等原JSON；在第三轮完整conversation验证后synthetic abstain，0模型/容器/旧probe重跑，原prefix不变。新resume method freeze包括投影，parent全部源/protocol/正负scope gate身份绑定，精确run命令与Flash/新增最多10call/36294tokens/累计50000/rertry0会话预列后执行一次。

新ledger原6事件逐字节copy前缀并沿用原run_id记预算，旧3费用不清零；累计task24000/max4calls/output2000/global50000及未开始任务首请求保护原样。首题原已完成candidate/execution/probe逐字节复用并origin=original_completed_prefix不叫新生成；其模型/原probe0重做。后当前第二题新第三请求、两个原未开始MM任务正常推进，原旧trial仍INTERRUPTED。真实新增7calls/29996tokens，加旧3/13706合计10/43702，无未结/重复请求，余额6298。四行终局completed，新generation-seal绑定255产物，原109prefix与全部method最终一致。

实际状态：SK13496复用子义务候选；SK26289第三轮新probe target通过但无故障候选，第四请求task reserve15351+11985>24000，未调用，budget stop；MM1252三新请求12498tokens，第四请求global reserve31757+10154>41520，未调用，budget stop；MM1359三新请求11945tokens、normal三次失败，第四重复动作被no-progress stop阻止，无再付费。不能把stopped叫正确/错误task率、不能声称四题通过。seal完成后精确gold命令0provider一次，唯一旧prefix候选Gold施加后rc0/消除true，attempted1/discriminating1；新增生成合格候选0，machine0/Agent repair0。旧Gold4/4/异常3/4不回填或拼入本轮。

只读归因：MM1252没有已暴露production binding，observer之前verdict.program存unexposed Schema，但scope.action_gate仅读qualification.program_evidence丢source建议，三反馈requests=[]；SK未执行先前Classifier建议，新probe自身List输入正常完成不证明原问题解决。新增dependency_feedback新协议/source/namespace4专项过后shadow audit，复用原gate把program映射为unknown/rejected资格视图，旧rejected/missing保持，三份Schema请求恢复；0模型/容器/Gold读、不改old Scope/score，不声称模型已采用。未接future live，下一新producer必须真正有界取得source并记录SHA；不继续旁路collector/同类smoke。

最终新增resume13/router4共17专项、重点36/Ruff/合成compact preflight ready=true，完整1615passed/4skipped/33warnings79.10秒，XML SHA01b43cd74e9b8331adba5c09c6bddbc304de5dca352a7000379bfbaa41812f2e；前1611/87.85秒XML保留。data/e1c_evaluation_2_scoped_resume_results.json绑定source/prefix/seal/Gold/shadow/账本与真实tokens，旧更早201producer产物也全部匹配。工程计数非repair，1/1Gold是复用已选probe的独立消除，不是新算法成绩/全issue证明。

无下载/删除/系统Docker重启/IPC/VHD/registry/代理/tunnel/key修改，私有raw/probe/Gold/密钥/负记录留本机。两Roadmap/交接更新唯一当前入口，日志本续档。下一步新producer实际路由/有界补证→压缩重复上下文和正确prior-action消息、两预算stop实际reserve零调用验收→整体source/预算freeze再同版DEV；原额度仅剩6298，不自动追加新paid批次、禁止重跑旧resume/run/gold/audit。仍未过质量gate，不开canary/TEST/C5/Fresh30/privateTest500/repair/E2，不保证一周或30/30完美。

## 2026-10-08：自动source取得、官方context依据与80k新批，JSON模板负结果

用户追加要求必要时增上下文、搜索一般配置并合理修改预算。完整读ARS执行/监控/output与ponytail，不新增subagent/依赖。查DeepSeek官方models/pricing（裸URL抓取timeout，官方索引带query页面可读）、SWE-agent model config与mini默认yaml；仅primary官方资料作为依据。Flash 1M是技术context上限不是项目建议消费，Agent分input/output/per-instance/global/calls，未给通用最优token。按自有真实reserve设计input软12k/estimated hard24k/output2k/tasksoft32k-hard48k/batchhard80k/max16/retry0/未开始任务首请求保护，不用Pro。原预算不回填，记录多因素变更不单因果。

新acquisition_context从program/q未暴露import binding经static resolve_symbol取得对应production class/func，路径一致/symlink/1MB/host LF==base Git校验，max2symbols/issue+base，独立overlay给next messages/execute，初始input不mutate、补源不重算当前资格。public payload spans/facts/源/锚/声明保留，旧30k/36k字符层改新estimated token检查+96k字符安全cap，system策略合并、动作/反馈只一次、prior kind准确。首次Ruff unused import和nested conversation test1failed/7passed留档，修复真实report owner，不弱化断言；另补resume内层projection覆盖防线，9专项全过。

原acquisition_context_zero_v1先freeze后在缓存turn2读compiler.json缺失停止，自动acquisition未执行，0模型/容器，原源和身份保全。新check_resume协议/源/namespace，2专项后仅原seal255文件（不含Gold）复制view，缓存compiler/contract/execution只按原109prefix SHA补齐；验证路径不逃scope/原seal身份，driver/protocol/旧fail冻结。精确零调用续接检查一次成功：真实取得DecisionTreeClassifier/Schema两源并next Human暴露，cached delegate不重执行probe。新context带新源reserve11985→11100(estimatedinput6500)、10154→8471(input4622)，仍unknown，无Gold读/新容器。边界实际接线不是模型成果。

新acquisition_dev完整源/协议/预算freeze，3预算/hook专项+整体重点33/Ruff后，按既有≤100k单实验免二次确认且用户最新合理增context授权，预列精确paid run/modelFlash/max16/batch80k/task48k/retry0执行一次。真实16completed请求/53212tokens，input2527–4610，无budgetstop/unresolved/APIretry；四任务终局1turn_limit/3abstained，0candidate/machine0/Agentrepair0，54产物seal；精确独立Gold0provider命令完成attempted0/discriminating0（没有候选，不启动Gold容器）。旧1复用Gold候选/更早4/4都不拼分。本batch自动source机制未被有效probe触发，不能宣称live取得收益。

响应只读归因：三题6probe复制system example英文setup说明为Python，syntax拒；另一题4回复closed {type:json_object,action:dict}未支持，其中2probe也复制说明。不是再次context耗尽；提升预算不等于效果改好。原paid/source/policy不改、不重跑。新action_protocol去probe代码示例值仅字段规则，精确known外层wrapper可拆其inner原值，其余不猜；原decoder只做schema造成1failed/6passed，实际加ast.parse前置不改断言，7过。新zeroProtocol source/proto/seal先冻，对16responses仅syntax包装诊断：4wrapper恢复、8有效nonprobe、8坏probe依旧SyntaxError，不补写代码不伪造成功，0新模型/容器/Gold。尚未集成future producer/实测新模型。

最终21新专项、重点40/Ruff/合成compact preflight ready，完整1636passed/4skipped/33warnings81.43秒/XML SHA8e54244136b2422b3b505df0e9e2d2f0b5b989e932a83dc17233c72233a9fcdc；前1629/107.46 XML保留。data/e1c_evaluation_2_acquisition_results.json绑定zero/80k state-ledger-seal/协议zero/真实token/预算与official links，原201/109/255与全部method保持。无下载/删除/系统Docker/IPC/VHD/registry/代理/tunnel/key改变，raw/probe/Gold/key/备份留本机，TEST/C5/Fresh30/canary/privateTest500关闭。

两Roadmap/交接唯一入口更新；日志本续档。下一步无示例policy+codec整体接新producer，最终messages/实际decoder同轮JSON smoke、坏代码仍拒，完整method/80k预算freeze再新DEV；不能只扩预算或旁路collector/在旧批重试。没过质量gate不九准入扩批/新canary/repair/E2，不保证一周/30题全过。公开safe源码/单测/协议/脱敏收据，旧负结果全保留。

## 2026-10-08：真实协议链小阶段、live自动补证与反馈缺口

用户继续授权推进研究，既有单实验≤100k/Flash/精确命令预列委托延续。使用ARS实验执行规范保留冻结边界、ponytail最小改动复用预算/检索/执行器；inline，无subagent/新依赖。上一turn中断只完成source/test/试验freeze，未付费；本turn先核对namespace无state/ledger及无正在执行模型，再继续，不盲目重复冻结/实验。

新protocol_pilot把去示例policy与closed wrapper/strict quote/Oracle/AST挂到实际nested parser，codec proof随动作传递，预算gateway实际max_calls=1；正负及预算恢复检查通过。按冻结四参考顺序每library family第一条，非人工文件定位，固定DEV12/准入9/screen2。预列精确run命令/Flash/max2call/20k/task12k/output2k/retry0，真实2calls/5997tokens都是有效成功retrieve，第二轮被call cap拦截，无probe，不报task失败或通过，11文件seal。

新probe-stage仅复用父seal turn2生产窗口输入，核对issue/base/Git/输入摘要，绑定parent及new input；上阶段正常完成、非API失败重试。新source/protocol/cap先freeze，source父协议常量修正发生freeze前，6测试/Ruff过；预列max6calls/40k/task24k/retry0精确命令后真实5calls/20914tokens。SK生成真实Python，normal因unsupported构造器setup rephase移出model绑定后NameError，两次control失败；另一MM重复DateTime._deserialize被no-information-gain stop。无candidate/Gold/机器可信，39文件seal。

新protocol_execution source-backed frontier守卫：只检查setup移出直接绑定与正常control读取的关系，明确缺失进容器前拒绝；normal显式重建receiver可放行，self-reference/conditional未知保守拒，不推导/编造control、不改旧compiler/期待。新增guard producer实际inner hook，策略明确setup两边执行、target-only缺陷配置/支持normal、成功查询不重复。12专项过，preflight只读前真实失败canon/input覆盖并拒绝；原stage seal/source不变，40k新identity冻结。预列精确Flash/max6call/40k/task24k/output2k/retry0后运行6calls/26797tokens，两题最终abstained，0qualified/machine/repair，52文件seal，无API重试。

最新MM第二轮probe normal两0/target重复ValidationError两1，program依赖未知使Controller要求Schema，实际adapter取得host/LF/base匹配生产定义；下一个请求含取得窗口。首次只读查turn3/input没Schema，因为overlay刻意不mutate input；随后按实际capture反馈重建overlay和第三轮消息，其prompt SHA与真实provider ledger完全一致且Human含Schema。零检查第一次agents import顺序错误，evals入口先import后修正验证；未写旧产物/新容器/模型。此为真实live补证，不是cached delegate；fixture Foo公共引用scope仍unknown，绝不授可信或称repair。

模型最后以环境未证明弃权；只读发现control1/control2/target执行都已记录强制阻断dateutil，executor readonly blocker明确，并非条件不存在，而是消息遗漏。新environment_feedback纯投影matching schema/input/image/base/module/offline有效运行，None/错条件不提升；自然未安装/guard runtime值/语义证明都false。5专项与实际旧记录project→compact零调用过，未接新paidproducer，不声称已经修复模型弃权。另一SK误将公开新增keyword请求在旧signature缺失判作不能测；下一方法要区分feature request与regression，公开明确参数可target失败入口、normal base支持，仍不证明default/增量/全issue。无task-ID特例，无Gold读/新评分。

新合计13calls/53708tokens，各三lineage独立、不混上一16/53212或旧50k。当前合格候选0/机器可信0/Agentrepair0，未Gold；两个旧DEV来源不可当6独立任务。新17专项、Ruff/预算V3重点/合成compact preflight ready；三完整回归1642/103.05秒、1648/93.83秒、最终1653passed/4skipped/33warnings87.86秒，各XML保留，最终SHA21a5b08d5b42a17cc55d0cdfd0b0059b56074588cb0a497b0a13d0317961c85b。原201/255/54 seal及新三11/39/52产物、冻结源码核验全保持；公开receipt/result绑定。

两Roadmap/接手更新当前唯一入口，旧版本与Git历史保留，日志只在本续档。下一步完整接environment_feedback与公开接口请求解释、现有fixture身份观察到主链；先实际最终消息/内层正负验证，新完整method/预算freeze，小额两个来源DEV，过关再四参考/九准入，真实质量gate才新不重叠canary一次≥2/3、Agent patch/official、DEV30/另授权Fresh30/E2。所有started namespace禁止重跑，当前无可运行新paid命令，不保证完美/一周30题全过。不删/下载镜像、不重启Docker、不改IPC/VHD/registry/代理/tunnel/key，raw/probe/Gold/密钥/备份/负结果本机保全，sealed TEST/C5/Fresh30/privateTest500继续关闭。
