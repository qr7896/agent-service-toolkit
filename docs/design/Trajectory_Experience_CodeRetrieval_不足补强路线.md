# Trajectory / Experience + Code Retrieval / CodeGraph：不足补强路线

> 基于当前 `PROGRESS(2).md` 的真实进度整理。  
> 本文**不重新规划整个 Agent**，只处理当前两个最明显的不足：
>
> 1. **Trajectory / Experience：设计已经比较深入，但真实实验不足**
> 2. **Code Retrieval / CodeGraph：已经进入研究阶段，但证据不足**
>
> 核心目标：
>
> > 把“设计得很完整”进一步推进成“有真实任务、有对照、有失败案例、有可复现结论”。

---

# 1. 当前不足到底在哪里

## 1.1 Trajectory / Experience

当前已经具备：

```text
Trajectory
    ↓
Experience Memory
    ↓
BGE-M3 / Chroma Retrieval
    ↓
Planner 注入
    ↓
Debugger 注入
    ↓
Experience Compatibility
    ↓
Experience Abstention
    ↓
Usage / Helped / Harmful
    ↓
Utility / Decay / Survival
```

所以现在真正的问题已经不是：

> “经验库有没有做出来？”

而是：

> **这些机制在真实 Coding Task 上到底有没有帮助？**

当前已有的经验 Benchmark 只有 `n=3`，并且结果中：

- 两边独立最终通过率都是 1.0
- 首次通过率反而从 0.667 降到 0.333
- 平均 attempts 从 1.33 增加到 1.67
- 工具调用下降
- 时间下降

因此目前最多只能说明：

> **经验检索链路确实运行起来了，并观察到一些成本变化。**

不能说明：

> “Experience 一定提升 Coding Agent。”

这部分日志本身也明确把它标记为样本太小、不能下结论。

---

# 2. Trajectory / Experience 下一步真正缺什么

## 缺口 A：没有足够的“重复问题”

Experience 的价值本质上来自：

```text
旧任务
   ↓
沉淀经验
   ↓
新任务与旧任务存在结构/语义相似
   ↓
经验可能帮助新任务
```

如果 20 个任务都是互不相关的随机问题：

```text
Task A → Experience A
Task B → 与 A 完全不同
Task C → 与 A 完全不同
```

那么经验很难表现出价值。

所以数据集必须包含：

### 同类问题簇

例如：

```text
Endpoint 找不到
    ├── Task 01
    ├── Task 07
    └── Task 14

测试失败
    ├── Task 02
    ├── Task 08
    └── Task 19

调用链误判
    ├── Task 03
    ├── Task 11
    └── Task 17
```

这样才能真正测试：

> **经验能不能跨任务迁移。**

---

# 3. Trajectory / Experience 的核心实验

建议把问题拆成 4 个：

## Q1：经验有没有帮助？

```text
Baseline
vs
+ Experience
```

指标：

```text
Final Success
First-pass Success
Attempts
Tool Calls
Tokens
Latency
```

---

## Q2：什么样的经验有帮助？

比较：

```text
仅 task
task + result
task + changed_paths
task + evidence
task + applicable conditions
```

这一点你已经做过一个很重要的早期实验：

> 将重复文件路径、步骤等结构字段塞进 embedding text 会稀释任务语义。

所以现在应该继续往：

> **结构化 Experience**

发展，而不是继续往 embedding 文本里堆字段。

---

# 4. Experience 应该从“文本”升级成“Decision Episode”

你目前最值得继续深挖的不是：

> “经验文本写得更漂亮。”

而是：

> **记录一次 Coding Agent 为什么做出某个决策。**

例如：

```json
{
  "task": "endpoint returns 404",
  "state": {
    "target": "...",
    "impact": "...",
    "verification": "..."
  },
  "action": "search_code",
  "observation": "...",
  "decision": "inspect router",
  "result": "success",
  "changed_paths": [...]
}
```

