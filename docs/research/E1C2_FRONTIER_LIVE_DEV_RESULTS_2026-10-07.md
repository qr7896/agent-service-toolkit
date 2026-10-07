# Docker 恢复、执行前沿零费验证与真实四参考结果

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent；ponytail
- Origin Mode: run
- Origin Date: 2026-10-07
- Verification Status: UNVERIFIED（执行与哈希核验完成；独立质量未达门槛）
- Version Label: frontier-runtime-reference-dev-v1-results

## 当前结论

Docker已在本轮明确授权范围内恢复，原DEV12全12镜像现场核验。执行绑定setup前沿的零模型缓存研究完成，Gold区分3/4；另冻真实新生成同四参考实验完成，**12Flash请求/40135tokens，Gold区分2/4，machine trusted0**。缓存收益不能改成新生成3/4，四参考gate仍未通过，不扩九题/抽canary/写Agent patch。实质收益是MM1359共享setup故障在cache与新生成都被机制隔离；整体质量没有提升到可独立验证，另一旧参考SK13496在新生成中偏离API请求而弃答。

公开收据：[zero研究](../../data/e1c_evaluation_2_runtime_frontier_zero_result.json)、[新生成](../../data/e1c_evaluation_2_frontier_live_dev_result.json)。原blocked/离线proof/旧ready10calls32826/全部负结果与seal保留，新产物不回填旧JSON。下面是真实完成/未完成，不承诺一周100%或30/30。

## 1. 本机恢复与安全

用户本轮明确允许正常停机后仅两IPC目录备份改名再启动一次。CLI stop确认Desktop不运行，Desktop/backend/proxy/secrets进程均已退出；确认两个精确绝对路径为普通目录、非reparse、备份sibling路径不冲突，全部检查后Rename-Item，保留原内容，不读取目录文件。备份后缀`20261007-144329`：

- `C:\Users\qq人\AppData\Local\Docker\run.ipc-backup-20261007-144329`
- `C:\Users\qq人\AppData\Local\docker-secrets-engine.ipc-backup-20261007-144329`

普通start仅一次成功，真实Docker Server可响应，原12个DEV immutable image/config身份全部核验。未删除/下载镜像、改VHD/registry/proxy/tunnel/key/旧备份，无force kill/WSL reset。上轮普通启动失败与本轮明确授权恢复分开记，不能假称反复启动的长期根因已根治。旧bridge strict-v5白名单没扩大；Docker恢复不等于Web新研究入口端到端已验。

## 2. 零模型执行前沿真实验证

`runtime-frontier-zero-reference-v1`在恢复后首次建立freeze/run，原ready动作按turn顺序回放，input/source需与原cached input完全一致，source ledger/state/响应/seal SHA核对；缺SK26289第四响应就`upstream_cache_missing_no_provider_call`，不补模型、不找另一批/后续最好答案。新provider/tokens0，不声称模型对改变后的feedback重新生成。

| 原固定参考 | 本批cache状态 | 独立Gold |
|---|---|---|
| SK13496 | 原turn2稳定候选 | 区分通过 |
| SK26289 | 原三响应用完，没有第四cache | 未尝试，不剔除分母 |
| MM1252 | 原turn1稳定候选 | 区分通过 |
| MM1359 | turn2/3检测到setup故障，turn3正常控制有效 | 区分通过 |

MM1359原shared setup的`s = MySchema()`在normal control之前就抛错，原模型把它误说成standalone DateTime失败。新方法只按两control的绑定源SHA/同顶层Assign(Call)帧，将该语句及suffix放到target；完整setup+target AST恒等、normal control_action/quote/oracle/assertion不改，control读取moved bindings则拒。turn2的control仍同bug配置，所以移动后仍失败，原件保留；turn3独立normal control两次通过、原完整target两次同错，producer seal后Gold通过。没有手改模型日期/数值/参数/源文件或以Gold挑响应。

trace不可信，free-name disjoint不证明alias/global状态独立，Gold区分也不证明所有期待语义；machine false。cache3/4只是局部机制开发证据，不是全新模型成绩/完整DEV12/独立canary/Agent修复。该namespace run/gold均已完成，不再执行。

## 3. 新生成四参考：完成与退化分账

新方法先提交`aa0d282`，两个repository synthetic smoke正常控制两过/通过target非bug，45相关专项/Ruff/完整1347passed/4skipped（85.63秒）、规定预算V3重点与compact preflight ready=true通过，freeze后展示唯一精确run命令，一次Flash新生成，再独立评分。

批50000、每题24000、输出2000、最多16/题4、reserve1.4、未跑题首reserve保护、Flash only/nonthinking/温度0/SDK+provider retry0。原ready每题20000不改，新cap容纳实测第四call spent11447+reserve9747；预算/提示/执行前沿一同变化，明确**不是单因素因果实验**，旧zero-study另提供固定原程序证据。实际12started/completed、40135tokens，provider失败/自动retry0，本轮未另付费扩批；10月5日起可见累计612686（非账单核验，含旧SDK错误4281，不是项目全部消耗）。

