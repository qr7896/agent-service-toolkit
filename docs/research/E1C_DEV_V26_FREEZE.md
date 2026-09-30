# E1-C DEV v2.6：单题回归反馈 canary

2026-09-24，付费调用前冻结。v2.5 真实限额探针 input=45、output=512、total=557，输出符合上限；该探针不计修复结果。

- 身份：`e1c-dev-v26-regression1-20260924`；入口：`uv run --frozen python -X utf8 -m evals.e1c_dev_v26 run`；runner SHA-256=`c577918873df2088e2a01e7908c2022d15d8220b1d8d104674ee6077aaf7dfa5`；原 n30 manifest SHA-256=`7d8e6569054195d8d68b406b1e51b9d43778b3b9699df4bc8c3672aa049a4435`。
- 仅 `django__django-16100`：v2.3 已通过 F2P 1/1、却丢失 P2P 1/59。新请求输入公开题面、base 源码、先前**模型候选**补丁与官方回归失败 traceback；不读取或输入 gold patch。候选回到原 base，仍用官方 Docker 评分。此题是 outcome-selected DEV，不能外推。
- DeepSeek `deepseek-flash`，thinking disabled；最多一次请求，max output 2,000，单题/整批 6,000 provider tokens，SDK retries=0。预检 ready，run 目录不存在，Ruff clean。失败/不确定即停，保留账本，不自动重试。
- 扩展门槛：若此题未产生净新 resolved，不把同一反馈模式盲目扩到其余 29 题；转零调用分析。30/30 是开发目标，不是可保证结果。