这样 Experience 就不再只是：

```text
“这个问题以前怎么修过”
```

而是：

```text
“在什么状态下，
为什么选这个动作，
结果怎么样”
```

这和你的 Evidence State 天然能够接起来。

---

# 5. Experience 最值得做的深化方向

形成：

```text
Trajectory
    ↓
Decision Episode
    ↓
State → Action → Observation → Outcome
    ↓
Experience Memory
```

然后检索时不是只问：

```text
“哪个任务和我最像？”
```

而是：

```text
“我当前 Evidence State
和过去哪些成功决策状态最像？”
```

这会比普通 Experience Retrieval 更有研究味道。

---

# 6. 进一步：Experience 不应该直接告诉 Agent“怎么做”

应该让它成为：

> **Action Prior / Retrieval Prior**

例如：

```text
历史任务：
类似状态下，
70% 的成功轨迹先查 caller
30% 的成功轨迹先查 test
```

那么当前系统可以得到：

```text
caller_search: prior = 0.70
test_search:   prior = 0.30
```

但最终还要结合当前 Evidence State：

```text
Experience Prior
        +
Current Evidence
        +
Current Cost
        ↓
Next Retrieval Decision
```

这就把：

> Experience

和：

> Adaptive Code RAG

真正接起来了。

---

# 7. Code Retrieval / CodeGraph 当前真正缺什么

现在你已经有：

```text
search_code
BGE-M3
CodeGraph
symbol_search
get_callers
get_callees
analyze_impact
find_related_tests
Evidence Gate
```

而且已经实际跑过：

```text
A Files Only
B search_code
C CodeGraph
D CodeGraph + Evidence Gate
```

但实验样本非常小。

所以当前最大的缺口不是“再加工具”。

而是：

> **缺少一个足够大的、专门评价 Code Retrieval 的实验框架。**

---

# 8. Code Retrieval 第一优先级：建立 Gold Evidence

现在 Coding Task 已经有：

```text
problem_statement
base_commit
FAIL_TO_PASS
PASS_TO_PASS
```

还不够。

需要新增：

```json
{
  "gold_files": [],
  "gold_symbols": [],
  "gold_callers": [],
  "gold_callees": [],
  "gold_tests": [],
  "gold_context": []
}
```

---

# 9. Gold Evidence 为什么重要

因为最终成功率并不能告诉你：

> RAG 到底有没有找到正确代码。

可能出现：

```text
RAG 找错了
↓
LLM 自己猜对了
↓
pytest 通过
```

此时：

```text
Task Success = 1
```

但：

```text
Retrieval Quality = 差
```

所以需要把两个指标拆开：

```text
Retrieval Quality
+
Coding Success
```

---

# 10. Code Retrieval 要有独立指标

至少需要：

### File Recall

```text
找到 Gold File 的比例
```

### Symbol Recall

```text
找到 Gold Symbol 的比例
```

### Test Recall

```text
找到相关测试的比例
```

### Context Precision

```text
最终给模型的内容里，
真正有用的比例
```

### Context Recall

```text
Gold Evidence 被覆盖了多少
```

---

# 11. 最重要的一个新增指标

## Evidence Efficiency

建议自己定义：

```text
Evidence Efficiency
=
Gold Evidence Recall
/
Context Tokens
```

例如：

```text
方法 A：
Recall = 0.90
Tokens = 18K

方法 B：
Recall = 0.88
Tokens = 7K
```

即使最终成功率一样，

B 仍然体现出了：

> **更高的证据获取效率。**

这非常适合你的研究主线。

---

# 12. CodeGraph 不应该只是“另一个 Retriever”

这是接下来最值得修正的思路。

不要做：

```text
BGE-M3
+
CodeGraph
=
Hybrid RAG
```

然后结束。

这太普通。

应该研究：

