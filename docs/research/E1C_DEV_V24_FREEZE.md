# E1-C DEV v2.4：两题低推理强度 canary

日期：2026-09-24。状态：**付费调用前冻结**。

v2.3 的五题定位→源码→补丁 canary 完成 5/5、10 completed calls、15,725 tokens、0/5 新增 resolved；每题首轮都选择 inspect，第二轮均形成有效候选补丁，但未通过完整官方检查。此结果提示瓶颈已从“空编辑”移到行为语义/回归保护，不支持直接把 v2.3 扩展到剩余 25 题。

- 新身份 `e1c-dev-v24-thinking2-20260924`，只取 v2.3 中 `sympy__sympy-13798`（目标检查仍失败，P2P 102/102）与 `django__django-16100`（目标检查1/1通过，P2P 58/59），代表两种失败；属于 outcome-selected DEV，禁止外推或称独立验证。
- Runner `evals/e1c_dev_v24.py` SHA-256=`30729c211eddf7f8a93c187279d0c190d52776cab97cd928eafc3f815fb49219`；原30题 manifest SHA-256=`7d8e6569054195d8d68b406b1e51b9d43778b3b9699df4bc8c3672aa049a4435`。每题从 exact base 建新 worktree，不叠加先前失败 patch。
- 输入仅包括公开题面、已暴露源码窗口、v2.3 模型候选 diff 与官方汇总检查**计数**；不输入 test/gold patch/grade log 文本。DeepSeek `deepseek-flash` 低强度 thinking，单题最多1次请求，最多2 calls；每题硬上限15,000、整批30,000 provider tokens，SDK retries 0。若 provider 状态不确定，立即停止并保留账本。
- 零调用预检2/2 ready；两题预留分别9,011与8,640，均低于15,000；运行目录不存在。Ruff 与定向测试通过。执行入口：`uv run --frozen python -X utf8 -m evals.e1c_dev_v24 run`。
- 只有两题中至少1题产生净新 resolved 且安全/账本正常，才考虑把该机制扩展到其他未解题；否则继续零调用诊断，而不盲目重复付费。30/30 是开发目标，无法以当前证据保证。
