# HDR 上下文：005 设置探针与八帧执行器独立审查

日期：2026-10-13（Asia/Shanghai）。只读研究源码、清单、原始回执和本机 SDK 声明，并在内存中抽算公开候选数值；仅写本文件，没有调用 Resolve/MCP/SDK、启动目标、修改工程/grade/配置或下载工具。

**最新结论：阶段 A 设置探针及阶段 B 八帧/五组读回的结果终审完成，无未关闭的 must-fix。** 八帧均 Complete 100，五份严格 DRX 保持精确 stored+1及来源参数；Rec.709/sRGB 的 +1 整幅输出有差异，同条件重放、返回重复和三张中性逐位一致。源003完整冻结快照恢复有执行回执。四个阶段 A P2与一个阶段 B非阻断P3均已关闭。历史“未准入/尚未执行”记录保留时序，以后面的阶段 B 结果终审节为最新结论；完整 HDR 运算域、公式及005 palette菜单仍未证明。

## 范围与输入

拟从已导出的 004 中性 DRP 导入新的 EXPO_005_HDR_CONTEXT；源 003 不调用设置/grade setter。启动前冻结源完整 ProjectSettings、TimelineSettings、ClipProperty、两个素材身份、timecode 与任务列表；正常结束 Load003 后按完整对象相等检查。005 只请求 Timeline Gamma=Rec.709、sRGB，重新指向独立 gallery/cache/media 路径，没有 ApplyGrade、GrabStill 或渲染操作。

独立只读核对：

| 输入 | SHA-256 |
|---|---|
| 初稿 probe-context-settings.py，5278 字节 | bdeb74d9d487b47ac8bbcb5fc0dec069ccf119c27ffcc045cb534675b7999727 |
| 最终修订脚本，6724 字节 | 1b9219f88d2142299a246babe6606b01b3fd072720efc50d8973c76d0e83444a |
| after-gamma-grid.drp | c531b19a0782ecb765e97e15a930d586ee4503bacaa20fc37509d669502e5567 |
| 自有 PNG16 | 2daa68135e4ac8c0585fb33630ce5d69a735640799b82a8173caafbfc8d9f09f |

两个固定输入及最终脚本均与更新后的 context-probe-manifest.json 一致；初稿摘要保留为历史版本，准入时清单 native_execution_pending=True。实际执行状态以下文回执为准。工程创建、设置、Save/Load/Close/Export 会改变宿主或研究副本状态，“无渲染探针”只表示不创建/启动测量渲染任务，不保证宿主内部无预览或缓存活动。

## 执行前发现及修复

| 严重性 | 状态 | 具体反例与最小修正 |
|---|---|---|
| P2：同名 Load 不能独立证明重开 | 已关闭，执行前修复 | 初稿 L55-57 Save 后直接 Load 当前已打开的 005，返回对象及 getter 相同不能独立证明关闭重开。修订版 Save→CloseProject(仅已保存的005)→Load005，并校验返回项目名；失败进入有限恢复路径。不 Quit 用户进程。 |
| P2：异常路径不恢复 003 | 已关闭，执行前修复 | 初稿 L67-70 只有正常执行才返回源。修订版整个副本操作置于有限 try/except/finally，一次 Load003 并核完整 source_before；exception 保存实际 stage/type/message，恢复异常另存 restore_error。任何异常均 ready=False；restored 只在名字及完整快照断言通过后为 True。不删除失败副本或盲目重跑创建步骤。 |
| P2：部分阶段遗漏非目标联动 | 已关闭，执行前修复 | 初稿 differences()只比 p/t/clip，遗漏两个身份、timecode/jobs，路径 setup 也未排除其它字段。修订版 unchanged_identity()用于路径 setup、Gamma setter 和重开后；路径设置只允许三个路径键，Gamma setter只允许 p/t Timeline Gamma键，clip/其他完整字段变化均停止。重开后的完整三属性组差异要求为空。 |
| P2：重读取当前工程覆盖已确认句柄 | 已关闭，执行前修复 | 中间修订版在 Load005/核名后再次 p=GetCurrentProject()，没有核名就 isolate(p)，返回句柄与当前工程不一致的反例可能先写到003再被恢复比较发现。最终版仅删除该不必要重赋值，保持已确认的005句柄；与中间版本逐字差异仅此一行。 |

