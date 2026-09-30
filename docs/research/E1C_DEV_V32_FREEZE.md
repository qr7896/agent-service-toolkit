# E1-C DEV v3.2：TLS 建连中断后的新身份

日期：2026-09-24，付费调用前冻结。v3.1 `e1c-dev-v31-agentic23-20260924` 在第一题第一请求的 TLS `start_tls` 阶段抛 `APIConnectionError`，provider ledger 为1条 started→ambiguous、0 completed，state rows=0。不能确认是否计费，旧身份永不重试或改写。随后无凭据 HTTPS GET `https://api.deepseek.com` 返回401，说明当前网络可达，不证明计费情况。

- 新身份 `e1c-dev-v32-agentic23-20260924`，入口 `uv run --frozen python -X utf8 -m evals.e1c_dev_v32 run`。轻量 launcher SHA-256=`89e17f270bff767551d95fec08a13650b6ac8c417028e62795986eec79d4140a`，复用的 v3.1 runner SHA-256=`d794f3398f87e3ecf18d33ab867a1eded54c49d2065d01050f0b5161f714ad9a`。两者共同构成执行身份；旧 v3.1 代码/账本保持原样。
- cohort、动作、公开 DEV 证据、官方 Docker grader 和预算与 `E1C_DEV_V31_FREEZE.md` 完全相同：23未解题、每题≤5请求、每次输出≤1,800、单题36,000、整批828,000 provider tokens，SDK retries=0；不能把 v3.1 ambiguous 用量视作0费用。
- 新身份零调用预检23/23 ready、run 目录不存在，Ruff clean。任一再次不确定请求仍立即停、记账；不静默重试。所有结果仍属 post-outcome DEV。
