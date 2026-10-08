# 新 Flash 旧 DEV scope-gate 校准试验

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent
- Origin Mode: run
- Origin Date: 2026-10-08
- Verification Status: UNVERIFIED（试验前登记）
- Version Label: scoped_dev_trial_v1

## 问题、方法与范围

检验完整有限scope method在真实新生成中能否保留可独立评分候选，并让未知程序/行为资格触发有界补证或弃答。只用旧四参考DEV（固定12/九准入/screen4分账），不是独立泛化试验，不宣称完整公开意图证明。生成侧只公开issue投影/生产源，不读Gold/原测试/原缓存诊断结果；调用模型deepseek-flash，thinking disabled，不用Pro。

新producer引用已冻结scoped-controller方法与正/负实际smoke，包括唯一header/owner参数范围、原compiler/oracle/normal/target、实际observer/qualification/behavior和scope动作gate。核验全部parent method SHA、parent协议/positive freeze-result SHA、negative driver与Controller freeze身份及实际partial scope gate。代码/预算/输入/本协议先冻结到新namespace；不是从禁用live的旧adapter绕过调用。完整范围是有限OLD DEV calibration，repair/canary权限false；子义务/假设最多独立DEV评分，unknown不terminal select。

## 精确命令、模型与预算

```powershell
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_scoped_dev_trial freeze
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_scoped_dev_trial run
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_scoped_dev_trial gold
```

freeze=0调用；run整批≤50,000 provider tokens，单task≤24,000/output≤2,000，最多16请求（4task×4），max_retries=0、保护未运行任务首请求预算。使用用户此前明确授予的单试验≤100,000无需再次确认权限；实际paid命令执行前仍在会话列明。原request ledger失败也记录；任何中断不自动重试、不换身份暗补。没有一次性30题或Fresh30调用。

新namespace `.codex/e1c/evaluation_2/scoped-controller-flash-dev-trial-v1`。全部生成结束并producer seal后才执行独立gold（0 provider调用）；其结果不回流模型，不改生成资格。只检查已有selected候选的Gold消除，不是Agent patch success。normal/target/observation/source/字节绑定与未过gate逐项分账，零候选时保留完整固定分母。

## 验收、失败与安全

工程与synthetic smoke通过只放行本次DEV校准，不放行repair或canary。报告真实模型请求/tokens、各任务生成状态、scope gate/补证/预算中止、独立Gold（若可运行）以及machine trusted=0。不是因全issue trusted为0就伪称系统没有新运行，也不将有限候选叫可信数。若未知阻断覆盖，按新失败回DEV改通用证据机制，另版先冻，不改旧namespace/source或预算。

只有剩余义务证据与同版DEV质量门槛真正通过，才历史排除新canary一次≥2/3，再Agent修复/official/DEV30/Fresh30/E2；本次全部关闭。容器离线、pull-never、不下载新task、不重启/修改Docker/IPC/VHD/registry/proxy/tunnel/key，不删除；Gold scorer可在独立评分容器临时施加Gold，不改宿主生产源。原201产物与全部旧负记录保持，不上传raw/probe/Gold/key，不保证完美或30/30。
