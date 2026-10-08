# 反馈投影：保留边界的零调用修复

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent
- Origin Mode: run
- Origin Date: 2026-10-08
- Verification Status: UNVERIFIED（执行前登记）
- Version Label: feedback_projection_v1

scope DEV trial v1真实运行在3次Flash完成请求后，第一题形成子义务候选；第二题新gate要求取得DecisionTreeClassifier生产依赖，但下次消息组装被BlindBoundaryViolation拦截。两个本地资格/行为诊断中的`Gold_used: false`字段本身含受禁marker；此前无独立Gold读取。原trial state/ledger/freeze/source保持、不得自动重试或换身份暗补。

新投影只移除已知schema(`e1c2-bounded-qualification-v2`、`e1c2-bounded-behavior-gate-v1`)各自顶层且严格Boolean False的这一诊断字段；未知schema/true/null/0/字符串均拒绝。不是全字符串替换，不屏蔽其他字段或真正评分内容。复制原反馈，保持scope gate、unknown、源码/异常/所有语义资格；投影后仍经过原assert_agent_payload/serialized marker/forbidden values审计。真正Gold文本或其他位置同名标记仍拒绝，不修改任何boundary源或规则。

零调用audit核验原中断状态，仅读取已保存唯一nonterminal feedback及对应公开input/canonical contract；新namespace先freeze原state/ledger/feedback SHA与投影source/protocol。重新绑定核验过的production workspace，将投影送入实际所有旧messages层，再审计最终Human JSON；不执行模型、probe/容器或评分。新context hook必须在真实nested配置中保持。raw诊断metadata仍留原产物，不改冻结scope/paid源码。

```powershell
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_feedback_projection
```

namespace `scope-feedback-projection-zero-v1`；provider/tokens0/0、started后不自动重试。通过只证明这份实际失败反馈能安全进入下一消息，不意味着原trial恢复或新付费实验已完成。任何新producer须将投影source纳入新完整freeze与预算，不用此context去绕过原trial身份或重新run。sealed TEST/canary/C5/Fresh30关闭，不下载/重启/删除/修改Docker/tunnel/key。
