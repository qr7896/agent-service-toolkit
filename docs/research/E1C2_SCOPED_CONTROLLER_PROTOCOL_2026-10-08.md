# Scoped Controller：定义范围与缺证动作门槛

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent
- Origin Mode: run
- Origin Date: 2026-10-08
- Verification Status: UNVERIFIED（预注册；实际结果另文）
- Version Label: scoped_controller_v1

## 方法与材料

复用已冻qualified-controller v1，旧源/namespace/成绩不改。新模块只修参数定义范围并增加候选动作gate，不添加模型、依赖或collector。Parameters声明只从与冻结窗口start_line精确一致且owner相符的唯一顶层/直接类方法读取，缺/错行号、多解、owner不符输出unknown且无声明；保留实际AST所属类/行号/source SHA。class/guard/nested helper不是函数参数证书。源host SHA与LF/base Git blob保持校验，≤1MB文件/8条记录/8参数；声明不覆盖明确变更请求，也不证明唯一target API意图。

实际selected candidate→原observer/qualification/behavior→新action gate：rejected不选、程序/行为资格unknown不提前终止搜索，返回最多两个来自既有production缺证记录的纯symbol retrieve建议或abstain。raw per-turn probe/执行/锁定oracle保留，不修改输入值或公开期望。已支持子义务或明确conditional hypothesis只能 `INDEPENDENT_DEV_GRADE_ONLY`；repair/full issue/canary权限始终false。公开意图、版本点、默认/增量行为须分别验证；当前不存在自动全issue证明。

## 零调用验收与命令

先专项单测（同名构造器串证、精确header/owner、unknown/拒绝gate、嵌套hook），再实际正例smoke与freeze，再实际合成失败分支。复用旧测试driver逻辑但使用新scope namespace，绝不重跑旧身份。最后对四份已发布qualification-v3/behavior缓存做完整shadow audit：SHA先核验、固定4/DEV12分账，不新生成/重执行/读Gold，不回填原资格。

```powershell
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_scoped_controller smoke
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_scoped_controller freeze
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_scoped_controller failure-smoke
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_scoped_controller audit-dev
```

四新namespace为scoped-controller-zero-smoke-v1/dev-v1/failure-smoke-v1/cache-audit-v1。所有provider calls/tokens均0；started不自动重试，失败原状封存。普通network-none/read-only/pull-never容器，不下载/重启/删除/改代理/IPC/VHD/tunnel/key。原201产物及新冻module SHA最终复核；sealed TEST/C5/Fresh30关闭。

## 预算与下一放行条件

预算仅继承旧四参考候选Flash最多16调用、整批50000/单task24000/output2000/retry0；本版CLI无run且preflight real_provider_run_enabled=false。工程/合成gate不放行repair或canary，不把shadow candidate资格报可信3/4。按需取得production依赖/paired input/对象/历史witness仍需完整producer接线、source/预算freeze；未可用证据明确unknown。真实新DEV生成与独立Gold须另freeze并列精确命令；不承诺30/30。
