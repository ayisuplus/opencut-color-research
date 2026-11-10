# HDR 第六轮 B：关闭重开后的八帧与调色重放对照

2026-10-13，Resolve 21.1.1.10。接续[阶段 A 的完整设置快照](resolve-hdr-context-sixth-pass.md)，实际完成八张 EXR RGBFloat 和五组原生 PNG/DRX 读回。正式测量帧累计 27 张。

**结果：** 在专用副本 005 中，每档设置后保存、明确关闭并重开项目。Rec.709 与 sRGB 的 stored Global +1 输出有可重复的差异：整幅最大通道差 0.03269296884536743。各条件内重新应用同一 grade 的输出逐位一致；返回 Rec.709 后又与最初 Rec.709 +1 一致。三张无 HDR 中性参照完全相同。五份实际调色参数读回也完全保持来源参数。

这证明本次关闭重开与顺序实验中的配置响应。它不确定差异出现在哪个内部转换，也不使“选择 sRGB 就等于逐通道 sRGB 解码曝光”的候选通过。005 的 HDR palette 菜单没有直接 UI 见证；原先 003 的两个「使用时间线」见证不能自动继承给它。

## 固定条件与实际执行

素材仍为自制 1920×1080 PNG16，SHA-256 `2daa68135e4ac8c0585fb33630ce5d69a735640799b82a8173caafbfc8d9f09f`；YRGB、独立 Gamma 字段、单层单节点、空 LUT、无音频/alpha，时间线帧 108000。两条件的完整冻结快照只在 project/timeline 的 Timeline Gamma 标签不同；Input/Output Gamma 均 Gamma 2.4、render cache mode=none。

执行器和八帧顺序已[独立审查准入](../reviews/hdr-context-review.md)，各自 SHA-256 为 `cf8fa5853eab87be58d049570dd37fca74ef083bca4e4b318d2eb25a07fffe1f`、`b9f2d67350c692bbb923f63fce9a1c7a9236aad7074f06c8abe49ac0901c0e38`。每步 Gamma setter 后 Save→CloseProject(005)→Load005，再重设三个独立路径并核完整设置、clip、身份和 timecode。需要重放才 ApplyGrade；设置导出后再次核对完整条件。

| 实际帧 | Timeline Gamma | 调色动作 | 测量结果 |
|---|---|---|---|
| cold-rec709-neutral | Rec.709 | 应用无 HDR 中性 grade | Complete 100 |
| cold-rec709-plus1 | Rec.709 | 应用 stored +1 grade | Complete 100 |
| cold-srgb-plus1 | sRGB | 保留现有 +1 | Complete 100 |
| cold-srgb-plus1-replay | sRGB | 重放同一 +1 | Complete 100 |
| cold-rec709-plus1-return | Rec.709 | 保留现有 +1 | Complete 100 |
| cold-rec709-plus1-replay | Rec.709 | 重放同一 +1 | Complete 100 |
| cold-srgb-neutral | sRGB | 应用无 HDR 中性 grade | Complete 100 |
| cold-rec709-restored | Rec.709 | 应用无 HDR 中性 grade | Complete 100 |

既有任务为空，八个新 ID 唯一且只逐个启动本轮任务；没有删除或取消任务。各状态完成后保存原始回执，五个非零状态才独立 GrabStill、ExportStills。最后保存中性的 005 并导出 DRP，返回 003；其被冻结的完整 project/timeline getter（各158键）、clip、两个素材身份、timecode、六项原任务列表和中性图守卫重新相等。failure=null、restored=true。该检查范围不等于全部工程 grade 字节或全应用状态审计。

“关闭重开”仅指项目，不是 Resolve 进程、GPU 或全部缓存的冷启动。三个路径仍须每次重新设置；路径 getter 与 cache mode 不能替代文件系统缓存审计。

## 浮点画面与严格参数读回

每张 EXR 都通过手工无压缩 scanline 解析与 OpenCV 的整幅交叉核对：6,220,800 个 float32 通道逐位一致，16个色块中心共48通道另采样。[公开测量摘要](../experiments/resolve-hdr-cold-context-result.json)包含文件/像素哈希、六组比较及原 003 的对照；没有原始工程、路径或任务 ID。

