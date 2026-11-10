# 曝光研究第一轮：静态入口与证据边界

日期：2026-10-12。阶段：1A 已启动，尚未完成真实曝光控件的行为对照。此次授权范围为原文件保留、选定文件副本分析，以及独立目录安装官方 REA 6.4.0 / Ghidra 12.1.4。

本文件保留第一轮的历史范围；后续实际运行 headless / Lua SDK 和像素函数研究见 [第二轮记录](resolve-exposure-second-pass.md)。下文“未执行”只描述第一轮。

## 已固定的对象

选定 `Resolve.exe` 与 `OpenColorIO_2_4.dll`，先计算原文件 SHA-256，再复制到 Git 忽略的 `evidence/local/resolve-exposure-20261012/targets/`，比较副本与原文件，并复查原文件摘要。两份副本匹配，原文件摘要未变。副本标为只读，未执行目标程序或 DLL。

| 文件 | 字节数 | SHA-256 |
|---|---:|---|
| Resolve.exe | 579935160 | `4f3a637aadb6817d3cb5afa2ebcb97d646af8fd67e8b262acda26ff06acfa91e` |
| OpenColorIO_2_4.dll | 4710840 | `a1658f7bbe6193ce34f9f6dd4beaf5820c19a2455758c91a9bdb6d2ba5444478` |

安装版本资源为 21.0.0.47。这是当前安装快照的静态元数据，不能证明官方文件完整性。详细原路径、描述符和输出保存在上述私有实验目录。

## 第一项确定发现：主程序声明引用 OCIO

按原始 PE 导入描述符遍历得到 146 个模块，其中有 `OpenColorIO_2_4.dll`，该项包含 57 个按名称导入的接口。接口涉及 Config、ColorSpace/Look/DisplayView 变换、FileTransform、CDLTransform、CPUProcessor 和 PackedImageDesc。主程序还存在 `Resolve FX OpenColorIO` 的文本入口。

这证明该快照中存在声明的库依赖和调用入口，不能证明这些接口运行时一定被调用，更不能证明原生曝光轮、全部节点或整套调色引擎由 OCIO 实现。主程序的这组直接导入中没有 ExposureContrastTransform 构造接口；配置驱动或间接路径仍可能使用它，不能据此作不存在的结论。