```text
Semantic Retrieval
回答：
“哪些地方看起来相关？”

CodeGraph
回答：
“这些地方在代码结构上是什么关系？”

Experience
回答：
“以前类似状态下什么动作有用？”

Evidence Gate
回答：
“现在证据够不够？”

Adaptive Policy
回答：
“下一步该做什么？”
```

这样每一种检索手段承担不同职责。

---

# 13. 建议形成“4 类 Evidence Source”

```text
1. Lexical Evidence
   search_code

2. Semantic Evidence
   BGE-M3

3. Structural Evidence
   CodeGraph

4. Episodic Evidence
   Experience
```

然后统一进入：

```text
Evidence State
```

---

# 14. 这样 RAG 才真正和你现有系统合起来

最终：

```text
                         Task
                          ↓
                    Task Understanding
                          ↓
                    Evidence State
                          ↓
       ┌──────────────────┼──────────────────┐
       ↓                  ↓                  ↓
   Lexical             Semantic          Structural
 search_code            BGE-M3            CodeGraph
       │                  │                  │
       └──────────────────┼──────────────────┘
                          ↓
                    Evidence Fusion
                          ↓
                 Experience Retrieval
                          ↓
                    Evidence State
                          ↓
                    Is it enough?
                     /         \
                   YES         NO
                    ↓           ↓
                   STOP      Choose Action
                                  ↓
                            Retrieval Again
```

---

# 15. CodeGraph 当前还缺一个非常关键的实验

## “有结构信息”和“使用结构信息”不是一回事

你已经证明：

```text
CodeGraph 能返回结构信息
```

但还没有证明：

```text
Agent 能正确利用结构信息
```

所以应该做：

### Experiment A

```text
LLM + search_code
```

### Experiment B

```text
LLM + search_code + CodeGraph
```

### Experiment C

```text
LLM + search_code + CodeGraph
+ Evidence Gate
```

### Experiment D

```text
LLM + search_code + CodeGraph
+ Evidence Gate
+ Experience
```

真正要看的是：

```text
Retrieval Quality
+
Cost
+
Final Success
```

而不是只看最终回答。

---

# 16. 还要加入“干扰代码”实验

这是 Code Retrieval 很重要的一项。

人为或从真实仓库中寻找：

```text
同名 symbol
相似函数
相似 endpoint
相似测试
不同模块同名类
```

例如：

```text
src/api/user.py
src/admin/user.py
src/test/user.py
```

query：

```text
“修复 user endpoint 的权限问题”
```

检查：

> RAG 到底会不会把三个 `user` 全部找出来？

---

# 17. 这个实验特别适合你的研究

因为：

```text
Semantic Retrieval
```

很容易：

```text
“看起来很像”
```

而：

```text
CodeGraph
```

能够进一步告诉系统：

```text
哪个 symbol 真的是调用链上的
哪个只是名称相同
```

于是你的研究可以明确研究：

> **Semantic Relevance + Structural Relevance**

而不是单独比较 embedding。

---

# 18. 再增加“Version Shift”实验

你已经有：

```text
repo_commit
stale_experience
compatibility
```

所以可以测：

```text
旧 commit
   ↓
Experience
   ↓
新 commit
   ↓
还能不能正确使用？
```

比较：

```text
No version awareness
vs
Version-aware retrieval
```

这非常适合你已经写好的 Experience 机制。

---

# 19. Trajectory + CodeGraph 可以形成一个更深的方向

这是我认为你现在最值得继续挖的一块：

## Retrieval Trajectory

普通 RAG：

```text
query
 ↓
retrieve
 ↓
answer
```

你的 Coding Agent：

```text
Task
 ↓
search_code
 ↓
symbol_search
 ↓
caller_search
 ↓
related_test
 ↓
edit
 ↓
test
 ↓
debug
```

这其实已经是一条：

> **Retrieval Trajectory**

---

# 20. 研究的不只是“取到了什么”

而是：

