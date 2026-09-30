# E1-C DEV v4.2：既有模型候选补丁机械组合（零模型）

2026-09-24，官方 grade 前冻结。v4.0 第一候选添加 `--skip-checks` 参数，v4.1 第一候选在源码断言点条件化系统检查；两者分别 F2P0/1、P2P245/245，并未独立解决。两份补丁分别由模型产生，不手写新的问题特定修复；按固定顺序在原 base 的隔离 worktree `git apply --check` 并应用，生成合并 diff，官方 Docker grade。重叠冲突立即失败，不自动改写补丁。

- 身份 `e1c-dev-v42-model-patch-union1-20260924`，入口 `uv run --frozen python -X utf8 -m evals.e1c_dev_v42 run`，runner SHA-256 `58adf7389cf6b3f59b415e11b6941647c31978f70c70c6345e3093d49846e904`，manifest SHA-256 `7d8e6569054195d8d68b406b1e51b9d43778b3b9699df4bc8c3672aa049a4435`。两块源 diff SHA-256 分别 `28e8040e393228cfe90202822ff811ec192b7e72437df3ca00d69ae98e065916`、`7a7e79e3499f80e038e547d82f5d0ff682a183907a8d726083abce6194862435`。
- 零模型预检 ready、两原候选官方 source identity valid、回归全保留且目标未过、SHA匹配、无 test 路径；Ruff clean。此次 provider calls=0/tokens=0。仍是观察过结果的同题 DEV 补丁组合，不是新模型运行，更不是独立修复率。不得替代一次冻结后的新任务实验。
