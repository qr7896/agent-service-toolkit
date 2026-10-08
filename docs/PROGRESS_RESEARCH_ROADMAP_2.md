# Roadmap 2：E1-C evaluation_2 当前状态与执行顺序

状态日期：2026-10-09。当前唯一执行入口；背景见[Roadmap 1](PROGRESS_RESEARCH_ROADMAP.md)，历史过程与旧页面原文见[集中续档](research/PROGRESS_LOG_ARCHIVE_2026-09-27_CONTINUATION.md)。

## 0. 最新结论

**最新状态：** 公开反例DEV v2已按精确授权执行：Flash3请求/20,385tokens，standard非空局部补丁official目标0/1、回归37/37；另两证据组同值无改动，固定三cell resolved0/3。没有JSON外壳拒绝，但反例尚未驱动真正修复。[完整结果](research/E1C2_BOUNDARY_V2_RESULTS_2026-10-09.md)、[收据](../data/e1c_evaluation_2_boundary_v2_results.json)。此前原probe完成/official失败与21变体覆盖缺口保持；新patch与旧patch字节相同，引用旧11/21 cache，不称新重跑/新task。

发现可检验配置缺口：原caller一直显式关闭thinking。下一步只发送与v2完全相同strict prompt，Flash开启thinking/high；max1call/30k含推理、生成max8k。[单请求新协议](research/E1C2_FLASH_THINKING_DEV_PROTOCOL_2026-10-08.md)已冻，reserve17,148≤30k，**paid0、待新精确授权**。actual SDK HTTP参数与reasoning ledger离线Mock验证过，不证明真实效果。预算也变化，不称单因素思考收益；共享准备读base对象，但model无既有测试/评分断言/Gold。旧unknown/所有原结果不改。

原2.19.3发行对照的旧normal/target各两0、base normal两0/target两1保持，[原结果](research/E1C2_RELEASE_WITNESS_RESULTS_2026-10-08.md)、[原收据](../data/e1c_evaluation_2_release_witness_results.json)不变。**完整可信0/Agent修复0，E1-C未完成**；另立有界 DEV 修复可行性协议不回填旧 trusted/repair_eligible，不证明公共namespace意图/全部义务。

最新工程1736 passed/4 skipped/33warnings（119.91秒），8新增专项/Ruff/合成compact preflight过；旧1680/1708/1728及XML保留，均非repair rate。public-release counterfactual不冒充canonical Git。当前不需下载/改Docker设置，旧strict记录和所有原结果保全。

## 1. 已完成与尚未完成