> **为什么 Agent 先取 A，再取 B，再取 C？**

于是可以记录：

```json
{
  "round": 1,
  "evidence_state": {...},
  "action": "symbol_search",
  "gain": 0.42,
  "cost": 1200,
  "new_evidence": [...]
}
```

然后：

```json
{
  "round": 2,
  "evidence_state": {...},
  "action": "get_callers",
  "gain": 0.31,
  "cost": 800,
  "new_evidence": [...]
}
```

最后：

```text
round 3
gain = 0.03
cost = 1600
→ STOP
```

这会非常直接地支撑：

> **Adaptive Retrieval**

---

# 21. 这样 Trajectory 就不再只是日志

目前：

```text
Trajectory
=
记录发生了什么
```

下一阶段应该变成：

```text
Trajectory
=
记录“状态 → 检索动作 → 新证据 → 结果”
```

于是 Trajectory 本身成为：

> **研究数据集。**

这一步非常关键。

---

# 22. Experience 也随之升级

现在：

```text
Experience
=
历史任务摘要
```

可以逐渐升级成：

```text
Experience
=
历史 Retrieval Decision Episode
```

例如：

```text
当前状态：
target 已知
impact 未知
verification 已知

过去相似状态：
caller_search
→ 找到 3 个关键调用者
→ task success

所以：
caller_search 获得较高 prior
```

---

# 23. 最终形成闭环

你真正可以长期研究的是：

```text
Coding Task
      ↓
Evidence State
      ↓
Retrieval Action
      ↓
New Evidence
      ↓
Trajectory
      ↓
Outcome
      ↓
Experience
      ↓
Future Retrieval Prior
      ↓
下一次 Coding Task
```

这比：

```text
BGE-M3 → Chroma → Top-K
```

深很多。

---

# 24. 第一阶段：先补数据

目标：

```text
20 Tasks
```

但这 20 个任务要有：

```text
Gold Evidence
Retrieval Trajectory
Final Result
Cost
```

---

# 25. 第二阶段：补 Retrieval Trace

每一轮记录：

```text
task
round
current evidence state
action
retrieval result
new evidence
token cost
latency
gain
redundancy
next action
```

---

# 26. 第三阶段：补 Experience Evaluation

至少形成：

```text
Cold Start
vs
Experience Warm Start
```

并且：

> Experience 只能由训练/历史任务产生，测试任务严格留出。

你现在已经有 `--holdout` 的切分机制，这个基础已经具备；但真实留出集还没有形成有意义的统计。

---

# 27. 第四阶段：正式做 Code Retrieval A/B

建议最终至少：

```text
A Files Only
B Lexical
C Semantic
D CodeGraph
E Hybrid
F Adaptive
G Adaptive + Experience
```

不需要一次全部跑完。

可以：

```text
第一轮：
A B C D

第二轮：
D E F

第三轮：
F G
```

这样更省 token。

---

# 28. 第五阶段：开始消融

最终必须回答：

```text
CodeGraph 有用吗？

Evidence Gate 有用吗？

Experience 有用吗？

Utility 有用吗？

Redundancy 有用吗？

Cost-aware stopping 有用吗？
```

不能只给一个“大一统方法”的结果。

---

# 29. 当前两个方向的真正升级路线

## Trajectory / Experience

```text
现在
设计完整
↓
真实任务
↓
留出集
↓
Decision Episode
↓
Retrieval Trajectory
↓
跨任务经验迁移
↓
Experience as Retrieval Prior
```

---

## Code Retrieval / CodeGraph

```text
现在
工具可用
↓
Gold Evidence
↓
Retrieval Metrics
↓
干扰代码实验
↓
固定 Budget
↓
Semantic + Structural Fusion
↓
Adaptive Retrieval
↓
停止策略
```

---

# 30. 两条路线最后汇合

最终不要做成两个孤立模块。

应该：

