# HDR 颜色上下文：官方范围与本机证据边界

日期：2026-10-13。本文仅记录一手资料与现有静态文件阅读；未调用 Resolve、其 MCP／SDK，未运行目标或修改工程、grade。范围是区分项目勾选项、HDR palette 菜单和节点设置，不制定渲染协议或曝光公式。

**结论：** 21.1 手册没有把 “Use Color Space Aware Grading Tools” 定义为 HDR palette 的总开关。它先说明 HDR 是 color space aware palette，再把勾选项用于 **“Other palettes”**，明确举例 **Qualifier、Curves**。Primaries／Log 的 node HDR Mode 是另一项设置。HDR 的 Color Space／Gamma 菜单默认 Timeline，但本轮材料未给出其与 SDK 字段、节点覆盖及保存／重载之间的完整解析合同。

## 来源快照

- **M：本机官方《DaVinci Resolve 21.1 Reference Manual》**，作者 Blackmagic Design，4,351 页；[原始 PDF](<G:/Davinci Studio/Documents/DaVinci Resolve.pdf>)。本轮重新核验 SHA-256：`5dad6e417159ade62b69e9c38295b80cac3f33a7381b6d29c21fba0e47fe4224`。以下 PDF 页序与印刷页码相同；精读 p149–150、234–235、242、3143、3162、3440，全文可提取文本作定点检索。
- **S：本机安装 SDK 声明**：[DaVinciResolveScript.pyi](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/DaVinciResolveScript.pyi>)，SHA-256 `b91b53b86a946e1902789ea898eedf00cb7dd6107aba6f1276ca77fe508816ea`；[README.md](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/README.md>)，SHA-256 `5e12a637aa8db77d8110ea8c05397e89dff1d3b2ecb33d2e96122d3c87502bfc`。均只代表该安装快照，不作厂商全部接口完整性保证。
- 官方网页亦已读取：[Blackmagic Color 页面](https://www.blackmagicdesign.com/products/davinciresolve/color) 的 “Next Generation HDR Grading／HDR Color Wheels” 和 Gallery 小节。它确认 HDR palette 与保存／复用 grade 的产品能力，没有细列本勾选项、Timeline Gamma 解析或 DRX 字段。公开检索没有取得补足这些合同的官方页面；论坛用户帖不作为证据。

## 官方明确说明的作用范围

| 问题 | 官方事实及限定 | 页码／来源 |
| --- | --- | --- |
| 勾选项适用于哪些工具？ | 手册先说 RCM 与 ACES 支持 HDR 等本身 aware 的 palette；接着说其他 palette，例如 Qualifier、Curves，经该 checkbox 变为 aware。Qualifier 改善跨原始／时间线空间的选区；Curves 调整曲线覆盖当前数据范围。文中并非所有工具的穷尽列表。 | M p242，Color Space Aware Grading Tools；[PDF](<G:/Davinci Studio/Documents/DaVinci Resolve.pdf>) |
| 默认与 UI 可见范围？ | 本段记载 checkbox 默认开启；同段 NOTE 限定该控件只在 Resolve Color Management preset 为 Custom Settings 时可见。此段属于 RCM 设置讨论，不能直接推广为非管理 YRGB 中该 SDK 字段的执行合同。 | M p242 |
| 是 Primaries／Log 的主要开关吗？ | Primaries 章节讨论的是节点右键 **HDR Mode**：把有关节点控件强制适应扩大的 HDR 数据范围，例子是 Lift/Gamma/Gain、Log。它不是 p242 的项目 checkbox。 | M p3143，HDR Grading With the Primaries Palette |
| HDR 是否需要 node HDR Mode？ | HDR 章节明确说其本身 aware，不必启用节点 HDR setting 来处理宽色域时间线或 ST.2084；它自行处理。这是对 node HDR setting 的说明，不自动等于一个针对所有 YRGB 条件的 checkbox 独立性定理。 | M p3162，NOTE |
| YRGB 与自动管理有什么不同？ | DaVinci YRGB 是原始、手动管理变换的 color science；RCM 与 ACES 是另一组自动管理选项。不能从 YRGB 的 Input／Timeline／Output getter 名称，直接推定 RCM 的自动变换链实际开启。 | M p149，Color Science |
| 非管理流程能用 HDR palette 吗？ | 可以，但须正确配置 HDR palette 自身的 Color Space、Gamma 子菜单；两个菜单默认为 Timeline，反映 display-referred 流程中的工作色彩空间。 | M p3162，Using the HDR Palette Without Color Management |
| Timeline 模式关联什么？ | HDR 章节把默认 Timeline 与所选工作空间相联系；RCM 章节把 Timeline Color Space 定义为调整的 working space，并解释 gamut／gamma 在 separate checkbox 开关时合并或分开。没有给出 HDR 菜单到 SDK 字段的精确查值算法。 | M p150、234–235、3162 |
| HDR 的运算路径？ | HDR 文本描述从 Timeline Color Space 进入其感知均匀 operational space，调整后返回 Timeline；RCM／ACES 下控件适应 Input→Timeline 后的数据范围。未命名该空间，也未给曝光数值公式。 | M p3162，Perceptually Uniform Adjustments |
| 节点也能设 Color Space／Gamma 吗？ | 节点右键有自己的设置；这不会像 CST 那样直接改变图像，而会改变通道控件处理的对象及调整方式。该段没给 HDR palette 菜单、节点设置和项目 Timeline 三者的优先级。 | M p3440，Enabling, Disabling, and Converting Node Channels |

因此，官方正文支持把 **HDR 自身的颜色上下文**、**项目 checkbox**、**node HDR Mode**、**node Color Space／Gamma** 作为分别识别的设置。没有依据将 checkbox=0 解释成 “HDR 无色彩空间意识”，也没有依据把本段解释成 “该字段在所有版本／YRGB 情境下永远不影响 HDR”。

## SDK getter 能说明什么

- ProjectSettings 明确声明 `colorScienceMode`、`separateColorSpaceAndGamma`、`colorSpaceTimeline`、`colorSpaceTimelineGamma`，以及 `useColorSpaceAwareGradingTools: str`（值说明仅 0／1）；TimelineSettings 也声明对应项。[S L490–509](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/DaVinciResolveScript.pyi:490>)、[L540](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/DaVinciResolveScript.pyi:540>)、[L1129–1134](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/DaVinciResolveScript.pyi:1129>)、[L1181](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/DaVinciResolveScript.pyi:1181>)。
- README 说明 getter 提供键值快照；部分项可能只读或在特定上下文不可用。`Timeline.GetSettings()` 在 `useCustomSettings='0'` 时返回项目设置。因此 Project／Timeline 两份相同读值不一定是两个独立配置层。[S README L215–239](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/README.md:215>)。
- `SetSettings` 的返回与快照可检验属性提交；它们没有声明某个隐藏／不适用的字段必然改变 HDR 像素。没有在本轮所读 SDK 中找到 HDR palette 菜单的专用 getter／setter，或 node Color Space／Gamma 与其优先级说明。不能把 getter 的 Rec.709／Gamma 2.4 标签当成实际解码函数或实际 palette 值。

## 现有持久化线索：线索不升级为菜单映射

1. **实际 HDR 参数容器已定位。** 原生样本中的 `0x86000305 → ParamValueType #16 → Global` 存在于 `VersionBody.graph.nodes.markstore.marktimelines.marks.mark.params`；这是控件值载体的实测路径。与之共现的 `0x860000bb/int=-1`、`0x86000309/int=2`、`nodeparams 的 0xc00000db/bool=true` 含义仍未确认，尤其不能把 int=2 命名为 palette Gamma。[既有报告 L33、L50–56](<E:/projects/逆向工程/capcut+达芬奇/docs/research/hdr-global-parameter-mapping.md:33>)。

2. **HDR #18 的名字不能替代颜色参数定义。** 现有 descriptor 记录中的 HDRNodeParams 是 zonename、defaultzonetype、zonetype、isvisible、isenabled；已观察快照没有实际 #17／#18。这些已列 HDR 消息没有明确 Color Space／Gamma 菜单字段；不能据此排除菜单可能由其他 generic Parameter key 或其他载体保存。[原始静态 descriptor 记录](<E:/projects/逆向工程/capcut+达芬奇/evidence/local/resolve-exposure-20261013/analysis/resolve-native-grade-schema-scan.json>)、[既有分支计数 L45](<E:/projects/逆向工程/capcut+达芬奇/docs/research/hdr-global-parameter-mapping.md:45>)。

3. **已有 UI 与 grade 读回证明不同对象。** 003 的两项菜单 Use Timeline 来自用户直接查看；004 的四份读回保留来源 grade 的全部 Parameter 字节、HDR presence/default 和节点身份。后者证明序列化参数保留，不独立证明 004 菜单值、菜单保存层级或查值路径。[003 菜单见证](<E:/projects/逆向工程/capcut+达芬奇/evidence/local/resolve-hdr-20261013/analysis/palette-context-user-witness.json>)、[004 严格读回验证](<E:/projects/逆向工程/capcut+达芬奇/evidence/local/resolve-hdr-domain-20261013/analysis/native-gamma-condition-drx-validation.json>)。

**仍缺的连接证据：** palette 菜单的确切参数 key／持久化层级；Timeline 模式如何选用 project、timeline 或 node 的 gamma；YRGB 下相关 setter 的实际消费路径；保存／重载对上述上下文的生效关系。官方文档已给各设置的职责，但尚未把这些本机连接点打通。这里不选渲染条件，也不据此写曝光结论。