原始描述符位置与每个 IAT 位置已记录在 `analysis/ocio-iat-seeds.json`，57 个符号及覆盖信息在 `analysis/pe-inventory.json`。地址采用 RVA 与首选映像基址标记，未冒充运行时地址。结构解释依据 [Microsoft PE 规范](https://learn.microsoft.com/en-us/windows/win32/debug/pe-format#import-directory-table)。

## 解析限制与更正

已有 pefile 读取器最初仅返回主程序 75 个导入模块，并报告导入符号/错误数量上限等 33 条警告。因此最初没有读到 OCIO 不能作为否定证据。之后按声明的导入目录、20 字节描述符和目标库查找表直接复核，确认上述引用。

读取脚本现在保留解析器警告、原始描述符、OCIO 查找表及摘要，明确将主程序的常规解析标为 partial。该交叉核查只补足当前导入目录，不宣称验证了主程序所有 PE 结构或所有导入符号。[读取脚本](../../experiments/inspect-resolve-pe.py)

对安装根目录中小于等于 24 MiB 的 220 个 DLL 进行常规导入表抽查，没有返回 OCIO 引用。该结果受范围和解析覆盖限制，不作为“只有主程序使用 OCIO”或“这些模块绝无间接调用”的依据。

## 可追查的入口

- OCIO 副本有 1010 个导出项，筛选到 35 个与 ExposureContrast / CDL / ColorSpaceTransform 相关的项；其中 ExposureContrast 相关 8 项。导出存在不等于原生曝光功能调用它们。
- 主程序出现 Exposure 字节标记 303 次，并有若干曝光变化信号及 RAW 摄影机曝光参数。它们可能对应不同功能，不能一概归入 HDR 曝光轮。精确位置在 `analysis/resolve-marker-locations.json` 与 `analysis/resolve-string-seeds.json`。
- 第一轮优先确认一个明确的 UI 控件，再使用相关信号/参数及库 IAT 位置寻找静态调用。当前没有函数到该控件的因果对应证据。

## 工具与接口核查

REA 6.4.0 已装入 `tools/rea/`；采用固定版本、npm 官方 registry 和关闭安装脚本的方式，未修改全局 PATH 或 Codex 配置。`inspect-artifact` 和执行无关的 managed 分类已对 OCIO 副本完成；后者确认 PE 没有 CLI 目录，属于本次原生分析入口。

Ghidra 12.1.4 官方完整包为 569649598 字节，SHA-256 为 `ddac49f903da9d5bac833e5cc79395098b9c33cfd3279be5f31bd00387d2d4db`，核验后解压至 `tools/ghidra/ghidra_12.1.4_PUBLIC/`，复用本机 JDK 21.0.11。[官方 release](https://github.com/NationalSecurityAgency/ghidra/releases/tag/Ghidra_12.1.4_build)。REA doctor 在明确的 Ghidra/自有 DLL 范围内通过 11 项检查，包含 Windows native authority；它不意味着所有其他 provider 或 MCP 客户端都已配置。

自有 [Rust 夹具](../../experiments/rea-exposure-fixture.rs) 的真实反编译已通过：输入摘要固定，完整函数为 5 字节，Ghidra 返回 `ADDSS XMM0, XMM0` 与 `RET`，浮点伪代码为输入与自身相加，与源码的乘二和独立编译器汇编一致。CLI 正常退出，DLL 摘要未变，没有加载或执行该 DLL。

随后对 OCIO 副本的 `ExposureContrastTransform::Create` 得到真实函数分析，入口 RVA `0x2b4380`、首选映像 VA `0x1802b4380`，函数体连续 211 字节、50 条汇编。静态结果显示对象和持有结构的分配/初始化，支持这是创建入口；没有在此定位像素曝光运算或 Resolve 的曝光控件。Ghidra 的函数签名与伪代码对 C++ 聚合返回类型存在差别，不能把推断的 ABI、类型或某个折叠符号名当原始源码。完整伪代码仅留在私有实验记录。

摘要、Evidence ID、工具版本、正常退出状态及分析后原文件/副本完整性复核见 [工具验证记录](../experiments/rea-native-verification.json)。两份选定原文件与副本的分析后摘要仍匹配最初记录。

本机 SDK 有 CDL/LUT/预设应用接口，但没有已声明的原生 Exposure/HDR Exposure setter。`CreateProject` 使用当前项目库，不自动提供独立测试库；官方附带批量样例还含删除渲染任务等操作，因此没有原样执行。详见 [SDK 边界核查](resolve-exposure-sdk-boundary.md)。

界面自动化也有实际能力限制：当前会话只提供浏览器控制，原生应用控制未启用；已安装 REA 6.4.0 的 `NativeUiObservation.js` L39-L40 则要求 Mach-O/macOS 目标。因此不能靠这个 REA 功能在 Windows 上设置曝光轮。本轮只读了实现与帮助，未尝试控制或启动 Resolve；下一轮需先在正常界面中确认专用测试库与控件设置。

已经生成自有灰阶/色块夹具，保留 16-bit 实际码值、颜色约定和摘要，供下一轮正常控件测试使用。它是 [实测输入准备](../experiments/color-protocol.md)，不是 Resolve 已经处理这些图像的证据。

公开 OCIO v2.4.0 源码可作为库函数的定位参照：曝光变换的 factory 创建对象，CPU linear 分支在对比度与 gamma 的乘积为 1 时将 RGB 乘以 `2^exposure`，保留 alpha。[factory 源码](https://github.com/AcademySoftwareFoundation/OpenColorIO/blob/v2.4.0/src/OpenColorIO/transforms/ExposureContrastTransform.cpp#L10-L13)、[CPU 源码](https://github.com/AcademySoftwareFoundation/OpenColorIO/blob/v2.4.0/src/OpenColorIO/ops/exposurecontrast/ExposureContrastOpCPU.cpp#L143-L166)。这是公开库的特定分支；本机 DLL 的 ABI 名称只表明 2.4 命名空间，未证明它正好由此 tag 编译，也未证明 Resolve 的原生曝光轮采用该分支。

## 本轮验证与后续工作

1. 已通过自有源码小 DLL 的原生静态验证，包含完整函数反编译、CLI 退出及摘要不变。
2. 已取得选定 OCIO 创建入口的真实反编译；像素处理分支与 Resolve 原生控件到函数的对应仍待追查。
3. 暂选 HDR palette 的 Global Exposure 为下一轮拟议控件，准确名称与档位仍以正常界面确认。真实画面对照需专用项目库或明确隔离的测试上下文、已固定颜色设置及经界面确认的控件档位。未确认这些条件前不打开用户现有工程或加载 SDK native DLL。
4. 导出帧的格式、位深、范围和颜色标签单独核验；缩略图、截图或 SetCDL 输出不能替代原生曝光的真值。

用户已确认当前没有专用测试项目库。下一轮准备步骤见 [测试库与首组画面对照](../experiments/resolve-test-library.md)。本轮独立复验与已关闭的问题见 [对抗性审查](../reviews/exposure-first-pass-review.md)。

本轮没有启动 Resolve、改变安装文件/补丁/许可机制、打开用户项目库，或导出并发布软件内置素材。阶段 1A 保持进行中，曝光数学与实际控件映射仍未知。
