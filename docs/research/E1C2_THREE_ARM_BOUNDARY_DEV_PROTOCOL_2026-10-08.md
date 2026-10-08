# 三组公开反例辅助修复DEV v2：新方法与预算

日期：2026-10-08。身份 `e1c2-three-arm-public-boundary-dev-v2`。原v1三次调用/15,764tokens、2封装拒绝+1无改动；后验解码保留模型patch，自身原probe正常/目标各两次完成，但official目标0/1、回归37/37。原v1成绩不回填。

零调用公开边界诊断已在同21个变体得到base6/21、原模型patch11/21、公开2.19.3完成21/21，存在10个patch未覆盖的公开派生条件。全部是同一个旧DEV的合成家族，不计新任务、独立样本、完整意图或准确率。未读取官方失败断言来设计算子；21案例是预定义时间类算子，不声称任意task通用完备。

## 方法变化（新身份，不改v1）

1. 相同三组：standard可读base旧测试、不加额外witness；standard_evidence同测试权限+额外证据；strict_evidence模型不输入既有测试+同额外证据。评分测试/Gold/未来提交仍三组隔离。
2. 三组共有的生产补证：从既有自动窗口中的完整函数AST获取加载的名字，只读取相同已暴露文件、固定base的顶层短assignment，最多4个/每个≤16行/文件≤1MB。包括真实依赖的regex等，而非人工按task挑文件。host/LF/base identity由原输入校验器先核验，新增窗口行直接取base blob；不能把全局定义获取叫语义证明。
   有条件重赋值时优先补同module-level控制块；超16行只展示原赋值并明确context不完整。所有赋值均非runtime value certificate；不能用静态True推翻原依赖缺失条件。
3. 两个证据组加入四个自产counterexample：仅根据公开base失败与公开旧版本完成记录筛选，取有序失败列表最前两个/最后两个。提供合成probe源码、原base失败trace（≤900chars并标截断）及旧版完成状态；**不输入official结果、失败测试名、断言或Gold，亦不提供原模型patch代码作答案**。
4. 修复decoder仅兼容额外且固定的`type: json_object`外壳，编辑path/old/new字符串不改；其余字段拒绝。raw原样保留、response标兼容动作。同值替换继续abstain；追加system明确只准edits、必须实际改生产行为、不靠安装依赖或回退合法功能隐藏故障。
5. 复用v1预算gateway、exact-edit/AST/暴露路径验证、全组三cell seal和独立official scorer。新源码/协议、原输入/方法、public sweep记录、所有最终prompt与预算整体freeze。动态接线只在新runner scoped context，旧源码/原namespace/旧trusted false不改变。

严格组允许自产probe及其完成guard，不读取现成base测试断言或新官方评分断言；“不读取现成断言”不等于“不得生成自己的检查”。

## 预算与精确命令

固定同一个旧DEV/三个cell；不是新两来源或从issue重新定位全链。Flash、thinking disabled、temperature0，最多3calls、整批48,000 provider tokens，每cell16,000、每输出3,000。输入估计×1.4加输出须适配每cell；未来cell全额保护，retry0、HTTP120s、official900s。不用Pro、不自动retry started/未知收费。不保证成功或30/30。

零调用预检：

```powershell
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_three_arm_boundary_dev preflight
```

**新付费命令，须用户精确授权，不沿用v1授权：**

```powershell
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_three_arm_boundary_dev run
```

只读base测试通道与v1上限一致，strict模型无测试但共享准备为标准组读base对象。全部生成seal后才offline/pull-never独立official评分，不把terminal shell rc0当resolved（原official eval会掩盖pytest失败，必须核对F2P/P2P）。所有宿主挂载只读，生产修改仅隔离容器层。

本轮未开始新付费时只记录preflight ready。下步通过后才两来源从issue的完整方法/成本闭环→固定12九准入→整体freeze/全历史不重叠canary；可信与official各自过关后另授权Fresh30/E2。失败封存回旧DEV，不能补看过canary再称独立。不开sealed TEST、Fresh30、C5或私有Test500，不改Docker/IPC/VHD/代理/tunnel/密钥或删除数据。
