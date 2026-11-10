# HDR 第七轮：sRGB 三档配对独立审查

2026-10-13（Asia/Shanghai）。本子代理只读计划、研究源码、公开结果与原始回执，使用 Python AST 解析内嵌常量及JavaScript标量公式抽算；未运行执行器或任何 Resolve/MCP/SDK/目标程序，未改变工程、grade、配置或数据。仅写本文件。

**最新结论：五帧与三份严格DRX结果终审完成，无新增must-fix；执行前P2已关闭。** 五帧均Complete100，三档精确存储值有实际读回；零档保持HDR分支并省略默认0的标量，像素与无HDR中性相同。旧八项任务完整对象保持、源003冻结完整快照恢复均有执行回执，正式EXR累计32张。五个固定候选仍有非零残差；005的palette/UI及完整公式继续未知。以下准入记录保留历史时间点，最新结果见末尾终审节。

## 执行前固定对象与范围（历史）

case为 `evidence/local/resolve-hdr-srgb-pair-20261013`。继续使用专用005，保存003的冻结完整源条件；只操作本case新输出和五个新任务，不删除、取消或重复启动上一轮八个任务。

| 对象 | SHA-256 |
|---|---|
| 初稿 run-srgb-pair-grid.py，32665字节（未准入） | a66abc80a3ff884a35a3b3808acb3e8b19b3210c074398c8960294750a6b53d5 |
| 修订执行器，32890字节（本次准入） | 7b61da88d29e572869910d63633b04f3d14d06cf63cb021d2f513b0a76113cca |
| frozen-srgb-pair-grid-plan.json，94407字节 | f4dbd8618d1179336336c62552d530763177e765b33cf6e3ebcc7ee919a02e9f |
| native-script-compilation.json | a1b4730545bb521d9b2ee321e2d5831026fd04c6d057696127d4c7d68dd05068 |
| 前轮 native-cold-context-render-results.json | ddad55d3ccf71c75f9edc7e0d1a3b2a1e84e3bb16544a5b399c4151b1a6ecdae |

准入gate要求scope、harness和plan摘要匹配，输入PNG及每档grade还需在原生调用前核SHA。编译回执绑定修订执行器和同一plan，offline_only=true、native_calls=0，十九个脚本覆盖初始1、render5、初次poll5、capture/export6、finalize1、restore1。本子代理核对编译记录，另外只做AST解析及计划逐对象比较，没有执行SDK脚本。

五帧顺序固定为：sRGB无HDR中性、stored−1、精确stored0、stored+1、Rec.709无HDR中性恢复。三份HDR级读回对应−1/0/+1；不新增UI校准，也不将中性参照称为HDR-zero。素材与grade来自既有固定输入：PNG摘要 `2daa68135e4ac8c0585fb33630ce5d69a735640799b82a8173caafbfc8d9f09f`，neutral/−1/0/+1 grade摘要分别为 `388c39fca8def009a6e143d6ca50de115494cc9448c4f61b27504c95fd286fbe`、`da7c37fb9cca4c044e235376d633d6a2eaeb673bbe3835c04aacff51db00d49c`、`97bc24d12ed3cc44ead7898b0957770aa3d57d80dc524e4d844b5e839513760d`、`4cbbdb411d94641095c82b45415a40c728a9e56eda28dfe6e9d9abc04fbe17ef`。此轮没有重新生成这些grade或扩大校准范围。

## 发现、修复与复核

| 严重性 | 状态 | 证据与最小修复 |
|---|---|---|
| P2：最后一帧后未证明旧任务完整对象保持 | 已关闭，执行前修复 | 初稿L73只检查旧/新任务Complete100；旧表全对象和全ID集合守卫只在循环前、关闭重开后。最后一帧SetRenderSettings/Add/渲染之后没有下一循环复核。若旧job的MarkIn/MarkOut/Target等改变而ID和Complete100保持，仍可输出最终成功；这是守卫缺口反例，不是已观察到SDK改写。修订仅在finalize增加旧八项完整对象等于initial snapshot、全ID集合等于existing_ids+owned两断言，结果的existing_jobs_snapshot_match仅在通过后为True。新源码和十九脚本编译回执已同步，未原生执行。 |

