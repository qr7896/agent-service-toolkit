# E1-C DEV v2.9：两题目标测试失败反馈 canary

2026-09-24，付费调用前冻结。v2.8 两题 outcome-selected DEV 中 `django__django-13279` 新 resolved，`django__django-12774` 仍失败；2次请求共5,772 tokens，均未超限。此轮只测试不同失败类型，不盲目扩张。

- 身份 `e1c-dev-v29-targetfail2-20260924`；入口 `uv run --frozen python -X utf8 -m evals.e1c_dev_v29 run`；runner SHA-256=`30dcc34de896f23d64f6a60172d23c72b9fc2f771a8e6d10b8b18c432ced98b2`；manifest SHA-256=`7d8e6569054195d8d68b406b1e51b9d43778b3b9699df4bc8c3672aa049a4435`。
- 固定两题 `sympy__sympy-13798`、`sphinx-doc__sphinx-9230`：两题上轮目标检查均未通过。仅输入公开题面、原 base 源码、先前模型候选 patch 与公开失败输出；没有 gold patch。每题从原 base 起步、官方 Docker grade。
- DeepSeek Flash thinking disabled；每题最多1次请求、max output2,000、单题8,000、整批16,000 provider tokens，SDK retries=0。零调用预检2/2 ready，预留6,914/7,364，run 目录不存在，Ruff clean。请求不确定即停、不自动重试。
- 此轮及全部 E1-C 反复调优只作为同题 DEV；成功不能替代独立验证。