本机 SDK 已声明 `Project.SetSettings(dict)`、`ProjectManager.LoadProject(name)` 和 `CloseProject(project)`；不是因为字段或方法存在就推断请求已经成功。[SetSettings L1874](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/DaVinciResolveScript.pyi:1874>)、[LoadProject L1697](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/DaVinciResolveScript.pyi:1697>)、[CloseProject L1748](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/DaVinciResolveScript.pyi:1748>)。

主代理报告最终脚本 compile 已通过；本子代理静态逐行核对修复，最终摘要和 manifest 同步，未执行 SDK。准入只涵盖新建005、三路径隔离、Rec.709/sRGB 两次设置及关闭重开/读回、保存导出研究副本、一次返回003并核被冻结对象。setter False、目标不符、非目标联动或恢复失败都应如实返回停止状态，不代表探针通过，也不允许直接开始后续帧对照。

## 实际读回增量核查

独立只读原始 `probe-context-settings-result.json`，SHA-256 `cf25db0938204c9dc128a63d5333c15b32a6a81619ff78d9ca81e6eb87be8982`；JSON-RPC 工具结果及正文没有错误。ready=True、failure=None、restore_error=None、source_full_snapshot_match=True、active_project=EXPO_003_HDR_MAPPING、rendered=False，palette_menu_verified_in_copy=False。执行源码仍为上表最终版本。

005 初始 Input/Output Gamma 均为 Gamma 2.4、Timeline Gamma=Rec.709、render cache mode=none。Rec.709 请求 True 且三属性组无变化；sRGB 请求 True，唯一属性差异是 project/timeline 的 Timeline Gamma 从 Rec.709 变为 sRGB。两阶段 accepted、saved_reloaded 和 persistent_condition_ready 都为 True。

按已审源码，这些 saved_reloaded 记录在 SaveProject/CloseProject(005)/Load005 断言通过后才产生；不是 Load 当前同名工程的旧初稿路径。独立比较每阶段 before/after：两个素材身份、timecode、jobs 均保持；after_set 与**重设三路径后的** after_reload 整个 snapshot 相等，完整 p/t/clip 差异为空。Rec.709/sRGB 只在本次构建、模式、副本和请求值下获得上述观察，没有尝试或推广其它 Gamma 值。

每次关闭重开之后、路径重设之前，cache 字段实际回到 `CacheClip`，gallery/media 字符串又变为反斜杠形式；它们随后由 setter 重指到本 case。故 stable/persistent 在这里仅指重设后的条件保持，不能说三路径整体已经持久化，或全缓存活动都隔离。cache mode=none 也不替代文件系统/应用缓存审计。项目关闭重开不是整个 Resolve 进程、GPU 或所有 HDR 缓存的冷启动证明。

源 source_before/source_after 逐对象 deepEqual：ProjectSettings、TimelineSettings 各 158 个 getter 键，完整 ClipProperty 263 个键，两个素材身份、timecode、原六任务列表。snapshot 还重新守卫单时间线/轨/素材、单层单节点、空 LUT、工具 None 与 idle。本脚本没有源设置/grade setter；这个结果证明被查询/冻结的对象恢复，不证明全部源工程文件、grade 字节、全应用配置、UI/缓存/日志都未写入或完全不变。本子代理没有运行 SDK 或重建这些操作。

## 阶段 A 时的八帧计划范围核对（历史，彼时未准入）

只读 `frozen-cold-context-grid-plan.json`：两个完整 conditions 精确等于本次 Rec.709/sRGB 各自 after_reload，source_snapshot 等于实际 source_after，probe_receipt_sha256 指向上述原始回执。两条件仅 p/t Timeline Gamma 不同，clip、身份、timecode、空任务表一致；既有任务为空。

计划仍为八帧：Rec.709中性、Rec.709 stored+1、切sRGB保留+1、sRGB重放+1、返回Rec.709保留+1、Rec.709重放+1、sRGB中性、Rec.709中性恢复；五个非零状态配套原生参数读回。其 stored+1 与 neutral grade 仍使用先前固定摘要，不新增 −1/0 UI 校准，不把中性改称 HDR-zero。没有直接005 palette 菜单见证，也不把设置/重开/重放后的微差单独归因为其中某一动作。

