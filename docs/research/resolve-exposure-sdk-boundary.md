# Resolve 21 曝光研究：安装附带 Scripting SDK 的能力边界

核查日期：2026-10-12（Asia/Shanghai）。只读范围：`G:\Davinci Studio\Documents`、`G:\Davinci Studio\Resolve.exe` 的静态 VERSIONINFO，以及 `C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting` 的文本文档和示例。未读取用户项目库或凭据，未导入 SDK 模块、加载 DLL、运行 Resolve、调用 REA、做 UI 自动化、修改安装或配置。

以上是第一轮文档核查的历史范围。第二轮已实际运行 headless 实例、SDK 导入探测和官方 Lua，只读查询成功；最新运行事实与边界见 [第二轮记录](resolve-exposure-second-pass.md)。本文件不能用作“目前仍未运行应用”的证明。

## 决策结论

**这份 SDK 可以辅助创建测试工程、应用已保存 grade、指定渲染与导出帧；本次未找到公开声明的原生 Exposure/HDR exposure 数值 setter。** 因此可考虑“正常界面中确认具体曝光控件与设置 → 保存每档 DRX → SDK 在独立测试工程应用该 grade 并导出”的真实画面对照路线。`SetCDL` 或自制曝光 LUT 的结果只能检验 CDL/LUT 通路，不能冒充原生曝光轮输出，更不能直接证明 DaVinci 的曝光实现已还原。[安装 SDK 的 SetCDL 声明](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/README.txt:508>)、[Graph 声明](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/README.txt:571>)。

“未找到公开声明”不等于证明运行时不存在任何未列出的接口。安装 README 自称列举常用 API，并允许检查对象；本轮按只读边界没有做运行时探测。[SDK API 范围说明](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/README.txt:81>)。

## 版本与来源的准确范围

| 证据 | 本次实际读到的内容 | 边界 |
|---|---|---|
| `G:\Davinci Studio\Resolve.exe` 静态 VERSIONINFO | ProductVersion / FileVersion 均为 `21.0.0.47`，ProductName 为 DaVinci Resolve | 不是本轮运行中 `GetVersion()` 返回值；未证明二进制官方完整性 |
| [安装 ReadMe.html](<G:/Davinci Studio/Documents/ReadMe.html:31>) | 标题 About DaVinci Resolve Studio 21 | 安装快照证据，不是本轮许可证或激活状态检查 |
| [Scripting README.txt](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/README.txt:1>) | Last Updated: 8 May 2026；介绍 Resolve Studio scripting | 可能随安装滞后于其他发行版本 |
| [Scripting CHANGELOG.txt](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/CHANGELOG.txt:4>) | Last Updated: 5 May 2026，顶部章节为 `21.0 Beta` | 未确认与 executable build 47 一一对应 |

