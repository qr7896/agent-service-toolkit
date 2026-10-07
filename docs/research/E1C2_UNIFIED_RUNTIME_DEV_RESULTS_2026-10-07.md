# 统一编译 / 原文引用运行反馈：真实旧 DEV 结果

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent；ponytail
- Origin Mode: run
- Origin Date: 2026-10-07
- Verification Status: UNVERIFIED（真实执行及seal核对完成；研究质量尚未独立验证）
- Version Label: unified-runtime-dev-results-v1

## 结论

两轮Flash真实新生成与独立Gold判别均完成：统一编译版Gold区分**3/12**，原文引用版**1/12**。后者引用错误减少，但整体质量与成本变差，不能取代前者或拼接best-of。机器trusted均0；不是Agent修复结果、不是独立canary、不是30题全过。两轮原件分别封存，停止付费扩批，先零调用修正DTO一致性与fixture/oracle可执行性。

公开哈希摘要：[机器收据](../../data/e1c_evaluation_2_unified_runtime_dev_result.json)。原始输入/响应/执行/评分只在本机`.codex/e1c/evaluation_2/`；Cloud缺这些材料时不能宣称重跑验证。没有打开sealed TEST/C5/Fresh30/private Test500/E2。

## 1. 完成的实现与门槛

- `compiled_runtime_dev`把单Compare→Assert语法规范、源码构造前沿、静态strptime正常控制正式接到真实反馈loop。raw/canonical/证明分开；先canonical后oracle锁定；target全程序/quote/预期不偷改。恢复语法不声称旧无Assert程序等价，格式控制不声称时区等价或target format binding已证。
- 不再只跑每仓库首题：原固定12、九双准入全部执行，三未准入题仍占分母；四历史参考保留。初始reserve合计60707，动态整批ceiling扣除未跑题的初始reserve，全部九题得到首调用机会；不降低1.4安全reserve，不保证未限定的provider实际usage永不超估计。
- `issue_quote_refs`无损显示公开issue原文行/offset/SHA，模型选ID，Controller解码为原文。超长行1400字符分块，没有按task/答案排序，没有模糊匹配或根据Gold补quote。引用来源真实不等于期待语义被证明。
- 真实两仓库smoke两次控制均通过、通过target不计bug；fixture为人工synthetic，不计模型成绩。native pytest生成skip依旧只是之前的有限合成组件，未接Agent/此处评分，不能伪造`safe_static_check`或默认收集原tests/conftest。
- 代码先提交`d06caba`、`0f4818b`，各自method/source/input/budget冻结后才展示精确run命令并使用用户既有授权。所有旧方法/开始过的namespace/账本/响应不重写。

## 2. 两批分账结果

| 批次 | 实际请求 | provider tokens | 重复失败候选 | Gold区分 / 固定12 | 四参考Gold保留 | 机器可信 |
|---|---:|---:|---:|---:|---:|---:|
| compiled-runtime-old-dev-v1 | 26 | 74336 | 3 | 3/12 | 2/4 | 0 |
| referenced-runtime-old-dev-v1 | 26 | 89923 | 2 | 1/12 | 1/4 | 0 |

每批各自上限100000、每题20000、输出2000、最多36/每题4次；Flash only/nonthinking/温度0/自动retry0。本轮新增**52请求、164259tokens**，不是一批超过10万；每批都未超。所有52started均completed，没有provider失败/自动retry。自10月5日可见累计539725（包含历史旧SDK错误4281，非账单核验、不代表项目全部消耗）。实际两批分别约旧全部九题；绝不将不同版本的过题合并成4/12或更高。

| task | 统一编译版：状态；调用/token；Gold | 原文引用版：状态；调用/token；Gold |
|---|---|---|
| scikit-learn-13496（参考） | executed；3/10839；通过 | 格式包装拒绝/turn_limit；4/12941；未评分 |
| scikit-learn-26289（参考） | 引用不合格后budget stop；3/11001；未评分 | 控制通过、目标未复现后budget stop；3/12857；未评分 |
| scikit-learn-15086 | budget stop；2/8934；未评分 | budget stop；2/11846；未评分 |
| marshmallow-1252（参考） | 两控制过、重复failure；1/2557；通过 | 两控制过、重复failure；1/2849；通过 |
| marshmallow-1359（参考） | 四次原文quote不合格；4/9161；未评分 | 控制未通过后budget stop；3/10903；未评分 |
| marshmallow-1164 | 两控制过、谓词AssertionError；2/5445；通过 | 两控制过、Assert内tuple索引TypeError；2/6374；不通过 |
| pytest-7432 | English伪Python/语法拒绝；4/8774；未评分 | 原生fixture拒绝后弃答；4/11160；未评分 |
| pytest-6680 | 伪造期望quote拒绝后弃答；4/7916；未评分 | parent fixture控制失败/turn_limit；4/10410；未评分 |
| pytest-7985 | 重复retrieve停止；3/9709；未评分 | 重复retrieve停止；3/10583；未评分 |

三候选Gold通过仍须严格核查issue期待/公共fixture和执行故障点的关系。比如构造参数被接受不等于完整证明warm-start重用行为；有效ISO输入正常控制表示可不同；容器复现和Gold区分都不能自行变成机器语义可信证书。

