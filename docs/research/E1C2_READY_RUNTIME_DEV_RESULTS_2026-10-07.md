# Readiness 四参考结果与故障前沿进展

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent；ponytail
- Origin Mode: run
- Origin Date: 2026-10-07
- Verification Status: UNVERIFIED（真实生成/评分完成；独立可信性未达门槛）
- Version Label: ready-runtime-reference-dev-v1-results

## 当前结论

新Flash四参考screen已完成：**10请求/32826tokens，Gold区分2/4，机器trusted0**。统一接口恢复了SK13496，但SK26289仍未复现、MM1359的共享setup先失败，未达到四参考全部保留的开发gate。不扩九题/抽canary、不拼历史最好成绩；不是完整DEV12得分或Agent修复。

下一步新增执行绑定setup前沿原型：只读本批3份失败control合同，2份（同一任务的两turn）满足移动条件，完整target程序AST不变、control/quote/oracle不改。**仅离线证明，新增容器执行0；不能报恢复一题。** 真实零调用研究被Docker健康gate挡在freeze之前，状态`INFRA_BLOCKED_BEFORE_FREEZE`。[公开机器收据](../../data/e1c_evaluation_2_ready_runtime_dev_result.json)绑定paid/cached/工程哈希。

## 1. 实际做了什么

1. 单一动作DTO：五string＋两integer引用，不再System/最后Human互相矛盾；精确旧字符串兼容；只解已知单层json_object/content dict，extra/recursive/string拒绝。原文无损紧凑ID/text pairs；实际Assistant/observation只保留一次，只有全等重复字段才移除，source/issue/不同previous_probe不删。
2. Predicate readiness接候选选择之前：生成Assert求值TypeError等回反馈，不误当predicate false或直接terminal。期望仍锁定，fixture只据生产API修。constructor位置异常留unknown，不一刀切当测试错误。
3. 两次同canonical行动、均invalid/控制失败/求值错误/目标通过，第三调用前停止，保留两份原response与额外调用0记录；不同source/read或不同fixture不停止。没有provider retry或自动修值/返回属性。
4. 所有已有两批52响应零调用审计：之前可解码全部保留，51/52格式可解码、4包装恢复、一份缺字段仍拒绝。**解码不是静态有效合同/可信复现**，bad quote/code仍由原执行gate拒绝，source/Gold不输入模型。审计method SHA等于准备时源码。
5. 两仓库真实synthetic smoke每control2通过、通过target不计bug；37相关专项/Ruff与完整1331passed/4skipped/33warnings（58.33秒）通过，规定预算V3重点及compact preflight ready=true。方法先提交ca9ef29、source/input/budget冻结，再列精确Flash命令一次paid run。

## 2. 真实分账与逐题

仅四条固定旧DEV参考，原队列12/双准入9/screen4分开，不能称独立canary或完整DEV12。批上限50000、每题20000、输出2000、≤16/题4、保守reserve1.4、未跑题首reserve保护、Flash only/nonthinking/温度0/retry0。实际10started/completed、32826tokens，provider失败/重试0。自10月5日起可见572551（非账单核验、含旧SDK错误4281），不是项目总消耗。

| 固定参考 | 本批状态 | Gold | 已确认原因 |
|---|---|---|---|
| SK13496 | 两control通过、target重复TypeError | 区分通过 | JSON动作正常进入执行；源码前沿保留target程序，期望未改 |
| SK26289 | budget stop | 未评分 | 首probe control遗漏导入，修正后两control通过但target也通过；feature_names来自load_iris的普通list，没有复现报告中的失败 |
| MM1252 | 两control通过、target重复ValidationError | 区分通过 | 静态production格式正常对照、原ISO Z目标不改；时区等价/target格式绑定未证明 |
| MM1359 | 两次control失败后弃答 | 未评分 | 实例`s = MySchema()`位于共享setup，在control行动前抛AttributeError；不能说standalone DateTime本身失败 |

与旧full九题中的同四参考比较：compiled版Gold2/4、referenced版1/4、本批2/4；不能因恢复接口就称研究质量已提升到独立可用。没有新patch/official repair score，machine trusted保持false。

