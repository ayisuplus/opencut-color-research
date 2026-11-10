# 达芬奇调色：已知能力、可实现原理与未知事项

研究日期：2026-10-12。对象：DaVinci Resolve 调色工作流；本机文件元数据为 21.0.0.47。

## 结论

值得研究。公开资料支持的核心线索是颜色转换、分区控制、局部选区、可调整的处理顺序和客观测量共同组成工作流。它们为我们的产品设计提供依据，但没有证明任何一项是达芬奇质量领先的唯一原因，也没有揭示私有算法。

## 公开事实

| 能力 | 可核查的公开说明 | 我们要问的问题 |
|---|---|---|
| 颜色管理 | 有输入、时间线、输出转换，支持自身管理系统及 ACES | 同一份素材经过显示和输出后，颜色怎样保持可解释？ |
| 精细控制 | 色轮、曲线、按色相/饱和度/亮度的局部调整 | 操作所在的颜色域、影响范围和顺序是什么？ |
| 局部控制 | 颜色选区、几何窗口和跟踪 | 如何避免只想改天空却影响肤色？ |
| 组织与测量 | 节点处理、画面对照、示波器 | 如何复查操作顺序，并量化高光、通道与色调变化？ |
| 图像处理 | 官方介绍 32 位图像处理、CPU/GPU 加速效果 | 我们的精度、缓存和加速要求该怎样验证？ |

上述功能事实来自 Blackmagic Design 的 [Color 页面](https://www.blackmagicdesign.com/products/davinciresolve/color)（Professional Color Management、Curves、Secondary Color Correction、Work with Nodes、Professional Scopes 等节）。这些是产品能力说明，不能当作内部源码或普遍性能证明。

## 从第一性原理看实现

一张画面的 RGB 数字只有连同色域、传递函数、范围、白点等约定才有明确含义。因此要先解释输入，再调色，最后转换到目标输出。公开的 sRGB 转换示例展示了编码值与线性值之间的非线性关系。[W3C CSS Color 4：转换代码](https://www.w3.org/TR/css-color-4/#color-conversion-code)

把在线性域增加一档曝光，与把屏幕编码值直接乘二混为一谈，会得到不同结果。我们已提供一个限定非负 SDR sRGB 灰值的 [小实验](../../experiments/linear-exposure.mjs)，以解析值与故意错误的操作作对照。它没有调用 Resolve，也没有估计 Resolve 的曝光按钮公式。

曲线、曝光、饱和度等也不是脱离颜色域的任意运算。OpenColorIO 的公开 API 分别提供颜色空间变换、曝光/对比度、ASC CDL 与 3D LUT；曝光/对比度支持针对 linear、log、video 的不同数学方式。[OCIO Transforms](https://opencolorio.readthedocs.io/en/latest/api/transforms.html#exposurecontrasttransform)

LUT 是一个明确输入域上的变换，不能代替完整的颜色解释与视频处理。要约定范围、颜色空间、网格顺序、插值和越界行为。OCIO 文档列出了 3D LUT 的网格、插值及归一化数据语义；这可作为候选实现的参考。[OCIO Lut3DTransform](https://opencolorio.readthedocs.io/en/latest/api/transforms.html#lut3dtransform)

这部分是公开原理和工程推论。我们自己的处理器可以采用 Rust 浮点实现；这不是对达芬奇内部数据格式或源码的断言。

## 开源实现候选与使用条件

OpenColorIO 提供独立的 CPU/GPU processor，是颜色管理候选。其文档同时明确 CPU/GPU processor 的动态参数相互独立，宿主仍需同步参数，不能把“同一个 processor 来源”误认为“实时参数自动一致”。[OCIO Processors](https://opencolorio.readthedocs.io/en/latest/api/processors.html#processor)

其项目是 BSD-3-Clause，项目目标包含高精度、性能与跨应用一致性。是否引入，要另验证 Rust/桌面/浏览器构建边界、版本、所用配置与 LUT 的许可证。[OCIO LICENSE](https://github.com/AcademySoftwareFoundation/OpenColorIO/blob/main/LICENSE)、[OCIO 项目](https://github.com/AcademySoftwareFoundation/OpenColorIO)

本次只把它列为候选，未安装 OCIO，也未据此声称它在 OpenCut 新主线能够直接运行。官方 latest API 文档目前包含开发版名称，实际实现时必须锁定可用 release，重新核对接口。

## 达芬奇本机实验计划

排期为立项书的 **阶段 1A**，先于阶段 1B 的自主调色实现。本文保留公开资料研究；本机副本的静态研究已启动，真实控件的行为实验尚未进行。第一轮确认主程序声明引用 57 个 OCIO 接口，这不能证明原生曝光轮使用 OCIO。见 [第一轮记录](resolve-exposure-first-pass.md) 与 [SDK 能力边界](resolve-exposure-sdk-boundary.md)。后续高级功能采用同样的“定点研究 → 规格与样例 → 自主实现 → 对照验收”顺序。

后续一次只研究一个操作。固定应用版本、项目颜色设置和素材摘要；先导出旁路基准，再在相同项目下改变单个参数，保存无损帧与参数记录。用灰阶、色块和原创真实镜头区分数值变化与主观风格变化。

本机安装来源由用户说明为修改版。行为记录应明确标记这一来源，不能将观察到的每个差异自动归因为官方实现。实验既不改变许可机制，也不将软件内置资源纳入产品。

公开学习材料可从 [Blackmagic 官方 Training](https://www.blackmagicdesign.com/products/davinciresolve/training) 开始；当前列出的 Colorist Guide 对应 Resolve 20，因此只能辅助理解公开工作流，21 的具体行为要另验。

## 尚未得到的证据

- 没有获取或恢复 Resolve 的私有调色算法、GPU kernel 或神经网络模型。
- 没有在本机启动 Resolve、做像素对照或测量帧率。
- 没有证明 OpenCut 和 Resolve 的图像质量、格式支持或性能等价。
- 没有决定最终界面、预设风格或产品名称。

立项结论是“可以开展有边界的自主调色研发”，不是“达芬奇调色能力已经被移植”。
