# 输入保真与公共API归属：零调用证据与新生成研究

## Material Passport

2026-10-06；原DEV12开发数据；四批独立canary均未达≥2/3，第4批0/3封存。以下机制只在合成与旧DEV开发，不重新计已看canary分数，不使用TEST/C5/Fresh30。付费前冻结新输入/源码/预算，新生成与零调用审计分别报告。

## 实际根因与修复

第4批暴露旧围栏投影会删掉`.astype(object)`等复现输入，模型据此构造不同dtype，base通过；另一题关键末端方法窗口未选中。新语法事实通道保留公开输入构造/类型/参数/seed/切片、纯声明fixture类与末端调用，输出JSON而非执行代码；断言/比较/答案变量/测试导入/断言别名/危险能力块整块拒绝，doctest只保留提示输入、不保留显示答案。拒绝和未知不算成功。

生产定位只解析导入/重导出/继承，公共末端API的定义窗口优先；不执行生产包、不手选路径。合成同名类冲突与继承fit案例验证，真实旧DEV自动找到MultiTaskLassoCV的继承fit。关系type/depth/origin(seed)、生产SHA与分段行号都记录；深度计入import/reexport和inheritance两类跳数。当前不能解析所有复杂语义或无导入的自然语言归属，局限保留。

公开输入原件先核官方Git blob SHA。仅公共problem_statement.md键来自冻结树的metadata，未读Gold/test正文做输入。原DEV九题零调用审计：3题共4块safe事实；6题无块/拒绝，分母仍12。Lasso输入n/d/X/y/seed完整保留（有块因预算拒绝），日期和内嵌字段声明得以恢复。初始原型v1–v4结果保留；最终audit-v5 source/locator SHA绑定，不将中间原型包装成已验证效果。

## 预算与验收

协议见[冻结计划](E1C2_FAITHFUL_INPUT_DEV_PROTOCOL_2026-10-06.md)。新身份faithful-input-dev-v1：固定12、九题实际生成，Flash非thinking/temperature0、最多18请求/每题2、输出3000、单题20000/整批80000、重试0、actual usage+reserve守卫。首轮reserve67335；prose+windows+facts≤23000字符、4窗/每窗2500，未扩大证据预算。

新输入freeze SHA00ab5ba6ccb4a3755b014191ddcb2c6aee5d989dd13b67d4825390b68b457581；零调用facts freeze16ebabfb0d8d8166e22570ac7430d534d9b77baab1587449a637c7cda0c7abe3，audit result b6c072f49c60dd7960d36773cc38f053440c207a2556f23b5bfc1ee286b24891。17项新专项、规定重点合计35passed，Ruff通过、V3规定preflight ready=true。新生成已完成，但容器验证无效，不能复制历史4/12或称本批0/12能力失败。

精确唯一付费命令：`uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_faithful_dev run`；沿用用户单实验≤100000许可，先列命令/模型/次数/80000预算。完成后同模块gold独立评分，保留原response/state/ledger；失败不自动重试。四参考/跨仓库及新增证据验收未过不抽新canary；即使DEV进步，也不是自主修复率或独立泛化。

工程第一次完整回归1143passed/1failed/4skipped是原Streamlit8秒冷启动超时；原失败项0.94秒独立通过，未改timeout/断言。第二次完整单次1144passed/4skipped/33warnings/0failed（181.75秒），不拼接结果。此为代码回归，不确认Docker运行态。

加入基础设施错误分类与零付费缓存回放的4项专项后，最后完整单次回归1148passed/4skipped/33warnings/0failed（49.54秒）。没有将工程通过数换算成可信复现率或补丁成功率。

## 模型已完成，评分INFRA_INVALID

按展示精确命令/Flash/18请求/80000的已有授权运行一次，16请求37593实际tokens，无provider失败/重试。但Docker Linux Engine管道不可用，所有执行日志是host transport错误；旧执行器将重复CLI错误错记nonsetup failure，随后七项Gold均无补丁应用。**原评分不可解释为软件失败/模型能力结果**；不报0/12，不晋升任何候选。真实盲canary v4的0/3仍是此前独立结果，与这个无效DEV验证分开。

所有原response/state/ledger/control/Gold日志保留，[公开invalid结果](../../data/e1c_evaluation_2_faithful_dev_result.json)绑定原SHA。自10月5日开始可见usage累计184676+37593=222269（含旧SDK错误4281额外usage，非账单核验）。停止新增付费，不重试provider。

普通docker desktop start未恢复，backend日志明确旧dockerInference IPC socket不可访问导致退出。未改注册表、socket目录、WSL、镜像、VHD、代理或tunnel；已向用户请求仅正常停止Docker/备份改名IPC run目录/再启动的明确确认，不擅自factory reset。

新增独立[零付费恢复适配器](E1C2_FAITHFUL_INFRA_REPLAY_2026-10-06.md)：必须真实engine及九个image ID健康，同原代码/输入preflight完全相等，再读取原B/A响应重放到新目录，API钥匙不用、0provider。每次验证前/后拒绝Docker transport错误；未收集角色记controller cache-missing而非伪造模型输出，不增付费。原试验文件与所有既有冻结代码不改。恢复后的结果另立，当前尚未执行，不宣称方法有效或完美。

本机实际执行新适配器preflight返回ContainerInfrastructureUnavailable（Docker Linux Engine不可用），在冻结/验证/模型调用前停止。此为失败关闭守卫的运行态检查，不是复现分数；没有继续run/gold。
