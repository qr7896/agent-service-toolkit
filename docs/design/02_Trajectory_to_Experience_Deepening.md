# Trajectory → Experience：把已有 Memory 做深

> 本文严格以当前 `PROGRESS(1).md` 的已有实现为基础，把已经完成的 Trajectory → Experience → Retrieval → Self-Correction 继续向“可审计、可归因、可验证、可失效”的方向深化。

---

# 1. 当前项目已经做到什么

项目已经形成：

```text
Coding Task
   ↓
Trajectory
   ↓
Experience Memory
   ↓
Experience Retrieval
   ↓
Planner / Debugger
   ↓
Self-Correction
```

当前实现的关键原则非常清楚：

1. Experience 只能从真实 trajectory 派生，不采信模型自述。
2. Experience 记录成功、失败类型、工具、改动路径、测试和 Reviewer 结果。
3. 经验通过 `trajectory_id` 回链到原始执行证据。
4. 轨迹和经验都有脱敏约束。
5. Retrieval 使用本地 BGE-M3 + Chroma。
6. Planning 阶段和 Debug 阶段都可以使用 Experience。
7. 如果没有命中，原有行为保持不变。

这些内容已经在 `PROGRESS(1).md` §4.15–§4.18 中形成比较完整的闭环。

---

# 2. 目前最值得深化的问题

当前 Experience 的本质还是：

```text
过去任务
→
结构化经验
→
相似任务检索
```

真正更深的问题是：

> **一条历史轨迹中，究竟是哪一个决策、哪一种证据、哪一次工具调用、哪一个修复动作导致任务从失败变成功？**

如果回答不了这个问题，Experience 很容易退化成：

```text
“以前这个问题最后这么改了。”
```

而不是：

```text
“在相同的失败条件下，这个决策经过什么证据支持，为什么成功，适用于什么范围，什么时候不应该复用。”
```

---

# 3. 从“Memory Record”升级成“Evidence-Linked Experience”

建议第二版 Experience 不再只是文本记录，而变成一个结构对象：

```json
{
  "trajectory_id": "...",
  "task": "fix FastAPI route registration",

  "task_signature": {
    "domain": "fastapi",
    "issue_type": "bug_fix",
    "operation": "route_registration",
    "language": "python"
  },

  "phase": "debug",
  "outcome": "accepted",
  "failure_type": null,

  "evidence": {
    "code_symbols": [],
    "files": [],
    "error_signature": "...",
    "tests": [],
    "review": {}
  },

  "actions": [
    {
      "action": "edit_file",
      "path": "...",
      "reason": "...",
      "result": "..."
    }
  ],

  "verification": {
    "tests_passed": true,
    "review_approved": true
  },

  "reuse_constraints": [],
  "source": "trajectory"
}
```

核心变化：

> Experience 不再只是“结果”，而是“结果 + 证据 + 条件 + 来源”。

---

# 4. 当前设计里已经存在的一个非常好的基础

现在项目明确规定：

```text
Model says “success”
        ↓
不可信

Trajectory evidence
        ↓
可信
```

例如：

```text
pytest = passed
Reviewer = approved
Approval = granted
Actual diff = expected
```

才可以形成 accepted Experience。

这是继续深化的最重要基础。

---

# 5. 深化一：把“成功经验”拆成可归因的决策片段

不要只保存：

```text
Task
Outcome
Changed paths
```

而要保存：

```text
Decision 1
  ↓
Evidence
  ↓
Action
  ↓
Observation

Decision 2
  ↓
Evidence
  ↓
Action
  ↓
Observation
```

也就是：

```text
Trajectory
   ↓
Decision Episodes
   ↓
Experience Units
```

例如：

```text
观察：pytest 报 route 404
↓
决策：查 route registration
↓
工具：search_code
↓
发现：router 未 include
↓
动作：edit_file
↓
验证：pytest passed
```

这样未来可以检索：

> “遇到 404 时，什么观察 → 什么动作 → 什么结果？”

而不是只检索：

> “以前 404 最后改了什么文件？”

---

# 6. 深化二：Experience 必须绑定“适用条件”

一条 Experience 不能直接说：

> “以后照做。”

应该同时保存：

```text
Applicable When
Not Applicable When
Confidence
```

例如：

```yaml
experience:
  strategy: include_missing_router
  applicable_when:
    - FastAPI
    - route returns 404
    - route definition exists
    - router import exists
  not_applicable_when:
    - reverse proxy returns 404
    - route is dynamically generated
  confidence: 0.78
```