无其余阻断项。零档工具None是既有SDK观察，不意味着HDR分支不存在；源码用 `stored_gainjz is not None` 决定capture/export，因此0不会被误判为False并跳过，且零档capture工具守卫也明确为None。导出只保存hash及 `type_validation_pending=True`，不提前宣告读回通过。

## 已核对的执行守卫

AST确认内嵌initial snapshot与plan逐对象相同，两处内嵌旧八ID列表也与plan相同。继承IDs精确等于前轮owned IDs，prior receipt摘要匹配；前轮八份均Complete100。plan的初始设置快照保留旧阶段jobs字段，不被当成本轮活任务表；本轮Load005后重新要求实际集合为旧八项、状态全部Complete100，再冻结完整 `existing_jobs_snapshot`，以它作后续比较基准。

两个完整颜色条件相对前轮只重指三条case路径，clip、两个素材身份、TC不变；条件彼此仅project/timeline的TimelineGamma键不同。源snapshot与前轮冻结源逐对象相同，含project/timeline各158键、完整clip263键、身份、TC和原六任务列表。源初末source_check不调用设置或grade setter，另核单timeline/轨/item、单层单节点、空LUT、中性和idle。

每档Gamma setter之后Save→Close仅005→Load005→重设三路径，再核完整p/t/clip、身份/TC及图；ApplyGrade和SetRenderSettings后再次核完整条件，工具状态按上一档及目标档检查。1920×1080/30、固定单帧108000、EXR RGBFloat、无audio/alpha；每个输出目录新建，已有脚本/回执/输出不覆盖。

每循环开始和关闭重开后比对旧八项完整任务对象，集合只允许旧ID和本轮owned ID。新增ID非空且排除旧/owned ID，新增后集合只多此项；StartRendering只传单新ID。逐该ID等Complete100和idle才继续，失败/超时保留partial receipt，不删旧任务、不全停、不盲目重跑。finalize再核完整旧表、最终十三ID集合和十三项Complete100，保存/导出005中性副本。

三档完成之后才单独capture/export；仍核完整条件、idle、工具和对应job完成，still标签及目录唯一。需要独立严格核验真实readback的 `0x86000305 → HDR #16 → Global` 身份、精确−1/+1，以及零档可能省略gainjz但由descriptor默认0的情况；字段省略不能写成显式wire零，ParseFromString成功或Tools=None也不能代替类型、分支、存在性/默认值和其他参数白名单核对。

有限finally只在已知003/005且idle时恢复003并比较完整冻结对象；仍rendering时不切项目、不Close或取消，保留同owned job供后续观察。失败/恢复错误单独记载，最终成功还要求completed5且restored。新副本可能保留失败中间状态，不能把返回源解释成自动修复整个005。

## 执行前准入边界（历史）

本次只准上述有界五帧与三组读回，不预判任何配对比值、候选公式或物理EV。项目关闭重开不是全进程/GPU/所有缓存冷启动；三路径仍每次重设，getter/cachemode不能替代文件系统隔离审计。源恢复证明限于被冻结getter/clip/身份/TC/jobs及图守卫，不是所有grade字节或全应用审计。005的palette菜单继续无直接UI见证，原003离散校准不能变成本轮新增校准；必须待实帧和严格DRX证据到位，再作限定的输入输出结论。

## 实际结果终审

已读新增比较器、公开测量摘要/三档候选、`resolve-hdr-srgb-seventh-pass.md`、README第17入口及立项书0.12，并追溯实际receipt、finalize、严格三DRX与独立数值记录。整幅解码依据另一代理的独立手写scanline验证；本子代理没有重解码EXR、原生重跑或重新加载目标descriptor。本子代理核对其公开投影，另从实际48中心通道独立抽算三档五候选的15个最大误差及五组配对全部统计，与公开值差为0。

