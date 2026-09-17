# EGCP：Evidence-Gated CodeGraph Planner

> **定位**：这是在当前 `agent-service-toolkit` / Coding Agent 基础上提出的一个“候选原创算法”，目标不是声称已经证明学术新颖，而是形成一个**可以真实实现、可以做消融、可以被数据证伪**的研究型 Agent Algorithm。
>
> 核心问题：**Coding Agent 什么时候“已经看够了代码”，什么时候应该继续检索，什么时候应该停止探索并开始修改？**

---

## 1. 为什么现在值得提出一个新的 Planner Algorithm

当前项目已经具备：

- `search_code`
- `read_file` / `list_files`
- Planning
- `run_tests`
- Debug / Self-Correction
- Reviewer
- HITL
- Trajectory
- Experience Memory / Retrieval
- Workspace Sandbox
- Cost tracking

现有 `search_code` 已经做过一个受控实验：同模型、同提示词、同任务下，引入 `search_code` 后，工具调用从 12 次降到 7 次，读取文件从 9 个降到 4 个，耗时从 17.1s 降到 14.2s；答案质量没有下降。该实验还指出，主要收益并不只是运行时间，而是减少无关上下文、让定位结果可复核。依据：`PROGRESS(1).md` §4.7。

因此下一步最自然的问题不是“再加一个搜索工具”，而是：

> **Agent 能不能根据任务需要，动态决定下一步应该获取哪一种证据，而不是盲目继续搜索？**

---

# 2. 算法名称

## Evidence-Gated CodeGraph Planner（EGCP）

中文：

> **证据门控式代码图规划器**

核心思想：

> **不是让 Planner 只生成“要做什么”，而是让 Planner 同时维护“每一个计划步骤目前掌握了什么证据、还缺什么证据”。只有关键证据满足门槛，步骤才能进入修改阶段。**

---

# 3. 现有方案的缺口

典型 Coding Agent：

```text
User Task
   ↓
LLM Plan
   ↓
Search / Read
   ↓
Edit
   ↓
Test
```

问题是：

- Planner 很容易认为“我大概理解了”。
- Search 很容易变成继续搜。
- Read 很容易变成继续读。
- 有时目标文件找到了，但不知道调用方。
- 有时知道调用方，却没有找到验证测试。
- 有时知道修改点，却不知道改动影响范围。
- 最终 Agent 可能“证据不足但仍然开始写”。

因此 EGCP 不把“是否继续检索”交给 LLM 的主观感觉，而是显式维护 Evidence State。

---

# 4. Evidence State：把“理解程度”变成可计算对象

对每一个计划步骤维护三个核心证据维度：

```text
Target Evidence
    ↓
我是否知道“具体改哪里”？

Impact Evidence
    ↓
我是否知道“改这里会影响什么”？

Verification Evidence
    ↓
我是否知道“改完怎么证明它对”？
```

可以表示为：

```python
EvidenceState = {
    "target": 0.0,
    "impact": 0.0,
    "verification": 0.0,
    "risk": 0.0,
    "queries_used": 0,
    "tokens_spent": 0,
}
```

例如：

```text
target       = 1.0
impact       = 0.4
verification = 0.0
```

意思是：

> 我已经知道应该改哪个函数，但还不知道它影响哪些调用方，也没有找到可靠的验证测试。

这时 Planner **不允许直接进入写阶段**。

---

# 5. CodeGraph 在这个算法里的作用

CodeGraph 当前已经提供结构化代码智能能力，例如：

- `symbol_search`
- `get_ai_context`
- `get_edit_context`
- `get_callers`
- `get_callees`
- `analyze_impact`
- `find_related_tests`

CodeGraph 官方当前推荐的典型流程也是先搜索符号、获取上下文、修改前分析影响、修改后查找相关测试。它本身已经解决“怎样获得结构化代码事实”的问题，所以本项目不重新实现 AST / Tree-sitter / Call Graph，而把 CodeGraph 作为外部 Code Intelligence Layer。来源：CodeGraph 官方仓库与 tool-calling guide。

这也是本算法的关键边界：

> **CodeGraph 负责产生证据，EGCP 负责决定“下一份证据是什么、什么时候证据足够”。**

---

# 6. Evidence Action Space

Planner 每一步不是只能选择“搜索”，而是从不同证据动作中选择一个：

```text
A1  symbol_search
A2  get_ai_context
A3  get_callers
A4  get_callees
A5  analyze_impact
A6  find_related_tests
A7  read_file
A8  search_code
A9  git_diff
A10 run_tests
A11 ask_clarification / abstain
```

不同动作补充不同证据维度。

例如：

```text
symbol_search
→ Target Evidence

get_callers / get_callees
→ Impact Evidence

analyze_impact
→ Impact Evidence

find_related_tests
→ Verification Evidence

run_tests
→ Verification Evidence
```

