# 原生 HDR Global：参数载体与两个 UI 显示点

2026-10-13（Asia/Shanghai）。本子任务只读主实验导出的 DRX，复用已有 descriptor 做严格结构解析；没有运行 SDK、Resolve 或目标二进制，没有改写 grade 或扩大二进制扫描。UI 来源由主实验关联：用户截图显示 Global Exposure **1.00**、Sat 1.00、X/Y 0.00；随后用户直接确认同一 Global Exposure 已改回显示 **0.00**。本子任务未独立读取截图，不把 UI 显示精度当作内部浮点精度。

**结果：** 两份原生 HDR 样本都在 `markstore → mark.params` 的 key **`0x86000305`** 中实际出现 HDR value **#16**，zone 为 **Global**。显示 1.00 时 `gainjz` 为 **1.003199815750122**；显示 0.00 时仍显式存有 **0.004799820948392153**。返回显示零点没有省略此分支，也没有把该字段写成数值 0。+1→显示零点的已解码 Body 字段值差异只涉及 `gainjz` 与 `lastmodtime`；这些观测不确定映射公式。

## 输入与可追溯证据

| 样本 | 文件/大小 | SHA-256 |
|---|---|---|
| 原有 neutral 参照 | [neutral_retry_1.1.1.drx](E:/projects/逆向工程/capcut+达芬奇/evidence/local/resolve-exposure-20261013/grades/neutral_retry_1.1.1.drx)，18,750 bytes | `388c39fca8def009a6e143d6ca50de115494cc9448c4f61b27504c95fd286fbe` |
| Global 显示 1.00 | [human_global_plus1_1.1.1.drx](E:/projects/逆向工程/capcut+达芬奇/evidence/local/resolve-hdr-20261013/grades/human_global_plus1_1.1.1.drx)，19,780 bytes | `7a661fbaed96a5408e649ac83737aa3ce7ffcf0a179d18ce0163ae5fc989c598` |
| Global 返回显示 0.00 | [human_global_zero_1.1.2.drx](E:/projects/逆向工程/capcut+达芬奇/evidence/local/resolve-hdr-20261013/grades/human_global_zero_1.1.2.drx)，18,832 bytes | `ed0a4ba94e0f91786569f85edb098e66fdef6724baccc1f2aba28f02dee90255` |

Descriptor 来源是已冻结的 Resolve.exe 副本，SHA-256 `1a109e719f2d5e20167ecd9e0f1a37407cf62702fcea366e5e7f6dbbdb826f83`。沿用此前提取的 39 个 `FileDescriptorProto`、401 个 message 定义，依赖全部闭合。本次复核文件 SHA 及各 descriptor 的序列化 SHA，仅从已有记录偏移读取，没有扫描新区域。[原始 descriptor 记录](E:/projects/逆向工程/capcut+达芬奇/evidence/local/resolve-exposure-20261013/analysis/resolve-native-grade-schema-scan.json)。

完整 neutral/HDR 字段树、每字段 wire/offset/type、参数 key 比较和检查结果保留在私有文件：[+1 分析 JSON](E:/projects/逆向工程/capcut+达芬奇/evidence/local/resolve-hdr-20261013/analysis/human-global-plus1-descriptor-match.json)、[显示零点与 +1 增量 JSON](E:/projects/逆向工程/capcut+达芬奇/evidence/local/resolve-hdr-20261013/analysis/human-global-zero-descriptor-match.json)。

## 严格结构检查

DRX 的两个 hex Body 都验证了 `0x81` 前缀和 Zstandard frame magic，再在内存中解压；neutral 解压结果亦与已有 `.bin` 哈希重新核对。Body 编号按文本出现顺序，不据此赋予 node layer 身份。以 `ProtoVersion.VersionBody` 递归检查 field number、wire type、nested 定义、required、unknown、oneof 与未消费字节，并独立检查动态 protobuf 消费长度及初始化状态。[检查明细与全字段树](E:/projects/逆向工程/capcut+达芬奇/evidence/local/resolve-hdr-20261013/analysis/human-global-zero-descriptor-match.json)。

