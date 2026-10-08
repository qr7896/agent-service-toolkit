# E1C2：环境反馈与模块函数检索，实链结果与下一道门槛

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent；Origin Mode: run。
- 日期：2026-10-08；状态：两新版本 completed/sealed/独立Gold完成；可信与修复门槛未过。
- 材料：两个固定旧DEV来源，生成只看公开issue、exact-base生产源、自身offline反馈。Gold仅生成封存后的独立评分，未输入模型。
- [脱敏收据及SHA](../../data/e1c_evaluation_2_environment_module_results.json)；父版[协议链结果](E1C2_PROTOCOL_EXECUTION_RESULTS_2026-10-08.md)保持，不能混算成绩。

## 1. 本轮结果

| 版本 | calls / provider tokens | 两条终局 | 独立评分 |
|---|---:|---|---|
| 环境反馈 + interface解释 | 4 / 16,647 | 一个新Boolean keyword有限候选；另一条3次零匹配检索后停止 | 仅有限候选Gold消除1/1 |
| 模块函数检索修订 | 5 / 23,320 | 同一任务另一个新有限候选；另一条3调用上限停止 | 仅有限候选Gold消除1/1 |

新增总 **9 calls / 39,967 tokens**；每版max6call/40k、每题3call/24k、output2k、retry0、未来首请求保护，实际未突破；API事件全部started/completed成对，无含糊请求。两个候选来自**同一旧DEV任务的两个不同版本**，不能报两个任务通过、2/2修复或best-of系统成绩。固定DEV12/准入9/screen2；上一13/53708等账本独立保留。

Scikit-learn新probe实际normal两0/target两1，生产签名/源码/异常观察支持公开Boolean keyword接受子义务。Gold消除故障说明probe对补丁有区分性，**不是Agent写补丁或官方resolved**；默认值/增量/其他请求未验证，全issue trusted=false/repair=false/canary=false。

Marshmallow最新真实链：`utils.from_iso`查询由0匹配变为1生产定义，第二轮正常两0/target ValidationError两1，取得缺Schema；第三轮看到新增源码和执行器强制dateutil导入失败条件，再次生成保持公共fixture值/同quote/Oracle的probe。第三请求重组消息SHA与真实provider ledger吻合，实际有环境条件和Schema，输入原件没改。不能把这两次probe叫两个任务或完整可信。

## 2. 通用根因修复

- 环境事实从matching control1/control2/target记录经真实executor返回→compact feedback→Human；不猜自然卸载或guard值、不升级unknown。正负测试与父真实产物消息核验，gate SHA被新freeze绑定。
- 公开请求新增参数允许成为base target失败入口，受支持normal独立、shared setup不放缺陷配置；没有task-ID规则/人工挑文件。模型不再因base缺请求参数直接弃权。
- 原检索将任意`left.name`的left当class，导致module.function不可达。新适配保留旧class/plain逻辑，只在0结果且预算未耗尽时做裸symbol生产检索，筛选模块basename和顶层函数；是候选source hint，不授alias证书。最多两次原32MiB扫描、原3候选上限，测试路径拒绝。
- 模块版首次Ruff发现unused import；冻结前将实际检索/最终Human核验放入freeze后该导入用于保存gate。preflight调用捕获原函数避免递归；未付费重试或改任何已冻结源。

## 3. 当前真实门槛与下轮顺序

最新Marshmallow依赖缺口已由自动源码补齐；第三轮 `unexposed_dependency...`消失，剩下 `public_fixture_constraint_unproven`。公开Foo基类/DateTime短名没有显式import，静态alias的可能解释不能直接叫公开意图证明。异常资格还有exception_correspondence=false，Schema包装ValidationError没有完整确认报告的生产异常链；旧版本“曾能通过”仍只是报告，不能凭Gold消除认证。

**暂停增加同类付费请求，先完成以下零模型工作：**

1. 对最新真实probe、公共fixture事实和新增依赖，在同一Controller主链接既有reference scope/export/运行时对象观察；输出已证明身份、条件解释、未证明公共意图三层。错误alias/改值/假继承反例必须仍拒，未证明不得改True。不再只做旁路collector。
2. 扩展生产依赖绑定到实际qualified attribute/字段构造器，使用真实call/exception路径挑有界观察文件；证明异常因果对应或继续unknown，不能用Schema的类型名代替完整异常链。保持代码/quote/Oracle不改。
3. 仅对公开report中可识别的旧版本注册同probe、相同optional条件的版本对照；验证资源不存在则明确INFRA_BLOCKED、任何下载交用户直连，不猜旧版本通过、不把其他任务的witness挪来认证。
4. 检查验收器的范围限制：现有 gate 对有限候选故意full_issue_trusted/repair_eligible=false。必须补齐真实行为义务或明确提议新的受限验收协议；**不能为了进canary把常量改True、把有限资格改名完整可信**。
5. 同版两来源正负链真正过后，新完整method/预算freeze、小额DEV，再四参考/九准入；全历史排除新canary一次≥2/3通过后才Agent patch/official grade/DEV30/另授权Fresh30/E2。现在没有新canary或可重跑paid命令，不保证完美/30题全过。

## 4. 回归与安全

7新专项、重点28、最终environment/module12、Ruff及synthetic compact preflight ready；全套 **1660 passed / 4 skipped / 33 warnings，96.77秒**，XML SHA见收据。Cloud这些测试不需要私有素材，测试变更仅预冻结fixture自包含化，无削弱断言；不是修复率。

父201/255/54/11/39/52文件seal、新52/130产物与全部frozen source SHA核验保持。零模型message/source检查不重执行旧probe；两次Gold分目录隔离。无镜像下载/删除、Docker重启、IPC/VHD/注册表/代理/tunnel/key改变；raw/probe/Gold/凭证/负结果保留本机。canary/C5/TEST/Fresh30/privateTest500/repair/E2继续关闭。研究规范使版本/费用/负结果保全，最小改动规范使检索/执行器/预算被复用，没有新框架或依赖。
