# DEV v2 输入准备与付费前冻结快照

随后已精确授权并执行，真实结果见[DEV v2结果报告](E1C2_PAIR_DEV_V2_RESULTS_2026-10-09.md)。本页保留付费前预检事实，不再是待运行状态。

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent
- Origin Mode: run（本轮零模型工程/输入核验）
- Origin Date: 2026-10-09
- Verification Status: UNVERIFIED（预检与回归核对，尚无新模型效果/独立重跑）
- Version Label: pair_dev_v2_readiness_v1

## 本轮实际交付

已实现[DEV v2统一执行协议](E1C2_PAIR_DEV_V2_PROTOCOL_2026-10-09.md)及`evals/e1c_evaluation_2_pair_dev_v2.py`，原frozen模块/paid/zero结果不修改。

repair响应raw/usage先保存，再在**编译前**正式调用既有精确JSON兼容器；仅去除固定type=json_object元字段，不改模型path/old/new字符串，未知key继续拒绝。保存canonical和removed审计，不等评分后挑兼容路径。

新增通用probe门槛和prompt：不重绑导入名、不通过直接/简单Name别名或setattr/delattr改写导入namespace。真实optional条件由公开issue与生产imports推断的既有blocker提供；构造后的对象参数变化仍允许。只读旧raw静态检查中，Scikit-learn原probe接受，Marshmallow原显式availability guard覆盖被拒绝；**不改原资格/分数，不把静态检查称新模型或新容器成绩**。该检查有限，不保证任意程序的完整语义或状态安全。

复用已经实跑的Flash SDK/budget/AST/严格patch编译/离线执行与显式row/root独立评分器，无新增依赖、没有全局OUT/preflight猴子补丁。全producer seal后才评分；基础设施异常与unresolved分开，full_issue_trusted保持false。

## DEV12输入核验

不下载、不拉容器数据，只从本机已缓存公开issue/base源码重新按同一方法检索：balanced→限定名→bounded globals→生产过滤→canonical SHA重算。公开issue Git blob与声明源码slice核验，cap分别lexical2200/AST连续5000/分段2500；字节身份、元数据、准入摘要绑定SHA。

| frozen DEV12 | 本轮输入准备 | 解释 |
|---|---:|---|
| Scikit-learn 3题 | 3 ready，双准入true | 不是三题模型评测完成 |
| Marshmallow 3题 | 3 ready，双准入true | 不是三个修复成功 |
| Pytest 3题 | 3 ready，双准入true | 新链效果尚未验证 |
| PyVista 3题 | 3 INFRA_BLOCKED | 缺本机source/issue；不下载、不记模型失败 |

固定12行保留，9份输入均通过只读dry核验和正式准备，source view约5.8k–19.3k字符；未突破32k cap。仅表示输入/已有准入材料准备，不是9/12 repair rate。

## 新两题pilot的完整冻结

按原DEV12顺序，排除上一pair v1全部已尝试题（不看成功/失败），每剩余repo第一ready且双准入题，取先两个repo：

| 任务 | 首请求预留（含20k生成） | 新canonical SHA |
|---|---:|---|
| scikit-learn-26289 | 28,098 | `692505cf386c0200627444e4d1e03b1f842e83721a475fe2a3f16637ea52c172` |
| marshmallow-1359 | 27,058 | `1552b4911f91f01ba85fa323b2f1dd8114f36e71b230eca25dc348be24d9a5be` |

二者是其他**旧DEV**，不称未参与调参的新canary。没有人工文件表或按官方patch/outcome排名；不同模型运行/不同题的结果不可拼成同版最佳率。

新身份`e1c2-pair-dev-v2`已preflight freeze，SHA `97085159edbd37abb6823800a66b8eff10bfb1baa5c48e6f37f1d0fafb9762ba`；首请求SHA、输入物理SHA/源码、codec、方法/协议、budget均绑定。Docker与两张不可变镜像只读健康检查通过。冻结当时started/ledger均不存在、provider_calls=0；现在已经授权执行，不按本快照重跑。

当时冻结的精确命令（现在已授权完成，禁止重跑）：

```powershell
Set-Location 'D:\codex\working\project20260827'
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_pair_dev_v2 run
```

全部Flash enabled/high，单批最多4calls/100,000 provider tokens含推理，每题2calls/50k；生成按余量16k–20k，HTTP300、retry0。预算不足/拒绝/弃答按固定两题记录，infra停整批；不自动扩展九题、重试或换身份继续消费预算。若以后扩完整九准入，必须先披露并冻结**全cohort总预算**，不能藏在多个100k子批。

## 工程与后续

10新增专项覆盖实际调用解码→原代码字符串→编译→配对/自验证→全seal→评分、4call/分题与共享cap、防重跑/预算floor、真实12行准备及准入摘要变更拒绝、lexical截断、namespace负例/对象正例。Mock模型与假密钥，无真实provider。预算/V3重点29及Ruff通过；全回归/XML见[后续真实结果收据](../../data/e1c_evaluation_2_pair_dev_v2_results.json)。

先执行上述两题新pilot、按同版结果检查定位与公开义务缺证，再完整DEV12/九准入质量验收和总成本freeze；可信门槛实际通过才全历史排除的新canary一次≥2/3、独立repair/旧DEV对照，最后另授权Fresh30/E2。**原最近实验1/2、后验另1/1不变；E1-C evaluation_2未收官，不保证30/30或完美。**

WebCodex可跑本版源码单测，缺本机私有source/镜像/评分材料报INFRA_BLOCKED；本轮未扩tunnel白名单，也未验证新远程live入口。本轮零下载/删除/Docker重启或IPC/VHD/registry/proxy/tunnel/key配置变化，旧readiness/收据/负结果保全；日志只集中归档。
