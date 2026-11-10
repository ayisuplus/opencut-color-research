# 近黑实验：素材属性联动与重新链接的补充协议

日期：2026-10-14。此补充只改变取得同字节输入的操作方法，主预测 `24298e00…628e61c`、输入冻结 `0f573da3…65a0fc5`、1e−6 门、一次自有 GPU 和至多六帧原生上限保持。执行前时点没有新的正式 EXR，累计仍 54 张；执行后状态见文末附记。[原观测前协议](hdr-near-black-preflight.md)按历史状态保留。

## 已发生的接口结果

从完成 007 归档导入 008，通过源 005 保存／备份和三路径修改的全快照守卫。在 008 的唯一素材上调用 `ReplaceClip` 后，脚本在颜色关键属性门停止，尚未应用 grade、抓取新 still 或渲染，也未到末尾 Save008。失败回执没有返回原先内存中的完整 before；后续不补写这份缺失证据。

实际 after 相对已有 007 目标属性记录，仅六个新文件路径／名称／创建与修改日期的派生项，以及 `Input Gamma: Rec.709 → Gamma 2.4` 不同。帧率、位深、数据范围和输入色彩空间标签相同。此对比来自旧参考与当前读回，不能冒充失败步骤中未返回的 before，也不能把标签直接解释成 HDR 实际运算域。

在完整当前 before 与所有时间线／素材池守卫后，单独尝试官方 `SetClipProperty('Input Gamma','Rec.709')`。该键／值在当前条件下返回 False；完整 after 的属性、已设 metadata、项目／时间线设置、结构、队列、节点 getter 和时间码均与捕获的 before 相同。没有扩大为所有 Gamma 路径都不可写的结论。

## 后续唯一重新链接探针

保存并归档失败的自有 008，加载并核对今日 005 的冻结 getter／对象和 23 个任务。随后从相同完成 007 归档导入 fresh 009；005、007 和原始图文件不接受素材替换。009 仍沿用两个时间线和 `MIXED_1080P30` 名称。

官方 `RelinkClips` 声明更新指定素材的目录位置；它比明确重置 asset 和 metadata 的 `ReplaceClip` 更适合本轮，但声明不保证标签或缓存保持。[本机 API](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/DaVinciResolveScript.pyi:2021>)

将原冻结 PNG 字节复制为旧素材 basename `mixed-permutations-srgb16.png`，放入仅含该文件的 fresh `experiments/output/hdr-near-black-input/relink009` 目录；SHA256 与原冻结 PNG 完全相同，不覆盖旧夹具。新文件路径是操作别名，不能借此修改输入码值、颜色元数据或预测。

导入 009 后，先要求原 `Input Gamma=Rec.709` 和目标素材在所有时间线中仅有一次引用。独立保存完整 before 回执，再执行唯一的 `MediaPool.RelinkClips([target], folder)`，无论 True／False 都返回完整 after，不先 Save 或渲染。必须核返回 True、文件路径正确、所有颜色关键属性及 metadata、UID／范围／时间码／轨道／其他对象／队列符合冻结，文件派生变化逐项解释后才保存 009 和建立六帧计划。

若重新链接仍改变 Gamma 或出现其他不明联动，停止此原生方案并保留，不再盲试属性键或改写预测。任何捕获状态的恢复只按已保存 getter／对象验证，不声称完整应用或不可见参数字节回滚。第一中性仍须原新 PNG 整幅 F32 位门；通过后才进入已固定 ±1 和重放／恢复对照。

## 执行后的附记

009 的 Relink 返回 True，完整实际 before／after 只有目标 File Path 与 Clip Directory 的变化；Rec.709 标签保留，保存后的完整读回再次相同。六帧均完成，第一中性全图 F32 门、固定预测门、两档重放及中性恢复控制均通过。008失败归档保留，009完成归档及005今日快照／23任务核对成功。上述执行前协议与冻结不改写；具体数值和仍未证明的范围见[本轮原生结果](hdr-near-black-native.md)。
