# E1-C DEV v2.5：真实 provider 输出上限探针

2026-09-24，付费调用前冻结。用户允许 E1-C 同题 DEV 反复优化及弹性预算，但 v2.4 首次 thinking 请求因错误字段得到 62,656 output tokens；零网络修复后，必须先验证真实服务端上限才恢复任务实验。

- 身份：`e1c-dev-v25-cap-probe-20260924`；入口：`uv run --frozen python -X utf8 -m evals.e1c_provider_cap_probe run`；脚本 SHA-256：`e78fe885ed74ece21cc0f65a88c4c6ca85aad7b4d0e8e4276c504400244fc44b`。
- `deepseek-flash`，thinking enabled/low，**只发 1 次请求**，输出上限 512 tokens，整次账面上限 2,000 tokens，SDK retries=0。提示要求长输出以测试限制；不含任务源码、不做 Docker grade，也不算修复率。
- 前置：run 目录不存在、Ruff clean、预算定向 10 tests passed。请求、用量及异常写入新目录 `.codex/e1c/e1c-dev-v25-cap-probe-20260924/`；若实际输出超过 512、超总预算、响应不确定或失败，立即停付费实验，保留原始账本，不自动重试。
- 如果输出限制实测有效，才能另建任务实验新身份；旧 v2.4 结果与账本永不覆盖。
