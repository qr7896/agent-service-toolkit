# 旧DEV新版：Import fallback与显式执行契约

## Material Passport

2026-10-06，原DEV12固定分母，九题双准入。五批canary全部未达门槛，尤其v5已0/3封存，不重测/不回填。新模块/目录executable-import-dev-v1，只旧DEV与合成开发；不读取新canary/TEST/C5/Fresh30/私有Test500，不按任务ID挑源码。旧所有协议、代码、响应、SHA及评分保留。

窗口顺序：既有terminal API→经生产AST/reexport核实的公开import前缀定义→原词法；去重，仍最多4窗/每窗2500/issue+facts+windows≤23000字符。复用已封存public facts-v5与import audit-v2；SHA和完整干净exact-base生产源码复查，未知/预算溢出拒绝。import来源只开头声明，非import立即停，拒绝测试/答案/能力根，不扫描断言体/函数体/输出值。

所有非弃答JSON额外有execution={mode,entrypoint,fixture_source}，fixture_source固定generated_public_issue_only。B只能direct_script/null；A可direct_script/null或call_entrypoint/一个普通本地标识符。直接脚本的仅定义函数形态拒绝；显式入口只能单个同步函数、零参数、无装饰/注解/定义副作用、模块顶层仅imports/定义/文档字符串，函数内有模型生成检查、入口名不得重赋值。控制器只追加一次该函数调用，不猜testdir/pytester，不自动test discovery或启动未知native harness。动态行为不被静态形态普遍证明；该版只保证受限入口确被调用，仍可能检查路径不可达或语义不忠实，Gold及人工行为审查边界不变。尚不宣称通用执行/语义正确性。

strip execution后旧B合同与oracle/counterfactual/正对照保持不变；原B和A解析都接同版解析器，避免B原始JSON多字段使fallback oracle编译器被意外绕过。A入口追加后的实际source先经过既有静态安全校验，再同一probe在base两次与独立Gold运行，不在评分时更换代码。每请求与候选验证之前真实engine/image必须健康；transport日志立即中断，不算软件失败。容器无网络、只读、pull never、不增加权限，模型不读评分补丁或官方test/日志。

Flash nonthinking/temperature0；每题最多B+A两请求、全九题最多18，输出3000，每题20000/批80000provider tokens，SDK重试0，actual+reserve在线守卫，首轮reserve必须≤80000，无借预算。明确弃答和派生控制失败STOP继承。先合成执行/输入隔离/预算/前置健康专项与完整回归，再生成freeze/输入/reserve，展示精确唯一run命令后使用用户≤100000单实验许可；失败不自动provider重试。先提交方法/协议，再冻身份，原代码和state不改。

唯一新付费命令（尚需现场preflight通过）：`uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_executable_dev run`。独立同模块gold不调用provider；输出`.codex/e1c/evaluation_2/executable-import-dev-v1/`。结果分别报告原四参考、Gold区分、人工语义、假阳性/弃答和成本；不拼接各版本best。未保持四参考/跨仓库或无实质新机制证据不抽第6批。仅DEV改善不能进repair/TEST/Fresh30/E2，下一独立method仍须完整先冻再排除全部历史选三题一次≥2/3。
