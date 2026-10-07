# E1-C evaluation_2：真实构造器关系观察结果

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent
- Origin Mode: run
- Origin Date: 2026-10-07
- Verification Status: ANALYZED（限真实构造器关系，非语义证书）
- Version Label: object_relationship_results_v2

## 1. 结论与口径

本轮provider calls/tokens **0/0**，Gold读取0。v1四参考审计因Schema无直接构造器停在unknown，未执行容器；原freeze/result保存。v2采用独立源码、范围、协议与namespace，执行一次新离线诊断，不重跑v1/旧模型/旧Gold。

v2从静态export链自动派生模块与构造器候选，不解释框架名或`with_metaclass`函数、不人工选文件。17项新单测、预算/V3重点36项与Ruff通过后执行；原probe readonly独立挂载，未改字节。容器network none/read-only/pull never，原dateutil缺失blocker保留；三份链源码同时验证runtime字节与exact-base Git blob/host LF一致。

真实观察覆盖：

| 声明对象 | 实际证据 | 不能推断 |
|---|---|---|
| DateTime | DateTime与Field构造器调用中，self类型exact对应模块声明DateTime | 不能推断任何输入均正确或全部行为义务 |
| Schema | BaseSchema构造器调用中，self类型非exact Schema，但MRO包含模块声明Schema | 不能把Foo子类叫exact Schema，也不证明公开namespace意图 |

共5个记录，其中2个早期构造器调用无对应声明类，全部保留；另3个具有对应关系，不能把3记录当3任务。按每个binding是否观察到关系汇总，不对task结果best-of。原故障返回码1，源身份和传输检查通过，不是infra失败。固定四缓存：3项not applicable、1项两个关系被观察；DEV12分母仍12。

**原资格仍2机制支持候选/1行为候选/1unknown；machine trusted0，旧Gold4/4、异常对应3/4不变。** 新诊断不是新模型生成、修复成功率或全DEV准入。Instrumentation可能改变时序/filename；不是恶意Python下attestation或完全语义等价证明。

## 2. 运行与保全

- [v1协议](E1C2_OBJECT_OBSERVER_V1_PROTOCOL_2026-10-07.md)：`uv run --frozen --offline python -X utf8 -m evals.e1c_evaluation_2_object_observer audit-dev`。
- [v2协议](E1C2_OBJECT_OBSERVER_V2_PROTOCOL_2026-10-07.md)：`uv run --frozen --offline python -X utf8 -m evals.e1c_evaluation_2_object_observer_v2 audit-dev`。

两个namespace均已完成，不再执行。初次v1/v2 Ruff的unused import在各自freeze前修正；未改已冻结代码或预算。原probe/source/state/ledger/seal/失败记录全保留，driver/log只在本机。仅安全源码、单测、协议和[脱敏哈希收据](../../data/e1c_evaluation_2_object_relationship_results.json)上Git。

## 3. 下一门槛

1. 行为资格校准：公开接口请求、同输入API对照、版本/依赖条件回归分账。首先补paired API真实共享输入/类型对应；不因源码或对象对应就认定原机制正确。
2. 公开信息省略或不充分的情况继续显式条件/unknown；不能利用原评分断言、Gold或官方失败日志编造期待。语义资格采用预注册可观测义务及反例，不追求对任意Python的形式化完备证书。
3. 定位/生成/scope/export/object/exception/判别与预算的完整method先冻结，再同版旧DEV/native验证。四参考不能报全部九准入或DEV12。
4. DEV gate实际达成后才历史排除的新canary一次≥2/3，再Agent patch/独立official grade；最后旧DEV30及另授权Fresh30/E2。当前不开canary/TEST/C5/Fresh30/privateTest500/repair/E2，不保证30/30或一周完美。

当前没有可放行的新付费命令；未来仍Flash、明确次数、≤100,000 provider tokens、retry0。无新镜像下载删除、Docker重启、IPC/VHD/注册表/代理/tunnel/密钥修改。研究动作限普通软件缺陷离线容器诊断，无生产系统访问或漏洞利用。

最终Ruff、预算/V3重点36项与合成compact preflight通过；完整回归 **1502 passed / 4 skipped / 33 warnings（81.24秒）**，XML与冻结observer源码摘要见收据。工程passed不作自动修复率。
