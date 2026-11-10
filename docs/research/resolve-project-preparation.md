# 原生曝光实验准备：隔离库、工程与素材

日期：2026-10-12。阶段 1A 进行中。本轮从第二轮停止位置继续：用户通过正常界面创建、选中 `OC_COLOR_001_TEST`，随后由官方 Lua API 准备工程。未改变原生 HDR Exposure 参数，测量帧尚未导出。

## 已完成的准备

1. 截图显示新库已选中；Lua `GetCurrentDatabase()` 返回预定 Disk 库，已连接库总数从 1 变为 2。
2. 创建并保存 `EXPO_001_HDR_GLOBAL`。在预期路径 `evidence/local/resolve-exposure-20261012/project-library/Resolve Projects/Users/guest/Projects/EXPO_001_HDR_GLOBAL/Project.db` 观察到实际工程数据库，支持库位置与工程创建的对应。
3. 导入固定 SHA-256 的 `opaque-srgb16-patches.png`，创建单个视频项的 `PATCHES_1080P30` 时间线。项目与时间线均读回 1920×1080、30 fps；节点图有一个节点，首帧时间码为 `01:00:00:00`，打开并读回 Color 页面。
4. SDK 素材元数据报告 PNG、1920×1080、16-bit、Online、无 alpha。源仍图的 FPS 元数据为 24，而时间线读回 30；本轮不是视频帧率或性能验收。
5. 导出格式查询返回 EXR 的 `RGBFloat`、`RGBFloatZIP` 等 codec，PNG/TIFF 有 RGB16。返回列表不证明已经导出有效的高位深或浮点文件。

输入完整摘要仍为 `2daa68135e4ac8c0585fb33630ce5d69a735640799b82a8173caafbfc8d9f09f`。原始截图、完整 SDK 属性、工程 UUID 和运行日志保留在 Git 忽略的实验目录。公开白名单摘要见 [准备结果](../experiments/resolve-project-preparation-result.json)。

## 准备脚本与检查

[一次性准备脚本](../../experiments/prepare-resolve-exposure.lua) 执行前要求当前 Disk 库名匹配、当前文件夹无既有工程或子文件夹，已打开的默认未命名工程没有时间线、媒体或子文件夹。新工程名称及 UUID 必须有效，随后每个修改阶段核查当前库与工程 UUID。脚本不切换数据库、不载入已有工程、不修改 grade、不请求测量渲染，也不退出用户打开的 Resolve。

设置返回值和回读通过后，核对唯一时间线的 UUID、尺寸、帧率、首帧位置以及页面，并保存工程。运行日志有完整的创建、导入和完成标记，CLI 返回 0。宿主可能因进入 Color 页面执行内部预览渲染；本轮没有追踪该调用链。

实际执行源码在私有 `runtime/prepare-resolve-exposure.executed.lua`，SHA-256 为 `2bf25f4b64ba07eb899077d55c59f218f6ea071d2261167875592a5aa11e2b9d`。当前提交候选只澄清两个输出字段：scope 表明没有脚本设置 HDR 或导出测量帧，零帧计数命名为 measurement_frames_exported；没有改变准备行为。实际日志与源码快照保持原样。

此脚本是固定研究目录的一次性工具；工程已存在后会因空文件夹守卫而停止，不能直接重跑来续接实验。后续操作须绑定已创建工程的 UUID，单独核对其当前状态。

SDK 方法与返回语义来自 [本机官方 SDK](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/README.txt:116>)；[属性快照和 setter 检查说明](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/README.txt:666>) 要求检查返回值，并可通过 UI 与前后属性快照确认取值。

## 当前颜色解释未固定

| SDK 项 | 当前读回 |
|---|---|
| colorScienceMode | davinciYRGB |
| colorSpaceInput | Rec.709 Gamma 2.4 |
| colorSpaceTimeline / colorSpaceOutput | Rec.709 (Scene) |
| 素材 Input Color Space / Input Gamma | 项目 / Gamma 2.4 |
| 素材 Data Level | Auto |
| colorSpaceOutputToneMapping / GamutMapping | None / None |
| useColorSpaceAwareGradingTools | 0 |

测试图是按 sRGB 编码生成的，以上默认值不能直接作为该图已经正确进入工作颜色域的证明。尤其在未管理的 YRGB 模式中，Input Gamma 字段不等于已经测得解码时采用了某一传递函数。不能仅凭元数据断定实际线性像素正确或错误。

下一步由用户提供当前工程“项目设置 → 色彩管理”的界面，用实际可选项固定颜色配置，并确认 HDR palette 的颜色域、Global Exposure 控件及初值。随后建立旁路和重复 0 档基线，检查真实导出文件与源代码值/传递函数的关系，再做 −1、+1 档比较。

## 本轮验收边界

隔离库、工程创建、素材导入、时间线和 SDK 查询已经实测。PNG 的 16-bit 属性是 SDK 报告，尚未通过导出像素证明解码精度保留；浮点 codec 是可用性查询，尚未核查实际文件头。没有生成原生曝光 grade、DRX、旁路/0/−1/+1 测量帧；阶段 1A 的行为对照仍未通过。

执行前独立审查提出的默认工程空白、有效 UUID 和时间线/页面回读检查已经落实。结果复核见 [准备独立审查](../reviews/resolve-project-preparation-review.md)。
