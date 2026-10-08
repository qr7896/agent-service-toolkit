# 已准备、从未执行的旧版本probe续接 v1（零模型预注册）

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent
- Origin Mode: run
- Origin Date: 2026-10-08
- Verification Status: UNVERIFIED（运行前协议）
- Version Label: prepared_version_resume_v1

命令：`uv run --frozen --offline python -X utf8 -m evals.e1c_evaluation_2_version_resume run`。provider calls/tokens=0/0、Gold读取0。新namespace `.codex/e1c/evaluation_2/version-witness-resume-zero-v1/`存在即拒绝。只续接公开failure receipt指明的source已准备、engine admission前停止的task，不执行旧v1 audit、重新找版本、复制源码或选择其他成功task。

原freeze/failure SHA绑定公开收据，必须status=INFRA_BLOCKED、phase=after_materialization_before_engine_admission、真实int容器数0、driver/task freeze均False，原目录无driver/freeze/run.log/result。11文件清单与所有字节SHA保持，原producer seal/全部产物/原probe SHA再核验；任何既有runtime产物或源变化拒绝。由源路径自动包根，原版本3.0.0rc8与原image/base不变。

只读Docker engine/image准入通过后冻新source/协议/receipt/原probe/源清单，记录started再执行一次隔离net-none/read-only/pull-never、90秒硬超时。用原已有snapshot readonly mount、原dependency blocker优先，实际导入版本/path与每源SHA必须匹配；不改原probe、原v1freeze/failure和旧资格/Gold。

rc0仅报同一原model程序在该明确旧版完成，不证明全issue、所有更早版本、原fixture完整忠实、repair或≥2/3可信gate；metadata/infra/真正probe失败分账。失败不自动retry，超时仅移除本轮临时容器。专项/Ruff通过后才执行，不下载、不动IPC/VHD/registry/proxy/tunnel/key，不开canary/TEST/C5/Fresh30/privateTest500/repair/E2。
