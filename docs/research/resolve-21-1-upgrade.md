# Resolve 21.1.1 升级与原生 MCP 检查

升级与实测日期：2026-10-12。执行后独立验收日期：2026-10-13。此次升级暂停原生曝光实验；旧静态研究副本保持独立。

## 已核对的安装来源

用户指定 `G:\dfq21 Win.zip`，并明确授权安装及使用其中的激活程序。实际主安装器为 21.1.1.10，MSI ProductVersion 为 21.1.10010。

- 主安装器、`ResolveInstaller.msi`、`SetupResolve.exe`、新 `Resolve.exe`、`ResolveMCP.exe` 均通过 Blackmagic Design Authenticode 验证。
- 19 个外部安装 CAB 均通过 Blackmagic Design Authenticode 验证。数据包完整性测试和解压均返回 0。
- 未打开包内的第三方教程链接，也未执行教程指令。
- 私有原始文件、日志、许可相关注册表备份保存在 `evidence/local/`，不进入 Git。

| 文件 | SHA256 |
| --- | --- |
| 主安装器 | d2b08344c9b61d7975cc037f05db0112a036841b8720e3d07305367297e9b55b |
| ResolveInstaller.msi | f23be5c1fc94c43c474cdb84a6ad41ae9786e35543f5656614909c53d0886217 |
| 新 Resolve.exe | 1a109e719f2d5e20167ecd9e0f1a37407cf62702fcea366e5e7f6dbbdb826f83 |
| 新 ResolveMCP.exe | edd5dee719f815b928b445c32fec4dbd6ef5d09210f50a1c72a57583af87fad8 |

## 激活程序检查

外层是未签名的 .NET 程序。只读提取发现四个内嵌文件，其中 `DVREMU2MAN.exe` 是 DVREMU2 Manager，名为 `vcruntime140_1.dll` 的文件产品信息也是 DVREMU2，并非普通微软运行时。

静态字符串和导入表显示其功能包括更换安装目录 DLL、执行 `install` / `renew`、写入许可注册表项及移除安装目录中的部分 Visual Studio runtime 文件。DLL 有进程内加载及内存保护操作。未由此证明存在服务、计划任务或修改 Defender 的行为；静态导入表也不能证明不存在动态调用。

外层和提取后的内层文件分别使用现有 Defender 进行自定义扫描，均返回 0、未检出威胁；未关闭实时防护、添加排除项或恢复隔离文件。扫描结果不替代行为审查。

旧安装的 `vcruntime140_1.dll` 与本次内嵌 DLL 字节相同，SHA256 为 `4a24da2b20defc6f8e000aeaba593b4a97ceac0f493e3b99cd51d4b096451f66`。此事实只证明旧环境已使用同一 DLL，不证明外层所有行为安全。

## 离线备份与升级边界

Resolve 关闭时完成四份逐文件 SHA256 核对的备份，共 4,372 个文件、13,456,989,591 字节：

| 范围 | 文件数 | 字节 |
| --- | ---: | ---: |
| `G:\Davinci Studio` 旧安装 | 3,609 | 5,913,315,420 |
| 用户 Roaming 配置与默认项目库 | 181 | 41,389,408 |
| `OC_COLOR_001_TEST` 专用库 | 10 | 5,849,435 |
| ProgramData 公共支持目录 | 572 | 7,496,435,328 |

备份位置：`evidence/local/resolve-upgrade-backup-20261012/`。另保存旧缓存 MSI、Resolve 安装及文件关联注册信息、已有模拟器许可注册表项。原旧安装的临时安装源已不存在，因此文件备份通过不等于 Windows Installer 回滚已验证。

原始新 MSI 的 `RemoveExistingProducts` 位于 `InstallInitialize` 之前，升级会先卸载旧产品。主 MSI 自带面板驱动安装、防火墙和 Extras 部署动作，不能声称只更换 Resolve 主文件。安装采用原路径 `G:\Davinci Studio`，禁止自动重启，不串联激活或自动启动 Resolve。

私有安装脚本在管理员权限下核对备份摘要、MSI 固定哈希和签名，运行官方 `msiexec`，保存详细日志及结果。独立审查指出的“重跑时覆盖旧结果”问题已修正；拒绝重跑时保留原回执。

