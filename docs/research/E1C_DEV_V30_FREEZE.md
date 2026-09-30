# E1-C DEV v3.0：失败断言聚焦 + 重复补丁拒绝

2026-09-24，付费调用前冻结。v2.9 两题均无新增 resolved，模型照抄既有失败补丁；本轮只验证更精准的公开失败证据能否改变行为。

- 身份 `e1c-dev-v30-focused1-20260924`，入口 `uv run --frozen python -X utf8 -m evals.e1c_dev_v30 run`，runner SHA-256=`8072c660a2e7d47a76f741724c5413283849173c4968129ad40ce73f73fd6fd0`，原 manifest SHA-256=`7d8e6569054195d8d68b406b1e51b9d43778b3b9699df4bc8c3672aa049a4435`。
- 仅 `sympy__sympy-13798`。输入公开题面/base 源码、先前失败的模型候选、官方测试中明确的 `test_latex_basic` 断言；不输入 gold patch。若返回与上轮完全相同的 edits，运行器在 Docker 前拒绝。
- DeepSeek Flash thinking disabled，最多1次请求，max output1,400，单题/整批6,000 provider tokens，SDK retries=0。零调用预检 ready、预留4,856、run 目录不存在、Ruff clean。从 exact base 开始，差异候选才做官方 Docker grade。
- 无净新 resolved 就停该付费路径；结果始终只是 outcome-selected DEV，不是独立修复率。
