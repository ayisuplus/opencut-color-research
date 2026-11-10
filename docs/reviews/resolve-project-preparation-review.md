# Resolve 研究工程准备独立审查

日期：2026-10-12。审查者：独立子代理。

**结论：本轮研究工程创建、导入与准备结果可由现存证据支持；未发现新的必须修复项。此前提出的默认工程内容检查、工程 UUID、时间线与页面回读已纳入实际执行版本。颜色管理及原生 HDR 曝光仍未验收，本轮停在等待用户颜色管理截图。**

## 范围和方法

只读核对实际执行脚本、stdout/stderr、解析后的私有快照、[公开结果](../experiments/resolve-project-preparation-result.json)、当前候选脚本、已哈希输入，以及预期库内的 Project.db 位置与文件头。本审查没有运行 SDK、启动或退出 Resolve，也没有创建、保存、导出、删除项目或改动已有库；仅新增本审查文件。

私有完整快照包含元数据，本报告不复制其内容、工程 UUID 或其他用户资料。未新增基准、框架或动态实验。

## 执行证据

- 实际执行源 `runtime/prepare-resolve-exposure.executed.lua` 的 SHA-256 为 `2bf25f4b64ba07eb899077d55c59f218f6ea071d2261167875592a5aa11e2b9d`，与公开记录一致。
- stdout 的 SHA-256 为 `c77115f0b9d44ea7e49612ecc5f6f5313e03d88469d77f766f024adc3e279fd9`；四个阶段标记按 before_create → created_and_saved → single_patch_image_imported → preparation_finished 顺序出现。
- stdout 恰有一条 record_json，按 UTF-8/JSON 成功解析，与 `runtime/prepared-project.json` 完全一致。快照 SHA-256 为 `f168f2f5bb28f5ae8e07ff929d7af415d05cadc92220b5d9c60c12040d015336`。
- stderr 为零字节，摘要与公开记录相符。CLI 退出码 0 依据根代理执行回执及公开摘要；本审查没有重复执行以获取新的退出码。

当前 [候选脚本](../../experiments/prepare-resolve-exposure.lua) SHA-256 为 `a1d251db21d60786b300c1bf855ea8368f7d88ca743d071bb070ff71618a2db7`。逐行比较确认，它相对执行版本只改变 scope 文案及 `native_frames_rendered` → `measurement_frames_exported` 两处快照标签，SDK 调用行为文本没有改变。不能将当前候选哈希当作已经执行的源哈希。

## 守卫与操作顺序

实际执行版本首先确认版本、当前 Disk 库名、当前项目文件夹无工程及无子文件夹；拒绝已命名工程，默认未命名工程存在时检查其没有时间线、根媒体池素材及子文件夹。脚本亦允许无当前工程，不能据前置通过就声称每次均取得了默认工程对象。

CreateProject 后检查新工程名称、非空字符串 UUID，并在主要变更与 SaveProject 前复核当前库和当前工程 UUID。重复执行将受到已有工程/命名工程前置检查阻止；失败后不删除项目、加载既有工程或盲目重跑。

1920×1080、30fps 设置在导入前完成，每个 setter 返回值及数值回读均检查。导入要求仅一个返回素材且源路径一致。创建时间线后检查总时间线数为 1、当前时间线 UUID、三个实际设置及单个 video item；Color 页、首帧时间码也有返回值与回读检查。JSON 在本次真实载荷上成功解析，未发现序列化失败。

脚本没有换库、加载既有工程、设置 grade、添加/启动测量渲染任务或 Quit 调用。初次与最终保存均由当前项目身份守卫约束。上述是现存脚本与本次执行记录的核查，不是跨 UI 并发事务或所有日常项目字节完整性的证明。

## 项目及文件结果

公开摘要中的库名、工程名、保存结果、时间线设置、素材元数据、颜色设置和编码器查询，均逐项与私有快照一致：

| 项目 | 支持的结果 |
|---|---|
| 库 / 工程 | OC_COLOR_001_TEST / EXPO_001_HDR_GLOBAL |
| 时间线 | PATCHES_1080P30；1920×1080；30fps |
| 素材与图 | 1 个 timeline item；GetNumNodes 返回 1 |
| 页面 / 时间码 | Color 页；起始时间码 01:00:00:00 |
| 帧位置 | API 返回 start=108000、end=108187；不自行推定末帧包含规则 |
| 文件保存 | SDK 保存断言通过，预期研究库内数据库文件存在 |

已确认 `evidence/local/resolve-exposure-20261012/project-library/Resolve Projects/Users/guest/Projects/EXPO_001_HDR_GLOBAL/Project.db` 为预期研究目录中的文件，大小 2912256 字节，前 16 字节为 SQLite 文件头。只读了文件头，没有打开数据库会话、解析私有行数据或重开项目；文件存在与 SDK 保存结果不替代完整的持久化恢复验收。

输入完整 SHA-256 独立重算为 `2daa68135e4ac8c0585fb33630ce5d69a735640799b82a8173caafbfc8d9f09f`，与实际执行记录及公开摘要一致；素材源路径与该输入相同。库由用户在 GUI 创建并选中，创建者依据用户操作回执与既有只读连接记录，本审查未重演 GUI 操作。

## 证据限度与停止位置

素材元数据报告 16-bit PNG、1920×1080、无 alpha、Input Gamma 为 Gamma 2.4；这不证明解码器保留了全部 16-bit 数值，也不能按自有 sRGB 参考直接推断曝光误差。静态图片素材 FPS=24 与时间线独立回读 30fps 并不矛盾，此轮不是视频或性能实验。

项目颜色属性只是当前快照，尚未冻结其实际有效处理域及 HDR 调色盘解释。单个 node 只证明图查询计数，不证明原生曝光中性值、旁路行为或 grade 内容。EXR RGBFloat 是可查询的编码器选项，不是已产生并验证 float 导出帧。

原始日志中的 `native_frames_rendered=0` 是脚本写入的旧标签，应按本轮没有主动测量导出来理解；它不能证明打开 Color 页时软件没有预览处理，也不能证明宿主内部未调用候选 renderer。公开摘要与候选脚本已将此边界写成 `measurement_frames_exported=0`，保留原始日志而不改写既有证据是正确处理。

本轮可以确认研究工程已经准备好供后续核查。待用户颜色管理截图确认具体设置与控件语义，再进行受控原生旁路/0/−1/+1 对照及实际高位深导出验证；当前不宣布阶段 1A 通过，也不把准备成功视作已复现达芬奇曝光。
