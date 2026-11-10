# HDR 曝光第五轮：候选公式与时间线 Gamma 配置对照

2026-10-13。Resolve 21.1.1.10，阶段 1A。存储和 UI 三个离散校准点沿用[第四轮](resolve-hdr-global-fourth-pass.md)，本轮继续辨别像素响应，尚未得到完整曝光算法。

**结果：** 五个固定数学候选中，BT.709 编解码候选最接近这批原生数据，但相对中性参照的残差仍存在。另导出七帧，比较时间线 Gamma getter 为 Rec.709 与 Gamma 2.4 的两个配置：中性画面逐位相同，非零档仅有约 10⁻⁷ 量级的浮点通道差异。配置名称本身不能确定实际 HDR 运算域，也不能据此宣布 Gamma 设置无效。

## 1. 五个固定候选

输入是第四轮 16 个色块中心的原生中性 EXR 编码值，48 个 RGB 通道。预测统一为 `F(D(C) × 2^E)`；D/F 明确定义，不把 EXR 容器自动解释为线性光。没有拟合参数，没有用候选输出替代原生画面。

| 候选 | −1 最大绝对误差 | +1 最大绝对误差 |
|---|---:|---:|
| 直接 EXR 通道乘 2^E | 0.2061225772 | 0.5965884924 |
| 零黑位、归一化白的纯 Gamma 2.4 | 0.0430310805 | 0.0685721303 |
| OCIO 视频指数 1.83 | 0.0214187828 | 0.0570740456 |
| sRGB 分段编解码 | 0.0292345251 | 0.0501559383 |
| BT.709 舍入常数／Colour 逆阈值 | 0.0006074873 | 0.0011337423 |

来源、分段阈值和代数延拓见[一手公式与候选假设](hdr-exposure-domain-primary-models.md)，完整分层误差和比值见[候选结果](../experiments/hdr-domain-candidate-result.json)。BT.709 逆阈值固定为 `1.099 × 0.018^0.45 − 0.099`，约 0.08124794403514046，跟随固定 Colour 实现；规范的舍入接点存在间隙。大于 1 的部分是本实验约定的代数延拓，不能称为 ITU 表的规范域。

在 baseline、原生 −1 和 +1 均为正的 36 个通道上，采用该 D709 后，`D709(+1) / D709(−1)` 为 3.999999042…4.000002139，最大离 4 为 2.13919×10⁻⁶。两档反推的共同参照 `2D709(−1)` 与 `0.5D709(+1)` 最大差为 2.41107×10⁻⁷。它们仍偏离 `D709(中性)`；该成对关系不能取消上表的绝对残差，或证明输入解码、物理 EV、Jz 算法。

独立 JavaScript 标量复算核对旧数据 280 项数值/计数，另一实现核对 170 项。实现之间的核对容差不是候选与原生的验收阈值。[独立审查](../reviews/hdr-domain-review.md)记录其范围。

## 2. 专用副本与配置探针

先读回源 EXPO_003_HDR_MAPPING 的 18 个冻结颜色/格式字段、完整 clip 属性、两个身份、节点与任务集合；保存并导出源，再导入新 EXPO_004_HDR_DOMAIN。只有副本调用设置 setter。通过同一官方 ResolveMCP 的 stdio `run_script` 运行，没有使用原生界面绕行。

| 设置请求 | 返回值 | 实际读回 |
|---|---|---|
| `separateColorSpaceAndGamma=1` | true | p/t 的 Timeline、Output 空间由 Rec.709 (Scene) 变为 Rec.709；clip Input Gamma 从 Gamma 2.4 变为 Rec.709。有联动，停止后续 Linear 请求。 |
| 六个 Input/Timeline/Output 空间与 Gamma 字段的批量请求 | false | Timeline Gamma 仍由空值改成 Rec.709；目标未全部满足，该探针未执行 Linear。 |
| 单字段 Timeline Gamma=Rec.709 | true | 已是该值，没有变化。 |
| 单字段 Timeline Gamma=Linear | false | 本次完整 p/t/clip 读回没有变化。仅说明本构建、模式、setter 和字符串的结果。 |
| 单字段 Timeline Gamma=Gamma 2.4 | true | p/t 只改变 Timeline Gamma，完整 clip 属性和两个身份不变。 |

