# 受限运行反馈 v4：真实上一动作/观察与明确下一步请求

方法/选题/隔离/信息边界继承[v1](E1C2_BOUNDED_RUNTIME_DEV_V1_PROTOCOL_2026-10-07.md)，格式归一化与60000预算继承[v3](E1C2_BOUNDED_RUNTIME_DEV_V3_PROTOCOL_2026-10-07.md)。v3实际6请求13341tokens，无provider异常，各两步重复同一query停止，合法probe0/独立grader attempted0。两个query确实找到了生产定义、一个错误owner限定查无定义；此前仅把last_feedback嵌在每轮Human JSON，没有真实上一Assistant动作或明确轮次请求，不能说已充分实现成熟Agent的线性动作/观察历史。原v1/v2/v3代码、预算、smoke和所有负结果不改。

本版只补交互接线：从本新run自身上一轮response/feedback原件加入Assistant raw动作与Human不可信观察，最后显式告知turnN/4、检索已执行、不要重复query、选择probe/read/新symbol或弃答。复制真实原件，不补造模型动作或人工定位文件；查无qualified符号可改用plain符号的提示任务无关。真实source/初始issue/原三题选择规则不变。数据仍不升为System，追加历史经信息边界检查，完整conversation≤36000字符；原窗口/数据单体≤30000不变。不是完整debugger、不是Agent patch，也没有以Gold修输入/断言。

Flash≤12requests/每题4、整批60000/每题20000/输出2000、temp0/nonthinking/retry0，真实budgeted invoke同上限，方法freeze用实际conversation计算initial reserve。前两版付费共38317tokens，本版hard cap60000，因此本轮三个付费实验总上限98317tokens，不借预算，不开新任务。候选/semantic/control/Gate全部原口径；没有人工匹配修复文件，没有按task ID写分支。

另立`bounded-runtime-dev-v4`与`bounded-runtime-zero-smoke-v4`，先历史/观察单测、完整回归、两仓库真实合成smoke，再提交方法→freeze→先列精确run/模型/预算后按用户授权一次运行。合成fake模型与普通API fixtures只证明控制器动作，不能当实际任务成绩；v4真实历史注入另由单测覆盖。完成generation seal后独立grade；失败留存，不自动重试provider，不在已开始的目录补跑。若仍无有效候选，本轮停止付费扩批，回到零调用分析动作/检索/执行约束，不无限抽样。

```powershell
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_bounded_repro_dev_v4 smoke
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_bounded_repro_dev_v4 preflight
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_bounded_repro_dev_v4 run
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_bounded_repro_dev_v4 gold
```

screen3/原DEV12不是完整/独立score，原九题全版与四参考仍未验证。只有开发证据有收益才完整同版DEV，再另冻不重叠canary；≥2/3且行为一致才另冻Agent repair，随后同版对照与最终新任务一次性验证。TEST/C5/Fresh30/private Test500/E2继续关闭。
