# E1-C DEV v4.6：受控交互式源码检索小样本

2026-09-24，首次模型调用前冻结。现有任务无关定位器覆盖 30/30 源码窗口，但 v4.3–v4.5 没有净新修复。本轮复用 v3.1 搜索/查看/精确编辑、Docker 官方验证与 provider ledger，只新增任务无关证据反馈：`search` 后自动给出一个安全匹配文件的原 base 短窗口；被拒的 `edits` 若指向安全生产文件，则自动给出该文件原 base 短窗口。无需研究者选文件，绝不自动模糊编辑。

- 身份 `e1c-dev-v46-bounded-aci3-20260924`；命令 `uv run --frozen python -X utf8 -m evals.e1c_dev_v46 run`。launcher SHA-256 `2810e34d4b187d1cc6a4d82bae6818074157e485d0a927662ff389c3bb79a975`；证据扩展 SHA-256 `fddbee974b480ee8ed6c8696cec266803c292514874e9582ae0948c802328ea2`；原30题 manifest SHA-256 `7d8e6569054195d8d68b406b1e51b9d43778b3b9699df4bc8c3672aa049a4435`。
- 从 v4.3 未解决行按冻结顺序选**首轮编辑被拒、没有官方 grade、当前 locator 只有词法 fallback** 的前三题，排除 v4.5 已试题：`sphinx-doc__sphinx-8056`、`django__django-13512`、`sympy__sympy-15875`。选择规则依据已见开发集结果，故是 outcome-selected DEV，不能作独立效果。
- 原 base 源码窗口来自公开题面与 Base-Fail 日志；安全路径验证排除 test/路径穿越/symlink；单文件读取≤1MB，每窗口≤5,000字符，搜索至多12文件，模型每轮仅看最近3窗口。没有 gold patch 或手选源码。DeepSeek `deepseek-flash` non-thinking、直连 `trust_env=False`、SDK retries=0；每题≤3请求、输出≤1,600、单题≤25,000、整批≤75,000 provider tokens。任何 provider 异常即中断且不自动重试。墙钟上限30分钟。
- 零调用准入3/3 ready；首轮 reserve 4,158/4,533/3,272；镜像 digest、Base-Fail、Gold-Pass 一致；新增 ACI helper 的2个定向测试与 Ruff 通过。仅当有新 official resolved 才考虑扩展该机制至更多开发题；否则停止同类付费抽样。任何跨版本拼接结果不称一次30题运行。

## 封存结果

3/3任务行完成、9次 started/completed 成对、18,433已记录 provider tokens、0 ambiguous、0新 resolved。三题动作分别为 `search,search,grade`（F2P0/1、P2P40/40）、`rejected,search,rejected`、`rejected,search,search`。自动显示源码使一题走到官方 grade，但尚未带来净新修复；按预冻结条件不扩大相同 ACI 流程。该结果与最初窗口覆盖率不混称 repair-rate。
