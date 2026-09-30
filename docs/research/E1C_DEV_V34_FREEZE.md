# E1-C DEV v3.4：直连客户端续攻剩余20题

2026-09-24，付费调用前冻结。v3.3 先完成1题、另1题首轮评分后第二请求 ambiguous、第3题首轮 ambiguous；按两条未决请求阈值停于3/23。旧账本原样保留，未知请求不重试、不视为0费用。Python `httpx` 直连 `trust_env=False` 对 DeepSeek 根地址5/5、聊天端点无凭据 POST 5/5均获预期401；这是网络诊断，不是付费请求成功保证。

- 新身份 `e1c-dev-v34-direct20-20260924`，入口 `uv run --frozen python -X utf8 -m evals.e1c_dev_v34 run`；launcher SHA-256=`bf9d1e289544000d4e149cad21cfa72550dbcf53da919ffd83ad12e449d8e649`，冻结 engine v3.3 SHA-256=`6f42b80c7429f9b425f427c59a4d2a2ce0f2b376c3bce1726879333d849df944`，原 manifest SHA-256=`7d8e6569054195d8d68b406b1e51b9d43778b3b9699df4bc8c3672aa049a4435`。
- 固定跳过 v3.3 已处理或 ambiguous 的3条 SymPy 题；只跑剩余20条历史未解 DEV 任务。模型 `deepseek-flash`、non-thinking、non-streaming、直连 `httpx.AsyncClient(trust_env=False)`、SDK retries=0。沿用确定性本地定位→exact edits→官方 Docker grade→公开失败反馈；每题≤3请求、输出≤1,600、单题20,000，整批隐含上限400,000 provider tokens。逐题账本，某题 ambiguous 不重试，累计2题 ambiguous 停批次。
- 零调用预检20/20 ready、run目录不存在、Ruff clean。墙钟上限4小时，监控 state/账本；只称 post-outcome DEV，不代表一次 n30 独立效果。
