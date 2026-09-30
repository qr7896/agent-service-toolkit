# E1-C DEV v3.3：确定性定位、只编辑、逐题独立账本

日期：2026-09-24，付费调用前冻结。v3.1 第一题 TLS 建连失败，1条 started→ambiguous、0 completed；v3.2 完成9/23行、46 completed calls/67,180已记录 tokens、0新 resolved，后在第10题 TLS 建连失败并保留第二条 ambiguous。前9题多数重复 `search`，0次官方 grade。两个旧身份都不重试或改写；ambiguous 可能另行计费，未知。

- 新身份 `e1c-dev-v33-localize23-20260924`，入口 `uv run --frozen python -X utf8 -m evals.e1c_dev_v33 run`，runner SHA-256=`6f42b80c7429f9b425f427c59a4d2a2ce0f2b376c3bce1726879333d849df944`，cohort manifest SHA-256=`7d8e6569054195d8d68b406b1e51b9d43778b3b9699df4bc8c3672aa049a4435`。固定23条历史未解 DEV 任务，旧best-of 7/30不变。
- 源码定位由本地确定性 evidence 完成，前三个短窗口直接供模型使用；模型**只能**输出 exact `edits`，不再反复要求搜索。无编辑时下一轮补一个源码窗口。不同补丁从原 base 应用，经已准入官方 Docker grader 检查，公开失败断言反馈给后续轮次；与既有 DEV 或本轮相同 diff hash 在 Docker 前拒绝。公开题面/源码/测试输出都属 DEV，绝不读 gold patch 或 E1-B sealed TEST。
- DeepSeek `deepseek-flash` non-thinking、non-streaming、SDK retries=0。每题最多3次请求、输出上限1,600、单题20,000 provider tokens，23题上界460,000 tokens/69请求。每题独立 run-id 和 ledger；若某题 API 连接不确定，只标该题 `ambiguous_no_retry`，不重试，继续其他题；若累计2题不确定，为防网络性浪费而停止批次。不能把未知计费视为0。
- 零调用预检23/23 ready、目录不存在；Ruff clean；Python httpx 无凭据 GET DeepSeek 根地址返回401。预计可能超过30分钟，批次墙钟上限4小时；监控 state 与逐题 ledger。任何结果只能算 outcome-selected E1-C DEV，不能写成单次 n30 修复率或 E2 证据。
