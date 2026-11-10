# HDR Global Exposure：官方定义、上下文与自动化边界

2026-10-13（Asia/Shanghai）。本文是背景资料阅读子任务：只读本机 Blackmagic 原始手册、安装 SDK 和官方网页，没有运行 Resolve、SDK 或目标二进制，也没有修改实验工程。问题是 UI 的 Global Exposure 表示什么，以及官方资料能否连接它与内部 `Jz/gainjz`。

**结论：** 官方描述 Global Exposure 调整整幅图像的明暗，并以 Black Offset 设定的黑位为基准。HDR palette 进入感知均匀的工作空间处理后返回时间线空间。官方存在 MCP 自动化、原生 grade 保存和 DRX 重放通道；已核对 SDK 没有公开 HDR Global Exposure 数值 getter/setter。所读资料未提供 EV、UI `Exp` 与 `gainjz` 的换算合同。

## 来源快照与检索范围

- **M：本机《DaVinci Resolve 21.1 Reference Manual》**，封面 September 2026，PDF metadata 作者 Blackmagic Design，共 4,351 页。路径 [原始手册](<G:/Davinci Studio/Documents/DaVinci Resolve.pdf>)；SHA-256 `5dad6e417159ade62b69e9c38295b80cac3f33a7381b6d29c21fba0e47fe4224`。本报告所引 PDF 页序与页面印刷编号相同。精读 HDR chapter 132（p3160–3182），并核对 Gallery、Node Editing 与 Workflow Integrations 的相关页。
- **S：本机安装 Scripting SDK**，[README.md，L1–L12](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/README.md:1>) 标注 2026-08-31 更新，SHA-256 `5e12a637aa8db77d8110ea8c05397e89dff1d3b2ecb33d2e96122d3c87502bfc`；[DaVinciResolveScript.pyi](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/DaVinciResolveScript.pyi>) 共 2,848 行，SHA-256 `b91b53b86a946e1902789ea898eedf00cb7dd6107aba6f1276ca77fe508816ea`。仅将其视为该安装快照的 API 声明。
- 官方在线入口：[Blackmagic Support](https://www.blackmagicdesign.com/support) 的 21.1 Manual 条目标注 2026-09-08。具体 UI 结论以本机 M 的页内容为准；不将网页条目本身当作 UI 算法证据。

全 M 的可提取文本已扫描 `Jz`（独立词）、`JzAzBz`、`gainjz`、`EV`（独立词）和 `exposure value`，均未命中；同时人工阅读上述 HDR 页。此结果不覆盖截图中未被 OCR 的文字、厂商未公开材料或完整实现源码。

## UI 定义、单位与默认值

| 项目 | 官方事实与证据强度 | 原始来源 |
|---|---|---|
| Global Exposure 的作用域 | 调亮或调暗整幅图像：向右提高高光，向左降低高光，阴影相对 Black Offset 保持锚定。这里的 Global 是图像范围的描述，正文没有说该动作批量作用于所有 timeline clips。 | [M p3165–3166，Making Global Adjustments](<G:/Davinci Studio/Documents/DaVinci Resolve.pdf>) |
| 黑位与非线性描述 | Black Offset 定义最低黑位；提高 Global Exposure 时最低值仍接触该基准，降低时阴影压缩更重，并平滑、非线性地过渡到中间调。极暗素材的 Black Offset 可以降到 0 以下，处理管线保留细节。 | [M p3169–3170，Black Offset Explained](<G:/Davinci Studio/Documents/DaVinci Resolve.pdf>) |
| 饱和度 | HDR 的明暗/对比度调整保持感知上的饱和度；手册明确提醒 vectorscope 仍可能出现小的实际饱和度变化。不能据此要求每个 RGB 通道按同一比例变化。 | [M p3162–3163、p3167](<G:/Davinci Studio/Documents/DaVinci Resolve.pdf>) |
| 官方曝光尺度 | HDR 的 zone exposure 以摄影 stops 为尺度；每级表示光量加倍或减半。zone 图的 0 stops 表示 18% photographic gray，图示横轴为 −8 到 +8。正文的单位说明位于 zone exposure 小节，没有单独给出 Global `Exp` 的数值转内部参数公式。 | [M p3174–3175，Zone-Based Exposure Adjustments](<G:/Davinci Studio/Documents/DaVinci Resolve.pdf>) |
| Global 的初始数值证据 | p3165 的原始 Global 控件图显示 **`Exp 0.00`**、`Sat 1.00`、X/Y 0.00；已直接查看该图。它提供文档界面的零调整基准，正文未另列 Global Exposure 的数值默认合同或 `gainjz` 的内部默认值。 | [M p3165，Global control cluster 图](<G:/Davinci Studio/Documents/DaVinci Resolve.pdf>) |
| 不能混用的零点/范围 | Global 控件图的 `Exp 0.00` 与 zone 图的 0 stops/18% gray 属于不同对象。手册的“16 stops”说明及 zone 图范围不能当作 Global 输入框的硬性 min/max；本轮未找到该输入框的正式范围声明。 | [M p3165、p3174–3175](<G:/Davinci Studio/Documents/DaVinci Resolve.pdf>) |

**术语边界：** 手册显示的控件名是 `Exp`，单位材料使用 stops。实验里口语称“EV”的数值，应明确记录为所观察到的 HDR Global UI `Exp`；本报告不把它自动等同于摄影测光 EV 的绝对值、线性 RGB multiplier 或内部 Jz gain。Global `Exp` 的精确数值语义仍需控件与真实输出的受控对照。

## HDR palette 的 Color Space / Gamma

| 项目 | 官方事实 | 原始来源 |
|---|---|---|
| 菜单与默认 | HDR palette 的 option menu 有 Color Space 与 Gamma 子菜单；两者默认均为 **Timeline**。非 color-managed 工作流也可使用 HDR palette，但需正确设定。正文没有列出这两个子菜单的完整选项表。 | [M p3162，Using the HDR Palette Without Color Management](<G:/Davinci Studio/Documents/DaVinci Resolve.pdf>) |
| RCM/ACES 上下文 | 在 RCM 或 ACES 中，HDR 控件适应素材 Input Color Space 映射到 Timeline Color Space 后的数据范围。手册描述控件在不同 source/timeline 环境具有相似操作感，不承诺输出像素逐值相同。 | [M p3162，Color Space Aware Controls](<G:/Davinci Studio/Documents/DaVinci Resolve.pdf>) |
| 处理范围 | 每个 clip 的数据由 Timeline Color Space 进入 HDR palette 的感知均匀 operational color space，调整后再回到 Timeline Color Space，供后续操作使用。手册没有在这里把该空间命名为 JzAzBz，也没有公布矩阵、传递函数或代码。 | [M p3162，Perceptually Uniform Adjustments](<G:/Davinci Studio/Documents/DaVinci Resolve.pdf>) |
| 与 node HDR mode 的关系 | HDR palette 会自动处理 wide-gamut/HDR 适配，无须为了该 palette 开启 node HDR setting。Node contextual menu 的 HDR Mode 另用于扩展 Lift/Gamma/Gain、Curves、Soft Clip 等控件的范围。 | [M p3162；p3403，Putting Nodes into HDR Mode](<G:/Davinci Studio/Documents/DaVinci Resolve.pdf>) |
| 配置层级的公开缺口 | 能确认菜单配置 HDR palette 的解释与处理上下文；正文没有明确说明此菜单选择的持久化粒度是 per-node、per-clip、per-project 还是 UI preference。不能凭菜单位置或 Timeline 默认值判定其保存层级。SDK 所列 `colorSpaceTimeline/Gamma/Input/Output` 是 ProjectSettings 项，未声明它们就是上述 palette 菜单值。 | [M p3162](<G:/Davinci Studio/Documents/DaVinci Resolve.pdf>)；[S ProjectSettings L490–L521](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/DaVinciResolveScript.pyi:490>) |

## 官方自动化与保存：通道存在，控件映射仍缺

1. **官方自动化通道。** M p4318 明确 Resolve Studio 的内置 MCP/AI assistant 可接受自然语言控制、创建 looks 和运行脚本；示例包括 LUT、render 与 project settings。该页没有承诺 HDR Global `Exp` 的直接数值控制，也没有描述 EV→Jz 转换。[M p4318，Using DaVinci Resolve with AI Assistants](<G:/Davinci Studio/Documents/DaVinci Resolve.pdf>)。
2. **原生 grade 保存。** Gallery 抓取 still 时保存该 clip 的嵌入 grade；导出通常产生图像及包含 grading metadata 的 DRX，也可在 UI 格式选择器中只导出 DRX。M p4319 的 Renderer 章节明确可传递原生 palettes，包括 HDR；它同时限定 temporal FX/Magic Mask 等不在该 Renderer 的传递范围。以上支持原生快照语义，未提供 HDR 参数字段编辑规范。[M p3333、p3346–3347、p4319](<G:/Davinci Studio/Documents/DaVinci Resolve.pdf>)。
3. **SDK 保存与重放声明。** `Timeline.GrabStill()`、`GalleryStillAlbum.ExportStills(...)`、`ProjectManager.SaveProject()/ExportProject(...)` 和 `Graph.ApplyGradeFromDRX(...)` 可用于收集与重放已有状态。重放参数 `gradeMode` 为 0 无 keyframes、1 source-timecode 对齐、2 start-frame 对齐；`applyToAllLayers` 默认 false，只作用 active layer，true 才应用全部 node-stack layers。这些是声明，本子任务没有调用验证。[S L2288](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/DaVinciResolveScript.pyi:2288>)、[L2765](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/DaVinciResolveScript.pyi:2765>)、[L1706/L1733](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/DaVinciResolveScript.pyi:1706>)、[L2801–L2804](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/DaVinciResolveScript.pyi:2801>)。
4. **直接控制缺口。** 整份 S 声明及 README 没有找到 HDR Global Exposure 或 palette Color Space/Gamma 的数值 getter/setter。Graph 的公开控制包括 LUT、node enable/cache 和 grade 重放；`TimelineItem.SetCDL` 的字段是 NodeIndex/Slope/Offset/Power/Saturation。HDR mastering/Dolby/HDR10+ 的项目项属于其他配置，不能当作原生 Global Exp setter。[S Graph L2772–L2806](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/DaVinciResolveScript.pyi:2772>)、[SetCDL L2531–L2533](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/DaVinciResolveScript.pyi:2531>)、[Project HDR settings L602–L614](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/DaVinciResolveScript.pyi:602>)。
5. **HDR zone preset 的边界。** M p3182 的 Save As New Preset 保存定制的 Zone settings；Reset 子菜单分别提供 Reset All、Reset Color Adjustments、Reset Zone Definitions。此处不能推出 preset 就是 Global Exposure 全状态快照，应使用原生 still/DRX/工程保存入口。[M p3182，Customizing and Saving Presets](<G:/Davinci Studio/Documents/DaVinci Resolve.pdf>)。

## 事实、未知与后续实验用途

**已核实：** Global 的整图与黑位语义、感知饱和度目标、HDR 摄影 stops 尺度、图示 `Exp 0.00`、palette Color Space/Gamma 默认 Timeline、HDR 运算进入/返回 Timeline 的流程、官方 MCP 和原生 grade 保存/重放入口。

**仍未知：** Global `Exp` 到 `gainjz` 的公式与内部默认值、原生 Jz 算法/空间的正式命名与参数、palette 菜单的持久化层级、Global 数值范围及直接数值自动 setter。文本未命中只证明本轮材料未公开这些名称，不能证明实现未使用它们。

**对实验的建议：** 将 UI `Exp`、Black Offset、palette Color Space/Gamma、项目/时间线与素材颜色管理、node layer/version 作为分别记录的上下文，原生 grade 保存后再比较实际渲染结果。官方摄影 stop 的光量解释不构成对最终编码 RGB、Jz 参数或单灰值的直接等式；公式归属需要本机控件、序列化载体与输出之间的连接证据。