阶段 A 终审时 render_execution_pending=True，runtime 尚无对应 harness；当时只核对真实条件来源和计划 scope，**未准入八帧、五次 still/DRX 读取或 grade 操作**。后续完整目标保持为这份八帧顺序实验；下面阶段 B 已另核具体执行器。

## 阶段 A 公开总结终审

已读取 `resolve-hdr-context-sixth-pass.md`、`hdr-color-context-primary-sources.md`、`resolve-hdr-context-setting-result.json`、README、立项书0.10，并按本文件的实际读回边界核对。公开探针摘要中的 script/receipt hash、两个条件的实际返回/差异/重开后颜色值、CacheClip、源158/158计数及恢复结果均与原始回执一致；当前摘要 SHA-256 为 `984dbcf7ef7fa7e60d4becedd69c745b69f7089860df2b63a085b7714f24898d`。

官方职责材料将 HDR 自身 aware、项目 checkbox、node HDR Mode、node Color Space/Gamma 分开，保留 YRGB、覆盖优先级和菜单持久化合同未知；没有将 aware=0 说成 HDR 关闭或推断该字段在所有 YRGB 情况下都无效。本增量核的是该摘要与实验声明的边界，不是另一次手册全文/PDF摘要重验。

第六轮 A 没有 grade setter、GrabStill 或新的测量帧，正式 EXR 总数仍为19；新八帧及五份非零读回均标待执行，执行器另需审查。没有把路径重设后完整快照相同写成全部路径持久化，没有把158/158 getter 加 clip/身份/TC/jobs 恢复说成全应用或 grade 字节审计，也没有新增005的 UI 菜单见证或像素验收。

非阻断渲染措辞建议已修复：主报告明确“未创建/启动测量渲染任务或导出测量帧”，公开 JSON 也限定 measurement job/frame 并说明内部预览未经审计。与阶段 A 真实动作和边界一致。阶段 A 终审无 must-fix，当时仅完成设置阶段的可审核记录，没有批准尚未提交审查的执行器或缩减既定八帧目标。

## 第六轮 B：八帧执行前准入（历史）

只读逐段审查私有 `runtime/run-cold-context-grid.py`，10775 字节，SHA-256 `cf8fa5853eab87be58d049570dd37fca74ef083bca4e4b318d2eb25a07fffe1f`；计划 `analysis/frozen-cold-context-grid-plan.json` SHA-256 `b9f2d67350c692bbb923f63fce9a1c7a9236aad7074f06c8abe49ac0901c0e38`。本次收尾再次核对这两个小文件摘要，未重验其它资料或运行原生程序。主代理另报告已实际离线组装并 compile 21 个 SDK 脚本（初始1、渲染8、capture/export10、恢复1、最终导出1）；这是主代理的离线验证记录，本子代理未重跑。

**执行前无新增必须修正项，准入仅限这两个摘要对应的既定八帧和五组 PNG/DRX。** 执行前 gate 必须匹配 harness 与 plan 摘要。当时主代理报告未创建准入标记、未执行原生步骤；该时间点没有成功帧数或读回结论。

已核对下列实际代码守卫及失败边界：

- 初始003须满足冻结源完整快照与中性/idle，再进入005。版本、Disk测试库、005项目名、单时间线/轨/素材、两个素材身份、timecode/frame、单层单节点和空 LUT 都有守卫。自有 PNG、两份 grade 摘要及所有新输出目录在原生调用前固定，已有脚本/回执/输出不覆盖。
- 各状态核上一档工具；Gamma setter 后 Save→Close仅005→Load005→重设三路径，再核完整 p/t/clip、身份/TC及任务集合。需要重放的状态才调用 ApplyGrade，保留状态不调用；Apply后和 SetRenderSettings后再次核完整条件。两条件只按 getter 配置命名，不继承003的 palette 菜单见证。
- 既有任务为空；每步实际任务集合须等于本轮 owned IDs，新 AddRenderJob ID 必须非空且不在 owned 中，新增后集合只多此一项。StartRendering 只传单一新 ID，逐该 ID 等待 Complete、100和宿主 idle；没有删除任务、全停任务、重启渲染或取消未知任务的路径。
- 非零档测量完成后才进入独立 capture/export 两次调用，复核005、完整条件、HDR工具及该任务完成。still 标签唯一、目录新建，输出 DRX 摘要保存并明确 `type_validation_pending=True`；成功 Export 或能解析 wire 都不能替代后续严格 descriptor、参数/分支身份和白名单差异验证。
- completed/owned、失败及恢复回执逐步保存。有限 finally 仅在已知003/005且 idle 时 Load003并比较完整冻结快照；仍在渲染时不切项目、不 Close/取消，保留该 owned job 和部分回执供同一任务后续观察。恢复出错或未完成均不能报成功；最终成功还要求八帧完成且 restored=True。失败步骤不得靠盲目重跑一次性 harness 覆盖证据。

