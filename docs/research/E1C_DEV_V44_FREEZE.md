# E1-C DEV v4.4：自动定位＋受限推理模式小样本

2026-09-24，首次模型调用前冻结。v4.3 对剩余 19 题 57 次 non-thinking 请求新增 0 通过，因此不重复同一提示做大批量付费调用。本轮仅验证 DeepSeek Flash low-effort thinking 是否值得扩展；这是对已看过结果的 DEV 任务选择，不是独立评估。

- 身份 `e1c-dev-v44-thinking-auto2-20260924`；命令 `uv run --frozen python -X utf8 -m evals.e1c_dev_v44 run`；launcher SHA-256 `33ea2c7a068b7f1ae96e77992827c56988909b9c4b9347fbd560ded851b088b1`；locator v1 SHA-256 `b65b5afb0dddee0b9176476b4780a0d89d118d2449598618d8c0fa7cc168653c`；30 题 manifest SHA-256 `7d8e6569054195d8d68b406b1e51b9d43778b3b9699df4bc8c3672aa049a4435`。
- 只选两条未解且已有公开 grade 失败的任务：`django__django-16502`、`django__django-12754`（原 manifest 顺序）。任务 ID 仅决定样本，不决定源码文件。两题均由任务无关公开失败定位器自动产生窗口，origin 为 `unique_failing_test_stem`。不引用 gold patch 或人工指定路径。
- DeepSeek `deepseek-flash`、`thinking=enabled`、`reasoning_effort=low`；每题恰至多 1 请求、输出≤6,000 tokens、单题≤20,000、整批≤40,000 provider tokens；SDK retries=0，直连 `trust_env=False`；任何 ambiguous 停整批、不得自动重试。零调用预检 2/2 ready，首轮 reserve 8,550 与 9,276，镜像 digest、Base-Fail 与 Gold-Pass 不变；Ruff clean。
- 只有至少一个新 official resolved，才考虑把同一机制扩展至更多公开 DEV；否则停止该方向，改进证据/交互策略。即使两题都通过，也不能宣称 30/30 或独立泛化。E1-B sealed TEST 与未来新任务集不触碰。

## 封存结果

2/2 任务行完成、2 次 started/completed 成对、15,256 已记录 provider tokens、0 次有效补丁 / 0 次官方 grade / 0 新 resolved；两题输出都恰触及 6,000-token 上限，`response.step1.txt` 为空，解析结果为 `rejected`。这不是网络异常或模型修复失败的有效补丁比较，而是低推理模式在此上限下没有给出可用 final answer。按预设停止条件，不扩大相同机制的付费批次。跨 DEV 身份 best-of 仍为 11/30；旧运行与账本未覆写。