| 样本 | Body0 解压 bytes / 已解释字段 / nested messages | Body1 同项 | HasCorrection（文本顺序） |
|---|---|---|---|
| neutral | 203 / 60 / 16 | 142 / 35 / 9 | false / false |
| 显示 1.00 | 284 / 86 / 29 | 142 / 35 / 9 | true / false |
| 显示 0.00 | 284 / 86 / 29 | 142 / 35 / 9 | true / false |

以上各 Body 的 unknown、wire/type 错误、required 缺失、oneof 多成员冲突及未消费字节均为 **0**，动态解析也通过。VersionBody 是 proto3，不能用 required=0 单独证明类型唯一；此处建立完整结构对应，未证明运行时反序列化入口。两份 HDR 样本均保留原节点身份和数量，没有新增节点。[+1 检查结果](E:/projects/逆向工程/capcut+达芬奇/evidence/local/resolve-hdr-20261013/analysis/human-global-plus1-descriptor-match.json)、[零点检查结果](E:/projects/逆向工程/capcut+达芬奇/evidence/local/resolve-hdr-20261013/analysis/human-global-zero-descriptor-match.json)。

## 实际 HDR 参数路径与值

观察到的容器是 `VersionBody.graph[0].nodes[0].markstore[0].marktimelines[0].marks[0].mark[0].params[1]`；该 `Parameter.key` 为 **2248147717 / `0x86000305`**。它的 `value` 实际选择 `ParamValueType.hdrgradeablekeyframeableparams_field (#16)`，连接 `HDRGradeableKeyframeableParamsList.gradeablekeyframeableparams[0]`。这条是样本实际存在的路径，区别于 schema 允许的 `Node.nodeparams` 路径。[实际 branch、key 和字段树](E:/projects/逆向工程/capcut+达芬奇/evidence/local/resolve-hdr-20261013/analysis/human-global-plus1-descriptor-match.json)。

| 字段 | 显示 1.00 的 wire 值 | 显示 0.00 的 wire 值 | 证据边界 |
|---|---|---|---|
| `zonename` #1 | `Global` | `Global` | 显式 string |
| `gainjz` #2 | `1.003199815750122` | `0.004799820948392153` | 显式 float32；little-endian payload 分别 `da68803f` / `d1479d3b` |
| `saturation` #7 | `1.0` | `1.0` | 显式 float32，保持非零；+1 截图同时报告 Sat 1.00 |
| `offsetaz` #3、`offsetbz` #4 | 未出现 | 未出现 | 不赋予 UI X/Y 映射 |
| `temperature` #5、`tint` #6 | 未出现 | 未出现 | 不推断 UI 数值或应用默认值 |

未出现的 scalar 在本次 proto3 descriptor reader 中有默认读取值 0；这不同于实际写入的 wire 值，也不同于 Resolve 的应用默认状态。原 neutral 没有任何 HDR #16 值，因此不能把其缺省解释为 Global `gainjz=0` 或 `gainjz=1`。返回显示零点的 `gainjz` 则明确在 wire 中，且非零。[scalar presence/default 明细](E:/projects/逆向工程/capcut+达芬奇/evidence/local/resolve-hdr-20261013/analysis/human-global-zero-descriptor-match.json)。

两个 HDR 样本的 Body0 各有 **1 个 #16**，没有实际 #17/#18；Body1 的 #16/#17/#18 均为 0。只观察到一个 Global item，没有观察到其他 zone 名称；不由此推断整个 palette 的其他 zone 不存在或它们的默认定义。[分支计数和观察到的列表](E:/projects/逆向工程/capcut+达芬奇/evidence/local/resolve-hdr-20261013/analysis/human-global-zero-descriptor-match.json)。

## 其他参数与 +1→显示零点的增量

两份 HDR 样本相对旧 neutral 都新增以下 key；按类型容器路径与 key 配对，未将 repeated params 的列表位置当作身份。

| 所在容器 | key | 显式值 | 语义状态 |
|---|---|---|---|
| `markstore...mark.params` | `0x860000bb` | `int_field=-1` | 配套参数，含义未确认 |
| `markstore...mark.params` | `0x86000305` | 上述 Global HDR #16 | 已建立结构与两个 UI 显示点关联 |
| `markstore...mark.params` | `0x86000309` | `int_field=2` | 配套参数，含义未确认 |
| 原 graph node 的 `nodeparams.params` | `0xc00000db` | `bool_field=true` | 布尔状态含义未确认，不命名为 node HDR mode |