```text
                 Coding Task
                      ↓
                Evidence State
                      ↓
        ┌─────────────┴─────────────┐
        ↓                           ↓
 Current Retrieval             Past Experience
        ↓                           ↓
 search / BGE / Graph        Decision Episodes
        ↓                           ↓
        └─────────────┬─────────────┘
                      ↓
                Retrieval Policy
                      ↓
                Next Action
                      ↓
                New Evidence
                      ↓
                 Trajectory
                      ↓
                 Outcome
                      ↓
                Experience DB
                      ↺
```

这才是你当前项目最值得深入的闭环。

---

# 31. 现阶段不要急着说“新算法”

当前更准确的描述：

> **Evidence-Guided Adaptive Code Retrieval Framework**

进一步研究后，如果实验确实支持，可以升级成：

> **Evidence-Guided Adaptive Code RAG**

如果后续真的形成：

```text
状态表示
+
动作选择策略
+
效用函数
+
停止策略
+
实验提升
```

再讨论：

> “是否可以称为一种新的 RAG 方法。”

---

# 32. 接下来具体只做 8 件事

## 任务 1

整理 20 个真实 Coding Task。

## 任务 2

为每个任务建立 Gold Evidence。

## 任务 3

给每次 retrieval 加 Trace。

## 任务 4

把 Trajectory 改造成：

```text
State → Action → Observation → Outcome
```

## 任务 5

重新做：

```text
Files
Lexical
Semantic
CodeGraph
```

四组 retrieval 实验。

## 任务 6

加入干扰代码 + 固定 token budget。

## 任务 7

在留出任务上测试 Experience。

## 任务 8

最后才把 Experience Prior 接入 Adaptive Retrieval Policy。

---

# 33. 第一阶段完成标准

当下面这些全部完成时，你才算真正进入“RAG 研究阶段”：

### Trajectory / Experience

- [ ] ≥20 个任务
- [ ] 有留出集
- [ ] Experience 真正跨任务迁移
- [ ] 有 helped / harmful 统计
- [ ] 有 Decision Episode
- [ ] 能解释某条经验为什么被召回

### Code Retrieval / CodeGraph

- [ ] Gold Evidence
- [ ] File / Symbol / Test Recall
- [ ] Context Precision / Recall
- [ ] Token / Latency / Tool Calls
- [ ] 干扰代码测试
- [ ] 固定 Budget 测试
- [ ] Semantic vs Structural 对照

### 两者结合

- [ ] Experience 不只是“提示词补丁”
- [ ] Experience 能影响 Retrieval Action
- [ ] Retrieval Trajectory 可以反哺 Experience
- [ ] 有完整的 `Task → Retrieval → Outcome → Experience` 闭环

---

# 34. 你目前最大的两个问题，一句话概括

## Trajectory / Experience

不是“设计不够深”。

而是：

> **还没有足够真实、重复、可留出的任务，证明经验真的能跨任务迁移并降低探索成本。**

## Code Retrieval / CodeGraph

不是“工具不够多”。

而是：

> **还没有 Gold Evidence + 独立 Retrieval Metrics + 足够大的任务集，证明结构化检索真正提升了代码证据获取效率。**

---

# 35. 最终应该达到的状态

项目不再只是：

```text
Coding Agent
+
很多工具
+
Experience
+
CodeGraph
```

而变成：

```text
一个研究型 Coding Agent Retrieval System

核心研究问题：
“Agent 如何决定下一步获取什么代码证据？”

输入：
Coding Task

状态：
Evidence State

动作：
Lexical / Semantic / Structural / Episodic Retrieval

决策：
Utility-aware Retrieval Policy

终止：
Evidence Sufficiency / Diminishing Returns / Budget Exhaustion

输出：
Evidence-aware Context

反馈：
Test / Reviewer / Outcome

学习：
Trajectory → Decision Episode → Experience
```

这才是你现在最值得投入的深度方向。
