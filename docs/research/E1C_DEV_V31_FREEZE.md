# E1-C DEV v3.1：23 条未解题多轮 Agent canary

日期：2026-09-24。状态：付费调用前冻结。用户授权 E1-C 同题 DEV 弹性预算连续优化，但 30/30 只是目标；任何跨轮 best-of 均不得冒充单次独立修复率。先前独立 DEV v2.1=4/30，跨身份 best-of=7/30。

- 新身份 `e1c-dev-v31-agentic23-20260924`，入口 `uv run --frozen python -X utf8 -m evals.e1c_dev_v31 run`；runner SHA-256=`d794f3398f87e3ecf18d33ab867a1eded54c49d2065d01050f0b5161f714ad9a`，原 cohort manifest SHA-256=`7d8e6569054195d8d68b406b1e51b9d43778b3b9699df4bc8c3672aa049a4435`。固定选择原30题中未被历史 DEV 任一身份解决的23条；历史7题集合在代码中核对。
- 每题从原 base 建新 worktree。模型动作仅 `search`（安全源路径列表）、`inspect`（候选路径的短源码窗口）、`edits`（已暴露源路径的 exact replacement）。公开题面、base 源码和本轮官方失败输出允许反馈；不输入 gold patch，不读 E1-B sealed TEST、SERBench private/Test500。既有 DEV 相同 diff hash 或本轮重复 diff 在 Docker 前拒绝；每个不同候选由官方隔离 Docker grader 判分，任务级 source identity guard 保持不变。
- DeepSeek `deepseek-flash` thinking disabled，SDK retries=0；每题最多5次 provider 请求、输出上限1,800 tokens、单题 hard ceiling36,000、整批 hard ceiling828,000 provider tokens，最多115请求。任一未决/异常 provider 请求立即停止、不自动重试。无调用的 preflight 23/23 ready、最大首轮预留5,707，运行目录不存在。Ruff clean，focused 11 passed，完整非模型回归664 passed/4 skipped/33 warnings。
- 预期进程可能超过30分钟；批次硬墙钟上限4小时，监控 PID 与 state/ledger 进度。结果是对23条未解题的 outcome-selected DEV 续攻；即使23/23解出，也只能报告跨轮 best-of 30/30，不能称一次 n30 运行或独立泛化证据。
