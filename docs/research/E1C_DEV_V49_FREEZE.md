# E1-C DEV v4.9：历史候选缺失标准库导入的零模型批诊断

2026-09-24，官方 Docker grade 前冻结。v4.8 对公开 NameError 做的单题通用机械修复官方 F2P3/3、P2P32/32、resolved=true，0模型调用。现在同一规则只筛查 v4.3 封存候选，不重新抽模型；任何新结果仍是 post-outcome DEV。

- 身份 `e1c-dev-v49-public-nameerror-batch-20260924`；命令 `uv run --frozen python -X utf8 -m evals.e1c_dev_missing_import_batch run`；launcher SHA-256 `49a99cfbc6b59dcc49e13fbab936619fa32fd701f58e5eeb9448402f88e06db5`；30题 manifest SHA-256 `7d8e6569054195d8d68b406b1e51b9d43778b3b9699df4bc8c3672aa049a4435`。
- 零调用预检按封存 v4.3 公开 grade 的标准库 NameError、生产 traceback 安全路径、父 patch 新增的模块点访问共同筛出且仅筛出两条：`django__django-15731` step2 缺 `functools`，父 patch SHA `7cbdc908f7c18dab67cffd79d1a42a69253b31c15bdf21e1e133509a80d0c1ae`；`astropy__astropy-7671` step3 缺 `re`，父 patch SHA `aa96cd398554f745f13fa165a064191a0969ab86792fcecf95f852289ff7d9dd`。两条源提交/镜像 digest/Base-Fail/Gold-Pass 有效；run 目录不存在；Ruff clean。
- 每题原 base 工作树应用原模型候选、AST 插入单个标准库 import、生成新 diff 后只运行一次官方 grade；任何异常中断、不自动重试，结果独立落盘，不覆写 v4.3/v4.8。0 provider calls。此前两题 F2P/P2P 均失败，此操作只针对可观测的基础设施式代码错误，不保证语义修复。

## 封存结果

2/2官方 grade 完成、0 provider calls。`django__django-15731` F2P1/1、P2P58/58、resolved=true，新 patch SHA-256 `a1dacd1a18e423648c391fd1452abd23276c81b58c91f7c6a4cc2379ed561d76`；`astropy__astropy-7671` F2P0/1、P2P3/3、resolved=false，新 patch SHA-256 `7bbc1783e81e037e96090cedef520f6393c944ce5cab40cd7bbdf0856878113d`。只前者计作新增 DEV 解，后者证明去掉 NameError 后仍有语义缺口。
