# E1-C DEV v4.0：模型建议文件的安全补证 canary

2026-09-24，付费调用前冻结。v3.9 自动定位高置信5题完成、10 completed calls/22,836 tokens、0新 resolved。两题首步失败原因相同：模型建议的生产文件未在既有 excerpt 中，runner 拒绝；不意味着建议路径不安全。新机制只针对这类错误：校验建议相对 `.py` 路径在原 base 内、非测试、非 symlink、无目录穿越，然后自动开放该文件局部窗口。没有任务 ID→人工路径规则。

- 新身份 `e1c-dev-v40-suggested-path2-20260924`；入口 `uv run --frozen python -X utf8 -m evals.e1c_dev_v40 run`；launcher SHA-256 `9558b9eb8621d7c14d71e0a54c07f443b969a003a76a279c0a605453c7ad8f24`；复用未修改的 v3.3 engine SHA-256 `6f42b80c7429f9b425f427c59a4d2a2ce0f2b376c3bce1726879333d849df944`；原30题 manifest SHA-256 `7d8e6569054195d8d68b406b1e51b9d43778b3b9699df4bc8c3672aa049a4435`。
- 准入选择规则是 v3.9 首步全部 `path was not exposed` 的未解任务，恰为 `sympy__sympy-13798`、`django__django-13809`；路径来自 prior model 输出，经通用安全检查。零调用预检2/2 ready，预留5,814/6,729，镜像/Base-Fail/Gold-Pass/源码身份一致、run目录不存在、Ruff clean。
- DeepSeek Flash non-thinking/non-streaming、直连、SDK retries=0；每题≤2请求、输出≤1,600、任务≤20,000、批次≤40,000 provider tokens；逐题账本，ambiguous 不重试并停；exact edits 原 base、diff 去重、官方 Docker grade。新身份仅为 outcome-selected public DEV，不能称独立非反复通过率。若无净新 resolved，不对相同机制扩批。
