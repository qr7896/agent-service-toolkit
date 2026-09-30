# E1-C DEV v3.7：未执行 HEAD 任务单题 canary

2026-09-24，付费调用前冻结。v3.5 在第2题第3次请求前因预留不足 fail-closed，第3题 `django__django-16502` 完全未调用；v3.6 用1次请求修复第2题近失未成功（F2P0/1、P2P7/112），不再同质重抽。新身份仅处理原未执行第3题。

- `e1c-dev-v37-head-canary1-20260924`，入口 `uv run --frozen python -X utf8 -m evals.e1c_dev_v37 run`，launcher SHA-256 `2313196a8e81afbbd8f1fbd0a56f8e6f0ef1fd154dd6001931930e1be42b6cd8`；manifest SHA-256 `7d8e6569054195d8d68b406b1e51b9d43778b3b9699df4bc8c3672aa049a4435`。不更改 v3.3/v3.5 引擎；从公开 HEAD 失败测试和原 base 定位 `django/core/servers/basehttp.py`，只读公开题面/base失败/源码，不读 gold。
- `deepseek-flash` non-thinking、non-streaming、直连、SDK retries=0；最多2请求、输出≤1,800、单题≤20,000 tokens，独立 provider ledger，ambiguous 不重试。exact edits 从原 base 应用、重复 diff 在 Docker 前拒绝、官方 grade。
- 零调用预检 ready，首轮预留7,570，Ruff clean，run目录不存在。该题是 human-localized, outcome-selected DEV，不算自动定位或独立有效性证据；若0新 resolved，停止这个证据形式的同质付费试验。
