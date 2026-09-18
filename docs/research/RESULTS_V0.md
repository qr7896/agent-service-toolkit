# Adaptive Code RAG V0 Results

> 2026-09-18；20 条任务，train/dev/test = 12/4/4；评测 dev+test 8 条。
> 全程 **0 次付费模型调用**；Semantic arm 使用本地 BGE-M3。原始逐条结果见 `evals/results/retrieval_v0.json`。

## A–G（8K budget）

| Arm | Context Recall | Precision | Context tokens | Tool calls | Evidence efficiency |
|---|---:|---:|---:|---:|---:|
| A Files | 0.2344 | 0.5000 | 15.00 | 1.00 | 15.75 |
| B Lexical | 0.2969 | 0.4333 | 33.00 | 1.00 | 12.42 |
| C Semantic | 0.4531 | 0.4000 | 68.00 | 1.00 | 6.66 |
| D CodeGraph | 0.8906 | 0.4000 | 87.88 | 1.00 | 10.14 |
| E Hybrid | 0.8906 | 0.4000 | 188.88 | 3.00 | 4.78 |
| F Adaptive | 0.8906 | 0.4000 | 120.88 | 2.00 | 7.65 |
| G Adaptive + Experience | **0.8906** | **0.4000** | **94.38** | **1.25** | **9.80** |

经验先验没有提高召回，但在召回不变时让策略更早选择结构证据：相对 F，G 少 **21.9%** 上下文、少 **37.5%** 工具调用，Evidence Efficiency 高 **28.1%**。这只证明检索决策更省，不等同于端到端修复成功率提高。

## Budget 与停止策略

2K / 4K / 8K / 16K 的结果完全相同：最小复现的实际上下文最多约 204 tokens，2K 已饱和。因此本批数据能测检索顺序，**不能**用于拟合大上下文预算曲线。

| Stop policy | Context Recall | Context tokens | Tool calls | Efficiency |
|---|---:|---:|---:|---:|
| Fixed K=3 | 0.2656 | 43.62 | 3.00 | 6.19 |
| Fixed K=5 | 0.3906 | 71.00 | 3.00 | 7.02 |
| Fixed K=10 | 0.7344 | 131.12 | 3.00 | 5.65 |
| Evidence Gate | 0.8906 | 120.88 | 2.00 | 7.65 |
| Utility Gate | **0.8906** | **94.38** | **1.25** | **9.80** |

V0 满足预先写下的第二个通过条件：在相同 16K 上限下，Utility Gate 的 Gold Recall 高于 Fixed K=10（0.8906 vs 0.7344）。

## Ablation、干扰与版本漂移

- `-CodeGraph`：Recall 0.8906 → **0.4531**，结构证据是本数据上的主增益来源。
- `-Experience`：Recall 不变，但 tokens 94.38 → **120.88**、calls 1.25 → **2.00**。
- `-Redundancy`：Recall 不变，tokens 94.38 → **221.88**，重复上下文只增加成本。
- `-Coverage` / `-Cost`：Recall 不变但 tokens 都升到 **203.88**；停止判据负责节省上下文。
- `-Uncertainty` 与 full G 完全一致：`uncertainty` 目前只记录、不参与公式；这是明确的未实现边界，不应包装成“消融无影响”。
- 12 个同名 distractor 加入后，G 的 Recall 反而微升到 0.9062，但 Precision 从 0.4000 降到 **0.3054**，Efficiency 从 9.80 降到 **2.36**；说明“找到 Gold”不代表上下文干净。
- 旧/错先验在干扰集上 Recall 未变，tokens 388.50 → **414.50**；没有造成正确性下降，但损失了部分成本收益。

## 结论与边界

Adaptive 在“问题文本不直接点名内部符号、结构证据能补 caller/test”的任务上有用；只需文件定位时，A/B 更便宜。Experience Prior 当前主要改变动作顺序，未提高召回。Semantic 比 Lexical 召回高，但单独使用找不到 caller/test。

本结论只覆盖检索层，不覆盖 LLM 写补丁的最终成功率；任务是最小复现，规模小、上下文短，2K 以上预算无法区分。下一批应使用更大的真实 issue / 仓库快照，保留本批作为快速回归集。