这样 Experience 就开始具有“条件化知识”的性质。

---

# 7. 深化三：把失败经验升级成“禁行路线”

当前项目已经区分：

```text
accepted
rejected
approval_denied
test_failed
review_rejected
unknown_failure
```

下一步不应该只告诉模型：

> “以前失败过。”

而要告诉：

```text
不要再走这条路
↓
因为哪一个前提不成立
↓
当时在哪一步失败
↓
后来采用什么替代路线
```

例如：

```text
Rejected Route

strategy:
  rewrite entire file

failure:
  introduced unrelated changes

replacement:
  minimal edit_file anchored by old_text/new_text
```

这种 Experience 对 Debugger 的价值比普通成功案例更高。

---

# 8. 深化四：把 Experience Retrieval 从“相似度”升级为“相似度 + 证据兼容性”

当前项目已经发现一个重要现象：

> embedding 中加入太多重复 metadata 会稀释任务语义，因此当前只把任务文本作为 embedding 主体，把结果、文件和步骤保留在 metadata。

这已经是很好的 ablation 结果。

下一阶段不应该直接继续加字段，而可以把检索分成两层：

```text
Stage 1
Semantic Similarity
        ↓
Candidate Memories

Stage 2
Evidence Compatibility
        ↓
Final Memories
```

第二层可以检查：

```text
repository compatibility
language compatibility
framework compatibility
failure type compatibility
phase compatibility
changed-symbol compatibility
verification compatibility
```

最终不是：

```text
score = embedding_similarity
```

而是：

```text
score =
    semantic_similarity
    × compatibility
    × evidence_quality
    × outcome_reliability
```

这里先做确定性加权，不要急着上学习模型。

---

# 9. 深化五：CodeGraph 让 Experience 有“代码锚点”

这是后续最值得做的一步。

当前 Experience 有：

```text
changed_paths
```

但“文件路径”还是比较粗。

可以升级为：

```text
changed_symbols
callers
callees
impact_nodes
related_tests
```

于是：

```text
Experience
   ↓
CodeGraph Nodes
```

例如：

```text
Experience #183

Task:
fix token validation

Target symbol:
validate_token

Callers:
AuthMiddleware
SessionService

Related test:
test_expired_token

Outcome:
accepted
```

这样下次 Agent 不是只问：

> “有没有类似任务？”

而是可以问：

> “过去哪些经验发生在与当前修改目标结构相近的代码区域？”

这会比单纯 vector memory 更深。

---

# 10. 深化六：Memory 应该知道“什么时候不要用自己”

这一点非常重要。

当前项目已有：

```text
没有命中
→ 不影响原行为
```

下一步应该升级成：

```text
命中
↓
可信？
↓
兼容？
↓
新鲜？
↓
证据足够？
↓
才允许注入
```

也就是说：

> **Memory Retrieval 也应该支持 Abstention。**

不要把“找到一条相似经验”理解成“应该使用它”。

---

# 11. 深化七：加入 Experience Freshness

Code 会变化。

一个过去成功的经验可能属于：

```text
commit A
```

而当前代码已经变成：

```text
commit Z
```

所以 Experience 应该记录：

```text
repo_version
commit_hash
code_symbols
framework_version
```

然后判断：

```text
结构仍相似？
调用关系仍相似？
相关测试仍存在？
```

再决定是否复用。

---

# 12. 深化八：Experience 不只是“成功率”，还可以学习“探索效率”

当前项目的 Benchmark 已经记录：

- attempts
- tool calls
- time
- success
- experience hits

下一步可以定义：

```text
Experience Efficiency
=
在保持成功率的前提下
减少多少探索动作
```

例如：

```text
Memory A
→ 以前平均 27 tool calls
→ 当前任务 18 tool calls
→ outcome accepted
```

那么经验的价值不是简单：

> “帮 Agent 做对了。”

而是：

> **“帮助 Agent 少走了 9 步。”**

---

# 13. 深化九：做 Experience Credit Assignment

这是可以进一步研究的方向。

一个任务可能：

```text
20 个工具调用
3 次错误
2 次修改
1 次成功
```

那么最后成功并不能证明：

> 第 7 次工具调用有用。

需要给 action 做 credit assignment：

```text
Action
↓
Immediate Observation
↓
Later Recovery
↓
Final Outcome
```

第一版甚至不用 RL。

可以先做规则式归因：