原 graph node 与 ptzrnode 的 `0xc0000001/int_field=1` 保留。+1→显示零点没有增删 key、节点或叶字段；Body0 仅改变 Global `gainjz` 和 graph/node/ptzrnode 的 `lastmodtime`，Body1 仅改变 graph/ptzrnode 的 `lastmodtime`。`saturation=1.0`、上述配套 int/bool 值及其他解码字段保持。`HasCorrection=true` 的保持是文件结构事实，不足以判定返回显示零点后的渲染像素是否中性。[逐字段与按 key 的增量](E:/projects/逆向工程/capcut+达芬奇/evidence/local/resolve-hdr-20261013/analysis/human-global-zero-descriptor-match.json)。

## 已知与仍待验证

**已知：** 本机原生 HDR 快照实际承载 `0x86000305 → #16 → Global`；两个 UI 显示点对应上述明确非零 float32。Global 返回显示 0.00 后仍保存显式 HDR 值，其余已解码参数保持。

**未知：** `gainjz` 与 UI 的完整输入/显示转换、实际计算使用的单位、默认中性值、配套 key 的含义、色彩空间与版本对映射的影响以及最终像素作用。两数分别可在两位小数显示为 1.00/0.00，故显示舍入是待核验解释；没有据此确认直接相等、线性、乘法或 `pow` 公式。此处是结构匹配及两个有限精度 UI 观测点，算法归属仍需实际 UI handler 与渲染证据连接。

## 原生候选读回（增量）

2026-10-13，后续阶段。在 `EXPO_003_HDR_MAPPING` 的隔离实验对象上，主实验将只更改 stored Global `gainjz` 为 −1/0/+1 的候选 DRX 经官方 `Graph.ApplyGradeFromDRX` 应用，再原生 GrabStill/Export。候选文件事前已独立检查：除 Global float32 payload 外，另一 Body 和外层原字节保持；档名当时不作为 UI EV 证据。[候选改动范围验证](E:/projects/逆向工程/capcut+达芬奇/evidence/local/resolve-hdr-20261013/analysis/stored-global-calibration-strict-validation.json)。本增量复核原生导出 readback，三档的用户 UI 见证现在均已到，区别于前文两份手动样本的历史状态。

| stored 候选输入 | 用户确认的 Global UI 显示 | 原生 readback 的实际表示 | 独立验证 |
|---|---|---|---|
| `gainjz=-1.0` | `−1.00`，并有完整 panel 截图 | 唯一 `0x86000305 → #16 → Global`；显式 `gainjz=-1.0`，float32 payload `000080bf`；Body0 284 bytes / 86 fields / 29 nested | [−1 readback JSON](E:/projects/逆向工程/capcut+达芬奇/evidence/local/resolve-hdr-20261013/analysis/stored-global-minus1-readback-validation.json)、[−1 UI 见证](E:/projects/逆向工程/capcut+达芬奇/evidence/local/resolve-hdr-20261013/analysis/ui-witness-stored-minus1.json) |
| 显式 `gainjz=0.0` | `0.00` | 同一 key/#16/Global 保留；原生省略 `gainjz` #2 的 tag+4-byte 零值，共 5 bytes；Body0 279 bytes / 85 fields / 29 nested。此字段 **未显式写 wire 0**，proto3 读取缺省为 `0.0` | [zero readback JSON](E:/projects/逆向工程/capcut+达芬奇/evidence/local/resolve-hdr-20261013/analysis/stored-global-zero-readback-validation.json)、[zero UI 见证](E:/projects/逆向工程/capcut+达芬奇/evidence/local/resolve-hdr-20261013/analysis/ui-witness-stored-zero.json) |
| `gainjz=1.0` | `1.00` | 唯一同一 key/#16/Global；显式 `gainjz=1.0`，float32 payload `0000803f`；Body0 284 bytes / 86 fields / 29 nested | [+1 readback JSON](E:/projects/逆向工程/capcut+达芬奇/evidence/local/resolve-hdr-20261013/analysis/stored-global-plus1-readback-validation.json)、[+1 UI 见证](E:/projects/逆向工程/capcut+达芬奇/evidence/local/resolve-hdr-20261013/analysis/ui-witness-stored-plus1.json) |

