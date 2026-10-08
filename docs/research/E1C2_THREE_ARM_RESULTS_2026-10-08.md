# 三组修复试验结果：完成原样封存，找到公开覆盖缺口

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent
- Origin Mode: run
- Origin Date: 2026-10-08
- Verification Status: UNVERIFIED（执行收据与SHA已核对，未独立重跑）
- Version Label: three_arm_results_v1

## 1. 已授权的真实试验

用户精确确认命令后执行 `uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_three_arm_dev run`，退出0。固定一个旧DEV/三个cell，Flash真实3请求，实际15,764 provider tokens，低于48,000上限；retry0、无未知收费或超额。它是共享缓存窗口/缓存witness的接线试验，不是从issue新生成的完整端到端或独立准确率。

| 组 | tokens | 原冻结结果 | 后验解码结果 |
|---|---:|---|---|
| standard | 5,592 | 多出`type: json_object`，原closed decoder拒绝 | 仅删元字段后发现old/new相同，无改动 |
| standard_evidence | 6,108 | 生产编辑old/new相同，abstain | 无改动 |
| strict_evidence | 4,064 | 多出同一元字段，原decoder拒绝 | 保留全部编辑字符串得到唯一非空模型patch |

**原固定三cell resolved=0；其中没有真实候选进入原评分容器，不能描述成三次软件测试都失败。** 输入/响应/ledger/patch/status已generation seal，原result不回填。SDK打印禁用自动代理检测提示，不是新增网络/代理配置；容器无网络/no-pull、无下载。

## 2. 零模型诊断（另立身份，不改原成绩）

### JSON外壳诊断

`three-arm-decoding-zero-v1`仅允许删除恰为`type: json_object`的元字段；原path/old/new一字不改，未知键仍拒绝。唯一非空patch独立official评分：源身份正确、日志有效、脚本退出0，**F2P目标0/1、P2P回归37/37，resolved=false**。日志显示1failed/37passed；official脚本可掩盖pytest退出码，因此不能把shell rc0称成功。

后验解码不是原冻结方法，亦非新模型产物或新任务；它证明新增scorer已在真实候选容器执行，而非只过mock。评分材料仍只供独立scorer使用，没有传给生成模型。

### 原公开自身probe检查

`three-arm-public-patch-probe-zero-v1`不读取评分材料。只对该保留模型patch运行原公开issue派生normal与target，各两次，四次rc0、patch apply成功，同镜像/base/强制缺失dateutil条件。原样target完成仍不能推断全部修复正确：它与official目标失败构成明确覆盖缺口。

### 公开派生边界差分

`public-temporal-boundary-zero-v1`自动定位自身probe中、同时存在于公开issue的唯一时间literal。运行前固定的时间类算子：fraction precision0..6 × `Z/+00:00/-04:30`，21个合成变体；生产调用/fixture/guard不变。算子参考已暴露生产解析分支，不读取官方失败断言或Gold。

| 相同21个合成变体 | 可完成 | 仍失败 |
|---|---:|---:|
| 未改base | 6 | 15 |
| 原模型patch | 11 | 10 |
| 公开2.19.3生产包 | 21 | 0 |

找到10个“旧公开版本完成、模型patch仍失败”的自产条件反例，集中在precision1..5的偏移后缀。**21不是21个新task；11/21不是修复准确率。** 旧包仅只读挂载，未安装；身份检查针对phase driver的实际包路径/版本/14源manifest，子进程继承同PYTHONPATH，没有逐子进程独立module attestation。只比较完成/异常，未证明返回值等价；旧版本可能丢掉微秒，不要求新代码复制旧错误。

覆盖诊断初次在读取freeze缺失`module`字段时预检报KeyError，未创建namespace/启动容器；正确组合已核验receipt/result身份、补专门测试后才首次启动本namespace。失败输出保留，不重跑任何started身份。冻结后的源码/协议/结果均保全。

## 3. 已准备的新修复版本，尚未付费

[v2完整方法/预算](E1C2_THREE_ARM_BOUNDARY_DEV_PROTOCOL_2026-10-08.md)：三组共用自动生产global补证，实际补得dateutil_available/missing/ISO regex；保留条件重赋值上下文，不认证runtime值。证据两组加入4个自产base失败/公开旧版完成counterexample，截断trace明确标注；不输入official失败内容、Gold或上一模型patch代码。新decoder兼容固定外壳且保存raw/兼容标记，继续拒绝未知键与testedits。

真实输入freeze已完成，reserve12,534/15,236/12,148，均≤16k。仍同一个旧DEV/3cell，Flash最多3请求/48,000 tokens、每输出3k、retry0。**v2模型调用0，待新精确命令授权**，不能用v1授权自动开始另一身份。

```powershell
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_three_arm_boundary_dev run
```

随后才两来源从issue的完整自动链/计入定位及probe成本→固定12九准入DEV→完整方法冻结/不重叠canary一次→另授权Fresh30/E2。当前full issue可信与正式Agent resolved仍0，E1-C evaluation_2未完成；不保证30/30或一周完美。可以复用的研究贡献是**把“原probe完成但官方失败”转成不读取评分断言的公开派生覆盖反馈**，此处仅时间字符串家族证据，不宣称全新普适算法或独立收益。

## 4. 工程与保全

完整1728passed/4skipped/33warnings，112.02秒；20新增专项、Ruff、预算/V3重点与合成compact preflight过。工程计数不作修复率。[公开收据](../../data/e1c_evaluation_2_three_arm_results.json)绑定paid ledger/seal/result、三份zero freeze/result、v2freeze及XML SHA。

没有新增镜像下载/删除或Docker重启，没有IPC/VHD/registry/proxy/tunnel/key配置改动；旧paid/失败/源码/原qualification false保留；canary、C5、sealed TEST、Fresh30、Test500/E2未打开。原raw/probe/评分答案/凭证不入Git，日志只追加集中续档。WebCodex可做无模型单测与审阅；本机私有父产物/镜像不随Git同步，缺材料必须报INFRA_BLOCKED，不能假称新live入口已通过tunnel远程验证。
