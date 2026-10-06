# Faithful DEV：引擎恢复后的零付费完整回放

## Material Passport

2026-10-06；旧DEV12开发数据，非独立确认。原模型试验16请求/37593tokens，验证INFRA_INVALID原件保持不变。本次只读16份原响应，另立`faithful-input-dev-v1-infra-replay-v1`，新增provider调用/tokens均0，无缺失缓存角色、无provider重试。

## 运行态恢复与安全边界

获准正常停止Docker，先备份改名`Docker/run`，启动发现另一个旧`docker-secrets-engine/engine.sock`；分别启动失败会再留下socket。获准最后一次联合修复，同一停机内将两个IPC目录备份改名后启动成功。备份原件均保留，不删除、不读密钥、不动镜像、VHD、注册表、代理或tunnel配置。最后两份备份为`C:/Users/qq人/AppData/Local/Docker/run.ipc-joint-backup-20261006-091211`与`C:/Users/qq人/AppData/Local/docker-secrets-engine.ipc-joint-backup-20261006-091211`。此前两份单独备份也保留。

启动命令stdout读取出现GBK解码警告，命令退出0；健康判断不依赖该stdout。真实engine及九个既有不可变image ID全部通过新预检，同source方法/输入逐项相等。回放/独立评分结束后真实engine仍健康。未声称tunnel端到端重验成功；本轮没有改动其文件/服务。D盘约38.64GiB空闲，无新增镜像下载。

## 完整结果与增益边界

9题完成，固定分母12，6个两次稳定base失败候选；Gold独立评分5真1假。原四参考warm_start、export_text ndarray、ISO-Z、List(DateTime)保留，新MultiTaskLassoCV为第五个Gold区分候选。跨两仓库。机器`trusted_reproducer=false`原样保留；人工可观察行为审查5/12，不是自动语义证明、真实Agent修复率或独立泛化。

Lasso输入seed/n/d/X/y与公共事实相符，终端API自动归属到继承fit；探针观察不同alpha的MSE，范围不等于模型拟合质量的全面验证。warm_start只证实API可用，不证明森林增长的所有性质；其他审查范围逐题列在[公开gate](../../data/e1c_evaluation_2_faithful_replay_dev_gate.json)。同一新生成结果回放替代无效环境验证，不能把这次0调用写成生成成本为0；源生成37593tokens，相较此前26762多10831（约40.5%）。覆盖4→5是开发描述，不是已控制消融的因果提升。

未过：generator探针Gold后仍失败；pytest7432定义测试函数但直接脚本未调用，6680简化fixture未产生稳定失败，7985公开行为不足而弃答；另三项历史准入失败仍在12分母，不替补。不补写逐题规则，不在已封存四批canary上重测。

## 放行与下一步

开发参考保持、两仓库及新增输入/定位有可执行证据，可完整冻结下一独立canary方法。不是独立≥2/3放行；新canary必须先冻全部源文件/协议/Flash预算，再metadata-only排除所有历史身份选三题，固定分母3且无替补。生成前/每请求前核真实engine/image，环境失败不得消耗后续请求或算软件证据。保持公开输入事实/生产源码，容器无网络，Gold仅独立评分。大镜像下载仍交用户直连终端，官方小metadata才可7892。TEST/C5/Fresh30、Agent repair、E2均不因DEV5/12而开放。

原freeze/state/cache SHA与六个独立结果SHA绑定公开gate；原错误试验不回填，全部日志仍在本机`.codex`，不上传Gold/test正文或任何密钥。
