# E1-C DEV v2.8：两题近失回归反馈 canary

2026-09-24，付费调用前冻结。v2.7 的 `django__django-16100` 使用公开回归 traceback 后通过官方 F2P 1/1、P2P 59/59，单次2,269 provider tokens；仅属 outcome-selected DEV。

- 新身份 `e1c-dev-v28-nearmiss2-20260924`，入口 `uv run --frozen python -X utf8 -m evals.e1c_dev_v28 run`，runner SHA-256=`de144e6e642cdf9d8ccae6838ae145d20d626a2b9a3c2c1c62f0f7d909b87d9d`，cohort manifest SHA-256=`7d8e6569054195d8d68b406b1e51b9d43778b3b9699df4bc8c3672aa049a4435`。
- 固定两题：`django__django-12774`（先前 F2P 1/1、P2P 39/41）与 `django__django-13279`（F2P 9/9、P2P 337/346）。只用公开题面、原 base 源码、先前模型候选补丁及官方公开回归 traceback；不读 gold patch。每题从 exact base 起步，官方 Docker grade。
- DeepSeek `deepseek-flash` thinking disabled；每题最多1次请求、max output2,000、单题8,000、整批16,000 provider tokens，SDK retries=0。零调用预检2/2 ready，预算预留6,523/6,303，目录不存在，Ruff clean。任何未决 provider 请求立即停止，不自动重试。
- 结果仅记同题 DEV；即使两题成功，也不能称 E1-C 独立通过率或 E2 效果。若无净新 resolved，不盲目扩大该模式。
