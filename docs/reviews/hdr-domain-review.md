# HDR 操作域：设置探针独立审查

日期：2026-10-13（Asia/Shanghai）。本次只读已安装 SDK 声明、源工程核查、私有探针源码和回执；只写本文件，没有调用 Resolve/MCP/SDK、执行目标、修改工程/grade/配置或下载依赖。前一轮 003 的六帧结果另见 [HDR 映射与执行审查](hdr-mapping-review.md)。

**当前结论：第五轮公开材料及 UTF-8/LF 序列化增量终审完成，无未关闭的必须修正项；七帧任务、四组配套图库读回及恢复范围有对应证据。** 884 项独立核查的原始字节已归档，当前 LF 版本通过对象一致及明确的规范化哈希策略关联；不声称旧 raw hashes 仍直接匹配当前文件。本子代理没有重跑新帧或重读全部 EXR。七帧在原计划的运行中快照下渲染；004 保存重载后出现设置联动，不能改称重载后的 Input/Output Gamma 2.4 配置实验。两个执行前 P2 已关闭，三次恢复失败均保留。实际曝光运算域及完整公式仍未证明，阶段 1A 继续进行。

## 声明、范围与来源

本机 SDK 的 `separateColorSpaceAndGamma` 声明为字符串 `0/1`；Input/Timeline/Output Color Space 和 Gamma 是分别声明的字段。`Project.SetSettings` 接受 settings dict；这不保证任意 Gamma 字符串在当前模式中都受支持。[字段 L494](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/DaVinciResolveScript.pyi:494>)、[SetSettings L1874](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/DaVinciResolveScript.pyi:1874>)。

`Timeline.GetSettings` 在不使用 custom settings 时返回 project settings，另有独立 timeline settings 声明。因此项目 getter 的 Linear 不能代替对 timeline 的读回，两个 getter 都应保留。[Timeline.GetSettings L2303](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/DaVinciResolveScript.pyi:2303>)。

源 `revalidate-source-result.json` 仍为 21.1.1.10 / Disk 测试库 / EXPO_003_HDR_MAPPING，单视频轨、指定 PNG16、首帧 108000、单层单节点、空 LUT、活动工具 None、没有渲染进行。冻结颜色项与第四轮一致，原六个任务仍列在源工程中。素材路径及两个唯一身份进入了实际脚本守卫。

探针先保存/导出 003，再在确认 004 不存在后导入新副本，只有副本调用设置 setter；gallery/cache/media 路径转到新 case 并读回核对。源有 Save/Export 动作，不能称为绝无状态变化；没有对源进行调色 setter 或改写其输出文件。新副本的任务列表应以实际读回为准，不能假定导入一定继承或清空源任务。

这里“无渲染探针”指没有创建/启动测量渲染任务。LoadProject、设置修改和保存会改变宿主状态；本审查不证明宿主内部没有预览渲染，也没有对应用全部缓存/日志作审计。

## 初稿发现与修复

| 严重性 | 状态 | 证据及处理 |
|---|---|---|
| P1：未声明的 setter 参数形式 | 已关闭，初稿未执行 | 初稿使用两参 `SetSettings(name,value)`，与本机声明的 dict 参数不符。已改为 `SetSettings({"separateColorSpaceAndGamma":"1"})`；保留 initial-not-executed 版本。 |
| P2：分离后未知联动仍会进入 Linear | 已关闭 | 初稿只检查开关和 color science 后继续第二 setter。修正版计算完整 project/timeline/clip 差异；首步非目标联动会跳过 Linear 并保存副本/证据。 |
| P2：选择性字段快照遗漏上下文 | 已关闭 | 原来每阶段只保留 18 个键且 clip 只在末尾读取。修正版每阶段存完整 ProjectSettings、TimelineSettings、ClipProperty 及素材/片段身份，另保留冻结项用于源守卫。 |
| P2：项目标签读回可能冒充有效 timeline/操作域 | 已关闭 | 修正版分别检查 project 与 timeline 的目标读回，Linear 的非目标变化也停止；ready 仅表示可设计后续实验，`operation_domain_proven=False`。 |
| P2：第二探针可能跳过缺失的有效 timeline 字段 | 已关闭，执行前修复 | 第二探针初稿对 `if k in timeline_settings` 的键才作核对，可能省略缺失的 Color Space。实际执行版本逐一要求 Timeline/Output 的四个目标键读回，不能以缺失键通过验收。 |

