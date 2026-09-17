# Evidence-Guided Adaptive Code RAG（研究方案）

> 只写四件事：研究问题、假设、算法定义、评测协议。**不写论文**——先让代码和实验证明想法。
> 定位见 [RUNTIME.md](../RUNTIME.md)；实现进度见 [PROGRESS.md](../PROGRESS.md)。

## 1. Research Question

> **Coding Agent 在解决代码任务时，如何判断"当前证据已经够用"，以及"下一次检索是否值得"？**

- Q1 `sufficient(E_t, task, plan) -> bool`：当前证据是否足以支持计划步骤？
- Q2 `worth_more(E_t, action, budget) -> bool`：即使还不够，再取一次值不值得？

普通 RAG 把检索当成**一次性相关性排序**；这里把它当成**逐步获取证据的决策问题**。

## 2. Hypothesis

- **H1**：检索质量不只由"检索到什么"决定，也由"什么时候停止检索"决定。
- **H2**：在相同 token / context budget 下，按 Evidence State 动态选检索动作，比固定 Top-K / 固定工具链更有效。
- **H3**：把 lexical / semantic / structural / episodic 四类证据放进同一个 Evidence State 动态选择，能减少无效上下文。

目标不是"检索越多越好"，而是：**用最少的代码证据跨过任务所需的充分性阈值。**

## 3. Algorithm Definition

状态（`src/agents/evidence.py`）：

```text
EvidenceState = {target, impact, verification, redundancy, uncertainty, queries_used, tokens_spent, retrieval_round}
```

动作（`src/agents/retrieval_actions.py`）：每个动作声明它补哪一维、成本与风险，并能真的执行：

```text
lexical_search / symbol_search   -> target
get_callers / get_callees / analyze_impact / git_diff -> impact
find_related_tests / run_tests   -> verification
experience_retrieval             -> episodic（作为 prior，不直接算覆盖度）
```

策略（`src/agents/retrieval_policy.py`）：确定性规则，**不用 LLM 决定下一步搜什么**：

```text
候选 = 当前可用且还没试过的动作
utility(a) = 预期证据增益 / (成本 + λ×风险)
选 utility 最高者；没有可行动作 -> abstain
```

终止（`evidence.py`）：`sufficient()` 判够不够，`worth_more()` 判值不值，三类出口分开——
`evidence_insufficient` / `diminishing_returns` / `budget_exhausted`。

**当前边界（诚实标注）**：

- **语义代码检索尚未实现**：项目里的 BGE-M3 用于经验库与手册知识库，**不是**代码语义检索；
  `semantic` 这一类动作目前只有 episodic（经验）这一路，代码语义检索是待做项。
- `redundancy` / `uncertainty` 已进入状态**但还没进入决策公式**，只是被记录。
- 停止策略目前只有关键词式条件 + 轮数/预算上限，没有学习型策略（这是后期 V3）。

## 4. Evaluation Protocol

**数据**：SWE 风格任务（`evals/swe_tasks.py`），每个任务需要 Gold Evidence：

```json
{"gold_files": [], "gold_symbols": [], "gold_callers": [], "gold_tests": [], "gold_context": []}
```

来源优先级：① 本仓库真实修复历史（`scripts/make_repo_tasks.py`）② 真实 GitHub issue ③ 人工构造。
**顺序不能反**——人工构造很容易"为了证明算法而设计题目"。

**对照基线**（分批跑，不必一次全跑）：

```text
A Files Only   B lexical   C semantic   D CodeGraph   E Hybrid   F Adaptive   G Adaptive + Experience
```

**指标**（`evals/retrieval_metrics.py`）：Gold File / Symbol / Test Recall、Context Precision / Recall、
Context Tokens、Retrieval Rounds、Tool Calls、Latency、Redundancy、Abstention Rate、Final Success，
以及自定义的 **Evidence Efficiency = Gold Evidence Recall / Context Tokens**。

**实验顺序**：先 Retrieval Quality → 再固定 budget（2K/4K/8K/16K）→ 再 Adaptive Stop → 最后消融
（`-Coverage / -Uncertainty / -Redundancy / -Cost / -CodeGraph / -Experience`）。

**门槛**：先做探针门禁（`evals/coding_benchmark.py --probe-only`）证明判分器有判别力；
难度校准（`calibration()`）发现各臂通过率全 0 或全 1 时必须先改题目，而不是继续比。

**V0 的通过条件**（只在满足时才进 V1）：在 ≥20 个任务上，要么"成功率持平但 context/token/工具调用更低"，
要么"同 token budget 下 gold evidence recall 更高"。

## 冻结清单（研究模式的前提）

| 冻结 | 原因 |
|---|---|
| 继续加 Agent 类型 / Multi-Agent | 平台已够，边际价值不在功能数量 |
| 重做前端 | 该先把 retrieval trace / evidence state / rounds / cost / final context 记下来 |
| 训练 embedding | 没有证据说明是 BGE-M3 不够好，缺的是检索决策 |
| RL / 学习型策略 | 数据不够时做 RL，reward 不稳定且无法证明（留到 V3） |
