# E1-C DEV v2.1：零调用预算修复与运行身份

日期：2026-09-24。状态：**FROZEN BEFORE V2.1 PROVIDER CALLS**。

用户已明确同意在零调用修复后直接继续付费开发集实验，并允许单题与整批使用弹性上限，不再要求逐命令确认。本次仅修复 DEV v2 首题第二轮前暴露的**累计预留**缺陷；旧 v2 中断身份、1 次调用/1,171 tokens 与原 E1-C `1/30` 结果均保留、不覆盖、不混合。仍是相同 30 题的 post-outcome DEV，不是独立确认或 E2 结果。

## 冻结对象

- Cohort manifest SHA-256：`7d8e6569054195d8d68b406b1e51b9d43778b3b9699df4bc8c3672aa049a4435`；任务顺序与官方镜像准入不变。
- Runner：`evals/e1c_dev_v21.py`，SHA-256 `02fcaeb7acfdbb0c9c9b1805c45728c45540ee5ffa4640c0bcd4534389465552`。
- Evidence：`evals/e1c_evidence_v2.py`，SHA-256 `b6c7804a76fc62a760afaa315768f41f816722183814e1e07d94da1557e22944`；题面路径/符号定位不变。
- Audit：`evals/e1c_dev_v21_audit.py`，SHA-256 `fedfc0758bdfe0b4a32ad0d1e3853428c66bce5c9ef80a19cebc3ed2b99e33f3`。
- Run ID：`e1c-dev-v21-n30-7d8e6569`，新目录 `.codex/e1c/e1c-dev-v21-n30-7d8e6569/`。
- DeepSeek `deepseek-flash`，thinking off，SDK retries=0；每题最多 2 次调用，总最多 60 次。单题软上限 6,000、硬上限 8,000；整批软上限 180,000、硬上限 210,000 provider tokens。第二轮按首轮**实际**用量计算余量，先尝试软限，放不下才使用硬限余量；仍不增加调用次数或强制用满额度。任何 provider 失败不自动重试。
- 模型可见范围仍只有公开题面与允许的 bounded source excerpts；test/gold/grader 不入 prompt。exact-old-match、路径白名单、官方 Docker grader 与源身份检查不放宽。

## 零调用验证与停止

30/30 preflight ready；首轮最大 reserve 3,944，第二轮在 2,000-token 首轮用量代理下最大 reserve 3,920。将旧 v2 首题的真实首轮用量 1,171 与第二轮 reserve 3,106 代入新规则，累计 4,277 ≤软上限 6,000；这只是预算回放，不是修复结果。新代码定向测试 3 passed、完整非模型回归 652 passed / 4 skipped / 33 warnings，Ruff 通过；运行目录不存在，provider calls=0。

执行入口：`uv run --frozen python -X utf8 -m evals.e1c_dev_v21 run`。运行完执行 `uv run --frozen python -X utf8 -m evals.e1c_dev_v21_audit`，保留所有任务和失败，报告原 E1-C、v2 中断和 v2.1 开发集结果的不同身份。若出现 provider/预算/容器中断，不修改此身份、不静默重试；先审计再决定是否另建版本。E2 main 仍须独立 cohort、预注册和零调用 gate，不能因重复 30 题分数上升直接声称有效。
