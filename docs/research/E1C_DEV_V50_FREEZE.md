# E1-C DEV v5.0：公开新增测试证据 canary（调用前冻结）

2026-09-24。本轮仅使用已反复调参的公开30题，属于 outcome-selected DEV；不读 gold patch，不开启 E1-B sealed TEST，也不构成独立/一次性修复率。前轮 v4.3 在19题57请求0新增、v4.7 在3题6请求0新增，因此不重复同一提示：新增机制只把 `test.patch` 中公开测试文件的 `+` 行（长度有界）作为行为证据，仍用任务无关的公开失败→源码窗口定位，绝无人工任务→文件映射。参考 Agentless 的层级定位/候选验证及 SWE-agent 的受控源码查看，但未宣称复现其结果。

- 身份：`e1c-dev-v50-public-test-additions3-20260924`；精确命令：`uv run --frozen python -X utf8 -m evals.e1c_dev_v50 run`。
- 30题 manifest SHA-256：`7d8e6569054195d8d68b406b1e51b9d43778b3b9699df4bc8c3672aa049a4435`；launcher SHA-256：`a1bf3ba933c2dcc84ccedc3ac1c81c6802db34a75bb14bef79647e7df8116a5d`；test-evidence SHA-256：`6e7bab64f4a9c17dd6f1686b867c4fa1bcb55425bf85d7184d93d2ad84c778f8`。
- 固定选择：v4.3 未解决任务中，按公开新增测试行包含 `assert` 的条数降序、任务 ID 升序取前三：`django__django-15957`、`django__django-12754`、`sphinx-doc__sphinx-9230`。不按人工想改的文件挑选。原 base 窗口分别由定位器给出。三题 Base-Fail、Gold-Pass、镜像 digest、prompt reserve、运行目录缺席均通过零调用预检。
- DeepSeek `deepseek-flash` non-thinking、直连 `trust_env=False`、SDK retries=0；每题最多2请求/20,000 provider tokens，输出上限1,600，整批最多6请求/60,000 provider tokens。按原 base 精确编辑并运行官方 Docker grade；ambiguous 调用不自动重试，遇到一个即停。已知失败可继续同题第二候选，但不无限续跑。只有出现新的官方 resolved 才考虑扩展这一机制；否则停止同类付费尝试。即使出现通过，也必须另行冻结同一版本完整30题运行，不能把跨版本 best-of 算作30/30。
- 零调用检查：`tests/test_e1c_public_test_evidence.py` 2 passed；Ruff clean。运行结果、账本和任何中断状态保留在独立 run 目录。

## 封存结果

3/3任务行完成、6次 completed provider calls、20,180已记录 provider tokens、0 ambiguous、**0新 official resolved**。`django__django-15957` 两次候选均因 `old` 原 base 文本不精确而被拒，0 grade；`django__django-12754` 两次官方 grade 均 F2P0/1、P2P103/112，回归受损；`sphinx-doc__sphinx-9230` 第一次尝试未暴露路径 `sphinx/util/docfields.py`、第二次重复历史失败 patch，0新 grade。公开新增断言没有弥补当前定位/精确编辑缺口，按预定规则不扩批此机制。跨 DEV best-of 仍13/30，未开展同版完整30题，也未选择独立新批次。账本、payload、响应及官方 grade 在 `.codex/e1c/e1c-dev-v50-public-test-additions3-20260924/`；镜像与原 base identity 由预检/grade 维持。