SDK 使用 `Project.SetSettings(dict)`。批量返回 false 不是原子回滚，必须读回实际状态；不能因此断定各个单字段都不支持。各探针请求/差异和回执哈希见[配置摘要](../experiments/resolve-hdr-setting-probes-result.json)。

## 3. 七帧冻结实验

两个运行中完整 Project/Timeline 字典只在 `colorSpaceTimelineGamma` 上不同；完整 clip 属性和两个身份相同。共用 YRGB、Rec.709 原色标签、separate=1、`useColorSpaceAwareGradingTools=0`、无 tone/gamut mapping。运行中 Input/Output Gamma getter 均为空，clip Input Gamma getter 为 Rec.709。此处未证明这些标签对应的实际解码流程。

自制输入为 1920×1080、不透明 RGB16 sRGB PNG，SHA-256 `2daa68135e4ac8c0585fb33630ce5d69a735640799b82a8173caafbfc8d9f09f`。固定单视频轨、单 clip、首帧 108000、单 node-stack layer、单节点、空 LUT。输出 EXR/RGBFloat，1080p30，无音频或 alpha。

| 顺序 | 时间线 Gamma getter | grade |
|---:|---|---|
| 1 | Rec.709 | 无 HDR 的中性参照 |
| 2 | Rec.709 | 已校准的 stored gainjz=−1 |
| 3 | Rec.709 | 已校准的 stored gainjz=+1 |
| 4 | Gamma 2.4 | 无 HDR 的中性参照 |
| 5 | Gamma 2.4 | 同一 stored gainjz=−1 grade |
| 6 | Gamma 2.4 | 同一 stored gainjz=+1 grade |
| 7 | Rec.709 | 恢复无 HDR 的中性参照 |

**本轮没有新增 HDR 零档帧。** 中性与精确 HDR 零档的关系由第四轮确认，不能把这三个中性 grade 重新标成 HDR 零档观察。用户确认 palette Color Space/Gamma 均“使用时间线”属于 003 原条件；未升级成 004 的菜单见证。

七个新任务 ID 均排除 inherited/owned ID，再只启动该 ID；全部 Complete/100%，无其他渲染进行。每档设置后、ApplyGrade 后及 SetRenderSettings 后均检查完整配置、身份、layer/node/空 LUT。没有删除任务或调用 StopAll。15 个生成原生脚本在执行前离线 compile，计划经独立审查准入。

## 4. 参数读回与整幅像素

四个非零档各抓取唯一标签 still，下一次 sandbox 独立导出 PNG/DRX。独立 descriptor 解析确认每份唯一 `0x86000305 → HDR#16 → Global gainjz` 为精确 float32 −1 或 +1。其他 HDR 值、presence/default、所有 Parameter 原始与 canonical 字节、节点身份均与来源相同。每份两个 Body 的未知字段、wire、required、oneof、未消耗字节问题均为零；Body 只改变 lastmodtime。该读回不是新的 UI 显示点。

每帧手写 uncompressed scanline 解码与 OpenCV 的 6,220,800 个 float32 通道逐字节相同，再比较整幅 RGB：

| grade | 改变通道数 / 6,220,800 | 最大绝对差 | RMSE |
|---|---:|---:|---:|
| 中性 | 0 | 0 | 0 |
| stored −1 | 5,054,400 | 1.49011612×10⁻⁷ | 4.34120372×10⁻⁸ |
| stored +1 | 4,406,400 | 2.63582642×10⁻⁷ | 9.06789276×10⁻⁸ |