没有因为 SDK 字段声明存在就将 setter 当作已运行；只读审查后，实际结果再按回执核对。失败/未知状态保存于副本，不删除或盲目重跑 one-shot 创建脚本。

## 已执行首步的实际结果

独立读取 `clone-and-probe-timeline-gamma-result.json`：工具正文正常返回，Separate setter 为 True，开关由 0 变为 1；但完整快照还出现以下联动。

| 位置 | 原值 | 读回值 |
|---|---|---|
| project 和 timeline 的 Timeline Color Space | Rec.709 (Scene) | Rec.709 |
| project 和 timeline 的 Output Color Space | Rec.709 (Scene) | Rec.709 |
| clip Input Gamma | Gamma 2.4 | Rec.709 |

回执明确 `linear_return=None`、ready=False、stopped=True、operation_domain_proven=False；004 已保存导出，任务列表为空，没有渲染进行。停止分支确实生效。

这个结果证明开关可接受并伴随字段联动，不证明新旧颜色条件等价。Linear 根本未调用，不能把本次 stopped 写成“Linear 不支持”或“SDK 不能控制颜色域”。也不能仅因项目 input 字符串看似未变，就忽略 clip Input Gamma 已变。

## 后续只读回探针的实际结果

独立读取 `probe-explicit-separated-conditions.py`、`probe-single-timeline-gamma.py`、`probe-timeline-gamma24.py` 及对应三份原始 JSON 回执，重算完整 project/timeline/clip 差异，核对两个素材身份及相邻探针 before/after 连续一致。每份回执任务列表为空、rendering=False；源码均没有创建或启动测量任务。

| 请求 | setter 与实际读回 | 停止/准入边界 |
|---|---|---|
| 六键明确设置：Input Rec.709/Gamma 2.4、Timeline Rec.709/Rec.709、Output Rec.709/Rec.709 | False；project 和 timeline 的 Timeline Gamma 从空串部分改为 Rec.709，其余五个请求键未变，clip 未变 | explicit_ready=False，Linear 未调用，保存实际部分状态。 |
| 单键 Timeline Gamma=Rec.709 | True；完整快照无变化 | 该当前值请求可接受。 |
| 单键 Timeline Gamma=Linear | False；完整 project/timeline/clip 快照无变化 | 不支持本次请求；不能推广为所有 Linear 途径或整个 SDK 不支持。 |
| 单键 Timeline Gamma=Gamma 2.4 | True；project 和 timeline 仅该键 Rec.709→Gamma 2.4，clip、两个素材身份均未变 | ready_for_render_design=True；operation_domain_proven=False、palette_menu_verified_in_this_copy=False。 |

六键 setter 的实际反例说明本路径不是原子提交：False 不等于没有改变，也不等于六个字段逐个都不支持。必须保存失败后的完整实际状态，后续守卫应以读回值为准，不能从返回值重建状态。各次 Save/Export 的动作已经发生，这些仍是工程设置探针。

Gamma 2.4 被 SDK 字段举例不等于运行成功；本次成功结论来自上述返回值和完整读回。当前 004 与原 003 的设置已不同，不能称为旧条件的语义归一化。

拟议 Rec.709/Gamma 2.4 七帧实验应另冻结实际全部 project/timeline/clip 值、输入摘要、身份、grade、帧和队列，只启动本轮新增的单个 owned job，按实际完成逐状态推进。两个条件的 neutral 必须作真实像素对照，另保存恢复态；不允许据名称直接宣布新旧 neutral 等价。以上是执行前要求，实际执行及恢复结果见下文。

## 七帧计划的执行前审查

