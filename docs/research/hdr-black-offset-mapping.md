# HDR Black Offset：一个原生UI校准点

2026-10-13，Resolve 21.1.1.10，005实验副本。**用户把「黑场偏移」从显示0改为0.010后，原生DRX新增一个浮点Parameter `0x86000303`；已有Global曝光保持精确1.0。** 这是一个控件与载体的受控关联点，没有据此建立任意数值换算或曝光像素公式。

## 观察及保存

自动保存／导出中性检查点，应用已验证的精确+1曝光grade并捕获原生基线。用户先确认原显示为0，再明确回复「已改为0.010」。自动捕获修改后DRX；同期完整项目／时间线设置、素材、任务和位置快照与基线一致，原13任务均完成，本次校准没有渲染。[原始人工见证](../../evidence/local/resolve-hdr-black-offset-20261013/analysis/black-offset-user-witness.json)、[原生捕获回执](../../evidence/local/resolve-hdr-black-offset-20261013/runtime/capture-after-result.json)。

| 对象 | 直接观察 |
|---|---|
| UI黑场偏移原值／新值 | 用户报告0／0.010 |
| 新Parameter key | `2248147715`，即 `0x86000303` |
| 载体路径 | `VersionBody.graph.nodes.markstore.marktimelines.marks.mark.params` |
| 数值分支 | `Parameter.value → ParamValueType.float_field`，字段#1、protobuf float、wire5 |
| 实际存储值 | `0.009999999776482582`，float32小端字节 `0ad7233c` |
| 新参数原始长度 | 13字节 |
| 修改前 | 此Parameter key不存在；不能将“缺少整个Parameter”直接等同于该应用所有状态的默认规则 |

该数值恰为float32对0.01的表示，仅说明此处观察到的点吻合；不能推断负值、大值或全部UI范围都采用恒等换算。序列化名称使用generic float分支，没有因为字段名而推导像素算法。[独立严格差分](../../evidence/local/resolve-hdr-black-offset-20261013/analysis/independent-black-offset-delta.json)。

## 严格验证

复用已验证的39个descriptor文件／401个消息定义，重验来源二进制和descriptor哈希。前后两个Body的unknown、wire／解析错误、required缺失、oneof冲突、未消耗字节均为0，动态protobuf完整消耗并通过初始化检查。原有7个Parameter按容器与key对齐后，原始和canonical字节全部相同；新增1项、删除0项、改变既有项0项。唯一Global `gainjz` 仍为精确1.0，节点身份不变。

新参数插入列表使后续`params[index]`位置移动，所以未经key对齐的叶子树会看见多处增删。验证另外从修改后Body移除**唯一新增的 `0x86000303`**，双方清除时间戳后，完整VersionBody canonical字节一致；并没有把位置变化误判为多个参数修改。外层XML图像和元数据变化另行记录，未声称整份DRX字节相同。

| 私有证据 | SHA-256 |
|---|---|
| 原生基线DRX | `5dbcf1425498ef1ef2d5b2d00b919976ba176c3b14db0b4dbf55f6b48a5b7907` |
| 原生修改后DRX | `89767932b27e1843852a69dd2bc2168c2a4cc734cfbfbedbe9b87d1b937394cf` |
| 独立差分JSON | `15405ff0510ed1187af2959becc164d91e9951ebbed9995bf0a1e1cde211700c` |

随后重新应用冻结的无HDR中性grade，并保存、抓取及导出。恢复DRX与冻结中性源相比，所有Parameter字节、节点身份和去时间戳完整Body一致；HDR #16／#17／#18均不存在，新增 `0x86000303` 也不存在。[独立恢复验证](../../evidence/local/resolve-hdr-black-offset-20261013/analysis/independent-black-offset-restored.json)，SHA-256 `18caeeec359d567a77f4d504f090636055cf9d664ca7fbfea716808dd0ffd379`。这是grade恢复证据，不替代全应用状态或输出像素审计。

官方手册说明黑位锚定和非线性阴影压缩，为调查该控制变量提供依据。[本机21.1手册p3166、3169–3170](<G:/Davinci Studio/Documents/DaVinci Resolve.pdf>)。本次没有新增像素样本，也没有证明它是此前曝光残差的原因；完整HDR曝光公式仍未确定。后续可用这两份真实原生grade做固定上下文的前／后／重复／中性恢复对照，无需先猜测或修改新的私有字段。

后续四帧重放已经另行执行，见[像素对照记录](hdr-black-offset-pixel-response.md)。上文的“没有新增像素样本”限定于UI—字段校准步骤；四帧实验有独立计划、任务和浮点输出。