| 环节 | 实际证据 | 边界 |
|---|---|---|
| DEV12基础设施 | 12镜像身份曾现场核验；双准入9/12 | 每次核验现场，异常留固定12分母 |
| 自动源码窗口/入口/guard | 公开issue与exact-base生产源、来源与SHA | 非人工选文件不等于语义正确 |
| 五批历史独立canary | 1/3、0/3、1/3、0/3、0/3封存 | 未达≥2/3；不再称独立调参 |
| 历史API/类型/codec版本 | Gold3/4、2/4、2/4保持 | 内部配置覆盖hook，效果归因不成立 |
| v1执行计划零费 | outer=true/inner=false；smoke/audit封存、付费0 | 原型负证据，不覆盖旧源 |
| v2真实完整执行链 | 五份旧probe零费5/5产物、1自身类型观测；新paid4/4产物 | 不将回放叫新生成；类型组件paid未触发 |
| v2四参考新生成 | 4请求11,909tokens；正常control与重复base失败、Gold4/4 | 固定12/九准入/screen4分账，不是完整DEV或独立成绩 |
| 前版witness grounding零费审计 | 全4审计，1项trace期待/公开guard未在失败trace观察到 | 其余也未获语义证书；组件未接live |
| 前版严格期待门槛 | 期待在lock前筛查、公开A/B/共享输入源绑定；Gold3/4 | 错误期待被拒，但新生成覆盖未保；unknown不trusted |
| 公开normal零费feasibility | 自动派生1程序、4次normal通过、Gold读取0 | 不是模型输出，未接live，不拼分 |
| 公共报告锚新版本 | 新假设口径下Gold4/4，真实A/B输入表达式/source绑定 | 前版3/4不回填，不是严格前版过关 |
| 真实异常观察与双source身份 | v1失败保留，v2观察3/4对应；CRLF/LF原副本/有效文件/Git blob核对 | 不等于语义证书或抵抗恶意程序的attestation |
| 新受限资格校准 | v3两机制支持候选/一行为候选/一unknown；旧v1/v2保留 | 非新运行时实验，不自动认证 |
| 辅助依赖authority | 两处host LF/base blob/runtime一致，已接v3审计overlay | 不改模型输入、不回填旧资格 |
| 条件范围与静态export链 | 四缓存3显式结构/1条件结构；两引用链静态身份支持，23单测 | 不证明runtime对象/namespace意图，不改旧资格 |
| 构造器运行时关系 | DateTime exact与Foo包含Schema MRO；5记录全保留；v1 unknown/v2独立身份 | 1缓存2关系，不是2任务；不证明公开意图/任意Python语义 |
| 调用前paired输入 | 两共享keyword typed SHA一致，分类器unknown；normal0/target1 | before-call不证明进入函数体，all_inputs_match=false |
| Parameters文档支持 | 自动提取四声明行；两个list声明不明确支持实际ndarray | 规格支持缺口，不判task非法；明确请求可改旧文档 |
| 行为分支与有限子义务 | 精确公共bool请求/闭合签名/相同control/原probe调用行TypeError；1子义务支持 | 不证明default/增量功能/全部issue，可信0 |
| 公开旧版本对照 | 旧v1前置失败保留；resume复用11文件/152704bytes，实际3.0.0rc8同一probe rc0 | 当前封存两次rc1不重跑，非全部旧版/DEV/修复成功 |
| 新统一Controller有限接线 | 参数声明/结构policy/既有执行/异常资格/行为分支；两正常正例+一真实合成故障，17专项通过，adapter冻结 | 非真实task成绩；paired/object/version未自动接入，live禁用 |
| Scoped定义与候选动作gate | 精确header/owner；unknown不terminal；四缓存3grade-only/1补证/0repair，实际正负smoke过 | 缓存不算新生成；所有有限候选不获全issue证明 |
| 新Flash旧DEV四参考试验 | 3请求/13706tokens；1有限候选，第二题真实补证路径出现 | 第三请求前metadata边界中断，另两题未开始、无新Gold/整批率 |
| 原失败反馈零调用投影 | 实际Human消息14857chars/原边界过、nested hook过、scope未变 | 原trial不恢复；后续resume另立身份 |
| 授权resume-only完整执行 | 原前两轮只缓存/不执行旧probe；7新calls/29996tokens，四行终局，新seal255产物 | 1候选复用、2budget stop、1重复stop；不是四题正确 |
| 新独立Gold | 唯一复用prefix候选施加Gold后rc0，1/1消除 | 新生成候选0，不是patch成功或完整issue证书 |
| program缺证建议分支修复 | 新route/shadow三MM1252反馈，Schema请求恢复；4专项 | 不改旧gate/结果，未验证实际live采用 |
| 自动production补证+context | 实际取得Classifier/Schema，host/LF/base/SHA，next messages可见；reserve11985→11100/10154→8471 | cached delegate非新probe；获取source不认证语义 |
| 合理分层预算新DEV | input12k/24k、task32k/48k、batch80k；16calls/53212，无budget stop | 0候选；模型不能仅靠预算自动变正确 |
| JSON协议零修复（历史阶段） | 去代码说明示例值、closed wrapper、AST前置；7专项及16回应shadow过 | 原8坏probe不补写；后续新模型实链见下行 |
| 实际协议/执行小阶段 | 三冻结阶段13calls/53708tokens；真实Python与normal/target容器观察 | 固定两个旧DEV来源，不是完整四参考或独立样本 |
| live自动补证与next消息 | Schema实际取得，next prompt含新源且与真实ledger SHA一致 | 公开fixture范围仍unknown，非trusted或修复 |
| 正常对照与环境反馈修订（历史阶段） | source-backed binding保护已实链；matching自身记录环境投影零调用过 | 当时未接paid；后续实链见下行，不编造自然环境 |
| 环境事实/接口请求新版 | matching执行条件到Human，新的有限候选Gold1/1 | 仅参数接受，非完整行为或Agent修复 |
| 模块函数检索新版 | 新生产query匹配与next消息过；另一新有限候选Gold1/1 | 同一旧DEV，不合并2/2；alias提示不认证 |
| 源码Controller零模型 | 属性依赖/2源选择/公开内层异常对应true/条件scope与运行关系到Human | 旧probe非新样本、namespace意图未证；后续版本对照见下行 |
| 公开2.19.3发行对照 | 同probe/image/optional条件，实际version/path/SHA过，旧normal×2/target×2都0 | 版本执行见证，不是canonical Git/完整意图/Agent修复 |
| 三组新路线零调用准备 | base Git blob测试读取/未来提交反例/生产exact edit/全组三cell seal后评分；真实输入预算已冻 | 缓存窗口/缓存witness接线，不是新付费成绩；严格组仅模型输入无测试 |
| 三组真实修复试验 | 3calls/15,764tokens，2外壳拒绝/1无改动，全部seal | 原resolved0/3；不重跑或回填 |
| 后验解码与真实official容器 | 唯一保留模型patch：目标0/1、回归37/37 | zero非新生成，不将脚本rc0作resolved |
| 原自身probe与公开边界 | patch下正常/目标各两0；同21变体base6/patch11/旧版21完成，10反例 | 一个旧DEV合成状态诊断；不证明全部值/意图 |
| 三组公开反例DEV v2准备 | 共用3生产global含重赋值上下文，证据组4自产反例，实际输入预算freeze | paid0、尚未验证新patch；不输出评分断言 |
| 三组公开反例DEV v2真实执行 | 3calls/20,385，1局部patch/2无改动，official目标0/1/回归37/37 | 原0/3封存，未证明反例收益，不重跑 |
| Flash thinking单请求准备 | 同strict prompt，actual SDK mode/high/8k及含推理ledger离线检查，reserve17,148 | paid0，模式与预算耦合，不保证效果 |
| 机器可信/Agent修复/E2 | machine0、新repair/official resolved未做 | 不报30/30，不开Fresh30 |

