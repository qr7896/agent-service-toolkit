# E1-C DEV v3.9：自动定位高置信5题 canary

2026-09-24，付费调用前冻结。此身份验证任务无关 locator 的修复效果，而非仅验证有源码窗口。

- 入口 `uv run --frozen python -X utf8 -m evals.e1c_dev_v39 run`；身份 `e1c-dev-v39-auto-highconf5-20260924`；launcher SHA-256 `6d76f7fbdb4b528dab9297d6cf0ab3a67595e95768d50ac483a45273c01449b1`；locator SHA-256 `b65b5afb0dddee0b9176476b4780a0d89d118d2449598618d8c0fa7cc168653c`；复用未修改的 v3.3 engine SHA-256 `6f42b80c7429f9b425f427c59a4d2a2ce0f2b376c3bce1726879333d849df944`；cohort manifest SHA-256 `7d8e6569054195d8d68b406b1e51b9d43778b3b9699df4bc8c3672aa049a4435`。
- 冻结选择：在原30题 manifest 顺序中，排除跨 DEV 身份已有10条 solved，取最先5个 `locate()` 有高置信路径的未解任务。预检固定得到 `sympy__sympy-13798`、`sympy__sympy-17318`、`sympy__sympy-18211`、`django__django-13809`、`django__django-15731`。文件/函数选择由同一 locator 自动执行，无按 task ID 写路径。此前结果用于选未解题，因此本轮仍是 outcome-selected DEV，不是独立非反复实验。
- `deepseek-flash`，non-thinking、non-streaming、直连 `trust_env=False`、SDK retries=0；每题≤2请求、输出≤1,600、每题≤20,000、整批≤100,000 provider tokens；逐题账本，ambiguous 不重试并停批次。exact edits 从原 base、旧 patch hash 去重、官方 Docker grade。新 identity 和原身份独立。
- 零调用预检5/5 ready、首轮预留4,444/6,923/4,373/5,109/4,054，镜像与 Base-Fail/Gold-Pass/源码身份一致、run目录不存在、Ruff clean。若0净新解决，不在相同机制上扩批；若有净新解决，再考虑自动定位的其余未解题。不能宣称 E1-C 单次通过率或 E2 成果。
