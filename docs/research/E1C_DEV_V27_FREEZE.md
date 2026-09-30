# E1-C DEV v2.7：缩短重复源码的回归反馈 canary

2026-09-24，付费调用前冻结。v2.6 `e1c-dev-v26-regression1-20260924` 因预留 6,211 > ceiling 6,000，在**没有 provider ledger、没有 API 请求**时停止；其 identity/state 原样保留，不能当成任务实验失败或重试。修复是去除无关源码窗口并在预检中精确计算预算预留。

- 新身份 `e1c-dev-v27-regression1-20260924`，入口 `uv run --frozen python -X utf8 -m evals.e1c_dev_v27 run`，runner SHA-256=`979d790a725c6a2fdc0169294e1efb4345943c137ff129f6fb822aebbaa13040`，原 n30 manifest SHA-256=`7d8e6569054195d8d68b406b1e51b9d43778b3b9699df4bc8c3672aa049a4435`。
- 仅 `django__django-16100`，公开题面、base 源码、旧模型候选与公开回归 traceback；无 gold patch。DeepSeek Flash thinking disabled，最多1次请求，max output 2,000，单题/整批 provider ceiling 6,000，SDK retries=0。零调用预检 ready、预算预留4,792、运行目录不存在，Ruff clean。
- 使用官方 Docker grade；若无净新 resolved，不扩展此反馈模式。结果只记 outcome-selected post-outcome DEV，不称独立 E1-C/E2 效果。
