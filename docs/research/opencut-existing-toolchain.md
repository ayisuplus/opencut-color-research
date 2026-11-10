# OpenCut 当前工具链与离线构建探针

2026-10-13。等待005的HDR菜单见证期间，完成独立的本机工具链检查；不改变阶段1A的公式验收条件，也没有开始实现调色模块。开发基线仍为 `e668010778568641babef2cc40be4703ae6916d6`。

**结果：本机现有Rust可读取新版workspace元数据，但桌面离线check在依赖解析阶段失败：当前配置的tuna索引未找到gpui。** 这不是源码类型检查通过或源码错误的证据。固定工具链、桌面运行与媒体闭环均未验收。

| 项目 | 仓库声明 | 本机实际观察 |
|---|---|---|
| Rust | `.prototools` 1.97.0 | rustc/cargo 1.96.0；使用已安装stable-msvc作兼容性探针 |
| Bun | 1.3.11 | 1.3.14 |
| moon | 2.3.3 | 当前PATH未找到 |
| proto | 桌面README建议 `proto use` | 当前PATH未找到 |
| Node | 本轮未建立精确pin验收 | v24.15.0 |

实际执行 `cargo metadata --offline --locked --no-deps --format-version 1`，退出0：workspace只有 `opencut-desktop` 0.1.0、edition2024，`resolve=null`。它确认manifest结构，不解析全部依赖，不检查Rust源码，也不使被注释的 `crates/*` 成为已启用成员。

随后执行 `cargo +stable-x86_64-pc-windows-msvc check --offline --locked -p opencut-desktop --target-dir <研究case目录>`，退出101：`no matching package named gpui found`，查找的是替换crates-io的tuna索引。保留诊断，没有移除offline重跑，没有修改Cargo源配置或请求安装依赖。这个结果不证明其它索引缓存也没有gpui。

OpenCut源码状态前后均干净，Cargo.lock原始字节哈希保持 `9c512116dc592f1df0da4ca53102d22da7126d932f41e50c7bb78831dc3a9323`。探针输出位于单独忽略目录，没有更改上游源码、锁文件或全局工具版本。

web根目录和apps/web本地node_modules均未见；未执行web build/test或启动服务。PATH检查不是整台机器的安装审计；未跑桌面UI、视频解码、预览、导出或性能测试。Rust1.96下的探针不能替代1.97锁定版本和上游CI验收。

[脱敏结果](../experiments/opencut-existing-toolchain-result.json)记录命令范围、真实退出码、元数据边界与回执哈希。后续先核定精确工具版本和可用依赖源，再做锁定工具链check；媒体/调色接入还需明确颜色约定与实际接口。原有[源码可行性研究](opencut-feasibility.md)的“源码证据”与本页“环境探针”分开保留。
