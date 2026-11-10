# 原生 HDR Global 第四轮：存储校准与 −1/0/+1 像素对照

2026-10-13（Asia/Shanghai）。本轮在隔离工程 `EXPO_003_HDR_MAPPING` 中完成三档原生调色校准及六张单帧浮点 EXR 导出。**实际参数载体、三个离散 UI 显示点和本次输入的像素响应已经连接；完整 UI 换算与内部像素公式仍未知。** 产品代码尚未开始，研究未把私有反编译代码纳入开源实现。

## 存储与显示关系

实际载体为 `markstore → mark.params` 的 key `0x86000305`，其 value 选择 HDR #16，唯一 zone 为 `Global`。`gainjz` 是 field #2 / float32，并非因字段名称而认定它是 RGB 增益。[完整结构与读回](hdr-global-parameter-mapping.md)、[结构化校准记录](../experiments/resolve-hdr-calibration-result.json)。

| 输入的精确内部值 | 用户确认的 Global「曝光」显示 | 原生保存的字段表示 |
|---|---|---|
| −1.0 | −1.00 | 显式 float32 −1.0，payload `000080bf` |
| 0.0 | 0.00 | 省略零 scalar，proto3 默认读取 0；Global 分支保留 |
| +1.0 | 1.00 | 显式 float32 +1.0，payload `0000803f` |

三档均经官方 `Graph.ApplyGradeFromDRX` 接受、保存、GrabStill/Export，独立按 descriptor 完整检查原生读回。除 zero 的零字段省略及各次 `lastmodtime` 外，其他参数状态、key 和节点身份保持。zero 的活动工具 API 返回 `None`；这不能用来否定保存文件中仍存在的 Global 分支。

首批手动样本的 UI 显示 1.00/0.00，实际存储却为 1.003199815750122/0.004799820948392153。后续精确候选说明本次 −1/0/+1 的显示与内部值相容；**没有证明全部输入范围的精确一一映射或显示舍入公式。** 旧无 HDR 分支的中性 grade、人工显示零点和内部精确零是三个独立保存的对象。

## 固定条件与原生执行

- Resolve `21.1.1.10`，官方 MCP `run_script`，使用安装的原生 stdio server；没有使用 unsafe script。
- 自有 `opaque-srgb16-patches.png`，1920×1080、不含 alpha、RGB16。SHA-256 `2daa68135e4ac8c0585fb33630ce5d69a735640799b82a8173caafbfc8d9f09f`，与原输入清单一致。
- GetClipProperty 实读 Input Color Space=`项目`、Input Gamma=`Gamma 2.4`、Data Level=`Auto`、FPS=24；这是素材属性，不单独证明实际解码变换。
- 工程 `davinciYRGB`，Input=`Rec.709 Gamma 2.4`，Timeline/Output=`Rec.709 (Scene)`；独立 Gamma 项为空，颜色感知工具项为 0，工作亮度 1000，输出 tone/gamut mapping 均 `None`。[固定项目项](../experiments/resolve-hdr-calibration-result.json)。
- 用户分别查看并确认 HDR palette 的色彩空间和 Gamma 均勾选「使用时间线」。完整 panel 截图显示 Global 饱和度 1.00、X/Y 0.00、黑场偏移 0.000。菜单见证与项目项分开记录，未用空 Gamma 项推断 linear。
- 单视频轨道、单素材、单节点、单层；检查素材/片段唯一身份及路径，固定首帧 108000。每档检查项目颜色项和素材属性没有变化。
- 单帧 EXR / RGBFloat，无音频和 alpha，1920×1080、30 fps。每次只启动一个明确新 job ID，完成度 100 且无渲染进行时才切换下一档。

初次循环在 zero 档创建任务之前因错误的工具列表预期停止：脚本预期 HDR，但先前原生 zero 回执已返回 `None`。纠正检查后，续跑采用新的脚本、回执及输出目录，保留错误证据和前两帧。原始循环、续跑和最终工程导出摘要均保存于[执行记录](../experiments/resolve-hdr-calibration-result.json)。

## 六帧结果

每帧为无压缩 scanline EXR。手动读取 header、offset table、各 channel scanline，与 OpenCV 4.13.0 对 **6,220,800 个 float32 通道**逐字节核对，六帧全部通过。输出与输出之间使用整幅 RGB 字节摘要；输入数值与候选公式比较限定 16 色块中心、48 个通道。[测量结果与完整样本](../experiments/resolve-hdr-global-grid-result.json)、[独立 EXR 读取器](../../experiments/measure-resolve-exr.py)、[对照程序](../../experiments/compare-hdr-grid.py)。

| 帧 | 相对无 HDR 分支中性 grade 的变化通道数 | 最大绝对变化 | 整幅 RGB 与中性一致 |
|---|---:|---:|---|
| neutral-before | 0 | 0 | 是，参照 |
| HDR −1 | 5,832,000 | 0.2938775420 | 否 |
| HDR 0 | 0 | 0 | 是 |
| HDR +1 | 5,832,000 | 0.4034119844 | 否 |
| HDR 0 重复 | 0 | 0 | 是 |
| neutral-restored | 0 | 0 | 是 |

这证明本输入/设置下精确零为像素中性，零档重复及中性恢复成功。±1 本轮各导出一帧，没有将其称为已完成多次重复。无 HDR 分支中性 grade 是此处的参照，不能称整个颜色处理管线旁路。

以两个灰色块的 **R 通道**为例，数值均来自原生 EXR：

| 样本 | neutral / HDR 0 | HDR −1 | HDR +1 |
|---|---:|---:|---:|
| id5，原输入约 18% 线性灰的编码值 | 0.4613565207 | 0.3112463057 | 0.6665466428 |
| id9，白色 | 1.0000000000 | 0.7061224580 | 1.4034115076 |

这里 id5 的 18% 只描述输入生成约定，实际 neutral EXR 保留其约 0.46136 的编码值，不能把输出表解释为已经解码的线性光量。白块 ±1 的 RGB 各通道存在微小差异，完整三通道数值见 JSON。

直接对 neutral EXR 通道计算 `value × 2^档位`，与原生输出在 48 个采样通道上的最大误差分别为 **0.2061225772（−1）**、**0.5965884924（+1）**，零档为 0。因此直接缩放本次 EXR 通道值的候选被否证；**这没有否证另一个已定义线性操作域中的曝光倍增关系。**

+1 全帧最大值 1.4034119844，超过 1 的通道仍保留在浮点 EXR 中；观察到的微小负值最低 −1.8558449710e−7。这些来自非负输入，未验证负输入处理。绘图未夹紧像素，曲线只连接十个灰阶中心，不能把连接线当作完整函数。[灰阶响应图](../figures/hdr-global-response.png)。

## 当前结论与下一步

已完成：实际存储路径、三档离散 UI 校准、零 scalar 原生规范化、固定颜色环境、原生三档对照、零档重复及中性恢复。最终工程已保存并导出，六个任务均 Complete 100，无渲染进行。

仍待研究：控件完整输入/显示换算、HDR 工作域与输入/时间线变换的实际连接、Jz 或其他内部算法、彩色色度行为、跨颜色空间、负输入、HDR/Log/RAW、alpha 和真实视频。下一步用已固定样本辨别操作域与候选变换，再决定自主调色核心的规格；不能因为一个显示 +1 就把 RGB 编码值翻倍，也不能将本轮对照等同于复现达芬奇全部调色。
