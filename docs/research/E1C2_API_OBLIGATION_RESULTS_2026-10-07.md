# API 义务与源绑定类型观测：真实开发结果

更正（同日后续审计）：付费runner内部重入配置覆盖外层executor，原两批API义务/类型观测产物均0；此前“组件已在paid链生效”的解释不成立，不能将3/4与2/4归因于该组件。独立零调用类型组件的观察证据仍保留，原分数/账本/协议不改。详见[执行链根因、修复与新4/4结果](E1C2_EXECUTION_PLAN_RESULTS_2026-10-07.md)。

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent；ponytail
- Origin Mode: run
- Origin Date: 2026-10-07
- Verification Status: UNVERIFIED（真实执行/独立Gold判别完成；独立质量gate未过）
- Version Label: api-obligation-and-type-dev-results-v1

## 结论与分账

| 同四固定旧DEV参考 | 请求 | provider tokens | Gold区分 | 机器可信 |
|---|---:|---:|---:|---:|
| API obligation门槛版 | 8 | 28363 | 3/4 | 0 |
| 类型观测接线版 | 8 | 28428 | 2/4 | 0 |

本轮新增16请求/56791tokens，provider失败/自动retry0，两批各50000上限/每题24000/输出2000/最多16/题4/reserve1.4/Flash only/nonthinking/温度0，旧预算不改。只同四参考，原固定12/九准入/screen4必须区分，不是完整DEV12/独立canary/Agent修复，不能best-of合成4/4。可见累计669477（自10月5日起、非账单核验、含历史SDK错误4281、不作项目总账）。本轮不再付费重采样、不扩大九题、不选canary。

[公开哈希收据](../../data/e1c_evaluation_2_api_obligation_results.json)绑定两批freeze/state/ledger/seal与Gold；原raw/probe/日志/Gold/test/key仅本机.codex，所有旧negative/freeze保留，已开始入口严禁重跑或改method/budget/state/response。

## 1. 实质实现与已验边界