## 原生 MCP 已验证到的范围

官方签名包内 `DaVinciResolve.mcpb` 的 manifest 和 Node 代理源码提供 14 个工具：启动及状态查询、更新说明、脚本 API 和文档查询、安全及非沙箱脚本执行、DCTL/LUT 列举和写入等。代理转发至原生 `ResolveMCP.exe`，内置 Python 为 3.14.4。

这证明安装包包含原生 MCP 组件。尚不能据此证明 MCP 能连接当前工程，或 SDK 能直接修改原生 HDR Global Exposure；后者仍须实际工具清单和工程调用验证。

进一步从签名有效的 `ResExt03.cab` 提取并核对官方 `DaVinciResolveScript.pyi`（123,195 字节，SHA256 `b91b53b86a946e1902789ea898eedf00cb7dd6107aba6f1276ca77fe508816ea`）。其 `Graph` 接口提供 LUT、节点启用、缓存、DRX 应用和重置等操作，未见直接设置 HDR Global Exposure 的公开接口；因此不能承诺原生 MCP 自动操作所有调色控件。

## 当前执行状态

用户完成 Windows 确认后，官方 MSI 于 23:31 完成，退出 0，无需重启；实际版本为 `21.1.1.10`。安装后主程序和 MCP 文件 SHA256 与受检官方包一致。测试 `Project.db` 在首次启动前与旧备份哈希相同，库列表保留。

已按用户授权，于 23:35 运行原始激活助手的同哈希副本。后续观察该助手已退出，模拟器 DLL 已替换，实时防护仍开启。未取得该 GUI 助手退出码，也未审计其全部运行期副作用；实际验证限于以下启动与 SDK 功能。

- 原生 MCP 完成 `initialize` 和 `tools/list`，实际返回 14 个工具及服务版本 21.1.1。
- `launch_resolve` 成功启动新版，`get_resolve_status` 返回 `running: true`。
- 沙箱 `run_script` 读取专用库，并在默认工程无时间线、素材和子文件夹时载入唯一指定的 `EXPO_001_HDR_GLOBAL`。回读得到一条 `PATCHES_1080P30` 时间线、1920×1080、30 fps、一个视频轨道及一个测试片段。
- 未调用 `run_script_unsafe`，未更改调色值、颜色管理设置或导出测量帧。

首次读取误用了不存在的 `GetCurrentProjectLibrary`。失败脚本和回执已独立保存；改为官方文档中的 `GetCurrentDatabase` 后重新验证通过。同时修正客户端的错误识别：除了 JSON-RPC 和 `isError`，也检查工具内容中的 JSON `error`，不以传输成功代替脚本成功。

原生 MCP 已通过官方 CLI 登记为 `davinci_resolve`，命令为 `G:\Davinci Studio\ResolveMCP.exe`。登记前备份 Codex 配置；CLI 省略了原有 `node_repl` 的空 `args`，已精确补回。除新增服务器外，解析后的全部配置与备份相同。[OpenAI 官方文档](https://learn.chatgpt.com/docs/extend/mcp?surface=cli)说明配置由桌面、CLI 和 IDE 共用，并支持本地 STDIO 服务。当前聊天尚未载入新工具目录；桌面重启后加载。当前本地直连已经完成实际调用。

本轮还发现新安装使用 `OpenColorIO_2_5.dll`，SHA256 为 `9123ffb192738b385f8884c973ab3e0f38f8fb26d1b4cdca21c07b065ebb0155`。旧 21.0 / OCIO 2.4 研究副本及哈希保持不变，其函数地址和分析不能直接套用到新库。下一轮曝光研究须重新固定 21.1.1 环境并确认颜色管理；原生 HDR Exposure 的直接控制和画面对照仍未完成。

脱敏验收记录：[升级与 MCP 实测结果](../experiments/resolve-upgrade-result.json)。

独立审查：[升级前检查](../reviews/resolve-21-1-install-review.md)、[执行后验收](../reviews/resolve-21-1-runtime-review.md)。旧工程入口：[真实工程准备](resolve-project-preparation.md)。