以下保留执行前准入时点的结论。已读取 `frozen-gamma-conditions-plan.json` 与当时尚未执行的 `run-gamma-conditions-grid.py`。计划两组完整快照分别等于 Gamma 2.4 探针的实际 before/after；只有 project/timeline 的 Timeline Gamma 键不同，clip 和素材身份相同。序列为 Rec.709 neutral/−1/+1、Gamma 2.4 neutral/−1/+1、Rec.709 neutral 恢复；中性 grade 与 ±1 grade 使用前轮固定摘要，没有把 CDL 或 OCIO 输出替换为原生对照。

脚本已核查版本/库/项目/单时间线/单轨单素材/单层单节点、新目录、PNG 与 grade 摘要、初始空任务表；明确单 ID StartRendering 并逐 ID Complete/100/idle 后推进。初稿发现两项 P2，修订版已独立逐行复核关闭：

| 严重性 | 当前状态 | 反例与必要修正 |
|---|---|---|
| P2：任务集合核对未单独排除已有 ID | 已关闭，执行前修复 | 集合 `jobs == old ∪ {job}` 在 `job` 已属于 old 时仍可能成立。修订版 AddRenderJob 后显式断言 `job not in inherited_ids+owned_ids`，再核对任务集合，最后才 StartRendering 单 ID。 |
| P2：完整条件核对早于 grade 应用 | 已关闭，执行前修复 | 初版 full project/timeline/clip 与空 LUT 检查在 ApplyGrade 前，Apply 后只验 nodes/tools。修订版 `verify_context()` 在 setter 后、ApplyGrade 后和 SetRenderSettings 后均执行，包含完整 project/timeline/clip、素材身份、layer=1、node=1 和空 LUT；全部通过才 AddRenderJob。 |

修订脚本已经加入四个非零状态的配套原生读回：各自 Complete/100/idle 后仍守卫当前条件、timecode 和 HDR 工具，使用新的 Domain 标签、独立目录及回执，GrabStill/标记/Save 后在下一次 sandbox 调用导出唯一 still 的 PNG/DRX，不覆盖早期证据，失败立即停止。这些是隔离副本图库的实际写入和导出；不能把它们称作无状态的只读 SDK 查询。

脚本只记录 `type_validation_pending=True`。导出成功不等于消息类型或参数语义正确；须再以 descriptor/严格结构确认实际 stored ±1 及其余上下文。这不是新的 UI 档位见证，也不是证明实际运算域的替代证据。

本次复核的 harness 为 6868 字节，SHA-256 `4b3dee555798dea9699147fb1eb191da6d20dcd4e4b1ef3131fdceb14b752bd7`。主代理报告已离线组装并 compile 七个 render 和八个 capture/export 脚本，摘要与本次所读版本一致；本审查没有执行这些 SDK 脚本。该版本准入仅限冻结计划的七帧 EXR 和四组图库读回，不代表实帧完成、类型确认、恢复完成或操作域证明。

## 七帧完成及恢复诊断的增量复核

只读七帧任务台账、对应原始 render 返回、四组读回文件及 descriptor 验证记录，以及五个恢复/诊断脚本和回执。七个新 ID 唯一、与最后成功回执中的七个 Complete/100 任务一致；初始继承任务为空。四份实际 DRX 的摘要与台账和独立结构记录一致；结构记录 4/4 为精确预期 Global.gainjz，保留同源 Parameter/节点身份，没有把条件标签从 grade 数值猜出来。本增量没有重新执行 descriptor 验证器、渲染或解码全部新帧。

| 步骤 | 原始回执与实际边界 |
|---|---|
| finalize-and-return-source | AssertionError 第 25 行。004 的原计划完整快照、中性守卫、七任务 Complete/100 和 Save/Export 已通过；Load003 后误把源 18 字段字典与完整 GetSettings 比较而停止。整个调用没有成功 result，不能用其未返回的 `source_full_settings_match=True` 当证据。 |
| verify-restored-source-and-copy | 源 18 字段、完整 clip、身份、原任务 ID 集合与中性守卫通过；Load004 后在第 23 行完整配置比较停止，不能将其结尾未返回的成功字段当证据。 |
| inspect-copy-after-reload | 成功保存完整实际快照：project/timeline 各 158 个键；相对原计划出现下面的重载联动，clip 无差异。 |
| verify-copy-reload-and-return-source | 第 23 行重载设置检查已通过，随后第 24 行错误采用 003 身份核对 004 而停止。此脚本没有设置 setter、grade setter、渲染或删除操作；尚未走到 Load003。 |
| verify-copy-reload-source-final | 使用正确的冻结 004 身份和实测重载快照，通过七任务 Complete/100、空 LUT、单层单节点、中性工具及 idle 检查，再 Load003；源既定守卫全部通过，最终 rendering=False。 |

