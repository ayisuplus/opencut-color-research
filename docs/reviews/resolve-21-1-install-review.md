# Resolve 21.1 安装独立审查

日期：2026-10-12。独立子代理只读审查。

**结论：修复回执保护后，当前独立官方 MSI 升级步骤没有新的必须阻止项，可以按已有用户授权推进。恢复尚未实测；激活组件不能据本次静态检查签收为安全、有效许可或可用。** 主代理最新回执为 prepared / pending-uac，尚无 MSI 完成回执，本报告不将提权请求写成安装成功。

## 范围

只读检查 PE、.NET 元数据、签名、现有扫描日志、备份摘要、CAB 签名清单及待执行脚本。MSI 数据库仅以模式 0 打开并执行 SELECT，没有调用安装动作。本审查未运行目标 EXE/DLL、SDK、激活器或安装器，未修改注册表/系统配置或下载工具；仅新增此报告。

## 官方升级

本人重新查询主安装 EXE、SetupResolve.exe、ResolveInstaller.msi 的 Authenticode，均为 Valid / Blackmagic Design。已核对主代理保存的 ResExt01–19 签名清单：19 项均记录为 Valid / Blackmagic Design，未重复逐包签名查询。

待执行脚本检查管理员令牌、Resolve 关闭、备份成功摘要、MSI 固定哈希/签名及 CAB 存在；使用原安装位置、禁止自动重启、等待退出并记录结果。它不自动启动软件，不串联激活，仅接受 0 / 3010。MSI 固定 SHA-256：`f23be5c1fc94c43c474cdb84a6ad41ae9786e35543f5656614909c53d0886217`。

发现的 P2 已关闭：原脚本在 try 内拒绝已有 result，但 finally 仍覆盖同一路径。主代理已将该检查移到 try/finally 外；只读复核时脚本 SHA-256 为 `ee3a6a1ecf42dbd83fbf791b7bf170e71ba00cd17873a8f2c70ea15206efcbca`。未执行拒绝分支或安装测试。

本人独立读取 MSI 表确认 RemoveExistingProducts=1499，InstallInitialize=1500：旧产品先移除，再进入新安装事务，不能当作侧装。[微软的序列说明](https://learn.microsoft.com/en-us/windows/win32/msi/removeexistingproducts-action)支持这一边界。

主 MSI 自带 BMDPanelDriverInstallAction、SetupFirewall、DDMXAction，不能声称只改核心、不动驱动或网络规则。前两者类型 3138 / 3170 含 Continue 位 0x40，允许忽略其退出码；MSI 返回 0 / 3010 不独立证明这些动作或整个应用健康。[微软定义](https://learn.microsoft.com/en-us/windows/win32/msi/custom-action-return-processing-options)

备份摘要覆盖四组共 4372 文件、13456989591 字节，四份 manifest 存在。逐文件 SHA 匹配依据主代理执行记录，本人未重复重算全部备份；脚本检查摘要成功标志，不是重新验证每个文件。旧缓存 MSI 和两份注册导出已备份，但旧完整安装来源缺失，rollback_tested=false。复制目录不证明恢复 MSI 注册、驱动、网络规则或旧软件可运行状态。[微软也说明](https://learn.microsoft.com/en-us/windows/win32/msi/rollback-custom-actions)，直接改变系统的自定义动作未必可由一般安装回滚逆转。

## 激活组件

独立 PE 读取与现有 imports.json 一致；四个内层文件本次解析无警告或 delay import。关键摘要：

| 文件 | 字节 | SHA-256 |
|---|---|---|
| 外层 .NET 助手 | 6618112 | a15cb68755749178733dcd6dd03b5856617364d461c0c0a2a7d53df5f9a2c78d |
| DVREMU2MAN.exe | 105368 | 2083beb78b4ceba4a8fe819ed2307b4c0a22622f32caea60fcea7de0bcbd76b8 |
| vcruntime140_1.dll | 13208 | 4a24da2b20defc6f8e000aeaba593b4a97ceac0f493e3b99cd51d4b096451f66 |
| libbz2.dll | 70656 | 57d9cb6e10ba90a3b8e9c2b2eab2b80937b088123adb482eab71ef550cce7794 |
| libcrypto-3-x64.dll | 6379520 | 2249476a14dea73ae271d661483bdc6c15e45b931f8dbfd0bd1b84193cf420ea |

MAN 中偏移 19488 的 13208 字节与所提取 DLL 相同；审查起点旧安装中的同名 DLL 也独立重算为同一摘要。这说明旧环境已有该组件，不能推广成外层全部代码或新版本组合安全。

外层未签名，MAN/DLL 的 R2R 签名当前无法建立信任根链；不据此直接判定恶意。实质线索是：外层 .NET 元数据包含定位安装路径、文件备份/替换、子进程运行及自动确认对话框的代码名称；MAN 导入注册表创建/写值、文件删除/写入与 ShellExecute，并要求管理员权限；替换 DLL 导入 VirtualProtect、动态加载/函数解析及注册表读取，导出 CRT、HID 和设备枚举接口。它们与持久性文件替换、许可模拟及进程内改写风险相符，不是普通微软 runtime 更新的证据。

这仍是声明导入、元数据和字符串观察，未恢复完整控制流或运行期副作用。在已检查范围未见明确的服务创建、计划任务、关闭 Defender 或安全排除入口；动态调用/子进程未覆盖，不能声明这些行为绝不存在。libcrypto 的通用网络导入不证明外联或窃取。

现有两份 Defender 日志分别报告内层目录与外层 EXE no threats。未检出不证明行为安全，也不覆盖后续注册表、DLL 替换或宿主运行效果。

## 许可与剩余验收

已有用户授权明确覆盖升级和所提供的激活程序，本审查不要求重复取得同一授权。执行授权、官方文件签名、安装完成与 Studio 许可是不同事项。若目标为 Studio，[厂商 Studio 21 说明](https://www.blackmagicdesign.com/support)列出许可 dongle、Blackmagic Cloud 许可或 activation code；安装官方包不能证明取得许可或模拟器对新版有效。本报告不作法律安全判断。

可以推进已审查的独立官方升级；不能将整个混合包、激活有效、软件可用或安全恢复一起标为通过。激活器风险单列，现有证据不足以给它安全背书。安装退出码、实际版本、重启需要、启动/许可状态和任何后来实际运行的组件需另行记录。本轮不再扩大分析。