三档 readback 的两个 Body 都通过既有完整递归及动态 protobuf 检查，unknown、wire/type 错误、required 缺失、oneof 冲突和残留均为 0；Body1 均为 142 bytes / 35 fields / 9 nested。−1/+1 的全部 7 个 Parameter 消息与输入的原始序列化字节相同，HDR scalar 的显式/缺省状态也保持。zero 的 Global Parameter 原始字节因零值省略而变化，但所有 Parameter 的动态 protobuf canonical serialization 均与输入等价；其余 HDR scalar presence/default、参数 key 和节点身份保持。三档在该零值规范化以外的解码变化均仅有 5 处 `lastmodtime`，没有新增参数或其他参数值变化。[−1 明细](E:/projects/逆向工程/capcut+达芬奇/evidence/local/resolve-hdr-20261013/analysis/stored-global-minus1-readback-validation.json)、[zero 明细](E:/projects/逆向工程/capcut+达芬奇/evidence/local/resolve-hdr-20261013/analysis/stored-global-zero-readback-validation.json)、[+1 明细](E:/projects/逆向工程/capcut+达芬奇/evidence/local/resolve-hdr-20261013/analysis/stored-global-plus1-readback-validation.json)。

原生保存亦更新了外层 still/version/thumbnail 的 DbId、CreateTime、压缩 Body 与缩略图缓冲区；没有新增或删除已检视的外层 XML leaf。整份 DRX 的大小和哈希变化分别记录，不能据此否定上述参数状态保持，也不把缩略图当作正式像素测量。readback SHA-256：−1 为 `12d8c54b1b29a04b2fd52c083e88c768c463604760ec44d3700bbbf17e38ea4f`，zero 为 `1caf0969a80381985d2f30fe1bddecae3fe17556f93272d4448241a89feaf8b7`，+1 为 `8faecee1ab3e75868193c3db115a7a1b85567088665c4a149564ec9d191fd082`。[外层 inventory 与 Body 状态分别记录](E:/projects/逆向工程/capcut+达芬奇/evidence/local/resolve-hdr-20261013/analysis/stored-global-plus1-readback-validation.json)。

**补齐的当前上下文。** 用户对 HDR palette 两个子菜单直接确认：Color Space 和 Gamma 都勾选 **“使用时间线 / Use Timeline”**；该菜单见证独立于 ProjectSettings。[菜单见证](E:/projects/逆向工程/capcut+达芬奇/evidence/local/resolve-hdr-20261013/analysis/palette-context-user-witness.json)。stored −1 的完整 panel 截图显示 Global Sat `1.00`、X/Y `0.00`、**黑场偏移 `0.000`**；此子任务已只读查看该截图。[原始 panel 截图](E:/projects/逆向工程/capcut+达芬奇/evidence/local/resolve-hdr-20261013/runtime/user-global-exp-stored-minus1-context.png)。

官方 SDK 当前 context 独立报告 Resolve `21.1.1.10`、工程 `EXPO_003_HDR_MAPPING`、时间线 `PATCHES_1080P30`、当前 timecode `01:00:00:00`；ProjectSettings 为 `colorScienceMode=davinciYRGB`、Input=`Rec.709 Gamma 2.4`、Timeline/Output=`Rec.709 (Scene)`，各独立 Gamma 字段为空，`separateColorSpaceAndGamma=0`，output tone/gamut mapping=`None`，`useColorSpaceAwareGradingTools=0`。以上保留原始项目项，不把空 Gamma 解释成 linear，也不由项目项推导 palette 菜单选择。[原生 SDK context receipt](E:/projects/逆向工程/capcut+达芬奇/evidence/local/resolve-hdr-20261013/runtime/capture-context-result.json)。

**本节封存状态：** 三档原生应用/保存读回及 `−1.00/0.00/1.00` UI 见证均已具备，palette Color Space/Gamma 见证已补，黑场偏移显示为 0.000；**正式 HDR EXR 像素渲染仍为 0 帧**。这些是离散校准点、序列化规范化和当前上下文证据，尚未确立完整 UI 显示公式、曝光像素公式、负值/高光/色度行为或跨色彩空间泛化。后续旁路/−1/0/+1 单帧真实像素实验应另行记录，不把本节的结构与 UI 验证计作渲染通过。
