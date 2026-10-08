# 公开旧版本资源：手动直连下载，不安装

状态更新：用户已下载并核验，本机[公开发行源码对照已完成](E1C2_RELEASE_WITNESS_RESULTS_2026-10-08.md)。以下原下载步骤保留作来源记录；当前无需重复下载，禁止重跑已started witness目录。

本轮本地Git标签与有界history查询均未找到Marshmallow2.19.3，旧版本witness未执行。需要的是公开纯Python包，不是新task镜像，不需要几十GB磁盘。

[官方PyPI版本元数据](https://pypi.org/pypi/marshmallow/2.19.3/json)（2026-10-08核对）列出 wheel：`marshmallow-2.19.3-py2.py3-none-any.whl`，49,981bytes（约49KiB），SHA256 `cb1e88b8b098ee6d0fb984e40762cb94e200c067426e43496e55b82b563feabf`。这是发行包身份，不冒充canonical Git snapshot，也不证明probe会通过。

关闭VPN全局/TUN或退出VPN，再在终端运行：

```powershell
Set-Location 'D:\codex\working\project20260827'
powershell.exe -NoProfile -File '.\scripts\download_e1c2_version_witness.ps1'
```

脚本使用系统curl，显式`--noproxy '*'`、HTTPS、进度条、15秒连接/180秒总超时、retry0；不改全局ExecutionPolicy、不改代理/环境变量/Docker/tunnel、不安装/解压包、不执行下载源码。同名已核验文件复用，错误文件/partial保留不删除不覆盖。若ExecutionPolicy拒绝运行，请报告该错误，不自行全局绕过策略。HTTP代理排除不能阻止OS级VPN/TUN路由，所以需先关闭它。

保存到 `.codex/e1c/evaluation_2/public-version-source/marshmallow-2.19.3/`。下载一般秒级，国内直连失败不能保证耗时，硬超时后停止并留文件，不自动走VPN。只需回传终端VERIFIED和路径，不发密钥。

后续仍须**另冻结零模型release counterfactual协议**：安全读取zip中生产Python（排除test/dist-info、拒绝symlink/path traversal/超预算）；只读挂载旧包，在相同镜像/同probe/同optional import条件下验证实际版本、导入路径和normal/target运行。不运行setup.py，不pip install，不把旧source或评分输入模型，源码witness不等于public namespace意图或完整可信。当前没有可执行的版本counterfactual命令，勿重跑旧version-witness namespace。
