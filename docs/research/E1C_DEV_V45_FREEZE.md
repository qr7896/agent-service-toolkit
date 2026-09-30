# E1-C DEV v4.5：模型提出安全路径后的原始源码回显

2026-09-24，首次模型调用前冻结。v4.3 的一些候选因路径不在原先窗口或 `old` 文本不精确被拒，后续请求没有看到该文件真实内容。本轮只试这个具体流程修正，不增加人工定位。

- 身份 `e1c-dev-v45-suggested-source2-20260924`；命令 `uv run --frozen python -X utf8 -m evals.e1c_dev_v45 run`；launcher SHA-256 `f92405715699f9254a92a191e267c5523ab00fb9644c506235244fc875dc3f6a`；manifest SHA-256 `7d8e6569054195d8d68b406b1e51b9d43778b3b9699df4bc8c3672aa049a4435`。
- 从 v4.3 首轮 `path was not exposed` 中，排除 v4.0 已跟进任务，按原 base 中可匹配的旧文本行数降序固定前2题：`django__django-15563`（13行）、`sympy__sympy-18211`（9行）。路径由旧模型回复提供，经 safe production path 检查；窗口锚点从原 base 精确匹配行自动选出，没有研究者指定文件或 gold patch。它仍是读过历史失败后的 DEV。
- DeepSeek `deepseek-flash` non-thinking，2题各≤1请求、输出≤1,600，单题≤12,000，整批≤24,000 provider tokens，SDK retries=0，直连 `trust_env=False`；遇 ambiguous 停止、不自动重试。预检2/2 ready，首轮 reserve 5,780/5,313，镜像 digest/Base-Fail/Gold-Pass 一致，Ruff clean；此前完整非模型回归复核为667 passed/4 skipped/33 warnings。
- 只有真实 official resolved 净增才扩大这条路径回显机制；无净增则停止同类付费实验。即便成功也不改变原正式 E1-C、Formal E1 或独立新任务结果。

## 封存结果

2/2 完成、2次 started/completed 成对、4,674 已记录 provider tokens、0新 resolved。`django__django-15563` 为 `no_edits`；`sympy__sympy-18211` 产生一个新的 exact patch，官方 grade F2P0/1、P2P54/54，仍未解决。原路径/窗口拒绝的问题在第二题已转化为可执行 patch，但没有转化为修复成功；按冻结停止条件不扩批。跨 DEV 身份 best-of 仍11/30。