后续只读核验更正：SK-26289引用版turn-2/3真实feedback为`target_not_repeatable_failure`，control运行正常；此前本表“控制未通过”系摘要误写。本表已纠正，集中日志保留错误与更正，原state/响应/反馈/账本/seal/机器收据均未修改。该probe将feature_names设为普通list，未产生报告中的ndarray失败；不能把目标通过解释成已修复生产缺陷。

## 3. 零调用诊断实证（未接live、不新增分数）

原编译版9次quote拒绝，引用版0次，11份真实probe引用证明落盘；但少了这些拒绝不等于修复成功。新格式额外信息与fixture质量限制导致每题保守预算stop，整批实际用量增加15587。

SK-13496四份raw实际为精确`{"type":"json_object","content":{...probe...}}`，不是无能力弃答。新`contract_feedback_diagnostics.unwrap_known_envelope`只解一层已知完整dict包装，extra/递归/string不接受；调用者仍必须完整strict action/ref/static校验。零调用对四份响应均成功解出原probe和有效原文ID，**没有执行它们、没有修控制或回填成绩**，尚未接live。

同模块`oracle_readiness`绑定candidate source SHA/execution SHA与自己的生成顶层帧，区分真正predicate AssertionError、Assert求值中的TypeError、其他unknown。实际统一版generator候选两次predicate_false、引用版两次oracle_evaluation_error。后者把返回tuple按dict索引，Gold仍TypeError；不能把它当预期谓词失败。该诊断只读不可信trace，不是信任证书，不自动修expected/assertion，不把构造处TypeError错杀为oracle错误。下一版需在选定前输出结构化反馈、由Agent据生产返回接口改fixture；不把评分反馈送模型。

审计`.codex/e1c/evaluation_2/compiled-runtime-feedback-zero-v1/result.json` SHA在机器收据绑定，provider0/live integrated false；所有负结果/候选原件仍原样保留。

## 4. 接手顺序（先零调用，禁止立即再付费）

1. **一套一致DTO。** 新runner一次定义canonical action schema，System/最后Human/schema样例不得冲突；只兼容精确已知JSON包装，unknown/extra拒绝，完整ref→quote绑定先于oracle锁定。对同一invalid行动原SHA重复停止，不再花四请求重复拒绝。当前两个已启动runner严禁修改/重跑。
2. **证明有效正常控制与消费关系。** 生产构造signature确认普通调用，无人工删target参数/改数值；若从源码派生control去掉unsupported keyword，必须另立明确control转换证明、target/quote/oracle不改，不能宣称等价。返回tuple/namedtuple/对象属性与模型消费关系未知时先反馈，不手修某题`.data`或视TypeError为谓词假。旧DEV/合成跨仓库证明、未知fail closed，不读取Gold生成规则。
3. **把readiness接到候选选择前。** 自有Assert求值错误与fixture错误继续observe/act，而非首次任意稳定非setup异常就terminal选中。正常构造Feature拒绝保留unknown/源码前沿证据，不简单要求所有target都只能AssertionError。schema合法/原文ID不能代替期待忠实性。
4. **成本预检与四参考。** 原文行/metadata不要重复进多份Human/previous_probe；只压确证冗余，不丢source/issue义务。用缓存计算实际reserve、固定100000批预算保护全9首轮；新方法/预算/代码/两仓库真实zero控制及完整回归通过后，才列新的精确Flash命令一次完整旧DEV。须保四参考/跨仓库与忠实性收益，否则不抽第6批。
5. **有限native与独立性。** 生成-only case_source/flags、有效期待quote、确定性/结构化报告、单独可信driver证书/评分身份都先实现和验证；不能解禁pytest.main/pytester原fixture或伪造旧safe_static_check。之后完整method先冻，metadata-only排除所有历史选不重叠新canary，一次盲态≥2/3且忠实性证据过；失败封存回DEV，不在原canary补规则仍称独立。
6. **最后修复。** 通过独立gate才同方法Agent patch→独立official score→同版旧DEV对照→另预注册全新任务一次性测试。现在没有新版repair得分、没有E2主实验，不承诺一周100%或30/30。

## 5. 工程与本机安全

最新单次**1320passed/4skipped/33warnings/0failed，56.44秒**；XML1324tests、0failures/0errors、56.423秒。Ruff、预算/V3规定重点与原V3 compact preflight ready=true通过（仅合成plumbing，未开sealed TEST）。所有旧测试/timeout/skip不弱化。新旧两批seal/method SHA逐一核对；本轮没有Docker stop/restart/IPC改名/镜像下载或删除，VHD/registry/proxy/tunnel/key/原备份不动。D盘空闲约34.22GiB（现场快照，不是容量承诺）。

只提交源码、测试、协议和脱敏摘要/文档，原raw/Gold/测试/密钥不上传；旧bridge白名单仍strict-v5，不声称Web已能端到端执行这两个paid入口。无新下载需要；Cloud可做本节零调用实现/单测，缺本机source/image/runtime报告INFRA_BLOCKED，不打开裸daemon或索取key。唯一逐轮日志在[集中续档](PROGRESS_LOG_ARCHIVE_2026-09-27_CONTINUATION.md)。
