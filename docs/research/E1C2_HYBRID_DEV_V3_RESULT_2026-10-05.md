# 旧DEV v3：节省回退调用，但可信覆盖门槛仍未达

## Material Passport

2026-10-05；原DEV12开发实验，原双准入9题/固定分母12；源码先提交e234a14、冻结新输入/方法后一次执行。协议见[DEV v3](E1C2_HYBRID_DEV_V3_PROTOCOL_2026-10-05.md)，[公开结果](../../data/e1c_evaluation_2_hybrid_dev_v3_result.json)。不是独立验证、不是Agent修复率，未将缓存/历史最好结果拼入本次。

完成9题、12次deepseek-flash请求、24712 provider tokens（冻结80000、单题20000、输出3000）；零provider失败/自动重试。明确弃答3题均未调用A。四窗口/上下文预算未增；准确生产路径锚点在一条旧DEV上提供两窗口，其余保持原自动规则。未人工选文件或读公开断言/Gold生成代码。

| 固定12的去向 | 数量 | 说明 |
|---|---|---|
| 原官方双准入未通过 | 3 | 保留分母，不调用 |
| 明确弃答 | 3 | fixture输入不充分、文档任务、讨论；不计成功 |
| 未形成稳定失败 | 1 | CLI行为/fixture无法在当前probe限制下可信表达 |
| base重复失败、Gold仍失败 | 2 | scikit-26289与Marshmallow-1164；不计可信 |
| Gold区分并经issue语义审查 | 3 | scikit-13496、Marshmallow-1252/1359；包含人工语义审核 |

机器trusted仍false/0，不回填原JSON。与上一新生成hybrid-v1相比，15→12请求（-20%），29864→24712 tokens（约-17.3%），Gold均3/12，但成功任务不同（日期恢复、export_text丢失）。单次非同输入随机配对，不能宣称因果成本增益。与controller v2缓存4/12/历史v4四条相比，缺一条，**预注册保留四条参考覆盖门槛失败**。不再抽新canary寻找好看结果，repair/Fresh30/E2仍关闭。

## 下一项有价值的通用工作：可信正对照，而非追加付费重跑

当前控制器允许正对照省略target的非触发参数，因此“control过、target错”不一定隔离issue故障。scikit旧DEV实例体现：生成fixture的一列特征与六个feature labels不一致；原base先报数组处理错误，Gold消除该错误后仍因另一输入约束失败。这里用于DEV诊断，不反推模型答案，也不在已看canary修复后重报独立。

后续先做零调用的**counterfactual fixture contract**：

1. 解析control/target调用AST，记录同API、输入对象、非触发参数的差异；不能证明可比就拒绝或明确弃答，不能把“control省略一切参数”当对照。
2. 从实际生产源码提取可执行前置条件（签名、shape/长度/类型检查），记录file/line/SHA；只校验fixture，不改变issue oracle，不拿Gold作约束发现器。
3. 对照只改变明确的触发因素，其余输入/形状保持一致；缺少生产依据时不猜修。参数支持类行为与类型兼容类行为必须可区分，避免错误拒绝原warm_start等有效实例。
4. 合成夹具覆盖“control省略约束但target违约”“允许新增待支持参数”“无有效oracle”“测试路径越界”，原DEV四条参考必须保持；零调用缓存仅作开发证据。
5. 零调用证明形成后，另冻新DEV方法/命令/Flash预算，完整一次生成评分；新版本保留四条、跨仓库并分账才考虑新独立canary。若协议需要筛选可观察bug与feature/doc任务，须另行预注册并单列coverage，不悄悄改变本次分母。

不新建样本、不加模型尺寸、不反复补任务ID规则即可先推进这一步。当前新方法尚未实现/验证，不能列成已有创新效果。CLI支持是另一个独立工作：未来只允许固定、无网络容器中的受限命令，不开放任意宿主subprocess或测试答案。

## 保全与成本

freeze SHA `87926c7d86e59b9d2b4a509d4986772de36d596a4cecb87d34dde35fe0cade66`；state `d46f4512eec83e9712ffbf9573bca1c7a90faa2fa22fe257024d172b04dd0fb4`；ledger `82051e06da40963cd02a1d28262089a55558ff5317f136cdf07a8a82a52f1264`。原件`.codex/e1c/evaluation_2/hybrid-dev-v3/`含新响应/正对照/执行/评分，不覆盖旧版本。

本轮canary+DEV共15请求/31992实际provider tokens；加此前本日已记录可见usage120326为152318（其中旧SDK错误4281为state.error额外usage，非核账单）。本轮没有失败调用或重试。完整工程回归1118passed/4skipped/0failed/33warnings（50.55秒），只能说明工程回归通过，不证明3/12以上修复成功。Docker、镜像和tunnel配置均未改，无清理删除。
