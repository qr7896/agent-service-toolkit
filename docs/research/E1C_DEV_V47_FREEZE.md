# E1-C DEV v4.7：公开失败测试 import→生产定义定位小样本

2026-09-24，首次付费请求前冻结。v4.6 受控 ACI 三题9次请求未新增通过，未扩大同类流程。本轮新证据机制只用公开 Base-Fail/FAIL_TO_PASS 的测试文件与静态 Python import/定义，一跳追踪包 `__init__.py` re-export；不执行测试代码、不读 gold patch、不设任务 ID→手工文件表。原 v1 定位器保持不变，新建 v2 身份。

- 身份 `e1c-dev-v47-public-import3-20260924`；命令 `uv run --frozen python -X utf8 -m evals.e1c_dev_v47 run`；launcher SHA-256 `3e6f2bd492a5271d0316cbab62fde1c39fc0990b4c0847961b21881e722dcffc`；locator v2 SHA-256 `76053ad51cfbf06b4b800e5b434571f74c642fecdd9d0a0cf3ba023cabe2f073`；30题 manifest SHA-256 `7d8e6569054195d8d68b406b1e51b9d43778b3b9699df4bc8c3672aa049a4435`。
- 零调用离线审计：v1 明确路径16/30；v2 在同30题额外给4题提供静态测试 import 路径，合计20/30，其余10题保留词法回退。它只是候选路径覆盖，**不是定位准确率**。v2 对泛泛的 `QuerySet` 题面提及不自动认定高置信，避免无差别拓展。新增3个 synthetic 规则测试通过，Ruff clean。
- 固定样本为 v4.3 尚未解决、v1 无明确路径而 v2 静态 import 有路径的全部3题：`sphinx-doc__sphinx-8056`、`django__django-13512`、`django__django-15280`。其原 base 窗口分别为 `sphinx/ext/napoleon/docstring.py`，`django/forms/fields.py` + `django/contrib/admin/utils.py`，`django/db/models/query.py`。这仍是读过旧结果后的重复 DEV，不是独立样本。v2 不附加不相关词法窗口。
- DeepSeek `deepseek-flash` non-thinking、直连 `trust_env=False`、SDK retries=0；每题≤2请求、输出≤1,600、单题≤18,000、整批≤54,000 provider tokens。按原 base 编辑/官方 Docker grade，单题 ambiguous 不重试，整批遇 ambiguous 即停；墙钟上限30分钟。零调用准入3/3，首轮 reserve 4,915/5,311/5,507，原镜像 digest/Base-Fail/Gold-Pass 有效。只有出现新 official resolved 才考虑扩大 v2；否则停止同类付费抽样。跨版本 best-of 不得算一次运行。

## 封存结果

3/3任务行完成、6次 started/completed 成对、15,457已记录 provider tokens、0 ambiguous、0新 resolved。`sphinx-doc__sphinx-8056` 为 rejected/no_edits；`django__django-13512` 两次官方 grade 均 F2P1/3、P2P32/32，公开失败为候选新用 `json.dumps` 而模块缺 `import json`；`django__django-15280` 一次 grade F2P0/1、P2P85/85，后续编辑被拒。v2 自动定位本身没有直接通过新题，不能据此扩大相同付费提示；上述 NameError 另用 v4.8 零模型机械规则独立验证。
