# Flash thinking完整输出窗口与计数核验

日期：2026-10-09。原thinking单请求确实enabled/high，实际13,708tokens＝input5,708＋reasoning8,000；finish_reason=length、JSON content为空。无候选补丁或评分容器，因此修复效果未测，不称软件测试失败。原namespace/源码/response/ledger/seal/result不改，不自动retry。

## 零调用计数核验

原legacy grader写固定fixed_cells=3，但freeze/ledger/rows均只有一个strict cell。新`flash-thinking-cardinality-zero-v1`先核验原freeze/生成seal，再保存独立verified-result：以freeze与实际唯一rows核对fixed1、标原raw3不一致，不修改原raw，未重跑模型或评分。缺行、错arm/task、重复行全部拒绝。不是把错误元数据回填旧方法。

```powershell
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_thinking_completion_dev audit-previous
```

## 待授权的新单请求

身份`e1c2-flash-thinking-completion-dev-v2`，same strict prompt/mode high，仍Flash，不用Pro/no-tools。不加评分答案/新源码/提示词；只有生成额度/总预算/HTTP上限变化。生成max24,000（含reasoning与最终JSON），总provider max40,000含推理；最多1请求，retry0，HTTP300秒，原official900秒不变。reserve×1.4+24k须≤40k。

仅因8k截断准备更大窗口，不保证高思考或24k会修复；也不能称因果收益。若仍截断/无改动/局部则封存，**不自动继续扩到64k**，回旧DEV检查context/effort与公开自验证→限次修改流程。不能用前次30k已消费授权开始新身份。

```powershell
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_thinking_completion_dev preflight
```

新精确付费命令须用户确认：

```powershell
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_thinking_completion_dev run
```

实际SDK在HTTP前核验model/enabled/high/JSON/24k/no-tools；create明确timeout300，离线Mock核验HTTP body/timeout与reasoning用量。只存配置/推理token/存在标记，不保存或暴露正文。one-shot无tools，不需要回传reasoning正文。生成全部seal后才独立official；原raw评分保留，同时写freeze/rows核验过的verified-result，避免固定三组元数据误用。

共享准备仍为standard获取base对象，但只strict payload发送；严格模型无既有测试/新评分断言/Gold。该实验仍同一旧DEV诊断，非完整从issue全链或新独立任务；full issue trusted不提升。不开canary/TEST/Fresh30/E2，不改Docker/IPC/VHD/proxy/tunnel/key、不下载/删除。
