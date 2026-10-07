# WebCodex 接手：E1-C evaluation_2

交接日期：2026-10-07。仓库qr7896/agent-service-toolkit。先读[AGENTS.md](../../AGENTS.md)、[当前Roadmap](../PROGRESS_RESEARCH_ROADMAP_2.md)、[本轮结果](E1C2_UNIFIED_POLICY_CODEC_RESULTS_2026-10-07.md)。

## 1. 已完成，不要重跑

unified-policy-reference-dev-v1：9 Flash请求25,928 tokens，接口解析拒绝、无候选、Gold attempted0。
unified-codec-reference-dev-v1：6请求18,038，独立Gold区分2/4，machine trusted0；SK26289未复现弃答、MM1359正常control失败。两个namespace的smoke/freeze/run/seal/Gold均已完成；所有原件禁止修改、重跑或best-of合并。

本轮共43,966 tokens、无retry，工程1388 passed/4 skipped/33 warnings（93.81秒）；Ruff和规定V3 preflight ready=true。公开[data收据](../../data/e1c_evaluation_2_unified_policy_codec_results.json)绑定哈希，不含raw/Gold/test/key。当前不需要下载。

## 2. 先做零调用，而非第三个付费screen

复用contrast_audit、guard_evidence、api_obligation、guard_type_observer，建立公开约束/已观察事实/模型输入假设/normal配置/目标/未证项的可执行契约。不是再叠提示或人工挑某题array/date/期待。

同动作control/target的AST相同只触发状态审查，不自动证明无效；不同AST也不证明独立。裸Name生产guard有隐式truth-testing协议，源码没有raise不能证明无异常。模型假设由自身执行验证，不能叫原报告exact输入或语义可信证书。

先验跨仓库有效control、同故障control、共享setup故障、类型声称冲突、未知入口/表达式。diagnostic目前未接live；normal两过/目标两失败/行为义务与源SHA一致后，另冻新方法和预算，一次旧四参考，再完整九准入；之后才新不重叠canary≥2/3、Agent修复、独立official grade、新任务。原四参考开发成功不算独立。

## 3. Cloud安全执行

确认checkout/uv.lock，不需要DeepSeek或tunnel密钥即可先运行：

```bash
uv sync --frozen --group dev
uv run --frozen python -m ruff check evals/e1c_evaluation_2_unified_policy_dev.py evals/e1c_evaluation_2_unified_codec_dev.py evals/e1c_evaluation_2_contrast_audit.py tests/test_e1c_evaluation_2_unified_policy_dev.py tests/test_e1c_evaluation_2_unified_codec_dev.py tests/test_e1c_evaluation_2_contrast_audit.py
uv run --frozen python -m pytest -q tests/test_e1c_evaluation_2_unified_policy_dev.py tests/test_e1c_evaluation_2_unified_codec_dev.py tests/test_e1c_evaluation_2_contrast_audit.py tests/test_model_budget.py tests/test_v3_pilot_runner.py tests/test_v3_compact_pilot.py
uv run --frozen python -m evals.v3_compact_pilot preflight
uv run --frozen python -m pytest -q
```

依赖未缓存时uv sync需要云端安装权限；安装失败报环境阻塞，不降低测试。不把合成V3 preflight当真实sealed TEST实验。

本机真实screen还要求exact-base生产源、原始.codex证据、不可变镜像与Docker执行器；缺任一项报INFRA_BLOCKED，不从公开摘要伪造原始输入。旧bridge白名单未扩、不假称已验证云端新paid入口，不开放裸daemon或上传key/raw/Gold。

## 4. 付费与机器边界

每个未来新实验必须先列精确命令、Flash模型、次数、≤100,000 token上限，另立未开始namespace；retry0、输入隔离、producer seal后独立Gold。不使用Pro，不抽/打开sealed TEST/C5/Fresh30/SERBench私有Test500。没有新canary/repair/E2授权命令。

不删除镜像/VHD/工作内容，不改注册表、代理、tunnel或凭证；旧IPC修复授权已消费，需新的明确授权才动指定目录。大文件下载交用户终端直连，不走VPN；当前无下载需求。

## 5. 回传与历史

回传源码diff、运行环境、精确命令、单测/工程数、实际账本、各固定分母、未过gate、下一步。不承诺完美/30/30，不把Gold或回归数称修复率。日志只写[集中续档](PROGRESS_LOG_ARCHIVE_2026-09-27_CONTINUATION.md)，更新两Roadmap唯一当前区；原交接页全文已保存在2026-10-07归档，不按其旧“当前”命令运行。