| 当前证据 | SHA-256 |
|---|---|
| resolve-hdr-srgb-pair-result.json，UTF-8/LF | 6d9b57d39e6e893eb3f298af5e01cc0104350c63f32e0443da5d7be4ec77f918 |
| hdr-srgb-pair-candidates.json | 70fd5f6744151c63e2aef962b2ba05fcae21125e2405fc53befc464b8e45130f |
| 私有 native-srgb-pair-render-results.json | 380e3cb1c811fa8f049863cd35311c4d5065ea9d8a7384a2c8a66d195f8e4f9c |
| 私有 pair-finalize-copy-result.json | c08fba8b2a3355a7b19a668209a6b8b9956da59cbf565adf4231701eca2c2096 |
| 私有 independent-srgb-pair-drx-validation.json | 9a0e8e6385c61e06b59e4bec6cbd81ef2c9553e596a1bd98d5a9f695fbc8ee2a |
| 私有 independent-srgb-pair-numeric-check.json | 5678e4fbd8dd41af7ddf7e5f2f4ef0e3ac47be9ac6f7608aec1311f5faee515d |

公开plan/receipt/strict摘要与实际小文件匹配；candidate的source_sha256是当前公开结果LF文本摘要。三份实际DRX文件摘要与receipt及strict记录一致，各来源grade也与对应计划/状态一致。严格解析器和独立数值脚本的当前源码摘要与其记录相同，没有将旧记录套给改过的数据。

receipt的五状态顺序与计划相同，五个owned ID互不相同且排除旧八ID；五份状态均Complete100、failure=null。initial已有任务快照含八项，与plan旧集合一致；finalize返回saved_exported/neutral/existing_jobs_snapshot_match均true，该结果来自已审最终旧表全对象、十三ID集合及十三状态守卫。restoration返回003、restored=true、source_full_snapshot_match=true、rendering=false。源恢复结论限于冻结的p/t各158键、clip263键、身份/TC/原六任务及中性图守卫，并非本子代理重新调用活宿主或全应用/grade字节审计。

最终比较器SHA-256 `5ef7af07639b2a139d2432af6b940672c65ad4dfc6427501a1d2d5eae5541eaa`，6801字节。检查覆盖三份不同名字、来源/实际DRX文件摘要、semantics值及完整canonical验证；收尾另加restored必须true、旧任务ID集合核plan、旧第六轮receipt摘要核冻结plan的完整性断言。主代理重算后公开JSON摘要未变，没有原生重跑或改测量结果。候选执行器仍为此前已审版本，三档只取本轮实际数据，没有借用旧Rec.709负档。

独立数值记录709项全部pass，绑定表中两个公开JSON、计划、receipt和strict记录；覆盖新五帧/240中心通道、前轮两帧、四组整幅比较、170个候选统计。候选统计最大复算差2.220446049250313e−16。本子代理逐对象比对每帧EXR/RGB摘要和中心值，四组全部公开统计都与独立记录相同。每帧6,220,800通道的逐位交叉核对与48中心通道的公式误差分开，没有以少量采样替代整幅一致。

四组整幅比较均逐位相同：零档与本轮无HDR中性、最后Rec.709中性与起始sRGB中性、相对第六轮sRGB中性、相对第六轮sRGB+1。像素摘要与EXR文件摘要分别保存；本轮相同像素没有被推广为任意元数据相同。新−1确为独立新帧，而非候选算出的伪观测。

严格三DRX均按既有39个descriptor/401消息定义检查，两Body严格错误为0，动态解析完整消耗且初始化通过；没有仅靠ParseFromString成功认定消息类型。非零两个档位有唯一Global gainjz float32精确−1/+1，原始与canonical Parameter、HDR存在性/默认及节点保持来源。零档源Body0显式float0，读回Body0省略唯一gainjz叶：86/284变为85/279，#16分支仍1，Global结构及饱和度1保持；descriptor字段2为float、has_presence=false、默认0。只有这一个删除被列为allowed normalization，其他五处叶变化均为lastmodtime。完整VersionBody清除时间戳后canonical同源，但零档原始HDR Parameter字节确实不同。没有将字段省略说成显式wire0，也没有将工具None或像素相同说成无HDR分支。