---

# 7. 核心：Evidence Utility

对于每一个候选动作 `a`，估计：

```text
Evidence Gain
        ↓
这一动作预计能减少多少“未解决证据缺口”

Cost
        ↓
token / tool call / time

Risk
        ↓
是否可能把 Agent 带向错误上下文
```

可以定义一个第一版启发式评分：

```text
Utility(a)
=
    ΔEvidenceCoverage(a)
    --------------------------------
    TokenCost(a) + λ × Risk(a) + μ × Latency(a)
```

然后每一轮选择 Utility 最高的证据动作。

---

# 8. 一个更重要的设计：Evidence Gate

Planner 不再是：

```text
Plan generated
→ Coder
```

而变成：

```text
Plan generated
      ↓
Evidence Audit
      ↓
┌──────────────────────┐
│ Target >= threshold? │
│ Impact >= threshold? │
│ Test known?           │
└──────────────────────┘
      │
  ┌───┴────┐
  │        │
 PASS     FAIL
  │        │
  ↓        ↓
Coder   Retrieve More
```

第一版可以采用简单阈值：

```text
target >= 0.8
impact >= 0.6
verification >= 0.6
```

但真正研究时不要固定死，而应通过验证集校准。

---

# 9. Evidence Card：让 Plan Step 自带证据

当前项目的 Planner 已经有：

```text
order
action
path
reason
verification
open_questions
```

下一版把它扩展成：

```json
{
  "order": 1,
  "action": "modify",
  "path": "src/auth/service.py",
  "reason": "fix token validation logic",

  "evidence": {
    "target_symbols": ["validate_token"],
    "callers": ["AuthMiddleware", "SessionService"],
    "impact_level": "medium",
    "related_tests": ["tests/test_auth.py::test_expired_token"],
    "impact_analysis": "3 direct callers, 1 related test"
  },

  "verification": [
    "tests/test_auth.py::test_expired_token",
    "tests/test_auth.py::test_valid_token"
  ]
}
```

这叫 **Evidence Card**。

它使计划从：

> “我觉得这里要改”

变成：

> “我要改这里，因为我找到了这些结构证据，并且知道这些测试可以验证它。”

---

# 10. 新增一个很关键的状态：Evidence Debt

这是本算法最值得尝试的概念之一。

如果 Agent 已经决定了一步：

```text
modify auth/service.py
```

但：

```text
affected callers 未确认
related tests 未确认
```

那么：

```text
Evidence Debt = 2
```

Planner 不能把这份“债”带入执行阶段。

只有：

```text
Evidence Debt = 0
```

才能自动进入写阶段。

---

# 11. 修改之后再进行一次 Evidence Reconciliation

EGCP 不只在修改前工作。

修改后比较：

```text
Prediction
    ↓
预计会影响哪些文件 / symbols / tests

vs

Observation
    ↓
真实 git diff
真实 tests
真实 reviewer
```

例如：

```text
Prediction:
只改 auth.py

Actual:
auth.py
utils.py
config.py
```

产生：

```text
Evidence Mismatch
```

然后强制：

```text
re-open retrieval
        ↓
重新分析 impact
        ↓
重新 reviewer
```

这会把当前项目已有的：

```text
CodeGraph
+
Diff
+
Test
+
Reviewer
+
Trajectory
```

真正连成一个算法闭环。

---

# 12. Abstention：证据不足时允许“不做”

这是非常重要的。

很多 Agent 的隐含逻辑是：

```text
不知道
→ 猜一个
→ 继续
```

EGCP 改成：

```text
不知道
↓
继续获取证据
↓
仍然不足
↓
ABSTAIN / ASK
```

例如：

```text
用户：把认证逻辑优化一下
```

如果 CodeGraph + search 后仍不能确定：

```text
修改哪一种认证逻辑？
性能？
安全？
代码结构？
```

则 Planner 应输出：

```text
open_questions != []
→ 不进入写阶段
```

你当前 Planner 已经有 `open_questions`，并且对模糊任务能够主动追问。这为 EGCP 提供了直接的接入点。

---

# 13. 算法伪代码

```python
def evidence_gated_plan(task):
    state = init_evidence_state(task)
    plan = draft_plan(task)

    while True:
        gaps = detect_evidence_gaps(plan, state)

        if not gaps:
            break

        candidates = generate_evidence_actions(
            task=task,
            plan=plan,
            gaps=gaps,
        )

        scored = []
        for action in candidates:
            gain = estimate_evidence_gain(action, gaps)
            cost = estimate_cost(action)
            risk = estimate_context_risk(action)

            utility = gain / (cost + LAMBDA * risk + EPS)
            scored.append((utility, action))

        best = max(scored)

        if best.utility < MIN_UTILITY:
            return Abstain(
                reason="evidence_insufficient",
                open_questions=extract_missing_evidence(gaps),
            )

        observation = execute_readonly(best.action)
        state = update_evidence_state(state, observation)
        plan = update_plan_with_evidence(plan, observation)

    return attach_evidence_cards(plan, state)
```