| 固定参考 | 本批结果 | 直接原因 |
|---|---|---|
| SK13496 | 弃答，未评分 | quote要求构造入口暴露参数，模型却用初始化后属性赋值测试已可工作的fit行为；target通过后错误认定无法复现。没有把quote支持的API义务与实际动作绑定 |
| SK26289 | 弃答，未评分 | import补齐后target以load_iris普通list参数调用并通过；模型据部分guard错误宣称源码已修好，未验证报告失败类型。输入类型假设/源码解释未与报告绑定 |
| MM1252 | candidate/Gold通过 | 静态生产格式正常对照两过、原ISO Z目标重复失败；时区等价和target binding仍未证 |
| MM1359 | candidate/Gold通过 | 执行绑定前沿真实新生成下再次隔离了shared setup fault，normal controls过、完整target重复失败 |

同四参考旧ready2/4、本批2/4；不能与zero3/4或其他版SK成功best-of合成4/4。没有恢复四参考开发gate、机器可信0，停止paid扩批和单纯提示反复采样；没有新版repair/official patch score，E2仍未开展。

## 4. 零费源码覆盖审计纠正假设

新`guard_evidence_audit`仅诊断，按probe imported target API/issue quoted API与public失败条件，遍历已自动selected且SHA验证的production AST guards（包括函数内嵌套分支），从AST行号自动取窗口；relation_type/depth/origin/seed/SHA记录，不含task ID/source手选规则，不读原tests/Gold，不改probe。source函数名匹配本身不证明API绑定正确/语义可信；未接live。保护路径/变更SHA/未知API/长定义窗外匹配专项通过。

真实只用四题第一合同与对应input，不按评分筛选：SK26289提取14个guard，公共issue失败条件`if feature_names:`准确匹配`sklearn/tree/_export.py:1040`，**already_visible=true**。这是机器定位的源证据，不是人工指定路径；也证明本轮不能把瓶颈说成缺少源码。模型所说“源码已用is not None修好”没有覆盖后面的真实bool分支；继续堆窗口会重复已有信息而不自动解决输入类型/期待绑定。其余3题本规则guard0不等于生产无guard或接口不存在。

此zero audit/新增3专项不增加可信数，语义/API绑定仍unknown。最终单次**1350passed/4skipped/33warnings/0failed（89.21秒；XML1354tests/0errors/0failures/88.361秒）**，Ruff与预算V3重点24/原compact preflight通过，旧断言/skip/timeout未削弱。源/score/raw/seal均保持，Git只源码/测试/协议/脱敏receipt/文档。

## 5. 当前唯一下一步：可执行 API 义务与输入类型假设

1. **在oracle锁定前绑定请求入口。** 从public quote声明的API/源码签名形成typed obligation，核验target是否真正经过该入口与所要求的调用方式；已有工作行为不能替代要求新增的接口参数。未知不硬判，不写SK/warm_start专属规则，不读Gold生成约束。不自动把declared reference当语义证书。
2. **区分原文事实与类型假设。** public fixture facts有明确字面值/类型就保持；缺信息时显式记录hypothesis与来源，用production guards/自己运行验证，同一允许值的control/target对比，不把synthetic参数伪称原报告事实、不人工把某题list改array。明确失败point/predicate/API是否对应issue，而不是任意稳定异常就选。
3. **对模型结论做源绑定核对。** 声称“已修复/不能复现”应对应完整相关源谓词与实际目标类型；已有guard audit证明关键分支已经可见，因此暂不接一批重复source windows或新semantic服务。guard结构诊断不替代行为忠实性。
4. **先零费验收，再小screen。** 所有10/12旧responses、source/trace/proof保留；用这些缓存和跨repo合成证明typed obligation能拒绝绕过入口、保留正确目标，未知fail closed；新方法/预算/提示/输入/代码完整另冻后才一次四参考新生成。四参考/跨仓库/忠实性未达gate，不跑完整九题、不挑第6canary，不靠增加额度或反复best-of。
5. **完整门槛后才独立试验。** 还须有限generated-native DTO/确定性证书/独立评分（不能开放原tests/conftest/pytester或伪造safe_static_check）；完整旧DEV同版验证后新不重叠canary一次≥2/3且忠实性过→同方法Agent patch/官方评分→同版DEV→全新任务一次性。sealed TEST/C5/Fresh30/private Test500/E2仍关闭；研究未完成，不能承诺30/30。

WebCodex可接本节源码/零费测试/公开摘要；本机raw/source/image/runtime缺失则INFRA_BLOCKED，旧tunnel权限未扩，不假称能直接调用新paid模块、不索要key/开放裸daemon。没有新大文件下载需求，当前全部12旧DEV镜像仍可用；用户上轮IPC授权本轮已消费一次，未来再出IPC问题必须另取得明确授权。