五候选零档误差最高1.1102230246251565e−16只是数值往返；非零仍不匹配。BT.709候选−1/+1最大误差分别0.01977496819266441、0.03245493024587631。36个共同正值通道的BT.709正负档比值为4.322951536729126至15.280799387983336，离4最大11.280799387983336，但对应common-reference绝对差也明确为0.07731003931107061；sRGB候选比值5.199147162382761至20.694772875987073。报告明确近黑小分母敏感、比值是指定解码模型下的有限样本算术，未换算成物理EV或认定JzAzBz内部算法，也未由配置标签或字段名确定实际域。

README/立项书0.12的32张总数为前轮累计27加本轮5，入口和主报告对应当前结果。旧003离散UI校准与本轮005存储值实验分开，005未新增控件显示或palette菜单见证；源码顺序是Gamma设置→保存关闭重开→路径/完整条件核对→ApplyGrade→渲染，不把它写成grade应用后又经历关闭重开的另一实验。

当前无新增must-fix。此轮验收是有限条件下的三档读回和画面关系；完整UI换算、实际转换位置、全部缓存持久化、物理线性EV、HDR/Log/RAW素材、负值/alpha及真实视频仍未验收。阶段1A继续，不能据此宣称完整曝光算法复现或固定OpenCut产品公式。

## 当前公开接口缺口增量审查

只读 `resolve-hdr-api-gap.md`、`resolve-hdr-api-gap-result.json`、四份所列原始查询回执、已执行的窗口查询源码、本机SDK声明，以及README第18入口/立项书0.12末段。没有调用SDK、操作窗口或扩大接口扫描。**无新增must-fix。** 公开摘要SHA-256 `e8aa69fdef72c60dee3c3b554fbd10fd45a8000916d33fa3b20248952ad032e0`；四份raw_receipt_sha256逐项匹配实际文件，SDK声明摘要 `b91b53b86a946e1902789ea898eedf00cb7dd6107aba6f1276ca77fe508816ea`也匹配本机所读文件。

实际tools/list确有14项，名称/顺序与公开列表相同；status返回running=true/version21.1.1，未把这个短版本当作完整构建号。Graph的11个方法与当前完整类声明及SDK文件一致；GetToolsInNode的工具名称不等于HDR菜单Color Space/Gamma选中项。主API查询pattern命中的项目/时间线Gamma、HDR监看/母版、GammaTag不能替代菜单getter；ui_api的SetPaletteColor是widget配色方法，不能因名称相似就认定是HDR palette。

UIManager声明是按ID匹配窗口，默认无参数调用实际返回dict，长度0。原始结果与公开投影一致：003活动、idle、ProjectSettings与任务列表前后相等、window_mutation_calls=0。对应 `inspect-registered-script-windows.py` SHA-256 `b6016775c241f2a1d8f9dca9772db3e0e28011dc917053f740d13c5a26f5195c`；源码仅做版本/测试库/003/idle守卫、读取设置/任务、Fusion.UIManager.FindWindows及前后比较，没有窗口事件或setter。本子代理核的是既有执行证据，没有重新枚举活窗口。

报告正确限定“当前安装的已公开查询接口未找到直接getter”；零窗口不证明所有native窗口不可访问、所有SDK/未公开接口不存在或全应用状态不变，也未取得005菜单。原003「使用时间线」见证没有被自动迁移到005，未知DRX int字段没有被当作菜单枚举。README/立项书新增链接继续保留32帧及公式未知，只要求补菜单见证；该解释缺口不撤销已有受控帧或将查询能力升级为任意UI自动控制。
