# 第4批独立canary：0/3，负结果封存

## Material Passport

方法/预算2026-10-05先冻，执行2026-10-06结束；普通软件缺陷评测，固定分母3，未换题/后验调规则/重试。公开[结果JSON](../../data/e1c_evaluation_2_counterfactual_canary_v4_result.json)，原件`.codex/e1c/evaluation_2/counterfactual-canary-v4/`；仅公开issue/生产源码进入模型，Gold/测试只用于独立评分。

| 任务 | 官方准入 | 模型阶段 | 最终 |
|---|---|---|---|
| PVLib-1048 | Base/Gold均失败 | 0请求 | 旧生产代码np.Inf与官方镜像NumPy2不兼容，导入失败；不是模型失败 |
| SymPy-20131 | 双通过 | B因Point.vel关键窗口缺失弃答，未回退 | 无可信复现 |
| scikit-15535 | 双通过 | B/A均执行但base通过 | 没形成失败候选，不提交Gold判别 |

三张official-bound不可变image ID核验通过；6次离线官方准入，双通过2/3，失败仍占分母。两条准入任务按原方法自动生成四窗口并冻结live（现场最多4请求/60000tokens，首轮reserve13472）；精确`evals.e1c_evaluation_2_counterfactual_canary_v4 run`在已有单实验≤100000许可下调用Flash3次，实际5596tokens、无失败/重试。随后同入口gold：attempted0、gold_discriminating0。固定可信**0/3<2/3**，Agent repair/Fresh30/E2仍不能启动，不拿旧DEV4/12补本批。

工程核验：重点19passed/Ruff通过/V3规定preflight ready=true。第一次全仓1126passed/1failed/4skipped是原Streamlit8秒冷启动超时；原单项0.81秒通过，不改timeout/断言。第二次完整单次1127passed/4skipped/33warnings/0failed（83.42秒）。这些不是修复率，首次失败保留。

## 确认的通用瓶颈

scikit公共原文提供`np.random.choice(...).astype(object)`，旧围栏投影因相邻Python符号启发式删除该输入定义。模型收到的是未定义x，于是构造Unicode字符串数组，两次base通过。SymPy同样存在输入/观察调用丢失和符号重名/末端方法窗口不足。PVLib则是独立环境兼容问题；本批不私改依赖或添加np.Inf别名放行。

这只解释本批局限，不授权在已看canary补规则重算独立成绩。回旧DEV的下一版提取assertion-free public input facts（不执行/不保留断言或显示答案），并按导入/重导出/继承关系绑定末端API窗口；先在合成和旧DEV零调用验证，再另冻付费实验。新方法不能把真实输入类型变更伪装成“模型优化”。

## 原件与后续

method SHA88df1067d0770a74ebe6d72d7eee74b78c3135defd1659b97c7b444c5fbd21ea，identity SHA06d55d996a2f6786d8718340d24c8debd5e8c2a566897cf55c3b24e114f3a337不变。live freeze a8a9057a03c09905ef5397f12bc8051e08b2aa682cb9980cb91388216a6b43aa；state ac81f7a55ed3c884397ff4d759eb0c6100be06242345c6512dd75614fdb285b2；ledger22cbe8bbf72dff98c0ba7823ef8466fa386d808feb09cb3de6262d48fdf99bd7。

最早0调用transport receipt保留为封板时快照，不覆写；当前由结果JSON补充。自10月5日起已记录可见usage179080+本批5596=184676（包含旧SDK错误4281额外usage，非核账单）。未改Docker/tunnel/VHD配置、未清理镜像。下一独立canary须完整新方法先冻后选，不能复用本三题或直接打开Fresh30。
