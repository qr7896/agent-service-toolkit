# E1-C evaluation_2：三组路线与首轮修复接线预注册

日期：2026-10-08。用户本轮选择三组路线；旧严格协议、全部负结果、费用与 namespace 原样保留。本文件只约束新身份 `e1c2-three-arm-cached-witness-dev-v1`，不替换过去的可信门槛。

## 1. 研究问题与三组

在相同模型、任务、生产源码窗口及资源上限下，增加带来源的复现证据是否有助于修复？限制读取 base 已有测试的成本是多少？

| 组 | issue / exact-base 生产源码 | base 已有测试 | 额外证据 |
|---|---|---|---|
| standard | 同一份 | 可读、不可编辑 | 无 |
| standard_evidence | 同一份 | 可读、不可编辑 | 同一缓存自身 probe / 源码异常 / 公开旧版本对照 |
| strict_evidence | 同一份 | 不输入 | 同上 |

只有 strict_evidence 符合本项目原来的“不读取现成测试断言”条件。标准两组没有该条件，不把其修复率宣传成“非公开断言”成绩。三组均不得读取新评分测试、Gold、未来提交或独立评分日志；官方评分必须晚于全组生成封存。

## 2. 首轮范围：只验证修复接线

不是正式三组准确率试验。只选旧 DEV 中唯一与已完成公开发行对照的成功版本引用匹配的任务，固定 1 个旧任务、3 个 cell。筛选按公开版本引用，不增加 task-ID→文件规则。公开版本对照自身有 package 约束且只有一个已验任务；不能称随机抽样或代表 DEV12。

本轮自动检索从固定 base Git blob 取得既有测试，路径/regular blob/对象 SHA 校验，最多 512 个测试文件、每文件 300,000 bytes、总扫描 2,000,000 bytes、3 个文件/6 窗口/9,000 字符；种子来自既有自动生产窗口符号。工作区新增/改动测试、符号链接、Git history、任意 ref 不读。严格组 messages 无 base-test 通道，但本轮三组共享准备阶段会为标准组扫描 base 测试；不宣称严格组进程完全未访问测试对象。

共同生产窗口沿用已封存自动检索结果，不人工重新定位。它们含之前 Controller 的检索积累，因此 standard 只是**共同缓存生产窗口下的单次修复 baseline**，不是独立标准 Coding Agent 从零定位基线。新增证据也沿用已封存模型 probe 与零模型观察，因此 treatment 是 **cached-witness-assisted repair**，不是新端到端复现生成。正式实验必须冻结从 issue 开始的整条定位/生成/验证链，并记录生成侧成本，不把本轮缓存收益推广成 Agent 全链能力。

旧 full_issue_trusted / repair_eligible 不改：本轮是另立条件机制支持下的 DEV 修复可行性试验，不把尚未证明的 namespace 意图与剩余义务改成 true。冻结后一次生成、零官方反馈到模型；不循环调同题挑最佳。

## 3. 冻结预算和运行

- 模型：`deepseek-flash`，禁用 thinking，temperature=0；不使用 Pro。
- 三组各 1 次、共最多 3 次；每 cell 最多 16,000 provider tokens，整批最多 48,000。
- 单输出最多 3,000；输入预估乘 1.4 后加输出额度必须 ≤16,000。未来 cell 全额预留。额度上限相同但输入长度不同，因此本轮不宣称相同实际消耗；正式对照同时报告输入/输出/总用量。
- HTTP 120 秒；SDK retry=0。namespace started 或账本存在则禁止重复生成；失败/未知收费停止保留，不自动重试。
- Actor 只返回最多四个生产源码 exact edit；old 必须在暴露窗口中且在完整 base 文件唯一。AST 校验、纯 diff 编译，不修改本机任务源码。
- 三组全部生成后 seal；只有 seal 核验通过，scorer 才读取既有官方评分材料。在独立容器中应用候选补丁，`--pull=never --network none`、无宿主写挂载、限制资源/权限。评分 900 秒上限，超时是基础设施/验证异常，不包装成有效故障。

零模型冻结：

```powershell
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_three_arm_dev preflight
```

待精确授权的新付费命令（不因本文件存在而视为已运行）：

```powershell
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_three_arm_dev run
```

仓库 `AGENTS.md` 要求真实模型实验获得精确命令授权；通用“继续”不改此门槛。命令自动先生成并 seal，再独立评分。预检无模型调用、不读新评分断言/Gold 内容、不拉镜像。缺本地父产物/镜像时报告 INFRA_BLOCKED，不伪造冻结。

## 4. 结果和下一门槛

逐 cell 报生成/拒绝/abstain、真实调用与 tokens、独立 official F2P/P2P、resolved；异常保留固定 3 cell 分母。以下必须分账：条件机制证据、完整 issue 可信、official 修复。零模型回归数不作任何一种研究成功率。

接线过关后：旧 DEV 至少两种故障/两个库，重新从 issue 运行同一自动流程、计入定位/probe 成本；再扩双准入 DEV，明确三组成本与失败原因。方法整体冻结后才预注册不重叠 canary，盲态一次运行；失败封存，回 DEV 修通用方法，后续新 canary 排除所有见过的任务。严格组可信门槛 ≥2/3 与 official repair 都真实核验后再考虑 Fresh30 / E2，当前不得打开它们。

不承诺一周 30/30 或“完美”。此路线的价值是用普通修复成功率和严格消融定位真实代价，避免继续以无法证明的完整语义门槛阻止所有 DEV 修复实验；对独立验证仍保留严格信息隔离。
