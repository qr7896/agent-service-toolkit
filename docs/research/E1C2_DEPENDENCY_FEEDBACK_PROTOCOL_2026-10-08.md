# Pre-observer依赖反馈：零调用分支修复

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent
- Origin Mode: run
- Origin Date: 2026-10-08
- Verification Status: UNVERIFIED（执行前）
- Version Label: dependency_feedback_v1

真实resume封存后发现：当candidate缺任何已暴露production binding而不能创建observer时，原verdict把依赖缺证写在program分支，scope action_gate只从qualification.program_evidence读取，丢失检索建议。新route仅对unknown_or_rejected_dependency_evidence分支构造unknown/rejected资格视图，复用既有action_gate；不创造支持证据，旧rejected/missing保留、最多两纯symbol建议、repair/trust仍false。不改原scoped/resume源或结果。

```powershell
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_dependency_feedback
```

新namespace dependency-feedback-zero-v1，source/protocol/原producer seal/全部feedback SHA先冻；只读取已封存generation feedback做shadow诊断，不读Gold或模型输出答案，不执行容器/模型。started不重试。结果不是新生成或修复效果；future producer必须接route并整体freeze才可检验建议是否被实际模型采用。保持TEST/Fresh30/canary关闭，无系统/镜像/tunnel/密钥修改。
