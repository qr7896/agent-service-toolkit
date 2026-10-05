# Counterfactual fixture contract：机制证据与新生成实验

## Material Passport

2026-10-05；普通软件缺陷复现，原DEV12开发数据；非独立确认。零调用审计、完整旧缓存回放与新生成分别记账。生成不读公开测试断言/Gold；仅独立评分使用Gold。原三批canary均保持负结果封存；sealed TEST/C5/Fresh30未打开。机制协议见[原协议](E1C2_COUNTERFACTUAL_DEV_PROTOCOL_2026-10-05.md)，执行适配见[快速输入协议](E1C2_COUNTERFACTUAL_FAST_INPUT_2026-10-05.md)。

## 零调用证据

完整审计旧DEV v3九条B响应：1条可证明literal-container对照、5条unproven、3条弃答，分母仍12。可证明case的原control一个标签、target六个标签，同时改变类型和值/长度；新控制器只把control改成与target六元素逐字相同的list。生产源码已冻结SHA，raise guard位置自动提取（长度必须匹配模型特征数）；两次原base派生对照都明确报长度不一致，未调用target/Gold即能拒绝错误fixture。target/setup/assertion/oracle均未改，不追加手写答案。

随后完整hybrid-v1旧缓存另立counterfactual-replay-dev-v1回放：五个选定probe的SHA与原controller v2回放完全相同，四条参考仍Gold区分，generator候选仍Gold失败。**4/12仅是开发缓存结果**，非新生成或独立成绩；继承人工语义审核边界，机器trusted不回填。零调用gate见[data](../../data/e1c_evaluation_2_counterfactual_zero_gate.json)。不把五条unproven称为已通过静态证明。

## 安全/性能与工程验证

AST literal分析不执行eval/setup；未知计算、重赋值、mutation、遮蔽numpy导入、dtype参数、多因素变化保留unproven。合成负例覆盖错误值/长度、额外参数变化、mutation、待支持新参数；派生正对照失败后不允许A回退绕过。新API参数支持case不被硬套为类型转换。

新生成入口复用原DEV v3 frozen input逐字内容，并逐次重查源码/干净Git/exact-base/image ID，避免每次遍历所有文件重建同一索引。原慢入口与其零调用freeze保留、不覆写；新旧task records（输入SHA/image/reserve/environment）逐字相同，科学方法与预算未换。快入口frame SHA `394b8c08da35f52e49257912546162513ce1df5adc6f3d58a976cfc1fb3e3234`。

第一轮全仓与重负载回放并行时：1123passed/1failed/4skipped，Streamlit原8秒启动超时；任务结束后同一个测试0.76秒通过，未改超时/断言。串行全仓1124passed/4skipped/0failed（152.06秒），新增快输入两项SHA/脏目录负面测试后，全仓单次1126passed/4skipped/0failed（181.12秒）。新canary适配器另做专项回归与最终全仓，不把不同运行拼接成全绿。

## 新生成实验状态

快入口counterfactual-fast-dev-v1按冻结身份完成九题、固定12：13请求/26762tokens，deepseek-flash非thinking、temperature0，冻结最多18请求/每题2、输出3000、单题20000/整批80000、SDK重试0、首轮reserve62980。无provider失败/重试。五个base候选Gold四真一假，机器trusted仍0，叠加人工可观察行为审查为4/12；未将缓存成绩计入。

四条参考为ctor warm_start、export_text ndarray兼容、ISO-Z缺dateutil日期、内嵌DateTime字段；generator候选仍Gold失败。export_text为一个标签ndarray、匹配一列训练fixture，list正对照保留同元素/长度。base在参数校验拒绝ndarray，Gold后成功；符合公开issue陈述的array兼容行为，但不是原多标签示例同一truth-value错误位置，不能宣称完全重现原栈。语义范围从一开始是issue可观察行为，非字面相同traceback；这一限制明确保留，不包装成自动语义证明。

相较上一DEV v3：Gold/经审核覆盖3→4，请求12→13、tokens24712→26762（+2050，约+8.3%），不是省费结论；与旧v4同为4/12，不证明SOTA或因果增益。新生成四参考/跨两仓库已保持，且已在零调用证明可拒绝错误fixture，开发机制门槛满足，允许冻结下一独立canary；还没有独立泛化或Agent修复结果。

已执行唯一付费命令：`uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_counterfactual_fast_dev run`，沿用用户单实验≤100000许可，先列模型/次数/预算；随后同入口`gold`独立零调用判别。两者不得重跑。原慢入口始终只有零调用freeze，无第二份付费trial。原始ledger/state/响应在快入口目录，SHA见[公开结果](../../data/e1c_evaluation_2_counterfactual_dev_result.json)。本轮新增26762 tokens，累计本日可见usage179080（含旧SDK错误4281额外usage，非核账单），系列不是无限预算。

## 继续/停止边界

新生成须保留原四条参考、跨两仓库并分别报告成本/假阳性/弃答；未达则封存回DEV，不增加独立样本。通过也只能先完整冻结新方法/适配器后选不重叠canary，一次≥2/3，再另冻Agent repair对照；目前不能跳到repair/Fresh30/E2。literal对照是局部可执行证明，不是通用语义验证或已证明的新SOTA。