纠正前次摘要：上一份逐题表曾把SK26289引用版写成“控制失败”，只读原turn2/3确为control通过且target_not_repeatable_failure，已在原结果文档加更正、集中日志记录；原机器收据、响应、feedback、state、ledger、seal不动。

## 3. 执行绑定前沿：已验与未验

新增`runtime_frontier_zero.shift_from_control`：control源SHA/execution SHA与phased setup前缀对应，两份真实失败normal控制的同一自生成顶层帧位于Assign(Call)，才把该语句及后缀从setup搬到target。完整setup+target AST恒等，control_action与四oracle字段不变；normal control读取suffix写入名字则拒绝。free-name disjoint只覆盖静态名字，**alias/global状态独立性仍未证明**；trace不可信，不是语义证书。

13新专项加readiness共24passed/Ruff通过，完整最终**1344passed/4skipped/33warnings/0failed（66.47秒；XML1348tests/0errors/0failures/66.458秒）**。只读paid旧日志的新离线审计遍历全部3份failed control，2份同一MM1359程序满足搬移，1份control-action故障拒绝；没有手选source/改参数/按Gold挑选。离线AST证明不替代真实normal控制两过与target重复失败，也不证明新模型会根据反馈正确修订。

真实zero runner按原turn顺序回放prior responses，最早满足base候选才选，缺cache不发provider、不借另一批响应。它**不是对新反馈重新采样的因果模型回放**；必须明确cache/全新生成区别。原ready namespace不改，zero独立目录，各turn原controls、frontier-validation子目录和证明都保留；先producer seal再Gold，只计cache开发结果。

2026-10-07下午尝试新zero run时，Docker Desktop/backend已不运行、LinuxEngine管道不存在；health gate在任何freeze/研究输出前失败，zero目录未建立。普通`docker desktop start --timeout 30`仅一次失败，最新日志明确`Docker/run/dockerInference`旧IPC不可访问，backend取消后退出。**未强杀WSL/重置/移动VHD/删除镜像/备份改名IPC**；已另向用户申请本轮仅两IPC目录正常停机备份并普通启动一次，尚待确认。旧授权一次机会不擅自复用，旧备份/代理/tunnel/key不动。

## 4. 下一次接手的具体门槛

1. 先处理Docker硬阻塞，获得本轮明确授权才仅指定IPC备份；仍失败就保留诊断停止重启，不动数据盘。确认真实Server/四immutable image可用，而不是磁盘loaded.json。
2. `runtime-frontier-zero-reference-v1`目前尚未创建freeze或开始生成：恢复后按[零调用协议](E1C2_RUNTIME_FRONTIER_ZERO_PROTOCOL_2026-10-07.md)运行一次run，完成并seal才gold。若后续已存在freeze/state，禁止照此旧“尚未开始”重新运行，先读新日志/结果。离线proof和上述启动失败始终保留。
3. 判断是否真有跨阶段control改善/重复target/Gold区分，不拼live2/4与cache收益。未知alias/语义/数组参数类型继续unknown；严禁人工把某题list改array、改assert或利用Gold反推生成规则。
4. 将观察到的任务无关fault-frontier和readiness机制合入另冻live身份，固定四参考/Flash/预算一次新生成；四参考/忠实性与跨仓库gate未过不扩批。已started的ready smoke/preflight/run/gold/zero-audit均不重跑、不改预算或源码。
5. 还须补有限generated-native DTO、确定性报告/证书/独立评分，不能开放原tests/conftest/pytester或伪造safe_static_check。完整开发gate后才预注册新不重叠canary一次≥2/3、Agent patch与official score、同版DEV和全新任务一次性。TEST/C5/Fresh30/private Test500/E2保持关闭，不承诺一周完美/30/30。

本轮无需新镜像下载或清理。公开Git只源码/测试/协议/脱敏收据，不上传raw/Gold/测试/密钥；old bridge strict-v5 whitelist未扩，不声称Web可以调用这些paid入口。Cloud可先做本节零调用source/测试；缺local artifacts/runtime/image明确INFRA_BLOCKED。