另一代理另写只读解析器，独立复算八帧、六组整幅比较和两帧旧003参照，共643项检查通过，整幅统计差为0；384个新中心通道与像素哈希也匹配。它随后用独立标量公式核对两条件的候选，206项检查通过，100个数值统计的最大复算差为 `2.220446049250313e−16`。这两组验证均绑定公开测量摘要的实际 LF 文本 SHA-256 `1c931083bcd6deace7b6d5393d047451c5ade3c200e7db1c86815dabf118df83`；脚本和详细回执保存在忽略目录。

| 比较 | 改变通道数 | 最大绝对通道差 |
|---|---:|---:|
| Rec.709 中性 → sRGB 中性 | 0 | 0 |
| Rec.709 中性 → Rec.709 恢复 | 0 | 0 |
| Rec.709 +1 → sRGB +1 | 5,832,000 | 0.03269296884536743 |
| sRGB +1 → 同条件重放 | 0 | 0 |
| Rec.709 +1 → 返回 Rec.709 +1 | 0 | 0 |
| 返回 Rec.709 +1 → 同条件重放 | 0 | 0 |

新 Rec.709 中性及 +1 又分别与第四轮 003 的 neutral-before / hdr-plus1 整幅 RGB 逐位相同。色块5的红通道由中性 `0.461356520652771` 变为 Rec.709 +1 的 `0.666546642780304`，sRGB +1 则为 `0.688713788986206`；仅用这一中心样本不能替代上述整幅比较。

独立严格解析五份实际 DRX：都存在唯一 `0x86000305 → HDR #16 → Global gainjz`，float32 字节 `0000803f`，值精确 +1。两 Body 的已知字段计数为86/35；unknown、wire/issues、required、oneof、unconsumed 都为0，动态解析消耗完整长度且初始化通过。HDR #17/#18 实际计数均0。

与固定来源 grade 相比，全部7个 Parameter 的原始与 canonical 字节、HDR 标量存在性/默认值和节点身份相同。`0x860000bb/int=-1`、`0x86000309/int=2`、`0xc00000db/bool=true` 保持；不为这些未知伴随字段赋予 Gamma 语义。Body 只出现5处 lastmodtime 变化，外层 Buffer、ClipThumbnails、CreateTime、GalleryPath 也改变；不是整份 DRX 字节相同的声明。严格验证脚本及原始结果留在忽略目录，公开摘要只保留验证范围及哈希。

## 固定候选仍有残差

继续使用[已冻结的一手公式](hdr-exposure-domain-primary-models.md)，以每个条件实际无 HDR 中性 EXR 为输入，计算 `encode(2 × decode(C))`。本轮只观察 stored +1；没有制造 −1 或 HDR-zero 数据，也不计算非零档配对比值。五个候选均不拟合参数。

| 固定候选 | Rec.709 +1 最大误差 | sRGB +1 最大误差 |
|---|---:|---:|
| 直接 EXR 通道 ×2 | 0.5965884924 | 0.5744007826 |
| 纯 Gamma 2.4 | 0.06857213027 | 0.09075984008 |
| OCIO video 1.83 | 0.05707404561 | 0.05427918964 |
| sRGB 分段 | 0.05015593829 | 0.07234364810 |
| BT.709 舍入常数 / 固定 Colour 逆式 | 0.001133742271 | 0.03245493025 |

见[Rec.709 候选数据](../experiments/hdr-cold-rec709-candidates.json)、[sRGB 候选数据](../experiments/hdr-cold-srgb-candidates.json)。误差是48个实际编码通道与 float64 预测的差，不是物理 EV；BT.709 超白结果使用显式代数延拓。候选执行器新增“仅计算存在的观测”后，历史 −1/0/+1 报告已重算，完整 JSON 对象不变。

第五轮运行中两个 Gamma 配置只有约10⁻⁷差；本轮显式关闭重开的 Rec.709/sRGB 条件出现更大且可返回的差异。两轮的标签、重开与操作历史不同，不能单独归因为关闭动作，更不能把前轮微差推广为所有 Gamma 配置无影响。

接下来应在已核对的关闭重开条件下补足非零档配对，检验同一固定候选是否跨档位成立，并继续确认 palette/node 的颜色上下文。完整 HDR 算法与任意 UI 数值换算仍未知，阶段1A继续；尚未据此固定 OpenCut 产品公式。
