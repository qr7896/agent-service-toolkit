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
