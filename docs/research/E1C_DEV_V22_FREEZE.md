# E1-C DEV v2.2：首轮空编辑子集诊断冻结

日期：2026-09-24。状态：**FROZEN BEFORE V2.2 PROVIDER CALLS**。

v2.1 已经完整审计：同一 30 题 `4/30` resolved、57 calls、90,621 tokens、首轮空编辑 18/30、critical safety 0、infrastructure failure 0。原封存 E1-C 为 `1/30`。v2.2 只对 v2.1 的**首轮空编辑 18 题**做 outcome-selected DEV 诊断，以少于完整 30 题的成本检查公开题面定位改动；不能把 18 题结果外推为整体修复率，也不能充作 E2 的独立证据。test/gold/grader 内容不进入 prompt 或调参。

- Cohort：固定原 30 题顺序，选择 `first_grade.schema == e1c-dev-v21-noop` 的 18 条；selection SHA-256（紧凑 JSON ID 列表）=`812ee4bd4d9f679e2864f4e2d0a7f71b70573b5e9682386373cd4f7f1e37ac58`。Runner 在零调用准入时验证该选择与 v2.1 状态完全一致。
- Run ID：`e1c-dev-v22-noop18-812ee4bd`；独立目录 `.codex/e1c/e1c-dev-v22-noop18-812ee4bd/`。不覆盖 v2/v2.1/原 E1-C。
- Runner `evals/e1c_dev_v22.py` SHA-256=`31877d99bdc1ce532f6e4a21fa712255e43964052c2b18cd0cf328dbfd3af1dc`；evidence `evals/e1c_evidence_v22.py` SHA-256=`2ca80d658e1ddcb1c52a07f768fb0c2a0eaaca320ccd6b8a3f70a28ff6a2967e`；audit `evals/e1c_dev_v22_audit.py` SHA-256=`81c6a971e7662dd0ef45987717636eaa4c4c32b9a5ab89cf42ad86a8b0e3aafd`。
- 干预：仅把公开题面首段的 `Class.method` / `snake_case` 当成强定位锚点，并将首个源码窗口上限从 1,200 字符改为 1,800，其他窗口最多 700 字符。原 exact-edit 写入白名单、禁止测试文件、官方 Docker grader、源身份检查、两次调用上限均保持。
- DeepSeek `deepseek-flash`，thinking off、SDK retry 0；18 题最多 36 次请求。单题软/硬 6,000/8,000，整批软/硬 90,000/126,000 provider tokens；按照首轮实际用量拟合第二轮，无 provider 失败自动重试。
- 零调用准入 18/18 ready，最大 first/second reserve=`3,994/3,910`；provider calls=0。新证据/runner定向 4 passed、Ruff clean；完整非模型回归 656 passed / 4 skipped / 33 warnings。运行目录尚不存在。

执行入口：`uv run --frozen python -X utf8 -m evals.e1c_dev_v22 run`。结束后用 `uv run --frozen python -X utf8 -m evals.e1c_dev_v22_audit` 对账，并与 v2.1 **同 18 条**的首轮空编辑数、最终 resolved、calls/tokens 做配对描述性比较。只看汇总与公开题面/源码，不依据官方测试细节再调机制。若改善有限，停止继续按同 30 题刷分，转向独立 E2 入口工作；任何 E2 main 仍须独立 cohort、预注册、零调用 gate 和单独身份。
