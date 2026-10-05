# E1-C evaluation_2：第二批 canary（传输修订）结果

日期：2026-10-05。状态：`sealed_negative_below_preregistered_threshold`。固定三题可信复现 **0/3 < 2/3**，该批封存。不得在这三题上修解析、加窗口、改probe后重报独立通过。Agent修复配对、sealed TEST/C5/Fresh30均未执行。

## 环境、输入与冻结

用户终端完成三张镜像直连下载。本机核对不可变image ID 3/3，六项官方离线Base/Gold检查全部通过：Seaborn目标测试base失败3/3、Gold通过3/3且47/47原测试保持；Marshmallow目标1/1、原测试24/24；pytest目标1/1、原测试127/127。官方脚本整体returncode=0并不否定Base目标失败；准入按官方日志中的明确FAIL_TO_PASS状态判定。

三条公开issue和exact-base生产源码按原v4规则自动物化，各四个窗口。原14份方法文件、选择身份、原direct-only目录均保留；传输修订和新live适配器在新目录执行。输入端不包含官方测试/Gold/grader输出，容器无网络、pull=never；独立Gold阶段只接收已锁定候选。

新适配器只绑定传输修订、路径与预算；生成提示和路由沿用原v4。执行身份 `e1c2-independent-canary-v2-metadata-proxy-v1-flash`，源码提交 `272f841`。live freeze SHA `5b3c8bb508019adb2fd33f32511d9d16f3bebc8cb5979e69e2cc7f4871c1004f`，ledger SHA `4fab3c9a61671094b3e0d71bea298fd2f50d3bcd2788457f3b66f00f3c047c94`。全部输入/源码/镜像、传输amendment/seal、六份准入、适配器与协议摘要已绑定。

## 命令、成本与逐题结果

按用户此前每个实验先列命令、≤100,000 tokens无需再确认的授权执行一次：

```powershell
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_canary_v2_proxy_live run
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_canary_v2_proxy_gold
```

请求模型`deepseek-flash`、non-thinking、temperature0；3次完成请求，共 **13,783 provider tokens**，初始预留27,760、硬上限42,000（每题14,000），SDK零重试。响应保存只含raw/usage，返回模型版本标识未完整保存，故不补写具体V4版本或声称模型快照固定。

| 固定任务 | tokens | 生成/验证结果 | 可信 |
|---|---:|---|---|
| Seaborn-2846 | 7,010（4,410输入+2,600输出） | 回显输入/源码到输出上限；未形成可解析的单一source JSON，原解析器拒绝，未执行probe | 否 |
| Marshmallow-1343 | 3,678（3,569+109） | base两次相同失败；同一probe应用Gold后仍ValueError：构造的validator引用不存在字段，属于fixture错误，Gold不区分 | 否 |
| pytest-8861 | 3,095（2,945+150） | 响应明确abstain，称生产窗口缺少相关执行路径；原runner统一记candidate_rejected。本报告另记弃答类别，原state不回填 | 否 |

Gold仅对唯一重复失败候选执行，补丁应用成功、probe退出1、未超时、`gold_discriminating=false`。它不能晋升可信，无需以人工语义审核弥补Gold失败。独立判别SHA `bb4fb3eb46021c819a85d559d49f501a122152a8133a6eb7adc01fcf14f96241`。原generation `trusted_reproducer_count=0`保持原样。

完整公共摘要见[data结果](../../data/e1c_evaluation_2_canary_v2_amended_result.json)，原始response/state/ledger、输入、执行日志和Gold判别仍留在`.codex/e1c/evaluation_2/canary-v2-metadata-proxy-v1/`，不发布题面、Gold正文或凭据。

## 下一轮仅回旧DEV

三个瓶颈分别是输出协议、可执行fixture、定位覆盖；只改JSON解析不能解决复现质量。下一DEV版本先做三个任务无关检查，再按同预算比较：

1. 明确区分合法`source`、合法`abstain_reason`和截断/输入回显；任何格式修复只在新DEV版本实现，不对本批重算。
2. 固定issue行为合同与构造前提，加入执行正对照：先证明自建fixture和API设置有效，再检查目标行为；对照失败分类为setup/fixture，不当作目标故障。预期关系不能随失败反馈改写。
3. 自动从允许的issue API/traceback线索扩展生产窗口并核验覆盖；无task-id→文件表、无人手选文件，超源码预算弃答。先用旧DEV/合成夹具验证，不为这三题补专用规则。

这些是待验证改进方向，不宣称已经提升成绩。新的方法若在旧DEV有同预算增益，再先冻完整方法/预算、选与DEV及v1/v2均不重叠的新canary；仍需固定分母≥2/3后才进入Agent修复。旧DEV30/Fresh30的30/30目标未达，不能把两个canary或多版本best-of合成成功。

本轮工程回归：新适配器专项8 passed、重点18 passed、指定Ruff通过、V3 preflight ready；全仓单次 **1093 passed / 4 skipped / 33 warnings**（70.29秒）。测试计数不是benchmark修复率。
