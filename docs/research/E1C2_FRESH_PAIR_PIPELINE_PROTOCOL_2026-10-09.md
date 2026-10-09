# 两来源issue-first完整执行链 DEV v1 预注册

日期：2026-10-09。新身份`e1c2-fresh-pair-repair-dev-v1`，原两个frozen library reference为旧DEV，不抽canary。前次一个缓存窗口/自身probe辅助的模型patch官方成功保留，不作为本次新生成。当前仅实现/零调用freeze，真实效果待测。

## 输入与源身份

仅使用已从公开issue重新检索及公开限定名补证的两份source artifact，先核验物理SHA，再逐window核验host SHA/LF==exact-base blob、声明slice（原连续窗口5000chars、AST窗口2500chars cap保持）。排除benchmark/examples，只保留library production；通用已暴露函数加载global补证，最多4/16行/1MB，条件重赋值上下文与非runtime证书保持。

新增canonical输入删除旧补证artifact继承的parent input_sha，重新计算完整issue/windows/candidate paths身份；真正调用前public boundary和messages审计，不能把旧ID作为新body身份。没有旧probe/modelpatch/official日志/Gold/测试断言进入actor，task-ID仅metadata/ledger，不用于文件表或模型提示。依赖缺失只由公开原文与当前production imports推断；不是借旧环境receipt猜题。

## 实际流水线

1. 每来源一次Flash生成JSON `normal_source / target_source / issue_quote`，必须公开原文quote、每程序≤6000chars、独立生产API/行为assert；来源没有数据时fixture是模型合成假设，不称作者数据。
2. 复用strict AST/import/动态与I/O/测试路径限制，拒绝常量assert与相同normal/target。离线容器运行normal两次和target两次；source/timeout/transport/patch基础设施错误停止，不包装软件故障。
3. normal全部rc0、target两rc1、日志SHA一致且无明显Name/Import/Syntax setup错误，才是**operational_pair_valid**。它非完整公开意图/忠实性证明，full_issue_trusted维持false；不能以此直接打开canary。
4. 仅满足该门槛才第二次Flash修复，输入同public source+新自产probe与执行反馈，最终request.json先保存/hash后调用。最多四生产exact edits，old必须暴露且base唯一、AST校验；不改probe/assert/tests，不安装依赖。无改动标abstain。
5. 新patch在两个相同原probe上各两次自验证；只写隔离容器层，host全部只读、network none/pull never。自验证完成/失败分别记录，不把失败转成真语义证书。
6. **两个来源所有model请求/产物/执行记录全部generation seal后**才独立official grader读取private材料/运行候选；必备两个来源input/generation/首次request/response、freeze/start/ledger，拒绝缺项、越界路径和SHA变更。不反馈分数/隐藏断言到模型。明确F2P/P2P/源身份/日志/rc，fixed tasks=2按真实rows，不沿用旧三组常量。

这是flat runner，函数接受明确view/row/root，不在执行过程中猴子补丁全局OUT/preflight来变更输入来源。旧frozen模块全部未改；复用的纯parser/budget/container/official parser有源码SHA绑定。

## 单一整批预算

模型全部`deepseek-flash`，enabled/high/no-tools，SDK retry0，HTTP300秒（probe90、official900保持）。整批最多4requests/100,000 provider tokens，**含推理**；每library最多2requests/50k。原8k/24k trial不恢复或加额度。

每call生成上限在16k..20k内，由 `min(20k, task50k - actual completed usage - ceil(prompt estimate×1.4))` 冻结规则选择；余量不足16k则不调用，不削到8k或自动加预算。完整产物需要推理room，20k基于既有14,132 generated完成观察，不保证足够。先第一library时整批可用cap50k以全额保留下一library50k；第二library用100k，所有调用账本共同约束。门槛不满足/截断/invalid/abstain按固定2分母记录，单来源剩余费用不无限再试。SDK/network/usage ambiguous停止全batch，不能跨namespace自动retry。

```powershell
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_fresh_pair_pipeline preflight
```

新精确付费命令须用户确认（目前未调用模型）：

```powershell
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_fresh_pair_pipeline run
```

条件pair、postpatch自身表现、official resolved分别计；两已见来源非独立泛化。此method完成≠复现质量完成，不把normal/target稳定当完整信任。后续真实通过两来源后才固定12/九准入、全方法freeze、全历史排除新canary；另授权Fresh30/E2。不保证30/30/一周完美，不改Docker/IPC/VHD/proxy/tunnel/key或下载删除。