---

# 14. 为什么这不是简单的“CodeGraph + Planner”

因为研究变量不是“用了哪个工具”，而是：

```text
Planner 的检索停止策略
```

Baseline：

```text
LLM decides when to stop exploring
```

EGCP：

```text
Evidence Coverage
+
Utility per retrieval action
+
Evidence Gate
+
Abstention
+
Post-edit Evidence Reconciliation
```

真正比较的是：

```text
Naive Planner
vs
Fixed Retrieval Planner
vs
EGCP
```

---

# 15. 建议的实验

## Experiment A：Repository Exploration

任务：真实 GitHub issue。

比较：

```text
A: search_code + read_file
B: CodeGraph fixed workflow
C: EGCP dynamic evidence acquisition
```

指标：

- Gold-file Recall
- Files Read
- Tool Calls
- Context Tokens
- Time
- Wrong-file reads

---

## Experiment B：Modification Safety

比较：

```text
A: 普通 Planner
B: EGCP
```

指标：

- Wrong-file modification rate
- Out-of-scope modification rate
- Test pass rate
- Reviewer rejection rate
- Human approval rate

---

## Experiment C：Verification

比较：

```text
A: Planner 先改再找测试
B: EGCP 先找 verification evidence
```

指标：

- First-pass success
- Failed attempts
- Test discovery coverage
- Regression failures

---

# 16. 与当前已有 Progress 的对应关系

| 当前能力 | EGCP 如何复用 |
|---|---|
| `search_code` | Evidence action |
| `read_file` | Evidence action |
| Planner | 核心改造对象 |
| `run_tests` | Verification evidence |
| Reviewer | Post-edit evidence reconciliation |
| HITL | Evidence不足/高风险时的 human gate |
| Trajectory | 记录 evidence decision |
| Experience | 保存“什么证据组合对什么任务有效” |
| Sandbox | 安全执行空间 |
| CodeGraph | Structured evidence provider |

---

# 17. 当前方案的“候选原创点”在哪里

不要把原创点说成：

> “我发明了 CodeGraph。”

也不要说：

> “我发明了 Planner。”

候选贡献应该表述成：

> **把 Coding Agent 的 repository exploration 从“LLM 自由检索”重新建模为“证据覆盖驱动的主动证据获取问题”，并将 target / impact / verification 三类证据统一进入 Planner State，再用证据门控决定是否允许进入修改阶段。**

进一步的候选贡献：

> **修改后的真实 diff / test / review 结果可以反向检验修改前的 evidence prediction，并对 evidence mismatch 触发重新检索。**

这两个点可以形成一个闭环，而不是孤立 heuristic。

---

# 18. 必须诚实的“新颖性声明”

截至本设计文档生成时，已有工作已经覆盖相邻方向：

- Agent Retrieval Bench 将 repository context acquisition 单独作为 Coding Agent 的前置检索问题进行评测。它包含 427 个 retrieval samples，并测量 gold-file recall、budgeted context yield 等指标。
- Repository Intelligence Graph（RIG）已经研究确定性的 repository structure / build / test graph 如何帮助 Coding Agent。
- 2026 年的 PMCoder 已研究 planning 与 episodic memory 的双向耦合。
- CodeGraph 本身已经提供结构化代码图、impact analysis、related tests 等能力。

因此：

> **不能在没有系统 literature review 和实验之前声称 EGCP 是“世界上第一个”。**

正确说法是：

> “这是基于现有项目约束提出的候选算法假设，我计划通过受控消融实验验证它是否构成一个有价值、可复现的设计增量。”

相关研究：

- Agent Retrieval Bench：<https://arxiv.org/abs/2607.24882>
- RIG：<https://arxiv.org/abs/2601.10112>
- PMCoder：<https://arxiv.org/abs/2608.06811>
- CodeGraph：<https://github.com/codegraph-ai/CodeGraph>

---

# 19. 最推荐的最小实现范围

不要一次实现完整算法。

第一版只加：

```text
1. EvidenceState
2. EvidenceCard
3. CodeGraph read-only tools
4. EvidenceGate
5. open_questions / abstention
6. trajectory 记录 evidence decisions
```

先不要做：

```text
RL
复杂学习型 Router
微调模型
复杂 Skill Runtime
多 Agent 协同
```

先证明一个最核心的问题：

> **EGCP 能不能在不降低任务成功率的情况下，减少无关读取和无效探索？**

如果证明不了，就不要继续堆算法。
