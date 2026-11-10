# 阶段 1A 第三轮：原生浮点导出、中性重放与 HDR 数据结构

日期：2026-10-13（Asia/Shanghai）。本轮在 Resolve **21.1.1.10** 中完成了六次真实单帧导出：三次初始中性验证，另三次用于 CDL 饱和度阳性对照、非中性重放及中性恢复。阶段 1A 仍在进行：本轮没有设置或测量原生 HDR Global Exposure 的 0/−1/+1。

## 可直接支持的结果

1. 官方原生 MCP 的沙箱 `run_script` 能复制指定测试工程、抓取 still、导出配套 DRX、应用该 DRX、创建单帧渲染任务并查询完成状态。没有使用 `run_script_unsafe`。
2. baseline-a、重复 baseline-b、应用中性 DRX 后的 neutral-replayed，三个渲染任务均返回 Complete / 100%。三张 EXR 的文件 SHA-256 和整幅 RGB float32 像素 SHA-256 均相同。
3. 在这套固定的中性 YRGB、PNG16 输入、EXR RGBFloat 导出条件下，16 个色块中心的 48 个通道值保持输入 PNG 的归一化编码值。它们与 `encoded_rgb_u16 / 65535` 的最大误差为 **2.9694545600200684e-08**；与输入清单按 sRGB 解码的线性值的最大误差为 **0.2870986529831294**。
4. 本机二进制中找到原生 HDR 参数 descriptor；这给后续定点分析提供了可定位的结构线索，尚不证明字段与 UI EV 的关系或渲染公式。[静态与公开源码研究](ocio-25-and-native-grade-api.md)
5. SDK CDL 饱和度阳性对照确实改变像素；非中性 DRX 重放与直接设置的整幅像素相同，恢复中性快照后又与最初基线相同。该对照单独记录，不充当 HDR 曝光证据。[阳性对照数据](../experiments/resolve-cdl-control-result.json)

第 3 项只覆盖这套设置下的色块中心，没有证明所有输入格式、管理模式或 EXR 输出都保持编码值，也没有确认原生 HDR 操作域。**浮点容器和“场景线性”是两件分别需要验证的事。** 原始目标、grade、项目导出和运行回执仅保存在 Git 忽略的本地证据目录；脱敏结果见 [resolve-neutral-export-result.json](../experiments/resolve-neutral-export-result.json)。

## 实验对象及保护措施

只在用户建立的 Disk 库 `OC_COLOR_001_TEST` 内操作。先保存、导出原工程 `EXPO_001_HDR_GLOBAL`，再从该快照导入副本 **EXPO_002_NATIVE_HDR_211**。原工程没有执行调色改动。副本的 gallery、render cache 和 project media 路径均改到本项目私有实验目录，并通过 SDK 返回值及规范化路径读回核对。

新版 `Resolve.exe` 和 `OpenColorIO_2_5.dll` 已复制到 `evidence/local/resolve-exposure-20261013/targets`；源与副本 SHA-256 一致。旧 21.0 / OCIO 2.4 targets 保留，旧函数地址不复用。SDK stub SHA-256 为 `b91b53b86a946e1902789ea898eedf00cb7dd6107aba6f1276ca77fe508816ea`。

测试输入仍为自有 `opaque-srgb16-patches.png`，1920×1080，16-bit RGB、无 alpha，SHA-256 `2daa68135e4ac8c0585fb33630ce5d69a735640799b82a8173caafbfc8d9f09f`。素材元数据报告 Input Color Space“项目”、Input Gamma“Gamma 2.4”、Data Level Auto；这些字段不能单独证明输入采用了某一传递函数。

| 固定设置 | 读回值 |
|---|---|
| colorScienceMode | davinciYRGB |
| input | Rec.709 Gamma 2.4 |
| timeline / output | Rec.709 (Scene) |
| useColorSpaceAwareGradingTools | 0 |
| output tone / gamut mapping | None / None |
| timelineWorkingLuminance / mode | 1000 / HDR 1000 |
| nodeStackLayers / clip node count | 1 / 1 |
| timeline / render | 1920×1080，30fps |
| fixed render frame | 108000；MarkIn = MarkOut |
| export | exr / RGBFloat，video only，无 alpha |

