# 有限公开引用范围协议 v1（零调用预注册）

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent
- Origin Mode: run
- Origin Date: 2026-10-07
- Verification Status: UNVERIFIED（运行前协议）
- Version Label: reference_scope_v1

目的：区分公开输入表达式确实改变与省略 import 的条件解释，不把候选升级为可信。仅使用已冻结旧 DEV 四参考的输入、已选 response、生产源与既有 authority；固定 DEV12 分母和四缓存分母分开，不读 Gold/test/grader日志，不新增模型调用、下载或容器执行。

命令：`uv run --frozen --offline python -X utf8 -m evals.e1c_evaluation_2_reference_scope audit-dev`。预算：provider calls=0，tokens=0。新 namespace `.codex/e1c/evaluation_2/reference-scope-zero-v1/`；存在即拒绝重跑。校验原 producer seal及所有生产侧产物摘要，原 public facts/model输入不修改。

规则：保留旧严格检查；独立计算条件结构结果。省略的完整引用路径必须与规范化后的模型限定路径严格后缀一致，例如 `fields.DateTime`，不只比较 `DateTime`。候选根库必须在冻结生产源码上下文内；复用静态定义解析器，唯一顶层定义、冻结host SHA、LF投影与exact-base Git blob均一致才记录条件绑定。拒绝同一公开引用的冲突绑定、改字面量/shape/字段和影射；缺源、歧义、外部库、控制流/对象修改仍unknown。别名拼写变化及同一限定对象的直接import不应误拒。

条件绑定必须标注 `public_import_explicit=false`、`export_chain_equivalence_proven=false`。现有静态解析器不证明完整重导出链与运行时动态namespace，旧资格unknown原样保留；`conditional_structure_supported`不叫语义证书或可信复现，machine trusted保持0，不接live。验收覆盖两个合成库正例、完整路径错位、改值、其他库同名、定义影射、alias影射、base变化、等价别名和输入不变。

若新缓存审计仍unknown，封存结果，不按task-ID补规则，不重跑旧run。下一步优先完整export链身份与运行时使用对象对应，再定义有限行为义务/机制门槛；完整方法未冻结、旧DEV语义gate未过之前不抽新canary，不开TEST/C5/Fresh30/repair/E2。此协议不是完成E1-C或保证30/30的承诺。
