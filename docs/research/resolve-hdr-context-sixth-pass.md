# HDR 第六轮 A：颜色职责与真实关闭重开的设置探针

2026-10-13，Resolve 21.1.1.10。本文保留阶段 A 的设置探针记录；当时像素实验尚待执行，后续已完成的八帧及五份参数读回见[阶段 B](resolve-hdr-context-sixth-pass-b.md)。

**结果：** 新副本 EXPO_005_HDR_CONTEXT 中，Timeline Gamma 的 Rec.709、sRGB 两个 setter 都实际成功，经过 `SaveProject → CloseProject(005) → LoadProject(005)` 保留。每次重开后重新设置三条 case 路径，再比较完整运行中快照：只有选定的 Timeline Gamma 不同。结束已恢复 003，冻结的两个 158 字段字典、完整 clip 属性、两个身份、timecode 和任务列表全部匹配。

## 官方职责核对

冻结的官方 21.1 手册 p242 把 HDR 作为本身 color-space-aware 的 palette，项目 checkbox 的说明则举例 Qualifier、Curves。它不是 HDR 的总开关。Primaries／Log 的 node HDR Mode 是另一项设置；HDR 本身不需要该 node mode。YRGB 的手动颜色管理也不能自动套用 RCM Input→Timeline→Output 流程。

HDR palette 的 Color Space／Gamma 菜单默认 Timeline，但手册及 SDK 没有给出 palette、node、project/timeline 三者的精确解析优先级和持久化合同。伴随的 DRX int 参数也没有菜单映射证据。[官方上下文来源](hdr-color-context-primary-sources.md)记录原手册页码、重新核验的哈希与 SDK 边界。因此本轮保持 `useColorSpaceAwareGradingTools=0`，不以它代表 HDR 关闭，也不把未知 `0x86000309/int=2` 当作 Gamma 枚举。

## 实际对象与动作

- 最初活动对象为 003 的中性测试工程；先采集完整冻结快照。
- 从第五轮已保存的 004 中性 DRP 导入全新 005；原工程没有调色/设置 setter。
- 005 初始为 YRGB、separate=1、Input/Output Gamma 均 Gamma 2.4，Timeline Gamma=Rec.709，render cache mode=none；同一自制 PNG16 素材与单层单节点空 LUT。
- initial path setter 只允许 gallery/cache/media 三个路径字段变化；完整 clip 与身份、timecode、任务列表不变。
- 每个 Gamma setter 后完整读回，核验返回值、字段差异和非设置状态；通过后才保存、显式关闭 005、重新打开 005，并检查返回句柄属于 005。
- 重开后重新设置 case 路径，核验其 getter，再比较完整运行中条件。
- 没有 grade setter 或 GrabStill，未创建/启动测量渲染任务或导出测量帧。有限 `finally` 无论正常或异常都尝试一次恢复 003，实际记录 failure/restore_error，核验失败不宣称成功。

| 条件 | setter 返回 | setter 的完整差异 | 关闭重开后、路径重设后的完整差异 |
|---|---|---|---|
| Rec.709 | true | p/t/clip 均无变化 | p/t/clip 均无变化，身份/TC/jobs 保持 |
| sRGB | true | p/t 仅 Timeline Gamma：Rec.709→sRGB；clip 不变 | p/t/clip 均无变化，身份/TC/jobs 保持 |

这证明本次字段请求和显式重开的读回结果，尚未证明 HDR 采用相应传递函数。`Timeline.GetSettings()` 在继承设置时返回项目值，这两份相同字典不一定是独立配置层。

缓存位置也不作完整持久化保证：重开后的 getter 仍会出现 `CacheClip`，脚本随后重新设置独立路径并读回。所谓条件保持，指这一步之后的完整运行中快照相同；不能省略重设步骤。原始工程、脚本和完整回执在忽略目录，公开[探针摘要](../experiments/resolve-hdr-context-setting-result.json)只保留预设值、计数及哈希。

## 独立审查与恢复

执行前独立审查要求并确认四个 P2 修正：真实关闭重开；异常时的有限恢复；每个 setter 的身份/TC/jobs 与路径变更白名单；保持已核对的 005 句柄，删除未校验的重赋值。实际回执 ready=true、failure=null、restore_error=null、source_full_snapshot_match=true，最终活动工程 003，中性且无渲染。[审查记录](../reviews/hdr-context-review.md)。

完整快照比较不等于全应用状态、缓存内容或 grade 字节不变的审计；005 的 palette 菜单没有直接 UI 见证。本轮没有新增 HDR 显示点或像素验收。

## 后续八帧已冻结，尚未执行

保持 stored Global +1 的同一来源 grade，拟比较以下顺序：

1. 已关闭重开的 Rec.709，中性参照。
2. Rec.709，应用 +1 grade。
3. 切到 sRGB、保存关闭重开，保留现有 +1。
4. sRGB，再重放同一 +1 grade。
5. 返回 Rec.709、保存关闭重开，保留现有 +1。
6. Rec.709，再重放同一 +1 grade。
7. sRGB，中性参照。
8. 返回 Rec.709，中性恢复。

五个非零状态计划另存原生参数读回。冻结条件来自本次实际关闭重开快照；后续执行器仍需独立审查准入。重复关闭重开、grade 重放及处理历史均是记录的动作，微小差异不能直接归因于某一步。只研究 +1 与无 HDR 中性，不新增 −1/0 的 UI 校准。

这些实验用于检查颜色上下文和 grade 重放的连接，完整曝光公式及 OpenCut 调色规格仍待确认。阶段 1A 继续进行。
