# E1-C DEV v3.6：12754 近失回归单次修复

2026-09-24，付费调用前冻结。v3.5 三题 canary 第一题3次精确编辑拒绝；第二题2次 completed 请求后，runner 因第3次预算预留不足而在请求前 fail-closed，状态 `interrupted_no_auto_retry`；第3题没有请求。第二题 `django__django-12754` 的 step2 官方 grade F2P1/1、P2P98/112，构成可反馈的公开近失候选；原身份和日志保持不变。

- 新身份 `e1c-dev-v36-12754-regression1-20260924`；入口 `uv run --frozen python -X utf8 -m evals.e1c_dev_v36 run`；launcher SHA-256 `e5955686a3e4ca957aabcccdd6ae3f869e26034918d64b73b9494d3db0891de8`；复用 v3.3 engine SHA-256 `6f42b80c7429f9b425f427c59a4d2a2ce0f2b376c3bce1726879333d849df944` 和 v3.5 定位模块 SHA-256 `561c148bffb0410feb2a9a4d1760215a89d7559592620761146384d1a0cf55fa`；manifest SHA-256 `7d8e6569054195d8d68b406b1e51b9d43778b3b9699df4bc8c3672aa049a4435`。
- 只处理 `django__django-12754`。输入公开题面、base失败、base源码、前一候选 diff（SHA-256 `9de741453f155ae6af919c06f1da7578cb5f3e4f013afed2f04fe8b20cb8ed96`）与前三段公开回归失败。模型须从原 base 生成新候选；同 diff hash 在 Docker 前拒绝。不能读 gold patch/ sealed TEST。
- `deepseek-flash` non-thinking、non-streaming、直连客户端、SDK retries=0；最多1请求，输出≤2,000，任务与批次≤12,000 provider tokens。零调用预检 ready，预留9,553/12,000，Ruff clean，run目录不存在。若无净新 resolved，不继续对此题相同提示付费重抽。仅是 outcome-selected DEV。