“cold”在本轮只指每步明确关闭重开005；不证明整个应用、GPU或全部 HDR 缓存冷启动。三路径仍每次重新设置，CacheClip的既有重载行为没有变成全路径持久化或全文件系统隔离保证。八帧含有配置切换、保存重开、保留及重放的顺序历史；结果尚未知，后续相同/不同只能按实际帧和严格读回报告，不能先归因于唯一内部状态或推导完整算法。恢复源检查的含义仍限于冻结 getter/身份/TC/jobs与图守卫，不扩展为全工程 grade 字节或全应用审计。

## 第六轮 B：实际结果与公开材料终审

只读比较器、候选执行器、公开测量摘要与两份候选、阶段 B 报告、阶段 A 首段历史链接、README和立项书0.11；追溯本 case 的原始执行回执及独立 DRX/数值/候选核验。本子代理没有原生重跑或重新解码八张 EXR。整幅解码依据已关联的另一代理独立 scanline 核验；本子代理逐对象核对其公开投影，并另用 JavaScript 标量式从48中心通道抽算两条件五候选的十个最大误差，与公布值差为0。

| 当前证据 | SHA-256 |
|---|---|
| resolve-hdr-cold-context-result.json，UTF-8/LF | 1c931083bcd6deace7b6d5393d047451c5ade3c200e7db1c86815dabf118df83 |
| hdr-cold-rec709-candidates.json | ce671dda4a720fb8ea2a61ac0e9ac17271bf67e5b6cce5f8020a0de45981ab66 |
| hdr-cold-srgb-candidates.json | cd897b03c207c8c4f98f63a4cab5bce66a9258618b05e36a5e9b86c51994df1a |
| 私有 native-cold-context-render-results.json | ddad55d3ccf71c75f9edc7e0d1a3b2a1e84e3bb16544a5b399c4151b1a6ecdae |
| 私有 independent-cold-context-drx-validation.json | 15bb4f67962a2327749efa20043a95b50c96a5e49992785d9b26985a8589d80c |
| 私有 independent-cold-context-numeric-check.json | f685c99439394ded4d4da27de8cc9a8389fc1ca98d7eda3c752fa24f54629093 |
| 私有 independent-cold-context-candidate-check.json | 16f40afba1a9cef5175144c235a0bba2f08f61fc0191590ab06d8f0d51cbf061 |

公开 plan/receipt/strict hash与上述实际文件相同；五份读回的来源摘要均为固定+1 grade，每个 readback hash与实际对应状态相同。三个独立核验脚本的当前源码摘要也与各自回执绑定一致；两份候选的 source_sha256均指当前公开测量摘要。此处 LF文本与原始字节摘要相同，没有将旧换行版本的数值验证误关联到新内容。

原始 receipt 顺序精确对应冻结的八状态，八个 owned ID唯一，八份状态都是 Complete/100，failure=null；restoration报告 restored=true、source_full_snapshot_match=true、rendering=false、active_project=003。此前已读 harness中的 source_check按完整冻结 p/t/clip、身份/TC/jobs以及中性/idle守卫产生该结果；终审没有重新读取活宿主。这是冻结的两个158键getter、完整clip、两个身份、TC及原六任务集合恢复证据，不是全应用、全源grade字节或配置无写入审计。

独立帧核验共643项、全部pass，绑定当前公开摘要、原计划、receipt和strict结果；覆盖八帧、六对、旧003两帧及384个新中心通道。公开的每帧文件/整幅RGB摘要与中心值、六组统计及旧003统计都与该核验对象相同。每帧6,220,800通道，与48中心通道分别表述。Rec.709 +1与sRGB +1改变5,832,000通道，最大差0.03269296884536743、RMSE 0.02011247258578681；其余五对以及旧003两对RGB逐位相同。文件摘要与像素摘要分开，未由RGB相同推断全部EXR元数据相同。