本审查用 Python `ast.literal_eval` 只解析固定脚本的字面量，并与原始回执作静态比较：末次 source 字面量完整等于最初 revalidate-source 记录，其中 project_settings 恰为 18 个字段；末次 004 身份等于冻结计划，错误版本身份确为 003；末次 expected 设置等于实际重载快照，早期 expected 则等于运行中计划。没有执行这些脚本中的 SDK 语句。

重载联动必须精确写明：Input Gamma、Output Gamma 均从空串变为 Gamma 2.4；gallery 和 project-media 路径从正斜杠形式变为反斜杠形式；**perfCacheClipsLocation 从 case 的绝对 render-cache 路径变为字面值 `CacheClip`，不是分隔符变化。** project 和 timeline 都出现这些差异。未确定 `CacheClip` 的实际解析位置，不能声称重载后缓存仍在本 case；后续操作 004 须重新核定其实际路径和全部条件。

末次 `copy.full_frozen_settings_match=True` 指匹配**实际重载快照**，不指原来渲染时的完整快照不变。七帧均是在原始运行中条件检查通过后启动；保存重载发生在七帧之后，不能以后来补出的 Input/Output Gamma 值重新命名这些实验，或声称后来的配置已经渲染验证。

最终源验证仅覆盖 18 个冻结颜色字段、完整 clip 属性、素材/片段身份、单时间线/轨/素材/节点/层、timecode/frame、空 LUT、活动工具 None、原任务 ID 集合及 idle。回执明确 `source_full_settings_comparison_claimed=False`；没有源 full settings、全 grade 字节、所有任务属性或应用缓存/日志全量不变的证明。三份失败原始 JSON 和脚本均保留，不能覆盖为成功；没有新增必须阻止当前收尾的执行项，缓存变化和像素汇总终审仍须按上述范围记录。

## 公开汇总终审（LF 规范化前记录）

本节保留当时的原始字节与代码摘要；这些公开 JSON 已另存 `analysis/pre-LF-public-json`。当前 LF 版本的关联与代码摘要见下一节。

已读取第五轮主报告、README、立项书 0.9、七帧结果、设置探针摘要、两份条件候选结果及两个复算脚本。主报告明确区分无 HDR 中性 grade 与 HDR 零档，本轮新 HDR-zero 观察为 0；004 的 palette 菜单没有直接见证。中性整图逐位相同与非零档的微小数值差分开，未用阈值宣布等价，也未把微差归因为 Gamma 设置：没有同条件非零重复渲染给出的噪声界。保存重载的 `CacheClip`、后来默认 Gamma 和源仅 18 字段的边界均已修正文案。

独立研究代理的 `independent-gamma-condition-numeric-check.json` 使用另写的 uncompressed FLOAT scanline 读取器和逐标量候选函数，没有导入生产测量器/比较器/候选器。其 884 项均记录通过，含七帧 6,220,800 通道/帧、336 个中心通道、三幅旧 003 图、两条件五模型 240 个统计核对；240 项最大差 4.440892098500626×10⁻¹⁶。该记录 SHA-256 为 `2a56886cbd6d14befa4eca3f78139e52ca44f8ecb5aee042ef8bd57e6d247daf`。

