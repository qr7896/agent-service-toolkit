# Roadmap 2：E1-C evaluation_2 当前状态与执行顺序

状态日期：2026-10-08。当前唯一执行入口；背景见[Roadmap 1](PROGRESS_RESEARCH_ROADMAP.md)，历史过程与旧页面原文见[集中续档](research/PROGRESS_LOG_ARCHIVE_2026-09-27_CONTINUATION.md)。

## 0. 最新结论

**最新状态：** 有限行为分支已校准：四缓存1显式bool keyword子义务支持、1比较假设、2回归假设，机器可信仍0（不是可信1/4）。旧版本对照已准备MM1359公开3.0.0rc8的11生产文件/152,704bytes，但Docker engine管道不存在、Desktop/backend未运行，准入前INFRA_BLOCKED，driver与probe均未执行。本轮provider/tokens0/0、Gold读取0，旧资格与Gold4/4/异常对应3/4不变。 [结果](research/E1C2_BEHAVIOR_VERSION_RESULTS_2026-10-08.md)、[公开收据](../data/e1c_evaluation_2_behavior_version_results.json)。

本轮新增22专项（behavior16、version6）；最终1541 passed/4 skipped/33warnings（104.58秒）、Ruff/预算V3重点41/合成preflight过。Git archive单次关闭自动换行后原字节严格等blob；不改全局Git，不回填旧实验，0镜像下载。

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
| 公开旧版本对照 | 3.0.0rc8本地祖先commit生产源152,704bytes已验证 | Docker准入失败，未执行，不计成功或故障失败 |
| 机器可信/Agent修复/E2 | machine0、新repair/official resolved未做 | 不报30/30，不开Fresh30 |

## 2. 当前瓶颈

检查器现在能组合已知公共fixture结构、production依赖、期待锚和异常证据，并拒绝明确改值/影射/对象改写。它只支持有限结构；状态/控制流/自定义行为、遗漏公共范围不认证。

行为分类器将显式请求、文档输入域证据、比较/回归假设分账，不因base文档缺新接口否定明确请求，也不将子义务自动认证全issue。当前运行硬阻塞是Docker应用/backend未运行；源码旧版准备未转成真实对照证据。先恢复Engine、另冻resume-only身份，只执行未开始probe。不要重跑version-witness v1或再次使用已消费IPC备份重启授权。

## 3. 严格验收定义

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
| 1（INFRA_BLOCKED） | 用户打开Docker，确认Engine running | 只读engine+immutable image准入；另冻resume-only身份 | 不改IPC/registry/VHD、不开旧namespace重跑 |
| 2 | 未执行公开旧版本probe及义务覆盖 | 同一原程序/明确旧版/生产blob/实际导入版本只读对照 | 失败/infra/不适用分账，不best-of |
| 3 | 跨repo正负例→完整method freeze | 资格scope/classifier/observer/双source身份与输入/预算先冻 | 不继续paid调提示 |
| 4 | 同版四参考/九准入DEV/native | Gold/受限候选/语义/原机制分别计，固定12 | screen不报全12 |
| 5 | 新不重叠canary一次 | 全历史排除，可信≥2/3且行为一致 | 负结果封存回DEV |
| 6 | Agent patch/独立official grade | 同预算小baseline/treatment修复证据 | 无收益不扩批 |
| 7 | 旧DEV30→另授权Fresh30→E2 | 单一冻结身份逐题resolved | 不保证30/30，不回调Fresh30 |

下一轮paid前先列精确命令/Flash/次数/≤100,000tokens，retry0不Pro。本轮provider0；资格v1/v2/v3与authority、scope proposal/reference-scope/export-chain各namespace以及所有已started的run/smoke/Gold/audit禁止重跑或改源/预算/账本。当前无新live/canary命令，不抽第6批，不开TEST/Fresh30/repair/E2。

## 5. 时间与停止条件

[原一周计划](research/E1C2_ONE_WEEK_PLAN_2026-09-30.md)保留预注册。本轮新假设口径Gold恢复4/4且成本较前版30,477下降至21,400，但不能称隔离因果收益、严格原口径达标或一周/30题保证。可控交付是有边界的行为资格校准、完整freeze和一次同版DEV实证；未过不抽新独立任务。

## 6. WebCodex与本机安全

云端可接源码、无模型单测和脱敏摘要，使用uv.lock；exact-base源码/镜像/私有.codex/凭证不会随Git同步。缺材料明确INFRA_BLOCKED；[接手说明](research/NEXT_SESSION_HANDOFF.md)给出安全检查命令。旧bridge白名单未扩，不假称新paid入口云端端到端已验证，不开裸Docker daemon。

本轮未下载/删除镜像或重启Docker，未改IPC/VHD/registry/proxy/tunnel/密钥。全部实验负结果和备份保留。sealed TEST/C5/Fresh30/SERBench私有Test500/Agent repair/E2仍关闭。

## 7. 更新纪律

本页只维护最新状态和可执行待办，逐轮日志只追加集中续档。此前本页及交接页的多份“当前/最新”快照已原文移入2026-10-07集中归档，Git历史也保留；不要按归档旧命令操作。原协议、结果、预算、response/state/ledger/seal均不回填。
