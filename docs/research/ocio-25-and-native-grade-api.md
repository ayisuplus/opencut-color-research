# 阶段 1A：OCIO 2.5 CPU 与原生 grade 快照

2026-10-13（Asia/Shanghai）。本文记录资料与静态分析子任务：这些子任务只读官方源码、安装附带 SDK 文档、DLL 文件哈希及实验快照，没有运行 Resolve/SDK、改实验工程、加载目标 DLL 或改静态 targets。主实验另有官方 MCP 导出与重放操作，见 [原生中性实验报告](E:/projects/逆向工程/capcut+达芬奇/docs/research/resolve-native-neutral-third-pass.md)。

## 已核实：OCIO 的曝光原理和版本差异

官方 `v2.5.0` tag 指向 **`592a122b37467c3376f2387fbbdbe7b571fad39f`**；比较基线 `v2.4.0` 为 `2831d2547d133b326c6e9a09726ceeb7fe46f997`。[官方 2.5 发布页](https://github.com/AcademySoftwareFoundation/OpenColorIO/releases/tag/v2.5.0)。本机 `G:\Davinci Studio\OpenColorIO_2_5.dll` SHA-256 已复核为 `9123ffb192738b385f8884c973ab3e0f38f8fb26d1b4cdca21c07b065ebb0155`；文件名和哈希不能证明厂商构建等于上述官方 tag。

逐文件比较这两个固定 commit：`ExposureContrastOpCPU.cpp` 的全部差异仅为两处加入 `DYNAMIC_PROPERTY_GRADING_HUECURVE` 的不支持分支；Linear/Video/Log 及各逆运算的 apply 数值代码未变。`ExposureContrastOpData.h` 字节完全相同。`Op.h` 新增 HueCurve Op 类型和该类型的 replaceDynamicProperty 重载，`OpCPU` 的虚函数顺序未变。此结论覆盖上述三份源码，不是 DLL 机器码或最终像素一致性结论。[2.5 CPU 分支 L86-L92](https://github.com/AcademySoftwareFoundation/OpenColorIO/blob/592a122b37467c3376f2387fbbdbe7b571fad39f/src/OpenColorIO/ops/exposurecontrast/ExposureContrastOpCPU.cpp#L86-L92)、[L119-L125](https://github.com/AcademySoftwareFoundation/OpenColorIO/blob/592a122b37467c3376f2387fbbdbe7b571fad39f/src/OpenColorIO/ops/exposurecontrast/ExposureContrastOpCPU.cpp#L119-L125)、[2.4 同文件](https://github.com/AcademySoftwareFoundation/OpenColorIO/blob/2831d2547d133b326c6e9a09726ceeb7fe46f997/src/OpenColorIO/ops/exposurecontrast/ExposureContrastOpCPU.cpp)、[2.5 OpCPU L34-L51](https://github.com/AcademySoftwareFoundation/OpenColorIO/blob/592a122b37467c3376f2387fbbdbe7b571fad39f/src/OpenColorIO/Op.h#L34-L51)。

以下为 2.5 官方 CPU 正向路径，`E` 是 exposure，`c = max(0.001, contrast × gamma)`；RGB 按 float 处理，alpha 保持。非线性标量支路的负值处理与 SIMD 支路应按实现分别核验，不能仅凭数学式承诺位级相同。[常数 L17-L19](https://github.com/AcademySoftwareFoundation/OpenColorIO/blob/592a122b37467c3376f2387fbbdbe7b571fad39f/src/OpenColorIO/ops/exposurecontrast/ExposureContrastOpData.h#L17-L19)。

| Style | 源码原理 | 固定源码位置 |
|---|---|---|
| Linear | `s = 2^E`；`c == 1` 时 `RGB_out = RGB_in × s`，该支路没有显式 clamp；其他标量支路为 `pow(max(0, RGB_in × s / P), c) × P`，`P = max(0.001, pivot)` | [L150-L230](https://github.com/AcademySoftwareFoundation/OpenColorIO/blob/592a122b37467c3376f2387fbbdbe7b571fad39f/src/OpenColorIO/ops/exposurecontrast/ExposureContrastOpCPU.cpp#L150-L230) |
| Video | `s = (2^E)^(1/1.83)`，pivot 也先做同一指数转换；后续曝光/对比结构与 Linear 相同 | [L360-L439](https://github.com/AcademySoftwareFoundation/OpenColorIO/blob/592a122b37467c3376f2387fbbdbe7b571fad39f/src/OpenColorIO/ops/exposurecontrast/ExposureContrastOpCPU.cpp#L360-L439) |
| Logarithmic | `e = E × logExposureStep`；`RGB_out = RGB_in × c + (e - P) × c + P`。`c == 1` 时为加法 `RGB_in + e`；`P` 根据 pivot、log step、log mid gray 转为 log 域 | [L567-L632](https://github.com/AcademySoftwareFoundation/OpenColorIO/blob/592a122b37467c3376f2387fbbdbe7b571fad39f/src/OpenColorIO/ops/exposurecontrast/ExposureContrastOpCPU.cpp#L567-L632) |

可复核的原始源码 SHA-256：CPU cpp，2.4 为 `6636bb1c6fb1f87b6faa8914c5c56023a299795164a5f585af1ce1c563421142`，2.5 为 `932a290b99b379b3e7a17dff2de32d051524bd8c540ea8562ad6bf23fdb2e514`；两个版本的 OpData.h 均为 `dc15ecc51afc3c9e6758039429e412ffd34c0ed31c857ce5b16fb6e96683d836`。GitHub 行号按原始文件计数，不能使用网页工具规范化文本后的行号。

**未知：** 本机 2.5 DLL 的补丁、构建宏、SIMD helper、优化器和编译参数；Resolve 原生 HDR Global Exposure 是否调用此算子；项目颜色管理如何影响实际结果。2.4 的地址不能搬给 2.5。以上 OCIO 公式也不能替代原生 HDR 控件输出证据。

## 已核实：新版本机 SDK 与 DRX 的公开边界

本机 Scripting README.md 更新于 **2026-08-31**，CHANGELOG.md 顶部为 **21.1**，更新于 2026-09-01。安装 `DaVinciResolveScript.pyi` 与指定提取 stub `evidence/local/resolve-21-1-install-inspection/sdk-doc-inspection/filC9D4E5F6A7B84C3D2E1F0A9B8C7D6E5F` 的 SHA-256 完全相同：`b91b53b86a946e1902789ea898eedf00cb7dd6107aba6f1276ca77fe508816ea`。[README](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/README.md:1>)、[CHANGELOG](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/CHANGELOG.md:1>)。以下是该安装快照的公开声明，不是本轮运行验证。

| 自动保存/重放入口 | 声明能做什么、缺什么 |
|---|---|
| `Timeline.GrabStill() -> GalleryStill`；`GalleryStillAlbum.ExportStills(stills, folderPath, filePrefix, format) -> bool` | 抓取当前 clip 的 still，再导出指定列表。新版 stub 的 `format` 仅标 `str`，未枚举格式、位深、颜色变换或 DRX 字段；应确认实际输出文件及配套关系。[GrabStill L2288-L2290](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/DaVinciResolveScript.pyi:2288>)、[ExportStills L2765-L2767](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/DaVinciResolveScript.pyi:2765>) |
| `Graph.ApplyGradeFromDRX(path, gradeMode, applyToAllLayers=False) -> bool` | `gradeMode` 0 无关键帧、1 源时间码对齐、2 起始帧对齐；21.1 的 `applyToAllLayers=True` 可应用所有 node-stack layers，默认只作用 active layer。多层原生 grade 不能默认按单层重放。[L2801-L2804](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/DaVinciResolveScript.pyi:2801>) |
| `Project.GetSettings()`；`Timeline.GetSettings()`；`MediaPoolItem.GetClipProperty()`；`TimelineItem.GetProperties()` | 可保存其**支持的**项目/时间线设置、clip 属性及 item 属性。ProjectSettings 声明包含 color science、input/timeline/output space/gamma、DRT、工作亮度；clip 属性包含 Input Color Space/Gamma/LUT。timeline 未用 custom settings 时返回 project settings。原生 HDR 曝光轮数值没有对应已声明 getter。[设置范围 README L213-L233](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/README.md:213>)、[ProjectSettings L490-L521](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/DaVinciResolveScript.pyi:490>)、[clip L184-L189](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/DaVinciResolveScript.pyi:184>)、[item L2465-L2467](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/DaVinciResolveScript.pyi:2465>) |
| `TimelineItem.GetCurrentVersion()` / `GetVersionNameList()`；`Graph.GetNumNodes/GetNodeLabel/GetToolsInNode/GetLUT` | 可记录当前 local/remote version、node 层、节点数/标签/工具名/LUT，不能由工具名反推出全部原生参数。[versions L2528-L2529 / L2564-L2566](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/DaVinciResolveScript.pyi:2528>)、[Graph L2772-L2796](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/DaVinciResolveScript.pyi:2772>) |
| `ProjectManager.SaveProject()`；`ExportProject(projectName, filePath, withStillsAndLUTs=True)` | 可保存/导出实验工程；参数包含 still/LUT，但该简短声明没有逐字段完整性合同。需要媒体归档时 `ArchiveProject(...)` 是另一个接口，不应把普通 project 导出当全媒体备份。[L1706-L1708](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/DaVinciResolveScript.pyi:1706>)、[L1733-L1736](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/DaVinciResolveScript.pyi:1733>) |

官方材料有 DRX 的**语义说明**：Resolve 20 Colorist Guide 描述 still image 与 DRX 配套，DRX 保留 grading/effects 数据；Resolve 19 New Features Guide 第 7 页明确 DRX 可包含原生色彩 palettes（包括 Primaries/HDR/Curves）、sizing 等。后者说的是官方 Renderer 插件的跨应用传递能力，且列出 temporal FX、Magic Mask 不转移；不能扩张为 Resolve 21.1 任意 grade 的全部字段都完整、或本项目已经完成重放。[官方 20 Colorist Guide，印刷页码 250](https://documents.blackmagicdesign.com/UserManuals/DaVinci-Resolve-20-Colorist-Guide.pdf)、[官方 19 New Features Guide，第 7 页](https://documents.blackmagicdesign.com/SupportNotes/DaVinci_Resolve_19_New_Features_Guide.pdf#page=7)。

**未找到公开结构合同：** 本轮读取的安装 README/.pyi 和上述官方文档没有 DRX 的 XML schema、二进制布局、原生 HDR 字段到 UI 数值的映射或稳定编辑规范。因此原生 DRX 应先作为 opaque grade 快照保存/重放；某文件即使能被 XML 解析，也不能擅自改字段来制造“原生 EV 设置”。这里的“未找到”限本轮已核对来源，不声称穷尽所有官方材料。

## 给主实验的建议（尚未执行）

对**隔离实验对象**，每档保存：原生 still/配套 DRX、实验 project 导出、当前 frame/timecode/version/node layer、支持的颜色管理及素材输入属性快照，再保存真实渲染像素与文件哈希。保持原生 UI 数值/实验动作的直接证据，DRX 成功导出不等于数值读取成功。重放时用新工程、明确 layer/keyframe 模式，并比较输出；LUT、CDL 和自有 OCIO 运算分别标明通路，不替代原生 HDR 曝光。这些 API 可自动收集既有状态和批量重放 grade，但本轮没有新增原生 HDR 数值自动 setter 证据。

## 2026-10-13 附加：原生 HDR descriptor 定点静态检索

新版实验快照 `Resolve.exe` SHA-256 为 `1a109e719f2d5e20167ecd9e0f1a37407cf62702fcea366e5e7f6dbbdb826f83`。对其 `.rdata`、`_RDATA`、`.rodata` 共 324,683,264 字节做分块只读扫描，找到 223 个 `.proto` 标记并成功解析 39 个内嵌 `FileDescriptorProto`；OCIO 2.5 DLL 相同范围没有 `.proto` 标记或此类 descriptor。结构检查使用 [Protobuf 官方 descriptor 定义](https://github.com/protocolbuffers/protobuf/blob/v29.3/src/google/protobuf/descriptor.proto)，没有运行目标程序。

其中存在实际 HDR 参数 schema：`IP/VaCommon/Schemas/Parameter.proto`，RVA `0x8a2dc00`，首选 VA `0x148a2dc00`，文件偏移 `144885760`，序列化长度 6309 字节、SHA-256 `4cfaab0a24cf9007cdca748c6e85f6d54c5265780de32bab2ee5b50a1bb4de4e`。它声明 `HDRGradeableKeyframeableParams` 的 `zonename` #1 / `gainjz` #2 / `offsetaz` #3 / `offsetbz` #4 / `temperature` #5 / `tint` #6 / `saturation` #7；另有 pivot/falloff 与节点状态消息。`ParamValueType` 的 #16/#17/#18 引用对应 HDR 参数列表。RAW Radiometry 的 exposure、HDR10+/Vivid metadata 和配置字段另有 descriptor，不能混为原生曝光轮。

**首次检索的边界与决定（后续结构连接见下一节）：** 此处获得的是本机内嵌参数结构的可追溯证据，不是官方公开 DRX 编辑规范。neutral DRX 的两个已解压 Body 长度确认为 203/142 字节，但首次检索时尚未把它们与该 schema 建立类型连接，也未确认 `gainjz` 与 UI EV 的数值映射；没有根据字段名猜 `2^EV` 或改写 DRX。停止“猜字段并编辑 DRX”路径，保留这些 descriptor 作为后续受控验证种子。检索未覆盖压缩/加密/无文件名的 descriptor、运行时生成 schema 或其他 section，不能把未匹配解释为算法不存在。私有证据见 [静态检索 JSON](E:/projects/逆向工程/capcut+达芬奇/evidence/local/resolve-exposure-20261013/analysis/resolve-native-grade-schema-scan.json)。

## 2026-10-13 附加：neutral Body 的结构连接验证

从已有 39 个 descriptor 重建了 401 个 message 定义，依赖全部闭合，没有追加 `.rdata` 扫描。223 是 `.proto` 子串位置数，不是 schema 数：39 处满足此前限定的 inline descriptor 名称头，39 处全部解析成功；其余 184 处不形成该候选头，不能当作 184 个“漏掉的根”。

203/142 字节的 neutral Body 均与 `ProtoVersion.VersionBody` 达成完整递归结构匹配，分别解释 60/35 个字段及 16/9 个嵌套 message；field number/wire type 错误、未知字段、required 缺失、oneof 多成员冲突和未消费字节均为 0，动态 protobuf 解析及初始化检查亦通过。每份还有 19 个仅把两块数据当 opaque bytes 的兼容类型，只有 VersionBody 解释了内部完整类型树。因此这是强结构对应证据，仍不是运行时反序列化入口的证明。[完整字段树与候选比较](E:/projects/逆向工程/capcut+达芬奇/evidence/local/resolve-exposure-20261013/analysis/drx-neutral-descriptor-match.json)。

**声明路径**已连接：`VersionBody.graph → Graph.nodes → Node.nodeparams → NodeParams.params → Parameter.value → ParamValueType.hdrgradeablekeyframeableparams_field (#16) → HDRGradeableKeyframeableParamsList → HDRGradeableKeyframeableParams`。它证明根 schema 允许承载 HDR 参数，不代表该分支存在于 neutral 样本。

**实际观测路径**只到 `Parameter.value.int_field (#2)`：body0 的 graph node 与 ptzrnode、body1 的 ptzrnode，均见 key `0xc0000001`、int 值 `1`；两份样本没有 HDR #16/#17/#18 value 分支。已检查的 VersionBody/VersionTable/Parameter descriptor 没有 enum 定义；`Parameter.key`、`Node.nodetype`、HDR zone type 都是 uint32，没有提供 HDR 参数 ID 或 UI 控件身份枚举。该 key 的用途、非中性 HDR 参数的 key/layer、`gainjz` 与 UI EV 的映射仍未知。此轮到此停止，不改 DRX，也不扩大扫描。

## 2026-10-13 附加：受控 CDL saturation 样本的增量结构

主实验报告通过官方 SDK 在隔离副本执行 `SetCDL(NodeIndex=1, Slope='1 1 1', Offset='0 0 0', Power='1 1 1', Saturation=0.75)`，随后导出实际文件 `cdl_sat_075_1.1.2.drx`（18,719 字节，SHA-256 `e0c347b61be016d6b674c0718652161c4e1c751930848a4df1737d44884387fe`）。本子任务只读该文件，在内存解压两个 Body，并复用已有 VersionBody 严格解析器与 neutral 比较；没有调用 SDK 或改写 DRX。Body 编号按 XML 文本出现顺序，不据此命名 node layer。

Body0 从 203 增至 429 字节，完整匹配 126 个字段及 49 个嵌套 message；Body1 仍为 142 字节，匹配 35 个字段及 9 个嵌套 message。两份的 wire/type 错误、未知字段、required 缺失、oneof 冲突及未消费字节均为 0，动态 protobuf 检查也通过。`HasCorrection` 按文档顺序由 `false/false` 变为 `true/false`；两个 Body 的节点身份与数量均保持，Body1 仅观察到 `lastmodtime` 值变化。

**实际新增参数路径**为 `VersionBody.graph[0].nodes[0].markstore[0].marktimelines[0].marks[0].mark[0].params`，并非原来的 `nodeparams`。该 mark 新增 15 个 `Parameter.key/value`，其中 key **`0x06000005`** 的 `ParamValueType.float_field (#1)` 为 **`0.75`**；其余 materialized 值为 0、负零、1，完整 key、类型、字段树及差异见 [私有 CDL 差异证据](E:/projects/逆向工程/capcut+达芬奇/evidence/local/resolve-exposure-20261013/analysis/drx-cdl-sat075-diff.json)。原 `nodeparams` 中 `0xc0000001/int_field=1` 保留。参数比较按容器路径与 key 配对，避免将 repeated 列表的位置当作参数身份。

**事实与未知：** 这是公开 SetCDL 动作之后出现的非中性序列化关联；单样本中的 `0.75` 与请求值相符，尚不足以建立完整 key→UI 控件映射，也不能区分其他 14 个键的显式改值与默认值展开。前节的 nodeparams→HDR 是 schema 允许的声明路径，此处的 markstore→mark.params 是 CDL 样本实际写入路径；两者分别保留，不能据前者指定未来 HDR 样本的落点。两个 Body 实际出现的 HDR #16/#17/#18 分支均为 **0**，本样本不提供原生 HDR 曝光或 `gainjz`→UI EV 证据。本增量到此收口，不扩大参数 ID 或机器码分析。