## 2. 当前瓶颈

检查器现在能组合已知公共fixture结构、production依赖、期待锚和异常证据，并拒绝明确改值/影射/对象改写。它只支持有限结构；状态/控制流/自定义行为、遗漏公共范围不认证。

当前实质瓶颈：复现覆盖不足已有public反例实证，但v2模型未利用它产出实际修改，继续扩同样one-shot不合适。先用单请求thinking配置诊断，再建立公开自身反例的实际自验证→限次修正反馈；不能把官方断言当答案或仅继续堆context。短名namespace/全部义务仍unknown，旧full_issue_trusted/repair=false不动。标准组若成功不能叫“不读取现成断言”；时间算子非任意task完整方法，暂无下载瓶颈。

## 3. 严格组验收定义（标准组另列base测试权限）

1. 生成侧只用公开issue允许投影与exact-base生产源，不输入原测试断言/题面可执行答案/Gold/官方评分日志。
2. 定位规则无task-ID→文件表、无人工挑文件；保留来源、rank、窗口预算与SHA。
3. 两次有效normal control和两次稳定非setup目标失败；独立Gold消除不自动授予行为忠实性证书。
4. 新probe须对齐公开行为义务，unknown保持unknown；自动语义门槛尚未完成。
5. Agent补丁由独立官方评分判resolved。代码回归、可信复现和30/30 resolved是三个不同目标，不best-of合并。

## 4. 当前唯一执行顺序