没有通过未声明的 RenderSettings 字段强设 DataLevel；实际导出头与像素另行读取。实验结束时仍在该中性副本中，当前时间码 01:00:00:00，没有运行中的渲染任务。

## 导出及独立读取

首先 `GrabStill` 返回一个 still，设置标签成功；紧接的 `ExportStills(..., "png")` 返回 False，脚本按断言停止。之后单独查询确认 still 已存在，重试同一个 still：Unicode 路径 PNG、ASCII 路径 PNG 和 Unicode 路径 DPX 均成功。没有重新抓取重复 still。**初次失败的根因未查明；这些结果不能据以认定 Unicode 路径不受支持。** PNG/DPX 是 grade 快照的配套图像，数值结论使用独立渲染的 EXR。

三个 EXR 均为 24,900,921 字节。读取时核对 magic、version、dataWindow、compression、lineOrder、channel type 和 sampling：普通单 part scanline EXR，1920×1080，未压缩，B/G/R 三通道 float32，30/1fps。自有读取器按 offset table 找到每一行，并从平面通道数据恢复整个图像；再与 OpenCV 4.13.0 的 IMREAD_UNCHANGED 解码做 **6,220,800 个通道的 float32 字节比较**。[官方 EXR 文件布局](https://openexr.com/en/latest/OpenEXRFileLayout.html)、[OpenCV 图像解码接口](https://docs.opencv.org/4.13.0/d4/da8/group__imgcodecs.html)

EXR 文件 SHA-256：`d18674c28197f09580b23db613ad9f4b67e623a9e3c70030d30a1c1c917eeb9b`。按 row-major RGB、little-endian float32 排列的 24,883,200 字节像素 SHA-256：`e91cb12d71527cf24e2efc3e3180fde844a5e7e3cfec950e784aab2ecaed5afb`。三次结果均匹配。

测量脚本 [measure-resolve-exr.py](../../experiments/measure-resolve-exr.py) 只接受此实验的固定格式，对其他 EXR 约定会停止；不是通用 EXR 库。`OPENCV_IO_ENABLE_OPENEXR` 只设在测量进程内，未改全局环境。调用器 [call-resolve-mcp.py](../../experiments/call-resolve-mcp.py) 启动已安装的官方 stdio server，检查 JSON-RPC、isError 和工具正文中的 error；完整响应/日志写入私有目录，控制台只输出成功标志和返回键。它不自动启动 Resolve，实验脚本另有版本、库、工程、时间线和节点守卫。

调用器要求本项目脚本的 `result` 为字典；正文或结果形状不符时停止，不打印成功。最末次只读状态查询已用修正后的调用器成功执行，回执另名保存，没有覆盖实验历史。

另用一个不调用任何 SDK 的故意失败脚本验证真实错误通路：原生 server 在工具正文返回 error，调用器非零退出且没有成功标志；错误原文保存在私有回执，控制台仅给通用错误说明。之后重新查询实验状态成功。公开结果记录了执行源码、原始回执和分析文件的 SHA-256，供本机复核。

## 中性 DRX 重放证明的范围

导出的 DRX SHA-256 为 `388c39fca8def009a6e143d6ca50de115494cc9448c4f61b27504c95fd286fbe`，clip/track version 均标 HasCorrection=false。重放前后节点数为 1，GetToolsInNode(1) 返回 null、GetLUT(1) 返回空字符串。

在明确只有一层时，对 `GetNodeGraph(1)` 调用 `ApplyGradeFromDRX(path, 0, False)`，返回 True；随后保存并导出实验副本，再渲染同一帧。它证明这份 opaque 中性 DRX 的应用入口可执行且输出保持一致。**这不是 HDR EV=0 的控件值证据；这一中性系列本身没有施加改变后重放或测试整条颜色链路旁路。** 非中性重放另见下节。

DRX 的两个 Body 解压后为 203 / 142 字节；文件并没有直接暴露一个可安全修改的“曝光”文本字段。用已提取的 39 份 descriptor / 401 个 message 定义递归核对，两者均完整匹配 `ProtoVersion.VersionBody`：分别识别 60 / 35 个字段和 16 / 9 个嵌套消息，wire 错误、unknown 字段、required 缺失、oneof 冲突及未消费字节均为 0。另有 19 个结构兼容候选把载荷当作 opaque bytes，不能解释这些内部结构。结构匹配仍不单独证明运行时采用的反序列化器。

descriptor 声明了 VersionBody → Graph → Node → NodeParams → Parameter → ParamValueType → HDR 参数列表的路径；**这两份中性样本实际没有出现 HDR 分支**。其中 HDR 参数名包括 `gainjz`，仍须确认所属参数 key 和控件数值映射，不能从名字猜出倍率后写入文件。没有编辑原生 DRX 的二进制数据。

## 附加阳性对照：CDL 饱和度、重放与恢复

为了排除“只对中性状态重复操作”的局限，在同一实验副本中使用 SDK 公开支持的 `TimelineItem.SetCDL`：NodeIndex=1、Slope=`1 1 1`、Offset=`0 0 0`、Power=`1 1 1`、Saturation=**0.75**，返回 True。[本机 CDL 声明](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/DaVinciResolveScript.pyi:146>)、[SetCDL](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/DaVinciResolveScript.pyi:2531>)

之后抓取第二个 still、保存及导出 grade/project，并渲染 cdl-control。先应用中性 DRX，读回单节点无工具/LUT，再应用该 CDL DRX 并渲染 cdl-replayed。最后重新应用中性 DRX、保存并导出工程，渲染 neutral-restored。只启动本次创建的任务；三次均 Complete / 100%。没有编辑 DRX Body，也没有调用通用删除/停止渲染接口。

| 检查 | 结果 |
|---|---|
| 对比初始中性帧 | 6,220,800 个通道中 4,795,200 个出现数值变化，最大绝对差 0.12218957394361496 |
| 10 个灰色块中心 | 最大绝对差 5.960464477539063e-08；不是承诺灰阶所有像素逐位不变 |
| 6 个彩色色块中心 | 最大绝对差 0.12218957394361496 |
| CDL 直接设置 vs DRX 重放 | 整幅 RGB float32 字节相同；像素 SHA-256 `41eef9eb38756c1be5b1c0ae3fd2476ae221cafca75e44f8086f07a65c76d7a6` |
| 最后恢复 vs 初始中性基线 | 整幅 RGB float32 字节及 EXR 文件 SHA-256 相同 |

附加三帧同样经过固定格式独立读取和整幅 OpenCV 字节核对。以上证明公开 setter 的可见作用、该非中性 grade 的重放和本次调色恢复；**未验证 CDL 的完整数学公式，未做整条颜色链路旁路，也未产生任何原生 HDR EV 样本。** 原生 CDL 与 HDR 参数要分别标记，不能因为都改变亮度/颜色就相互替代。实验副本最终已恢复中性，原工程没有执行此控制变化。

只读增量结构分析发现，这次 CDL 的新增参数实际写在 `graph.nodes.markstore.marktimelines.marks.mark.params`，原有 `nodeparams` 保留。新增 15 个参数中，`0x06000005 / float_field` 为请求中的 0.75；两个 Body 均无实际 HDR #16/#17/#18 分支。这个单样本关联尚不提供完整的 key→UI 映射，也不能把 CDL 的存储位置套给 HDR。[结构差异摘要](ocio-25-and-native-grade-api.md)

## 后续边界

接下来沿已找到的结构路径确认 native HDR 参数 key、UI 数值映射及实际操作域。只有直接证据支持时才改变实验副本中的参数；否则需要一个明确记录原生 HDR UI 值的最小变化样本。之后才能保存旁路/0/−1/+1、重复渲染并比较线性、video、log 或其他候选解释。

阶段 1B 的自研 Rust 调色仍未开始。公开 OCIO 2.5 与 2.4 的曝光 CPU 公式比较已完成，但不能替代 Resolve 原生 HDR 的调用及行为证据。当前结论也不包含 OpenCut 接入、视频性能或完整产品验收。

[独立对抗审查](../reviews/resolve-native-neutral-review.md)已完成，采样范围表述及调用器结果形状检查两项均已关闭，无遗留必须修正项。审查只读原始回执、代码、字段树及 EXR 头，没有重新运行 Resolve、全帧解码或静态扫描；这一范围与主实验的实际执行证据分开。