−1/+1 不能称逐位相同：改变通道很多，绝对差很小。没有事后选择阈值宣布等价，也没有同条件重复非零渲染给出的噪声界，不能把微差单独归因于 Gamma。Rec.709 配置的中性、−1、+1 三幅整图与 003 第四轮对应 RGB 字节相同；最后中性恢复也逐位一致。

两个配置的 48 个中心通道各复算五候选，只纳入实际 −1/+1 观察。Gamma 2.4 配置的 BT.709 候选仍最接近：−1/+1 最大误差 0.0006074873 / 0.0011338615；纯 Gamma 2.4 为 0.0430310805 / 0.0685722495。BT.709 假设解码后的两档比值离 4 最大差 2.21674×10⁻⁶。**Timeline Gamma getter 改成 Gamma 2.4，没有使这个纯幂候选吻合输出。** 这仍不是原生实现归属证明。

独立数值复核 884 项全部通过，其中两配置五模型 240 个统计最大差为 4.44×10⁻¹⁶；独立 scanline 解码核对七幅 RGB 哈希、336 个中心通道、跨配置差异及与三幅旧原生图的字节关系。中性恢复的 RGB 和 EXR 文件字节都相同。

数据：[七帧结果](../experiments/resolve-hdr-gamma-conditions-result.json)、[Rec.709 候选](../experiments/hdr-rec709-condition-candidates.json)、[Gamma 2.4 候选](../experiments/hdr-gamma24-condition-candidates.json)。工具：[解码](../../experiments/measure-resolve-exr.py)、[配置比较](../../experiments/compare-hdr-gamma-conditions.py)、[候选复算](../../experiments/evaluate-hdr-domain-candidates.py)。原始 EXR、DRX、工程和完整回执保存在忽略目录；公开摘要不包含用户素材、授权信息或目标伪代码。

公开 JSON 按仓库规范固定为 UTF-8/LF；候选报告的 `source_sha256` 明示以 LF 文本计算，私有原生文件/回执仍按原始字节计算。LF 与 CRLF 两份同内容输入实际复算得到逐字节相同的候选报告；换行修正前后，三份候选的所有模型数值相同。此前独立核查的原始公开文件字节已另存私有目录，保留版本关联。

## 5. 保存、重载与恢复

004 恢复 Rec.709 配置的中性 grade，保存并导出 `after-gamma-grid.drp`。第一次恢复检查把源的 18 字段子集误比完整 GetSettings，断言停止。改正检查后，004 保存重载出现真实差异：p/t 的 Input/Output Gamma 从空值变为 Gamma 2.4，gallery/media 路径改反斜杠；**perfCacheClipsLocation 从 case 绝对 render-cache 路径变成 `CacheClip`**。clip 属性无变化。

这些是七帧之后的重载读回。没有在后来状态重渲染，不能声称配置完整不变或缓存仍隔离。下次操作 004 前须核定实际缓存路径和颜色配置。

恢复还出现一次脚本误把 003 身份用于 004 的检查，在身份守卫处停止，未执行设置操作。所有失败脚本/回执保留。最终用冻结的 004 身份和实测重载快照，确认七个所属任务 Complete/100% 与副本中性状态，再切回 003：源的 18 个颜色/格式字段、完整 clip 属性、两个身份、原任务 ID 集合、单节点/空 LUT/中性状态均通过，无渲染进行。这不是源全部 ProjectSettings 的变化审计。

## 6. 下一步

已确认原生 HDR 载体、−1/0/+1 离散 UI 校准、固定输入输出响应和两个配置下的观察。任意 UI 值完整映射、实际解码、palette 持久化层级、HDR 感知空间/色度处理及完整曝光公式仍未知；`gainjz` 的名称不替代调用链证据。

先核对“使用时间线”、项目 color-space-aware 配置和重载状态如何连接 HDR 上下文，再设计能使候选给出明显不同预测的控制点。固定样本拟合不能直接升级成 OpenCut 产品公式；自主核心仍需明确颜色语义和独立实现规格。阶段 1A 继续进行。
