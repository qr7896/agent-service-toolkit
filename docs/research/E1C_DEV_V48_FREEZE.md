# E1-C DEV v4.8：公开 NameError 的零模型标准库导入修复

2026-09-24，官方 Docker grade 前冻结。v4.7 的三题6次 DeepSeek Flash 请求已完成，0新 resolved；其中一条模型候选保留全部回归且通过部分目标检查，公开失败明确为候选新引入的标准库模块名未导入。本轮只作任务无关的机械修复，不再调用模型，不读 gold patch，不人工指定任务/文件。

- 身份 `e1c-dev-v48-public-nameerror-import-20260924`；入口 `uv run --frozen python -X utf8 -m evals.e1c_dev_missing_import run`；launcher SHA-256 `6698488ea73fa3e280f71e8d10708024ce50cf928e16b7f14e8130a4c0917369`；30题 manifest SHA-256 `7d8e6569054195d8d68b406b1e51b9d43778b3b9699df4bc8c3672aa049a4435`。
- 固定选择规则：v4.7 已官方 grade、未 resolved、F2P有通过；公开 grade traceback 有标准库模块 `NameError`，安全生产路径明确，且上一模型 patch 的新增行确实使用该模块的点访问。全批唯一符合者是 `django__django-13512`、step2、`json`、`django/contrib/admin/utils.py`；父 patch SHA-256 `62e2c7321460842577f5dc28539105e7de4c1b2bffa73b2bd3a358eaebe5d1a3`。这仍是 outcome-selected DEV，不是泛化证据。
- 在原 base 单独 worktree 应用父 patch，AST 验证缺少 import，在模块 docstring / future import 后插入 `import json`，再生成完整候选 diff 并交同一官方 Docker grader。无模糊文本替换、无自动重试、0 provider calls；只允许这一次 grade。零调用预检 ready=true，父 patch/镜像/Base-Fail/Gold-Pass 身份有效；定向测试和 Ruff clean。无论结果如何，不回填 v4.7 账本或把 best-of 当单次30题运行。

## 封存结果

官方 Docker grade：F2P3/3、P2P32/32、resolved=true、source identity valid；新完整 patch SHA-256 `ae0927ae7d640dfb6ea2a2c231631bf826615a2d75c553e3c2cbcbc3450a7c37`，0 provider calls。该题是跨身份新增加的 DEV 解，不能覆盖 v4.7 未通过的记录。