| 顺序 | 下一步 | 放行证据 | 未过时 |
|---|---|---|---|
| 已完成 | authority接入v3辅助源校验 | 原host摘要/LF/base Git/runtime均绑定，8项身份单测 | 不改旧model窗口或结果 |
| 已完成 | 有限范围与静态export链协议/审计 | 完整引用后缀、单一静态定义/重导出、host/LF/base身份、23单测 | 条件解释不回填旧unknown |
| 已完成（有限范围） | 条件对象构造器/MRO观察 | 新源码/namespace，network none/read-only/pull never，host/LF/base/runtime一致 | 非语义/恶意probe attestation |
| 已完成（有限范围） | paired caller输入与Parameters文档 | 两共享keyword typed SHA一致；文档源行/SHA/base核验 | 训练对象unknown、API体未证明、期待仍需分支 |
| 已完成（有限范围） | 行为资格分支与反例 | 16专项、四缓存完整核算，1子义务支持/3假设 | 全issue trusted0，不回填旧评分 |
| 已完成 | Engine恢复后的resume-only执行 | 原source/probe/failure SHA绑定，旧版实际导入及rc0 | 原v1/新resume均不可重跑 |
| 已完成（有限范围） | 统一Controller基础接线 | 11专项、实际inner hook、两类真实正常正例、adapter freeze | 未宣称完整method或可信成果 |
| 已完成（有限范围） | 真实selected-candidate分支 | 新零调用身份引用v1 SHA，normal×2/target×2、真实observer/qualification/子义务 | 仅合成fixture，不算真实task |
| 已完成（有限范围） | scope动作gate/精确定义/DEV trial freeze | scope15专项/实际正负链、独立预算/源身份 | 未称完整公开意图/repair过关 |
| 已完成（有限范围） | metadata反馈投影修复 | 10专项/实际原失败Human roundtrip，原边界不改 | 不自动retry旧paid |
| 已完成 | resume-only/新seal/独立Gold | 原109文件不变、账本保留旧6事件前缀、255新产物seal | 执行完成不等于质量通过 |
| 已完成（零调用shadow） | pre-observer program依赖反馈 | Schema建议三反馈恢复、unknown/reject不提升 | 尚未接新live |
| 已完成（有限范围） | 自动补证/合理context预算/新DEV | 2实际源码读取/next view、输入和成本分层、80k批次封存 | source取得不等于模型产物有效 |
| 已完成 | 去示例值policy+closed codec实链、小额真实输出 | 三阶段真实JSON/Python、内层hook及实际容器反馈 | 非任务通过，旧namespace禁止重跑 |
| 已完成（有限范围） | source-frontier正常绑定保护与live补源 | receiver丢失执行前拒绝；Schema next prompt SHA与账本一致 | 不证明fixture意图/剩余行为 |
| 已完成（有限范围） | 环境反馈/接口请求/模块函数检索实链 | matching条件到真实next请求，有限候选及独立Gold，两个来源runtime过 | fixture/异常链/版本资格仍未知 |
| 已完成（有限范围） | 属性依赖/异常路径/fixture分层Controller零模型 | 公开内层异常对应true，scope/export/object到Human，原unknown不改 | 新zero目录不重跑，不是新生成/完整可信 |
| 已完成 | 公开release-source counterfactual | 同probe/镜像/optional条件、实际版本/路径/源SHA及normal×2/target×2通过 | 新namespace已运行勿重跑，发行包不冒充canonical Git |
| 已完成（零调用） | 用户选择三组路线、边界/预算/真实输入freeze | 固定base测试独立通道，三组无Gold/新评分测试输入 | 不改变旧strict结果 |
| 已完成 | 首轮旧DEV三cell修复/零调用覆盖诊断 | 3calls/15,764；真实official/公开原probe/21变体分账 | 原0/3不回填，不把11/21作修复率 |
| 已完成 | 新v2公开反例辅助修复 | 3calls/20,385，原0/3，payload/ledger/seal保留 | 未达质量，不扩canary，不best-of |
| 1 | Flash thinking同strict输入单请求诊断 | 新精确授权，≤1call/30k含推理，生成8k，实际wire guard→seal→official | 无修改/局部/截断封存，不自动扩大预算 |
| 1b | 公开自验证→限次修正闭环 | 自产失败trace/补源真正作为下一次反馈；全部方法/费用冻结 | 不回传官方答案，不继续同模板盲试 |
| 2 | 从issue开始的两来源DEV完整链 | 同一自动定位/probe/判别/patch方法，三组生产窗口获取一致，全部成本记账 | 缓存首轮不推广成端到端/正式组效应 |
| 3 | 同版完整九准入DEV/native | 条件机制/完整可信/official resolved分账，固定12，比较成本 | 局部机制/工程数不作修复率 |
| 4 | 完整方法/预算冻结，新不重叠canary一次 | 全历史排除，严格可信≥2/3及独立修复门槛 | 负结果封存回DEV，不能重称独立 |
| 5 | 旧DEV30→另授权Fresh30→E2 | 单一冻结身份逐题resolved及开TEST授权 | 不保证30/30，不回调Fresh30 |

下一轮thinking精确命令在新协议：Flash/1call/30k含推理，retry0不Pro，preflight完成但paid0，须新精确授权。原v1/v2/三个zero或其他started namespace不恢复、不改源/协议/结果。不抽第6批，不开TEST/Fresh30/E2。

## 5. 时间与停止条件

[原一周计划](research/E1C2_ONE_WEEK_PLAN_2026-09-30.md)保留为历史预注册；当前执行以三组新协议为准。历史Gold4/4与1复用候选不属于本轮。先做三cell修复接线，再从issue开始两来源完整链与同版DEV质量验收；不能保证一周/30题全过，未过不抽新独立任务。

## 6. WebCodex与本机安全

云端可接源码、无模型单测和脱敏摘要，使用uv.lock；exact-base源码/镜像/私有.codex/凭证不会随Git同步。缺材料明确INFRA_BLOCKED；[接手说明](research/NEXT_SESSION_HANDOFF.md)给出安全检查命令。旧bridge白名单未扩，不假称新paid入口云端端到端已验证，不开裸Docker daemon。

本轮未下载/删除镜像或重启Docker，未改IPC/VHD/registry/proxy/tunnel/密钥。全部实验负结果和备份保留。sealed TEST/C5/Fresh30/SERBench私有Test500/E2仍关闭；新旧DEV修复权限只适用于上述另立协议，不回填旧资格。

## 7. 更新纪律

本页只维护最新状态和可执行待办，逐轮日志只追加集中续档。此前本页及交接页的多份“当前/最新”快照已原文移入2026-10-07集中归档，Git历史也保留；不要按归档旧命令操作。原协议、结果、预算、response/state/ledger/seal均不回填。
