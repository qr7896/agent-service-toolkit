# E1-C DEV v4.1：失败断言自动回指先前编辑文件

2026-09-24，付费前冻结。v4.0 在 `django__django-13809` 得到两份 P2P245/245、F2P0/1 的候选；最新公开失败断言包含 `Performing system checks...`，文本可以在先前模型选定的 `runserver.py` 中精确匹配。新规则从已评分 patch 提取编辑文件、从官方公开失败提取被断言的文本，再自动建立局部源码窗口；不是研究者手动指定函数。

- 身份 `e1c-dev-v41-assertion-source1-20260924`；入口 `uv run --frozen python -X utf8 -m evals.e1c_dev_v41 run`；launcher SHA-256 `24026a1c28db1b7e52aae591faa4e59a71f150b892cf5cbf00738d55edeaf481`；复用未修改的 v3.3 engine SHA-256 `6f42b80c7429f9b425f427c59a4d2a2ce0f2b376c3bce1726879333d849df944`；原30题 manifest SHA-256 `7d8e6569054195d8d68b406b1e51b9d43778b3b9699df4bc8c3672aa049a4435`。
- 选择规则：v4.0 中最后一份官方 grade 为目标失败、回归全保留的候选。输入公开题面、base-fail、先前自己生成的 patch、该候选官方失败及原 base 的断言对应源码窗口；不读 gold patch / sealed TEST。新候选仍从原 base 生成，并拦截重复 diff。
- DeepSeek Flash non-thinking/non-streaming、直连、SDK retries=0；≤2请求、输出≤1,800、任务≤20,000 provider tokens，ambiguous 不重试；官方 Docker grade。零调用预检 ready、预留6,244，镜像/准入/source identity一致，Ruff clean，run目录不存在。仅属 outcome-selected DEV，不能称独立成绩；若无净新 resolved，不继续同质抽样。
