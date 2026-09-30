# E1-C DEV v4.3：自动定位＋安全窗口外路径，剩余19题

2026-09-24，付费前冻结。跨多身份 best-of 11/30，且现有30题均为反复开发集；本轮按原 manifest 顺序固定其余19题，一次完整 DEV pass 检查任务无关定位能否带来净新通过。研究者不为任何 task ID 指定文件/函数。

- 身份 `e1c-dev-v43-auto-remaining19-20260924`；入口 `uv run --frozen python -X utf8 -m evals.e1c_dev_v43 run`；launcher SHA-256 `768b2efe6498b23b2b25841f5849b958130c1bdfe9c998f4eea86e888b0589b7`；locator v1 SHA-256 `b65b5afb0dddee0b9176476b4780a0d89d118d2449598618d8c0fa7cc168653c`；复用未修改的 v3.3 task engine SHA-256 `6f42b80c7429f9b425f427c59a4d2a2ce0f2b376c3bce1726879333d849df944`；30题 manifest SHA-256 `7d8e6569054195d8d68b406b1e51b9d43778b3b9699df4bc8c3672aa049a4435`。
- 源码窗口由公开 base-fail 定位器给出；若模型建议窗口外文件，必须满足现有原 base 生产 `.py`、无路径穿越/测试/symlink、所引 `old` 在文件内**恰出现一次**才允许编辑。候选在原 base 应用、旧 diff 去重、官方 Docker grade 反馈。此措施是自动校验模型路径提议，不是人工定位；但还未经全新任务验证。
- DeepSeek `deepseek-flash` non-thinking/non-streaming、直连 `trust_env=False`、SDK retries=0；每题≤3请求、输出≤1,600、单题≤30,000、全批≤570,000 provider tokens（最多57请求），无自动重试；逐题账本，单题 ambiguous 不重试，累计2题 ambiguous 停整批。预检19/19 ready，每题首轮预留3,219–6,981，镜像/Base-Fail/Gold-Pass/源码身份有效、run目录不存在、Ruff clean。墙钟上限4小时。
- 完成后只能报告该身份19题的真实结果、已记录 token/调用、跨 DEV best-of，不能把拼接成果记作单次30/30或独立效果。E1-B sealed TEST、E2/E3不触碰；任何中断保留账本，未知费用不可算零。