五份strict checks名字唯一且覆盖所有非零状态。每份两Body已知字段计数86/35，unknown/issues/required/oneof/unconsumed均0，动态解析完整消耗并初始化通过；唯一Global gainjz float32为精确1，HDR #17/#18为0。全部7个Parameter原始/canonical字节、HDR标量存在性/默认值与节点身份保持来源，非时间戳语义叶变化为空。该结论没有依赖ParseFromString成功来判定消息类型，也不将时间戳/外层元数据变化说成整份grade字节相同。

| 发现 | 状态与最小修复 |
|---|---|
| P3：比较器仅按checks长度认定五份读回覆盖 | 已关闭。初版只assert长度5；把同一合格check重复五次的反例仍可能输出all=True。实际证据已由本子代理独立核定五个不同名字，本轮结果未受影响。最小修订增加check名字集合等于readbacks集合，并要求各check的source SHA等于该状态grade SHA；结合长度5可排除重复/遗漏和错来源。未扩展通用验证框架。 |

修订比较器 SHA-256 `e5e62f848bdb03085b5ef29a552f607d29edb6c25ffcaa0d08a1837a77f9d1a9`，当前源码中两个新增断言与上述反例对应；实际五份来源链接通过。主代理重算后公开测量摘要仍为表中同一 SHA，无需原生重跑。候选执行器 SHA-256 `1c824137901be048cda536abf9f620fb7f577cec55ed71971f221f224f9bc479`。

候选增量只筛选真实存在的观测，并仅在−1和+1都存在时计算配对。新两份JSON的每个model仅level1、observed_stored_levels=[1]，没有paired_nonzero_levels，没有制造−1或HDR-zero；基准明确是无HDR中性。独立候选核验206项全部通过，100个标量统计最大差2.220446049250313e−16，来源关联当前两份JSON与当前独立帧核验。BT.709最大误差仍为Rec.709条件0.0011337422705839373、sRGB条件0.03245493024587631，不能抹去残差或把标签当成实际解码域。

主代理新生成的历史003候选回归JSON与已发布报告逐对象完全相同；本子代理也将原003、第五轮Rec.709和Gamma2.4共三份历史候选与git HEAD逐对象比较，全部相同。公式、LF文本哈希约定和历史配对统计没有被单档处理改写。这里核的是固定历史对象及小增量，未新增EXR实验或重算完整旧帧。

README/立项书0.11的正式EXR累计27张与第三轮6、第四轮6、第五轮7、第六轮B8一致。阶段 A 首段已明确当时待执行并链接B，历史19张没有被改成阶段A渲染。主报告将读取/设置、保存重开、Apply、Grab/Export和测量渲染视为真实副本状态变化，没有宣称纯只读原生操作。

当前无未关闭must-fix。结果仅确认这次既定顺序和配置下的可返回响应：同条件重放相同不证明所有上下文/缓存等价，项目重开不证明GPU冷启动，路径重设不证明全文件系统隔离。005没有直接palette菜单UI见证，新帧只有stored+1与无HDR中性；固定候选不等于已恢复原生公式，也没有物理EV、负值/alpha、HDR/Log/RAW或真实视频验收。完整阶段1A继续，未据本轮确定OpenCut产品算子。

## 已合理限定与未验证项

初稿在 gamma setter 的 False、三属性组非目标联动或目标读回不符时停止后续请求；保存当前副本并返回源的正常路径不删除证据。空工程名检查使创建步骤为一次性操作，不能将重跑当作恢复方法。

从 004 DRP 导入后的初始状态需用实际 getter 确认，不能把旧运行中空 Input/Output Gamma 自动继承给 005；初稿已要求它们读回 Gamma 2.4。三条路径必须重开后再隔离并核定，尤其前轮曾出现绝对 cache 路径变为 CacheClip。路径字符串读回只证明 SDK 报告的配置，不证明全缓存写入位置经过文件系统审计。

aware=0 在本次作为固定配置，不测试它作为 HDR 开关；HDR palette 与其它 aware 控件的文档分工由资料任务另记录。本审查不新增 005 palette 的 UI 见证。阶段 A 的 sRGB setter 与保存重开读回本身只支撑实验设计；阶段 B 执行准入来自上面的独立 harness 审查，两者都不证明实际解码、HDR 内部域或完整公式。