`api_obligation`复用既有production symbol/method resolver与assertion-free fixture expression。有限明确英语语法“expose/accept/support `parameter` in/on/via `Owner.__init__()`”从完整public issue取owner/parameter/原文位置；数据来自原文，不含task ID/类名/参数名专属规则。不匹配的请求not_applicable/未知，不自称通用intent理解。module/alias→production class/constructor签名/源SHA，qualified module不明/alias shadow/死函数/**dynamic mapping/缺绑定不能算满足；仅顶层普通无条件语句的直接构造keyword调用满足**语法入口**，不证明已实际执行/行为忠实。

新gate在oracle锁定前拒绝绕过明确constructor入口的属性赋值/已有workaround，不锁该错误子目标；程序、quote、数值、控制和assertion不由Controller补写。输出source-bound接口证据是结构检查，不是machine trust证书。正常control两次、target重复/Gold仍另验。

旧两批四题第一合同全审（不按Gold挑、source seal核对、provider/容器0）：frontier版SK13496属性赋值被判未履行/未知，ready版真正constructor keyword保留；另三题有限语法不适用。模型setup的list/dataset返回与public binding分账，public表达式exact match也不证明runtime类型，synthetic不能变原报告事实。10新helper专项+3接线/相关budget V3共34passed/Ruff，真实两repo synthetic控制2过/pass target非bug，完整1363passed/4skipped/33warnings（96.23秒）、规定compact preflight ready=true通过；代码先提交87f9e4d，再冻新方法/输入/预算，展示唯一精确paid命令后一次新生成。

## 2. 第一版真实收益与剩余问题

- SK13496：首请求正确请求constructor接收keyword，原正常control过、target重复TypeError，Gold区分通过；没有再以属性赋值测试已工作的行为。接口门槛未替模型生成代码。
- MM1252/MM1359：都产生候选并Gold通过，原格式正常控制/执行前沿机制保持；Date格式时区等价、alias/global状态独立仍未证。
- SK26289：普通list fixture通过后，模型把它称为numpy数组、误判源码已修好并弃答。已有source guard事实保持`_export.py:1040 if feature_names:`，输入类型未被source/schema事实固定。

本版3/4优于上轮同四参考2/4只是局部开发证据，样本小/反复调参，不能当泛化或显著算法收益。机器trusted仍0，未过四参考全保留/行为忠实性gate。

## 3. 类型观测组件与第二版负结果

`guard_type_observer`是**可信Controller代码**，不是开放给模型的trace/sys/runpy工具，不伪造model safe_static_check给driver。只接受已验证且SHA绑定的自生成probe与≤2个public失败production单变量guard sites；网络none/read-only/pull-never/原base identity/资源限制。固定driver只runpy运行自己/e1c2_model_probe.py，实际source文件和probe字节SHA在container核对；nonce唯一marker。sys.settrace仅匹配文件/行/该局部名，最多8记录，只用已知builtin type identity和启动前捕获的numpy ndarray type；不调用对象bool/len/repr/getattr、不输出参数值/预期、不读原tests/Gold。源字节不改，但filename/trace/timing可能改变行为，**不声明instrumented语义完全等价**。失败不采用type facts，infra/timeout停止不retry；optional import blocker场景明确诊断不支持而跳过。

7新保护专项通过，零provider组件选择第一target通过且有public guard匹配的合同（遍历全四，不用task ID挑）：真实在`_export.py:1040`观察到`feature_names`类型为**builtins.list**，值未输出，原probe/source SHA绑定/returncode0。这只证明模型自己fixture类型，不证明原报告dtype，也不增加候选/修复分数。

新类型接线反馈只传这些自己输入的actual type/source事实，Controller不把list转array。源/protocol先提交42c15a3；两repo真实synthetic smoke/相关30/Ruff，完整1372passed/4skipped/33warnings（92.73秒；XML1376/0errors/0failures/92.702秒）、规定compact preflight ready=true通过。另冻方法/相同预算/同四题，列精确命令一次新生成/独立Gold：

- SK13496与MM1252仍候选/Gold通过。
- SK26289收到真实list观测，纠正了事实错误，但认为public未明确dtype就不能构造假设而弃答；观测改善事实判断，没有产生新的有效target。
- MM1359生成同bug配置normal control失败后弃答，本版未保住该参考。不能把这次退化全部归因于observer，因为提示与新生成程序不同；observer只在另一个任务命中。

两版8请求各自完成seal/Golddiscriminator3与2，不能拼接。事实准确度、结构scope合法与实际复现率不同；工程1372passed不是修复率或自主率。

## 4. 下一步止损顺序

1. **开发比较基线保留API obligation版3/4**，类型组件保留为diagnostic，2/4接线不直接取代。所有旧源码/原件/seal不改，不复制旧命令重跑。
2. **统一hypothesis政策再做零费。** 区分“缺期待语义应弃答”和“缺输入类型可提出明确source-consistent假设”；现有保守输入约束与新增假设许可仍使模型把unknown input等同不准测试。先整理成一个一致可执行协议，设事实/假设/未知三层，不称假设为原报事实，不把source-consistent counterexample升级成report-exact可信。不要再追加层层提示或靠加预算解决。
3. **正常控制机制仍要跨repo证据。** 正常配置不得重复target故障；source/自己trace定位shared setup后保持完整target AST/expected不改。不能手修某题field类型、日期、数值或读取Gold/test生成控制程序。原始types/公共constraints一致性未知必须显式记录。
4. **约束实际同版比较。** 缓存可做拒错/来源/程序保真审计，不能作为新反馈因果生成score；有限source假设空间协议、输入、预算、代码完成zero验收和完整freeze后才一次小DEV新生成。四参考/忠实性/cross-repo全gate未过，不跑完整九题/第6canary，先保留负结果，不无限paid重采样。
5. 完整DEV与有限generated-native DTO/确定性证书/独立评分仍未做完；通过后新不重叠canary一次≥2/3/行为忠实性过，才Agent patch/官方评分/同版DEV/全新任务一次性。TEST/C5/Fresh30/private Test500/repair/E2保持关闭，研究未完成，不承诺30/30或一周完美。

本轮没有Docker重启/IPC改名/镜像下载删除，原12镜像与备份保留，VHD/registry/proxy/tunnel/key不改。旧bridge strict-v5 whitelist不扩大，Cloud可做本节source/zero单测，缺本机source/private artifact/image/runtime即INFRA_BLOCKED，不假称新paid入口Web端到端可用/不索取key或开裸daemon。所有逐轮日志仅集中续档，Roadmap页首与handoff指向本结果。