本子代理在该时点独立关联了记录引用的六个小型来源摘要、七份测量 JSON 摘要、公开图像/像素摘要及中心值、整图比较统计、配置探针和最终恢复回执摘要；它们与当时待提交的原始字节版本吻合。规范化前七帧公开 JSON SHA-256 为 `3af74f336054d984bdc31c6287b25562502f9ce0fa41ba33de98ac48ae1d164e`，当时两份候选的 source_sha256 均指向此完整文件；condition 分别为 rec709/gamma24，实际 observed_stored_levels 仅为 −1/+1。884 项是上述独立研究代理的实帧/标量核查，不是本子代理另跑一轮的数量。

跨配置整幅数值差已对应公开表：−1 改变 5,054,400 通道、最大差 1.4901161193847656×10⁻⁷；+1 改变 4,406,400 通道、最大差 2.635826419350451×10⁻⁷，均不能称逐位相同。中性与恢复的 RGB 字节相同；当前两配置中性/恢复的 EXR 文件也相同。Rec.709 三档与旧 003 比较的是 RGB 字节，不把旧文件容器字节也说成相同。

`evaluate-hdr-domain-candidates.py` 的新增条件路由只切换输入样本并读取实际已有的档位；未构造新的 HDR-zero。旧 `hdr-domain-candidate-result.json` 对象与本子代理前次冻结对象逐项相同。公开候选算术可由七帧 JSON 和 source/output/condition 三个参数复算；整幅比较另需私有计划、EXR、测量记录和旧 case，不能称只靠公开中心值证明整图。比较脚本检查原图/像素摘要并保留 byte equality、数值变化计数、最大差和 RMSE；没有拟合或裁切后再比较。

本次所读代码摘要：`compare-hdr-gamma-conditions.py` 为 `8577cb6ee138702237dd103f615929d64dbb0a802cfd013ae6c012abf6bd9c0e`，`evaluate-hdr-domain-candidates.py` 为 `5e207c225a0a1458a1d08befad78f3f0c6604a478a3c7f5d126407ecb4205bc3`。这次只读核查没有再次运行它们或安装依赖。

两项非阻断文案建议已关闭：README 的六帧计数明确属于第三轮；恢复段已改为在身份守卫处停止、未执行设置操作。立项书累计 19 张正式 EXR 对应第三轮 6、第四轮 6、第五轮 7，不计图库 PNG/DRX。当前有限观察可供继续设计辨别性实验，不能直接升级为物理 EV、Jz 算法、任意 UI 映射、视频泛化或 OpenCut 产品公式。

## UTF-8/LF 序列化增量审查

仓库的 LF 规范会改变原 CRLF 公开 JSON 的 raw SHA-256。主代理先保留五份原始公开文件，再将待提交文件固定 UTF-8/LF；候选报告新增 `source_hash_encoding="UTF-8 text with LF newlines"`，source_sha256 对完整输入 UTF-8 文本的 LF 换行形式计算，不受条件样本选择影响。两个 writer 显式 `newline="\n"`。私有原生文件、回执与原审查归档仍按各自原始字节核对。

本次只读逐字核对代码：相对于上一审查版本，候选器只改变上述 hash/声明/writer，比较器只改变 writer，没有预测函数、模型、渲染或 grade 变化。五份归档对象均等于本子代理先前实际读取的对象；884 记录中受影响的七帧公开结果及两条件候选 raw hashes 精确匹配归档。当前七帧结果与设置摘要的整个 JSON 对象未变；三份候选除 source hash/encoding 元数据外对象完全相同，所有 models 均 deepEqual。

当前旧 003 候选的 LF source SHA-256 为 `3e4a3914667364ca96fcf225ac652cd0aa9342621d4b700f8cfd5e6a15b4e2c4`；本子代理只读取得 HEAD 的旧 003 JSON 原始 LF blob，独立验证摘要相同，旧源未被本增量修改。当前七帧 JSON 的 LF source SHA-256 为 `3b4a09525df53282de909e234a00120ee8ab024d4a6456a4461207a10e2c7419`，两个条件候选均正确引用它。

只读 `LF-portability-check.json` 和实际两输入/两输出：LF 与 CRLF 输入仅换行不同，规范化文本相同；实际输出逐字节相同、均为 LF，SHA-256 为 `061e2c211dd845623f2632908e40bd21890a5da6c92501e0e48ba879cd9ccab0`，与记录一致。五份当前公开 JSON 均无 CR 字节。没有重新运行候选器、解码器、SDK 或原生渲染。

