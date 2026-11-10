# Resolve 21.1.1 安装后独立审查

审查日期：2026-10-13（Asia/Shanghai）。安装及运行回执发生于 12 日晚。本文件是执行后审查；[安装前审查](resolve-21-1-install-review.md)保留当时 pending-uac 的历史状态。

**结论：本次已读证据支持官方 MSI 完成、新版基本启动、原生 MCP 本地调用及指定测试工程读取；无新增已证实必须修正项。当前聊天工具加载、原生 HDR 曝光和测量导出仍未验收。**

## 核对结果

仅通过文件读取检查了私有安装回执、三轮 MCP 摘要/响应、最新客户端源码、配置备份/差异记录、[脱敏结果](../experiments/resolve-upgrade-result.json)和立项书 0.6。没有运行任何待审 EXE/DLL、SDK 或安装器，没有修改配置/注册表或下载，也没有重新做大范围哈希/PE 分析；仅新增本报告。

安装原始 result 与脱敏 installation 对象一致：installed=true、MSI exit=0、restart_required=false，23:31 完成。它证明包级安装结果，不替代回滚或各个自定义动作验收。

原生探测 responses 中确有 initialize 和 tools/list，返回 14 个工具；只证明工具清单与本轮实际调用，不表示全部 14 个工具均已运行测试。

| 回执 | 工程读取结果 | 可支持的结论 |
|---|---|---|
| first-native-mcp-runtime | 工具内容 JSON 含 GetCurrentProjectLibrary 的调用错误 | 启动/状态成功不能代替脚本成功 |
| second-native-mcp-runtime | library_matches=true，project_matches=false | 已连接目标库，尚未读到目标工程 |
| 最新 native-mcp-runtime | library/project 均匹配，loaded_by_probe=true | 在前置守卫下载入指定测试工程并完成读取 |

最新结果独立与脱敏 project_read 对象比较一致：版本 21.1.1.10、PATCHES_1080P30、1920×1080 / 30fps、1 条时间线、1 个视频轨道、1 个测试片段。不能引用前两轮来补出第三轮的成功。

最新客户端和 responses 的 SHA-256 与脱敏结果精确匹配。源码已改用 GetCurrentDatabase，并检查 JSON-RPC error、isError 和工具文本 JSON 内的 error。载入工程前要求当前 Disk 库为指定测试库；其他工程只有默认未命名且没有时间线、媒体和子文件夹时才允许切离。源码没有调用 unsafe 工具、改变调色/颜色管理或测量导出。LoadProject 本身会改变当前工程选择，不能把整段调用描述成完全无状态变化。

## 登记与基线边界

只读核对了配置备份摘要、CLI 差异记录和当前空参数项：CLI 曾省略 node_repl.args，现已恢复为空数组。完整 TOML 解析等价依据主代理已保存的核对回执，本审查未重新进行完整语义解析；原始文本差异不能直接当作配置值变更。没有打印、复制或提交敏感配置值。

当前可见工具目录没有 davinci_resolve 条目。本地直连成功与 CLI 登记不等于当前聊天已热加载；重启后的新聊天工具可用性仍需验证。

主程序/MCP 的包一致性、激活后签名状态及旧研究副本摘要沿用根记录，本审查未重复大文件校验。新 OCIO 2.5 与旧 2.4 分开：旧 RVA、首选 VA、函数体和数值解释不能直接移用。下一轮须重新固定 21.1.1 环境及颜色管理。

激活助手已执行并在后续观察中退出，但没有捕获其 GUI 退出码或审计完整副作用；软件启动不能证明其安全或正式许可有效。实时防护开启也不补足该证明。

## 未通过项目

回滚仍未实测；当前聊天 MCP 加载、激活程序完整行为、颜色管理协议、原生 HDR Exposure 直接控制与旁路/参数帧对照均未通过，测量导出仍为 0。立项书 0.6 已保留这些边界，阶段 1A 不据本轮宣布完成。

