# 原生曝光实验：专用测试库准备

日期：2026-10-12。用户已通过正常界面创建、选中 `OC_COLOR_001_TEST`，指定目录已有实际库与 `EXPO_001_HDR_GLOBAL` 工程数据库。官方 Lua 已在新库创建工程、导入色块、准备 1080p30 时间线并保存。当前停止点变为颜色管理确认和原生 HDR 控件输入；测量帧仍未导出。[实际准备记录](../research/resolve-project-preparation.md)

以下步骤的建库、工程和素材准备已执行；颜色解释与原生控件采样仍待确认。历史第二轮的建库入口限制保留在 [第二轮记录](../research/resolve-exposure-second-pass.md)。

## 正常界面中的准备

1. 在 Resolve 项目管理器中，为实验新建一个**本地项目库**，建议库名 `OC_COLOR_001_TEST`。选择项目内的空目录 `evidence/local/resolve-exposure-20261012/project-library/` 作为专用位置；路径完整写法为 `E:\projects\逆向工程\capcut+达芬奇\evidence\local\resolve-exposure-20261012\project-library`。实际按钮和路径可用性需在本机界面确认。
2. 在该库创建实验工程 `EXPO_001_HDR_GLOBAL`，记录库名、位置、应用运行版本和工程名。创建工程与创建项目库是两件事；SDK 的 CreateProject 只能证明工程创建。
3. 将 [输入生成器](../../experiments/make-exposure-inputs.py) 生成的 `experiments/output/exposure-inputs/opaque-srgb16-patches.png` 用作首个素材。记录 Resolve 实际识别的输入颜色空间、位深与范围；PNG 标签本身不证明应用已正确解释。
4. 先记录 color science、输入/时间线/输出颜色空间与传递函数、tone/gamut mapping、HDR palette 使用的颜色空间以及节点顺序。配置未确认前只作导入检查，暂不判断曝光公式。

目录由 Resolve 创建和管理；工程修改通过官方 SDK 完成，没有手工改写数据库。此步骤未修改全局 PATH 或开启网络脚本访问。

## 第一组画面对照

拟研究 HDR palette 的 Global Exposure，准确控件名称、单位和范围以本机界面为准。保留旁路、原生控件 0、-1、+1 四组设置，重复导出两次 0 档基线，并保存参数记录及对应 DRX；数值“+1”先记为原始控件值，尚不能直接解释成线性 +1 EV。

选用的高位深无损导出格式须在本机确认可用，再检查真实文件头、位深、范围与颜色解释。0.18 灰块在输入中实际为每通道 30235（16-bit），按约定 sRGB 解码约为 0.18000033259998335；若比较工作线性像素，基准应使用该量化后值。白值样本在增加曝光后可能越过 1，因此只看整数输出中的裁切不足以定位裁切发生在哪一步。

完整输入摘要见 [exposure-input-manifest.json](exposure-input-manifest.json)，实验语义与验收范围见 [color-protocol.md](color-protocol.md)。真实行为完成前，阶段 1A 保持进行中，阶段 1B 不据此声称复现原生曝光。
