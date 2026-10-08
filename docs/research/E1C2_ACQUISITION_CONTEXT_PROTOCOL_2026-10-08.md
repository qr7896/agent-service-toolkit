# 自动import依赖补证与合理上下文预算

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent
- Origin Mode: run
- Origin Date: 2026-10-08
- Verification Status: UNVERIFIED（运行前）
- Version Label: acquisition_context_v1

## 研究依据与预算分层

[DeepSeek官方规格](https://api-docs.deepseek.com/quick_start/pricing/)当前Flash支持1M上下文/最大384K输出；这是技术上限，不是每题建议消费。规范模型名deepseek-flash，旧v4-flash别名由现Flash处理。不使用Pro或模型切换。

[SWE-agent模型配置](https://swe-agent.com/latest/reference/model_config/)分别提供max_input_tokens、max_output_tokens、per_instance_cost_limit、total_cost_limit和调用限制；没有给所有任务一个通用最优token量。[mini-SWE-agent默认配置](https://raw.githubusercontent.com/SWE-agent/mini-swe-agent/main/src/minisweagent/config/mini.yaml)也独立限制成本并截断过长观察，不是把整个仓库始终装满。此处只借鉴预算分层，不采用其自动重试/不受限shell。

基于本项目真实输入与两个reserve停止样本，设置项目建议值（不是上述项目规定的行业标准）：输入软目标12000/硬限24000 **estimated tokens**，输出2000；human/conversation字符安全上限96000；单题软额度32000/弹性硬限48000，四参考整批硬限80000；最多16请求、retry0、thinking disabled、保护每个未开始任务首请求。旧50000预算/24k task及所有旧source不改；新版预算/消费必须另完整freeze。

输入估计与最终provider usage分别记录，字符数不当token。历史caller 30k/36k字符限制由新messages直接public payload与token检查替代；不传Gold/test/评分日志，source/facts/锚/参数声明全部保留。system安全/Oracle/JSON/范围约束合并成一份；last_feedback只一次，原raw prior action只一次，不重复完整身份诊断。rejected/unknown/行为缺口与scope权限不丢。预算参数提升不是效果已经改善的证据。

## 自动补证机制

只根据inspect_program产生的unexposed import binding(module/symbol/path)，复用项目静态resolve_symbol与signature/body窗口；max2符号/issue+base、depth4静态reexport解析、单文件≤1MB。要求production路径、正则静态模块、非symlink、绑定path一致、host LF==exact-base Git blob，保存来源、seed、depth1/source SHA。否则硬错或unknown，不猜taskID→file，不扩大至tests/任意shell。

Controller执行后scope为ACQUIRE_EVIDENCE_OR_ABSTAIN才补证，补到的新窗口进入独立overlay。初始frozen输入不mutate，下一实际messages和下一execute都使用effective view，保存effective-input/取得记录。取得源不回填当前probe资格，不重跑原probe，不产生trusted升级；下次新probe才重新核验。

## 零模型验收

```powershell
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_acquisition_check
```

新namespace acquisition-context-zero-v1；source/protocol/旧producer seal先冻。缓存delegate只返回已封存自身反馈/锁定Oracle/执行，**不执行probe或模型**；Controller生产依赖读取/静态解析、window/SHA、下一Human消息暴露是真实执行。对两个真实budget-stop输入重新计算旧/新相同multiplier1.4+output2000的reserve。class/context正负单测、nested hook与恢复必须过；结果不算新生成或repair rate。0 provider/容器/Gold读取，无下载/删除/系统Docker/代理/tunnel/key修改，TEST/canary/Fresh30关闭。started失败封存不自动重试；新paid producer须另freeze完整方法/80k预算和精确命令。