官方网页明确区分 primary wheels（Lift/Gamma/Gain/Offset）、HDR 分区曝光和 RAW 曝光；RAW 处理在节点编辑器输入之前。故实验必须写明研究哪个控件，不能把这些操作统称为一个曝光算法。[Blackmagic 官方 Color 页面](https://www.blackmagicdesign.com/products/davinciresolve/color)。官方 [Resolve 21 New Features Guide](https://documents.blackmagicdesign.com/SupportNotes/DaVinci_Resolve_21_New_Features_Guide.pdf) 用于确认 Resolve 21 的公开文档来源，本报告不把该 guide 当作具体 scripting setter 的证据。

本轮没有使用第三方镜像 API 文档来补全本机 API。官方完整 API 文档的在线直链未核实；具体签名以下面安装附带 README 的行号为准。

为使安装快照可复核，记录 SHA-256（仅读取文件）：

- Scripting README.txt：`4DA3E2BFA828408181120E1F34067CA2C41174DA2FFF2AE489FA36509BDCDE7B`
- Scripting CHANGELOG.txt：`65057495F82503125CC78B147B9792B7553AB44AC1111FBCF09B35181E457E63`
- Documents ReadMe.html：`D0ED8F14717E6EC5E4FD36A49E6F6568A25839D88C9CF5DCF18B3A756BD20591`
- Modules DaVinciResolveScript.py：`0E78F374E452CED64C3D570EF620C310BCBB7685E836BFC3BCBD7599A0D4509D`

## 已声明的颜色控制 API

| 对象与准确入口 | 声明的能力 | 与曝光实验的关系 |
|---|---|---|
| `TimelineItem.SetCDL(cdlMap) -> Bool` | 字段 `NodeIndex`, `Slope`, `Offset`, `Power`, `Saturation`；节点索引 1-based。文档例子传 Python dict，RGB 值为以空格分隔的字符串。[L508-L509](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/README.txt:508>) | 可控制 CDL 参数。即使令 slope 相当于某个曝光倍数，也没有证明与原生 HDR/RAW/primary 控件等价。此处 CDL Offset 不是原生 Offset wheel 的公开 setter。 |
| `TimelineItem.GetNodeGraph(layerIdx) -> Graph` | layerIdx 可选，不传时第一层；范围由项目 nodeStackLayers 决定。[L530](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/README.txt:530>) | 取得既有 clip graph，不承诺能新增、连接或重排节点。 |
| `Timeline.GetNodeGraph() -> Graph` | 取得 timeline graph。[L439](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/README.txt:439>) | clip、timeline、group pre/post graph 不应混淆。 |
| `Graph.GetNumNodes() -> int`；`Graph.SetLUT(nodeIndex, lutPath) -> Bool`；`Graph.GetLUT(nodeIndex) -> String` | LUT 路径可绝对或相对，但须已被 Resolve 发现；可调用 `Project.RefreshLUTList()`。索引 1-based。[L571-L576](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/README.txt:571>)、[RefreshLUTList L193](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/README.txt:193>) | 设置 LUT，而非设置原生 Exposure。为项目测试 LUT 配置路径或刷新列表也涉及应用状态，本轮未执行。 |
| `Graph.SetNodeEnabled(nodeIndex, isEnabled) -> Bool`；`GetNodeLabel()`；`GetToolsInNode()` | 开关既有节点、读标签/工具列表。[L579-L582](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/README.txt:579>) | 节点开关可作 bypass 对照；工具名称不能代替参数值或算法源码。 |
| `Graph.ApplyGradeFromDRX(path, gradeMode) -> Bool` | 载入 grade 到该 graph；模式 `0` 无关键帧，`1` 源时间码对齐，`2` 起始帧对齐。[L583](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/README.txt:583>) | 可重放由正常 UI 保存的原生曝光设置，是后续条件性可行路线；仍需验证设置确已应用和输出匹配。 |
| `Graph.ResetAllGrades() -> Bool`；`TimelineItem.CopyGrades([tgtTimelineItems]) -> Bool` | 重置该 graph；复制当前 node stack layer 到目标同层。[L585](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/README.txt:585>)、[L517](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/README.txt:517>) | 限于本次新建实验工程可作对照，不能运行在现有用户工程上。 |

README 的 Graph 列表没有 Exposure、Gain、Lift、Gamma、HDR 分区参数的 setter，也没有节点创建/连接声明；`TimelineItem.SetProperty` 的公开 key 列表是变换、裁切、合成、retime 等，未列原生曝光。[Graph L571-L585](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/README.txt:571>)、[SetProperty 支持 key L894 及后续](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/README.txt:894>)。`Project.SetSetting` / `Timeline.SetSetting` 面向项目与时间线设置，不应凭空传 `Exposure` 并声称成功。[设置范围 L666-L682](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/README.txt:666>)。

`TimelineItem.SetLUT/GetLUT/GetNumNodes/GetNodeLabel` 旧入口列在 Deprecated 段；新工作优先用 `GetNodeGraph()` 返回的 Graph 方法。[Deprecated L1108-L1117](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/README.txt:1108>)。附带 `3_grade_and_render_all_timelines.py` 仍使用 `Timeline.ApplyGradeFromDRX`，而本机 README 主 API 只声明 `Graph.ApplyGradeFromDRX`；示例还会处理当前工程所有 timeline 并删除所有 render jobs。它只能阅读作参考，不能原样运行于本研究。[示例 L24-L36](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/Examples/3_grade_and_render_all_timelines.py:24>)、[L51-L78](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/Examples/3_grade_and_render_all_timelines.py:51>)。

## 测试工程与帧导出的 SDK 边界

- **工程创建不等于创建独立库。** `resolve.GetProjectManager()` 指向当前打开数据库；`ProjectManager.CreateProject(projectName, mediaLocationPath)` 创建唯一名称工程，不是新 Project Library。不能因为名字叫 Test 就认为已和用户项目库隔离；后续应先明确测试库/工程位置，操作只针对新建实验对象。本轮没有读取、打开或创建任何工程。[L88](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/README.txt:88>)、[CreateProject L116](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/README.txt:116>)。
- **素材与时间线入口已声明。** `MediaPool.ImportMedia([items])`、`CreateEmptyTimeline(name)`、`AppendToTimeline(...)`；`Project.SetCurrentTimeline(timeline)` 与 `Timeline.SetCurrentTimecode(timecode)` 可定位测试帧。[L224-L227](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/README.txt:224>)、[L251-L254](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/README.txt:251>)、[L155](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/README.txt:155>)、[L399](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/README.txt:399>)。
- **最快的单帧入口：** `Project.ExportCurrentFrameAsStill(filePath) -> Bool`，扩展名必须是有效导出格式；文档未列该方法的完整扩展名集合、bit depth、compression、data levels 或 ICC/transfer 处理。可以实测使用它，但仅返回 True 或生成 PNG/TIF 文件不能证明无损、高位深或颜色可比。[L198](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/README.txt:198>)。
- **Gallery 导出：** `Timeline.GrabStill() -> GalleryStill`；`GalleryStillAlbum.ExportStills([galleryStill], folderPath, filePrefix, format) -> Bool` 支持 dpx/cin/tif/jpg/png/ppm/bmp/xpm/drx。没有在该声明中指定每种格式位深、压缩或输出颜色管理；DRX 是 grade 交接，不能当作像素输出。[L429](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/README.txt:429>)、[L561-L566](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/README.txt:561>)。
- **更可控的候选：Deliver 单帧/序列。** 可查询 `Project.GetRenderFormats()`、`GetRenderCodecs(renderFormat)`，选择 `SetCurrentRenderFormatAndCodec(format, codec)`；`SetCurrentRenderMode(1)` 为 single clip；`SetRenderSettings(settings)` 可传 `SelectAllFrames`, `MarkIn`, `MarkOut`, `TargetDir`, `CustomName`, `ExportVideo`, `ExportAudio`, `FormatWidth/Height`, `FrameRate`, `ColorSpaceTag`, `GammaTag` 等。通过 `AddRenderJob()` 取得唯一 jobId，只启动该 jobId，并读 `GetRenderJobStatus(jobId)`。当前实际支持的格式、codec 字符串和单帧范围包含关系需要在测试工程中验证。[L161-L191](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/README.txt:161>)、[settings L813-L844](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/README.txt:813>)。
- **尚未有“高位深无损导出已实现”证据。** 公开 settings 未列通用 `VideoBitDepth` 或 `DataLevels` key；`AudioBitDepth` 是音频，`EncodingProfile` 限 H.264/H.265。需要先在测试工程建立/核验可用 EXR uncompressed/ZIP 或 16-bit TIFF 等 preset，再用 SDK 导出并检查真实文件头、样本类型、压缩方式、颜色标签、尺寸和像素。候选格式不是本机可用性承诺；本轮没有取运行时 format/codec 列表或创建 preset。[settings L828-L840](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/README.txt:828>)。
- **缩略图不合格。** `Timeline.GetCurrentClipThumbnailImage()` 声明输出 RGB 8-bit 缩略图，不能用来检验高位深曝光或超白保留。[L401-L402](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/README.txt:401>)。

## 调用前置条件：本轮均未执行

SDK 文档要求 Resolve 正在运行；脚本可由应用 Console/菜单或命令行执行，外部调用受偏好设置约束。后续是否已允许本地脚本调用未知，不应静默启用 network access。[L10-L12](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/README.txt:10>)、[L24-L37](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/README.txt:24>)。

`DaVinciResolveScript.py` 是动态 native-loader：先 import fusionscript，再尝试 `RESOLVE_SCRIPT_LIB`，最后用标准安装位置加载 DLL；它不是无副作用的纯 Python 文档。导入即可能加载 native library。其 Windows 默认位置是 `C:\Program Files\Blackmagic Design\DaVinci Resolve`，与当前 G 盘安装不同。[loader L24-L46](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/Modules/DaVinciResolveScript.py:24>)。后续获准运行时可以考虑仅在该测试进程提供正确的模块/DLL位置，不需要改全局 PATH、原文件或 Codex 配置；本轮没有确认 DLL 路径、加载它或设置环境变量。

## 建议的真实画面对照方案（未实施）

1. 先选择具体原生控件，例如 HDR palette 的 Global Exposure；明确项目 color science、工作/输出空间、input tagging、range、alpha、节点顺序，并保持固定。不要用 CDL Slope 代替目标控件。
2. 使用独立测试库/新工程与自制梯度、RGB 色块、超过 1 的 float 样本；设置 0、正/负曝光多档。正常 UI 人工确认数值与其余控件不变，并保存对应 DRX/工程与截图；SDK 在固定 graph 重放已保存 grade 只是减少重复工作，不产生原生曝光值读取证据。
3. 首先导出两次零曝光基线并回读，确认渲染稳定及颜色边界可解释；再导出各档原生控件输出。导出成功、文件字节哈希与像素相同是三个不同检查，不混用。
4. 在固定工作空间比较整个 RGB 域、暗部、肤色/高饱和色、超白、负值与 alpha；记录误差、适用域和竞争解释。匹配单灰值、一个 ramp 或某库函数，只能证明局部数值相符。
5. 不把相同画面输出推成“私有实现已找到”。需区分公开算法的自主实现、原生行为拟合、REA 静态定位、真正源级证据和用户观感验收；各自的结论只覆盖其证据。

当前状态：**文档级条件性可行；原生曝光数值自动设置无已验证 SDK 路径；无损帧导出、真实输入输出、隔离工程、性能和数学对应关系均未运行验收。**
