# E1-C DEV v3.5：公开失败测试定位 canary

2026-09-24，付费调用前冻结。v3.4 的18个未解任务中，多题被定位到与失败测试无关的源码，故先测试定位修正，不直接再跑整批。

- 身份 `e1c-dev-v35-testtrace-canary3-20260924`；入口 `uv run --frozen python -X utf8 -m evals.e1c_dev_v35 run`；launcher SHA-256 `561c148bffb0410feb2a9a4d1760215a89d7559592620761146384d1a0cf55fa`；复用未修改的 v3.3 engine SHA-256 `6f42b80c7429f9b425f427c59a4d2a2ce0f2b376c3bce1726879333d849df944`；cohort manifest SHA-256 `7d8e6569054195d8d68b406b1e51b9d43778b3b9699df4bc8c3672aa049a4435`。
- 固定3条历史未解公开 DEV：`django__django-11740`、`django__django-12754`、`django__django-16502`。研究者仅从公开失败测试名/traceback和原始 issue 确定相关源文件与函数，不看 gold patch；因此是 **human-localized, outcome-selected DEV**，不可作为自动定位器/独立成功率证据。
- 每题向 Flash 提供公开题面、base-fail 断言、原 base 源码三个窗口；exact edits 从原 base 应用，旧补丁去重，官方 Docker grade 后向下一轮反馈公开失败。DeepSeek `deepseek-flash`、non-thinking、non-streaming、`httpx.AsyncClient(trust_env=False)`、SDK retries=0；每题≤3调用，输出≤1,800、单题≤18,000、整批≤54,000 provider tokens。单题独立账本；任意 ambiguous 即停，不自动重试。
- 零调用预检3/3 ready，窗口都在相关源文件，预留分别9,165/9,066/7,570，Ruff clean，run目录不存在。成功门槛：至少1条**净新**官方 resolved 才考虑扩大使用此定位机制；否则分析失败并停止同质付费抽样。所有结果仍只是同题 DEV，E1-B TEST、E2/E3不触碰。
