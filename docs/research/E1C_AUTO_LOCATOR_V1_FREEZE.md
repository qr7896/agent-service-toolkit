# E1-C 自动定位 v1：公开失败日志→源码窗口

2026-09-24，第一轮模型 canary 前冻结。代码 `evals/e1c_failure_guided_evidence.py` SHA-256 `b65b5afb0dddee0b9176476b4780a0d89d118d2449598618d8c0fa7cc168653c`。输入仅公开 issue、base-fail 日志和原 base 源码；没有任务 ID→人工路径表，没有读取 gold patch 或 sealed TEST。

规则：公开 traceback 的生产源码帧最高优先；题面明确生产文件次之；失败测试 `test_<stem>.py` 与唯一生产 `<stem>.py` 对应再其次。`tests.py`、`setup.py` 等排除。对高置信文件按函数名与题面/失败词重叠选完整函数窗口；大函数改选得分最高的45行窗口，避免从函数头硬截断。无高置信文件时用既有词法检索回退，并显式标 `lexical_fallback`。

零模型审计：现有30条 DEV **30/30有窗口**，其中**16/30有高置信路径**、14/30为词法回退；这是 evidence coverage，不是路径命中真值，更不是修复率。`django__django-11740` 自动窗口含此前截断的真实 `field=field` 调用。新增3个纯本地单元测试通过，Ruff clean。下一步以冻结 v3.9 的5个按顺序选定的高置信未解 DEV 任务检查净新 resolved；若无收益，不直接扩到20题。
