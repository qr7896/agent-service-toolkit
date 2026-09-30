# E1-C DEV v2：付费重跑前冻结说明

日期：2026-09-24。状态：**ZERO-CALL READY；待精确命令授权**。

本轮使用已见过 E1-C v1 结果的同一 30 题，因此是 **post-outcome development rerun**，不替代、不合并原封存的 E1-C `1/30`，也不能充作 E2 的独立有效性验证。Formal E1 `0/30` 和 E1-B sealed TEST 均保持不变。任务题面与冻结 base checkout 可用于证据定位；test patch、gold patch 和 grader 内容不进入模型 prompt 或调参语境。

## 冻结身份与干预

- Cohort manifest SHA-256：`7d8e6569054195d8d68b406b1e51b9d43778b3b9699df4bc8c3672aa049a4435`，固定顺序 30/30。
- 新 run id：`e1c-dev-v2-n30-7d8e6569`；独立目录 `.codex/e1c/e1c-dev-v2-n30-7d8e6569/`，不覆盖 v1 artifacts。
- Runner `evals/e1c_dev_v2.py` SHA-256：`9317c1827ac72287d44fae4aeea636b54f6be7cbe892485006129dc5d1743b45`。
- Evidence `evals/e1c_evidence_v2.py` SHA-256：`b6c7804a76fc62a760afaa315768f41f816722183814e1e07d94da1557e22944`。
- 模型：当前 DeepSeek `deepseek-flash`；temperature 0.5、thinking off、SDK retry 0。每题最多 2 次请求 / 4,000 provider tokens；总上限 60 次 / 120,000 tokens；首轮最多 600 输出 tokens，第二轮最多 400。无失败请求自动重试、无额外预算。
- 改动仅限：公开题面中源码路径/符号锚定的窗口；首轮无效空编辑不运行未修改代码的官方 Docker grader，改用剩余一次请求补充同源窗口；普通验证失败也可用第二次请求获得有限反馈。仍仅允许写已展示的非测试路径，exact-old-match、源身份检查与官方 grader 不放宽。

## 零调用准入与评估边界

最终零调用准入 `30/30 ready`，最大首轮 reserve `3,944/4,000`、第二轮 reserve `3,920/4,000`；新目录尚不存在，provider calls `0`。新旧定位示例可见本轮本地回归；定位改善不是修复率结果。全项目非模型回归 `647 passed / 4 skipped / 33 warnings`，新代码 Ruff 通过。

付费执行只允许在用户明确授权精确命令后运行：

```powershell
uv run --frozen python -X utf8 -m evals.e1c_dev_v2 run
```

完成后用 `uv run --frozen python -X utf8 -m evals.e1c_dev_v2_audit` 对账，报告 30 题配对描述性差值、首轮/最终 resolved、no-op、有效 patch、F2P/P2P、费用、基础设施与安全事件。若结果差，不删题、不重试失败请求、不无限重复同 30 题；需另建版本、明确成本及新的精确授权。E2 的预冻结运行可靠性门槛此前已经 PASS，但 E2 main 仍须独立 amendment、100-task cohort、零调用 dry-run 和单独付费授权；本开发集重跑不能替代这些门槛，也不能保证“完全变好”。