本次代码 SHA-256：比较器 `85b0f94a70b081563b73200278e16604a359fed9657e417a2fb0e13d9338fbec`；候选器 `8eed34e848c73c574cd22c15b075116b7ead51c0f615fcd0f86550d8c760d1aa`。此前 884 项保持为归档原始版本的历史核查；当前数值凭完整对象/模型同一关联，新增 hash 元数据和换行可移植性另按本节验证。没有新增实帧、精度或跨平台数学一致性的验收声明。

## 固定 48 通道候选的独立复算

本节使用原 003 第四轮的固定 48 个中心通道，并非新增 004 两配置的帧。只读 `evaluate-hdr-domain-candidates.py` 和 `hdr-domain-candidate-result.json`，用独立 JavaScript 标量函数复算五个固定候选的三个档位、全部/灰阶/色块误差、最差点、假设解码域的有效档位和非零两档比值。280 项数值/计数核对在绝对差 2×10⁻¹² 内吻合；这只是两个 float64 实现之间的复核容差，不是原生模型的误差验收阈值。当时工作副本来源 JSON 的 raw SHA-256 为 `64e270cc23fc5722be95a013640c977ab2382dc27fe70b8305546f345c24e760`，与上节当前 LF 文本 hash 属于不同字节约定；48 个中心 RGB 值与本审查上一轮手写 EXR 解码的实际样本逐值相同。没有重新运行 Resolve 或重读整幅 EXR。

BT.709 候选使用固定舍入常数及 Colour 逆式阈值 0.08124794403514046；在 36 个 baseline、−1、+1 均为正的通道上，解码后 +1/−1 比值为 3.999999042042889…4.00000213919231，最大离 4 为 2.1391923104×10⁻⁶。但相对 neutral 的绝对预测仍有 −1 最大误差 0.000607487268278、+1 最大误差 0.001133742270584，不能省略这些残差或称精确恢复。

这是非零两档之间在假设解码域中的相对关系。共同偏差相对于 neutral 可以同时存在，因此 ratio≈4 不能证明每档相对 neutral 恰为 2^E，也不能证明实际输入解码、物理 EV 或 Jz 运算。选择 36 通道是分母和正值域的明确筛选，不包含 baseline 为零的 12 通道；原生小负值仍留在全部 48 通道的误差统计中，没有裁切后再对照。

五个候选都没有拟合自由参数；纯 Gamma 2.4、sRGB 分段函数和 OCIO 视频指数 1.83 是不同的数学候选，名字不代表它们曾被 Resolve 调用。BT.709 大于 1 的部分是约定的代数延拓，舍入接点的间隙也已明示。只核对本次固定点回环，不能推广为全实数域严格互逆。[一手公式与候选假设报告](../research/hdr-exposure-domain-primary-models.md) 已区分标准、固定实现、未取得的原论文正文和未证明的原生运算；本次独立复算没有另行认证其全部外部来源或 Jz 分支。

## 必须保留的混杂因素

003 的 palette Color Space/Gamma“使用时间线”是原用户见证；004 导入后的持久化粒度没有独立确定，不能升级成 004 的菜单实测。项目/时间线字段可以成为受控条件，palette 和实际算法域仍是另一层证据。

YRGB 的项目 Gamma、clip Input Gamma、浮点 EXR 格式或 getter 中的 Linear 都不能单独证明实际解码→HDR→导出链路已处于线性光域。固定输入由 sRGB 编码生成，而已观察到的 clip 标签为 Gamma 2.4；输入生成的约 18% 线性灰与 neutral EXR 的编码通道值须分开描述。

后续在固定 48 个采样通道上检验 decode→2^stored level→encode 候选，应明确传递函数、阈值、超白/负值约定和候选输入来源。不用 LUT/CDL/OCIO 输出替代原生样本；候选拟合或排除也不能直接证明内部公式或跨颜色空间泛化。