```text
某 action 后
↓
error disappeared
↓
next test passed
```

将其记录为：

```text
likely_effective = true
```

而不是把所有轨迹平均成一段总结。

---

# 14. 深化十：把 Trajectory → Experience → Evaluation 连起来

最终形成：

```text
Trajectory
    ↓
Candidate Experience
    ↓
Experience Retrieval
    ↓
Future Task
    ↓
Evaluation
    ↓
Did this Experience help?
    ↓
Experience utility update
```

这样 Experience 才真正形成闭环。

可以为每条经验维护：

```text
retrieval_count
used_count
helped_count
harmful_count
ignored_count
```

最终：

```text
Experience Utility
=
helped_count / used_count
```

但必须做时间切分 / held-out evaluation，避免同任务泄漏。

---

# 15. 与当前 Benchmark 的直接连接

当前 benchmark n=3 的结果是：

| 指标 | Baseline | +Experience |
|---|---:|---:|
| 独立判分通过率 | 1.000 | 1.000 |
| 首次通过率 | 0.667 | 0.333 |
| 平均 attempts | 1.33 | 1.67 |
| 平均工具调用 | 27.0 | 23.0 |
| 平均耗时 | 103.7s | 64.2s |
| 命中经验的运行数 | 0/3 | 3/3 |

当前正确结论应该仍然是：

> 经验链路确实被触发，工具调用和耗时出现方向性下降，但 n=3、任务简单，而且首次通过率和 attempts 并没有改善，因此不能宣称“Experience 已经被证明有效”。

这是下一阶段实验设计的出发点，而不是需要隐藏的结果。

---

# 16. 下一版 Experience Benchmark

建议至少做到：

```text
30–50 real coding tasks
```

最好固定：

```text
same task set
same model
same prompt
same base commit
same sandbox
same evaluator
```

仅改变：

```text
Experience Retrieval
```

再记录：

- Task Success Rate
- First-Try Success Rate
- Average Attempts
- Tool Calls
- Files Read
- Context Tokens
- Time
- Test Pass Rate
- Reviewer Rejection
- Human Intervention
- Experience Hit Rate
- Experience Helpful Rate
- Harmful Memory Rate

---

# 17. 一个真正值得研究的 Memory 问题

不要问：

> “Experience Memory 能不能提升成功率？”

这个问题太大。

改成：

> **“什么时候过去的 coding trajectory 是可复用证据，而不是相似但危险的噪声？”**

再继续拆：

```text
Semantic similarity
        ↓
Code-structure compatibility
        ↓
Failure compatibility
        ↓
Repository/version compatibility
        ↓
Evidence quality
        ↓
Outcome reliability
        ↓
Use / Abstain
```

这就从普通 Memory 变成了：

> **Evidence-aware Experience Retrieval**

---

# 18. 与现有研究的关系

这个方向已经有明显相邻研究，因此不能把“Trajectory → Experience”本身称为原创。

例如 2026 年已有研究提出从 Agent trajectory 自动抽取 actionable learning 并进行 contextual retrieval；另有 PMCoder 将 planning 与 episodic memory 双向耦合，并用于 SWE-bench Verified。还有工作研究“是否应该使用某条 memory”的 risk-sensitive abstention。

因此真正可以作为你自己的研究问题的是：

> **在 repository-level coding agent 中，把 Experience 与具体代码结构、验证证据、版本条件绑定，并让 Memory Retrieval 具备 evidence compatibility 与 abstention。**

相关研究：

- Trajectory-Informed Memory Generation：<https://arxiv.org/abs/2603.10600>
- PMCoder：<https://arxiv.org/abs/2608.06811>
- Risk-Sensitive Contextual Bandits for Memory Retrieval：<https://arxiv.org/abs/2604.27283>

---

# 19. 最终目标架构

```text
                Real Coding Task
                       ↓
                 CodeGraph
                       ↓
                  Planner
                       ↓
                 Executor
                       ↓
              Test / Reviewer
                       ↓
                  Trajectory
                       ↓
        ┌──────────────┴──────────────┐
        ↓                             ↓
 Evidence Extraction           Evaluation
        ↓                             ↓
 Experience Store ─────────────→ Utility Update
        ↓
 Evidence-aware Retrieval
        ↓
 Next Task
```

真正的目标不是“记住更多”，而是：

> **记住经过验证、与当前代码结构兼容、具有明确适用条件的经验，并且允许系统在不确定时选择不用这条经验。**
