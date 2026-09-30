# E1-C DEV v2.3：五题定位→源码→补丁 canary

日期：2026-09-24。状态：**付费调用前冻结**。

E1-C 固定 30 题现由用户明确改作开发测试集；任何反复优化后的分数只能标为 post-outcome DEV / best-of，不作为独立修复率、E2 或 E3 证据。30/30 是优化目标，不是保证可达到的停止承诺；不得读取 sealed TEST，也不把官方 test/gold patch 内容送入模型或据此改策略。

- 身份：`e1c-dev-v23-locator5-20260924`；原 30 题 manifest SHA-256=`7d8e6569054195d8d68b406b1e51b9d43778b3b9699df4bc8c3672aa049a4435`。从 v2.1 完成行与 v2.2 已完成行的 resolved 合集排除已解题，再按原 manifest 顺序取前五：`sympy__sympy-13798`、`sympy__sympy-17318`、`django__django-16100`、`sympy__sympy-18211`、`sphinx-doc__sphinx-9230`。这是 outcome-selected canary，不作整体率外推。
- Runner `evals/e1c_dev_v23.py` SHA-256=`cd803b6eeb94ee53ddb09b136ddc2bdcece3dd7b2a3168d4cddf0f60eee3d5e2`；复用 v2.2 evidence SHA-256=`2ca80d658e1ddcb1c52a07f768fb0c2a0eaaca320ccd6b8a3f70a28ff6a2967e` 与 v2 evidence SHA-256=`b6c7804a76fc62a760afaa315768f41f816722183814e1e07d94da1557e22944`，不更改既有 runner/artifacts。
- 干预：首轮并列呈现两个候选源码窗口和最多 12 个候选路径。模型可直接给 exact edits，也可在白名单内请求一次 `inspect(path,symbol)`；后者从 base source 定位函数/类并供第二轮补丁使用。首轮空编辑时只有存在新源码证据才继续调用。官方 Docker grader 与 exact-edit guard 保持；不输入 test/gold 内容。
- DeepSeek `deepseek-flash`、thinking off、SDK retries 0；最多 5 题×2 calls=10 calls；每题硬上限 12,000 provider tokens，整批硬上限 60,000，实际用量以独立账本为准。任何 provider ambiguous 均中止，不自动重试。源码/镜像 admission 每题核对。
- 判定：canary 至少产生 1 个此前未解题的 resolved、0 关键安全违规且账本完整，才考虑在新身份下扩展到其余未解题；若无净增益先做零调用诊断，不直接花费下一批。任何后续完整 30 题 best-of 都必须逐题列明来源身份与覆盖，不可包装为一次性盲测。

零调用预检：5/5 ready、每题首轮 2 个源码窗口、最大 first reserve 3,100，provider calls=0，运行目录不存在。执行入口：`uv run --frozen python -X utf8 -m evals.e1c_dev_v23 run`。
