# E1-C evaluation_2：零模型受限资格与反例校准

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent；ponytail
- Origin Mode: run / analysis
- Origin Date: 2026-10-07
- Verification Status: ANALYZED（缓存/源出处/工程核对；非通用语义认证）
- Version Label: bounded-qualification-calibration-v2

## 1. 本轮交付

新增模型调用/tokens **0/0**，Gold读取0，未重跑任何paid实验。上一版Gold4/4与异常对应3/4保持原记录；本次四缓存的受限资格为 **2项mechanism_supported_candidate、2项unknown**，machine trusted仍0，不能叫可信2/4、修复率或新实验成绩。

| 旧DEV参考 | v2资格 | 原因 |
|---|---|---|
| scikit-learn-13496 | 机制支持候选 | 明确请求锚、已暴露production绑定、正常/目标证据、缺keyword异常对应 |
| scikit-learn-26289 | 未知 | 辅助DecisionTreeClassifier依赖源不在原暴露窗口；原报机制未对应 |
| marshmallow-1252 | 未知 | Schema辅助源未在原窗口；公开Foo/DateTime/Schema示例没有import来源，范围仍未证 |
| marshmallow-1359 | 机制支持候选 | 已知公开class/绑定结构保持、production依赖与异常对应 |

“候选”仅受限结构与运行证据组合，不是语义资格认证。已知约束库存也不是所有公共约束。

## 2. 检查与校准

- 复用assertion-free fixture facts与production resolver，检查已知binding/class结构、import alias、源码SHA、精确期待锚、observer的原probe身份、正常控制/重复目标失败。bool与int严格区分，不将True和1当同一公开值。
- 拒绝公共值/shape结构改写、import影射、直接生产import对象改写、动态能力；实例/容器修改、自定义行为/控制流、缺失约束、遗漏公开import范围均unknown，不作普遍否决或证书。
- 17项单测涵盖同异常wrong fixture、影射/对象改写、动态能力、另一probe观察、真实源变化、缺失条件、未知状态修改、bool/int、缺public import、增量赋值/删除、嵌套恢复等。
- 四原缓存各做一个内存alias-shadow反例，均被拒。它们是静态信息包，不是四个新运行时故障，也不是独立任务成绩；旧输入/源码/响应/观察/预算/seal未改。

v1将未暴露辅助依赖与真实源码不匹配混同，四缓存2项被误拒；原v1 freeze/结果保留。v2另立source/namespace，缺出处标unknown，真正已暴露SHA变化仍拒，并标记增量赋值/删除等非规范binding修改未知。原结果不回填。

## 3. 辅助依赖出处的新增证据

自动发现两处缺口：`sklearn/tree/_classes.py`、`src/marshmallow/schema.py`。只读查询本机exact-base Git blob与不可变容器中的有效文件/Git blob；两处原host副本的LF投影均与canonical/runtime摘要一致，未改任何源码/原model窗口/输入。该authority独立记录，**尚未并入v2资格，不把unknown改成通过**。

出处核验和语义范围是不同问题：即使补齐Schema源身份，也不能自动替省略的公开import来源做承诺，更不能因相同异常认证用户意图或任意状态等价。

## 4. 下一步唯一顺序

1. 另版将只读authority证据接入辅助依赖校验，分别验证host原摘要、LF投影、Git base与runtime；不把检查器自行添加的证据叫原model窗口。补上wrong base/digest/路径/环境反例。
2. 为省略public import的示例制定有限、明确标记的范围推断或unknown协议；不凭同名类伪称原文明确namespace。继续保留输入约束与公共锚来源。
3. 把完整资格、observer/双source身份与拒错逻辑接入新冻结方法，先跨repo正负例再同版四参考/九准入DEV，仍分Gold/受限候选/语义可信/原机制指标。
4. 只有可信/行为gate真过才新不重叠canary一次≥2/3、Agent patch/独立official grade、旧DEV30及最后另授权Fresh30。当前没有新live/canary命令，不追加paid、不抽第6批、不承诺完美或一周30/30。

## 5. 工程与安全

最终单次完整 **1453 passed、4 skipped、33 warnings，102.31秒**；Ruff/预算V3重点/compact preflight ready=true，不削弱断言/timeout/skip，不当repair rate。[公开收据](../../data/e1c_evaluation_2_qualification_results.json)绑定v1/v2/authority/代码/XML和原producer seal；raw/probe/Gold/test/key不上Git。

本轮无下载删除/重启Docker/IPC/VHD/registry/proxy/tunnel/key改动；只普通隔离只读诊断containers，所有原记录/备份保留。TEST/C5/Fresh30/private Test500/repair/E2未开，当前无下载需求。Cloud可接zero单测与源码，缺本机材料报INFRA_BLOCKED，不扩旧bridge白名单或假称云端新paid已端到端验证。
