# OpenCut 新版重写：调色功能立项可行性

核查日期：2026-10-12（Asia/Shanghai）。范围是用户指定的 `OpenCut-app/OpenCut` 新版 main，以及该仓库 README 直接指向的官方 `OpenCut-app/opencut-classic`；classic 只作实现参照。没有使用其他组织的同名项目。本文是源码研究与方案提案，没有安装依赖、运行应用、测试编码器、修改功能代码或验证调色画质。

## 结论与证据边界

**可以立项，也可以推进基于新版 main 的本地改造准备。当前不能把它描述为“已有成熟剪辑器，只需插入达芬奇调色插件”。** 锁定快照中新版的 web 编辑器与桌面预览仍是占位；Editor API、第三方插件、Rust core、MCP、headless 都列在 README 的未来内容中。用户已决定参与新版重写，因此开发主线是新版 main，classic 不作开发底座。[新版状态](https://github.com/OpenCut-app/OpenCut/blob/e668010778568641babef2cc40be4703ae6916d6/README.md#L17-L28)、[web 占位](https://github.com/OpenCut-app/OpenCut/blob/e668010778568641babef2cc40be4703ae6916d6/apps/web/src/routes/editor.tsx#L5-L11)、[desktop 占位](https://github.com/OpenCut-app/OpenCut/blob/e668010778568641babef2cc40be4703ae6916d6/apps/desktop/src/panels/preview.rs#L7-L19)。

最小可推进内容是**一个可独立验收的自研颜色运算核心、输入输出颜色约定与测试素材**，随后接入新版媒体/渲染链。现在没有已实现的插件 API 可供接入，不能为了“将来可能有插件”先造完整插件系统。上游 README 明确现阶段尚未准备接受外部贡献；本地分支工作可推进，但上游是否接受、何时接受都不能保证。[贡献状态](https://github.com/OpenCut-app/OpenCut/blob/e668010778568641babef2cc40be4703ae6916d6/README.md#L64-L66)。

研究达芬奇的公开工作方式、公开颜色科学及可观察的输入输出，与把它的私有实现搬进项目是不同任务；本报告只支持自主或有明确开源来源的实现，没有取得或验证 DaVinci Resolve 私有算法源码。

## 固定源码快照

| 项目 | 核查 ref / SHA | 本次用途 |
|---|---|---|
| [OpenCut 新版](https://github.com/OpenCut-app/OpenCut/tree/e668010778568641babef2cc40be4703ae6916d6) | `main` / `e668010778568641babef2cc40be4703ae6916d6` | 唯一开发主线；已核对本地 checkout |
| [官方 classic](https://github.com/OpenCut-app/opencut-classic/tree/cf5e79e919144200294fb9fed22a222592a0aeea) | `main` / `cf5e79e919144200294fb9fed22a222592a0aeea` | 只读实现参照；README 明确已归档且不再维护 |

两个 SHA 由 GitHub 官方 branches API 的 commit 字段取得。classic 身份与归档状态同时由其固定快照 [README L1-L5](https://github.com/OpenCut-app/opencut-classic/blob/cf5e79e919144200294fb9fed22a222592a0aeea/README.md#L1-L5) 核对。不要把新版目录中的历史 changelog 当作新版当前功能已经存在的证明。

## 已核实事实：新版 main

| 事项 | 证据与实际状态 |
|---|---|
| 根代码许可 | MIT；保留原版权与许可通知。[LICENSE L1-L7](https://github.com/OpenCut-app/OpenCut/blob/e668010778568641babef2cc40be4703ae6916d6/LICENSE#L1-L7)。第三方依赖的许可须另行核查。 |
| Web 技术栈 | React `^19.2.0`、Vite `^8.0.0`、TypeScript `^6.0.2`、TanStack Router/Start 部分声明为 `latest`；这些是声明版本或范围，不是本机实测安装版本。[package.json L15-L65](https://github.com/OpenCut-app/OpenCut/blob/e668010778568641babef2cc40be4703ae6916d6/apps/web/package.json#L15-L65)。 |
| Rust / desktop | workspace 版本 `0.1.0`、edition 2024、GPUI `0.2.2`；当前 workspace 仅包含 `apps/desktop`，`crates/*` 被注释。[Cargo.toml L1-L14](https://github.com/OpenCut-app/OpenCut/blob/e668010778568641babef2cc40be4703ae6916d6/Cargo.toml#L1-L14)。桌面依赖只有 GPUI。[desktop Cargo.toml L1-L13](https://github.com/OpenCut-app/OpenCut/blob/e668010778568641babef2cc40be4703ae6916d6/apps/desktop/Cargo.toml#L1-L13)。 |
| 工具版本 | `.prototools` 声明 moon `2.3.3`、bun `1.3.11`、rust `1.97.0`。本次没有安装或验证这些工具在本机可用。[.prototools L1-L5](https://github.com/OpenCut-app/OpenCut/blob/e668010778568641babef2cc40be4703ae6916d6/.prototools#L1-L5)。 |
| 编辑与预览 | web `/editor` 显示 Coming soon；desktop Preview、Inspector 都只显示标签。[editor.tsx L5-L11](https://github.com/OpenCut-app/OpenCut/blob/e668010778568641babef2cc40be4703ae6916d6/apps/web/src/routes/editor.tsx#L5-L11)、[preview.rs L7-L19](https://github.com/OpenCut-app/OpenCut/blob/e668010778568641babef2cc40be4703ae6916d6/apps/desktop/src/panels/preview.rs#L7-L19)、[inspector.rs L7-L22](https://github.com/OpenCut-app/OpenCut/blob/e668010778568641babef2cc40be4703ae6916d6/apps/desktop/src/panels/inspector.rs#L7-L22)。 |
| 媒体基础准备 | 有 FFmpeg `8.1.3` 构建清单、源码/平台包地址与校验值，声明 LGPL-2.1-or-later；这是构建准备，不是已工作的媒体导入/导出 API。[ffmpeg.json L1-L24](https://github.com/OpenCut-app/OpenCut/blob/e668010778568641babef2cc40be4703ae6916d6/crates/media/setup/ffmpeg.json#L1-L24)。源码自建 flags 禁用 programs、avfilter、network、autodetect，因此不能假定现成 FFmpeg 滤镜或 ffmpeg.exe 已被集成。[setup.ts L84-L98](https://github.com/OpenCut-app/OpenCut/blob/e668010778568641babef2cc40be4703ae6916d6/crates/media/setup/setup.ts#L84-L98)。本次未核验远程二进制包实际内容。 |
| CI 配置 | `.github/workflows/bun-ci.yml` 有 main push / PR 触发、Linux/Windows/macOS 矩阵和 `moon ci`；desktop 定义 cargo check/build，web 定义 build/test。配置存在不等于本机或该 SHA 的 CI 已通过，本次未运行或读取 CI 结果。[CI L7-L37](https://github.com/OpenCut-app/OpenCut/blob/e668010778568641babef2cc40be4703ae6916d6/.github/workflows/bun-ci.yml#L7-L37)、[desktop tasks L12-L28](https://github.com/OpenCut-app/OpenCut/blob/e668010778568641babef2cc40be4703ae6916d6/apps/desktop/moon.yml#L12-L28)、[web tasks L12-L27](https://github.com/OpenCut-app/OpenCut/blob/e668010778568641babef2cc40be4703ae6916d6/apps/web/moon.yml#L12-L27)。 |
| 外部贡献 | 固定快照没有 CONTRIBUTING 文件；README 的明确状态为尚不接受外部贡献、架构仍在设计。存在 PR CI 配置并不能覆盖这个贡献状态。[README L64-L66](https://github.com/OpenCut-app/OpenCut/blob/e668010778568641babef2cc40be4703ae6916d6/README.md#L64-L66)。 |

对该 SHA 的文件清单和 `apps`、`crates` 源码做了定点搜索，未发现可调用的帧解码接口、时间线执行核心、图像效果 shader、调色处理函数、视频导出函数、Editor/plugin ABI 或 MCP server 实现。这个否定结论限于已锁定的源码快照与本次审计范围，不代表未来一定没有这些功能。[workspace 结构](https://github.com/OpenCut-app/OpenCut/blob/e668010778568641babef2cc40be4703ae6916d6/Cargo.toml#L1-L6)、[当前 editor](https://github.com/OpenCut-app/OpenCut/blob/e668010778568641babef2cc40be4703ae6916d6/apps/web/src/routes/editor.tsx#L1-L12)、[媒体 setup 目录](https://github.com/OpenCut-app/OpenCut/tree/e668010778568641babef2cc40be4703ae6916d6/crates/media/setup)。

## classic 实现参照：能共享渲染，但并非专业调色链

classic 根代码同为 MIT；其 README 和 AGENTS 描述了业务逻辑向 Rust 迁移的历史架构方向。这是旧版快照的说明，不能据此认为已归档的 classic 仍在维护或迁移。[LICENSE](https://github.com/OpenCut-app/opencut-classic/blob/cf5e79e919144200294fb9fed22a222592a0aeea/LICENSE#L1-L7)、[AGENTS L3-L16](https://github.com/OpenCut-app/opencut-classic/blob/cf5e79e919144200294fb9fed22a222592a0aeea/AGENTS.md#L3-L16)。

- **版本边界：** Next.js `16.1.3`、React `^19.0.0`、Mediabunny `^1.29.1`、opencut-wasm `^0.2.10`；本地 Rust WASM crate 声明版本 `0.2.10`，GPU crate 声明 wgpu `29.0.1`。没有检验发布的 npm WASM 二进制是否与本地 Rust 快照完全对应。[web package L50-L61](https://github.com/OpenCut-app/opencut-classic/blob/cf5e79e919144200294fb9fed22a222592a0aeea/apps/web/package.json#L50-L61)、[wasm Cargo L1-L27](https://github.com/OpenCut-app/opencut-classic/blob/cf5e79e919144200294fb9fed22a222592a0aeea/rust/wasm/Cargo.toml#L1-L27)、[gpu Cargo L5-L17](https://github.com/OpenCut-app/opencut-classic/blob/cf5e79e919144200294fb9fed22a222592a0aeea/rust/crates/gpu/Cargo.toml#L5-L17)。
- **预览路径：** `buildScene(isPreview: true)` → `CanvasRenderer.render()` → `resolveRenderTree` → `buildFrameDescriptor` → 上传纹理 → WASM compositor；预览直接挂载 compositor 的 canvas。[preview L105-L119](https://github.com/OpenCut-app/opencut-classic/blob/cf5e79e919144200294fb9fed22a222592a0aeea/apps/web/src/preview/components/index.tsx#L105-L119)、[preview L159-L211](https://github.com/OpenCut-app/opencut-classic/blob/cf5e79e919144200294fb9fed22a222592a0aeea/apps/web/src/preview/components/index.tsx#L159-L211)、[CanvasRenderer L53-L73](https://github.com/OpenCut-app/opencut-classic/blob/cf5e79e919144200294fb9fed22a222592a0aeea/apps/web/src/services/renderer/canvas-renderer.ts#L53-L73)。
- **导出路径：** `RendererManager` 重新 buildScene 后创建 `SceneExporter`，后者逐帧调用同一个 `CanvasRenderer.render()`，再将输出 canvas 送入 Mediabunny `CanvasSource`。MP4 选 AVC，WebM 选 VP9；音频选 AAC/Opus，并有 AAC 支持检测与回退。[manager L179-L195](https://github.com/OpenCut-app/opencut-classic/blob/cf5e79e919144200294fb9fed22a222592a0aeea/apps/web/src/core/managers/renderer-manager.ts#L179-L195)、[exporter L94-L127](https://github.com/OpenCut-app/opencut-classic/blob/cf5e79e919144200294fb9fed22a222592a0aeea/apps/web/src/services/renderer/scene-exporter.ts#L94-L127)、[逐帧渲染 L137-L147](https://github.com/OpenCut-app/opencut-classic/blob/cf5e79e919144200294fb9fed22a222592a0aeea/apps/web/src/services/renderer/scene-exporter.ts#L137-L147)。
- **共享边界：** 源码结构支持让预览和导出走同一效果处理链，但没有证明最终像素、颜色标签或性能相同。预览图片可限制到 2048，导出不设置该预览限值；两条路径的输入分辨率与后续编码不同。[scene-builder L21](https://github.com/OpenCut-app/opencut-classic/blob/cf5e79e919144200294fb9fed22a222592a0aeea/apps/web/src/services/renderer/scene-builder.ts#L21)、[image 预览限值 L88-L105](https://github.com/OpenCut-app/opencut-classic/blob/cf5e79e919144200294fb9fed22a222592a0aeea/apps/web/src/services/renderer/scene-builder.ts#L88-L105)。
- **效果能力：** TypeScript 的 EffectDefinition 支持参数和 pass；默认注册仅 blur。Rust pipeline 只注册 gaussian-blur，uniform packing 也专门读取 sigma/step/direction，并拒绝其他 uniform。因此不是“写一个 TS 调色 definition 就自动有可执行 shader”。[EffectDefinition L12-L40](https://github.com/OpenCut-app/opencut-classic/blob/cf5e79e919144200294fb9fed22a222592a0aeea/apps/web/src/effects/types.ts#L12-L40)、[默认注册 L1-L15](https://github.com/OpenCut-app/opencut-classic/blob/cf5e79e919144200294fb9fed22a222592a0aeea/apps/web/src/effects/definitions/index.ts#L1-L15)、[Rust shader 注册 L80-L135](https://github.com/OpenCut-app/opencut-classic/blob/cf5e79e919144200294fb9fed22a222592a0aeea/rust/crates/effects/src/pipeline.rs#L80-L135)、[uniform packing L265-L289](https://github.com/OpenCut-app/opencut-classic/blob/cf5e79e919144200294fb9fed22a222592a0aeea/rust/crates/effects/src/pipeline.rs#L265-L289)。
- **顺序能力：** clip effects 的数组顺序经 enabled 过滤后保留；compositor 先把 source 放入画布纹理，再执行 layer effects、mask，随后 blend；SceneEffect 处理此前累积的 scene。调色放置在哪一层会影响结果。[resolve L99-L128](https://github.com/OpenCut-app/opencut-classic/blob/cf5e79e919144200294fb9fed22a222592a0aeea/apps/web/src/services/renderer/resolve.ts#L99-L128)、[layer L420-L460](https://github.com/OpenCut-app/opencut-classic/blob/cf5e79e919144200294fb9fed22a222592a0aeea/rust/crates/compositor/src/compositor.rs#L420-L460)、[scene L313-L336](https://github.com/OpenCut-app/opencut-classic/blob/cf5e79e919144200294fb9fed22a222592a0aeea/rust/crates/compositor/src/compositor.rs#L313-L336)。
- **精度与颜色限制：** GPU 工作纹理固定为 `Rgba8Unorm` 或 `Bgra8Unorm`；外部图像拷贝显式 sRGB。shader 用 f32 运算不能改变中间纹理是 8-bit 的事实。持久化 MediaAssetData 未声明 transfer、primaries、matrix、range、bit depth；已检查的 exporter 未显式设定这些颜色字段。不能据此宣称支持专业 float、Log 或 HDR 管线。[GPU format L66-L70](https://github.com/OpenCut-app/opencut-classic/blob/cf5e79e919144200294fb9fed22a222592a0aeea/rust/crates/gpu/src/context.rs#L66-L70)、[外部颜色边界 L514-L527](https://github.com/OpenCut-app/opencut-classic/blob/cf5e79e919144200294fb9fed22a222592a0aeea/rust/crates/gpu/src/context.rs#L514-L527)、[MediaAssetData L17-L31](https://github.com/OpenCut-app/opencut-classic/blob/cf5e79e919144200294fb9fed22a222592a0aeea/apps/web/src/services/storage/types.ts#L17-L31)、[CanvasSource L102-L105](https://github.com/OpenCut-app/opencut-classic/blob/cf5e79e919144200294fb9fed22a222592a0aeea/apps/web/src/services/renderer/scene-exporter.ts#L102-L105)。

classic 的 effects-renderer 文档中仍出现 `src/lib/effects` 与 `rust/crates/gpu/src/shader_registry.rs`，而该 SHA 的实际 definition 在 `src/effects`、shader 注册在 `rust/crates/effects/src/pipeline.rs`。文档中的 color grading/bloom 是能力示例，不能当作已注册效果。[文档 L3-L20](https://github.com/OpenCut-app/opencut-classic/blob/cf5e79e919144200294fb9fed22a222592a0aeea/docs/effects-renderer.md#L3-L20)、[文档 L57-L69](https://github.com/OpenCut-app/opencut-classic/blob/cf5e79e919144200294fb9fed22a222592a0aeea/docs/effects-renderer.md#L57-L69)、[实际 blur 注册](https://github.com/OpenCut-app/opencut-classic/blob/cf5e79e919144200294fb9fed22a222592a0aeea/apps/web/src/effects/definitions/index.ts#L1-L15)。

## 工程提案：参与新版重写的最小切片

以下是建议，均不是上游已承诺的接口，也不是本轮已实现功能。

1. **先限定一个颜色任务。** 首个切片建议“明确标注的不透明 SDR 输入 → 内部线性 RGB float → 曝光调节 → 明确的 SDR 输出”。首期只接受 opaque RGB；负值与透明输入明确不支持，扩展 alpha 时另定直通/预乘规则。曝光可用 `RGB × 2^EV` 作为参考数学关系；首组样例输入 [0,1]、曝光 [-1,+1] EV，内部输出 [0,2]，保留其中的超白值而不提前截断。具体传递函数、范围和终端输出策略以 [实验协议](../experiments/color-protocol.md) 为准，不猜 DaVinci 的私有实现。色轮、节点编辑器、HDR、跟踪和 AI 调色留待后续。
2. **在新版 Rust 方向准备一个小颜色模块。** `crates/color` 可作为待讨论的位置，但该 crate 当前不存在，也未启用 `crates/*`。只有开始实现并需要独立编译时再增补具体 workspace member。核心接收浮点像素和明确参数，输出浮点像素；不依赖 GPUI、React、账户服务或插件管理器。先用 CPU 确定参考结果，GPU 实现是否需要由实测帧预算决定。
3. **颜色约定先于调色控件。** 用已知测试素材验证输入 transfer/primaries/range 到工作空间的转换。未知元数据应标为未知或由用户指定，不能默认为“支持所有 Log/HDR”。工作 float 的收益只有在解码到编码的各个边界都保真时才成立。
4. **当前可定位的 UI 接入位置只有占位壳。** 桌面 Preview 可承担未来画面显示，Inspector 可承担曝光控件；web `/editor` 可承担后续网页入口。它们现在没有帧源或渲染回调，不能把“加了滑块”当作调色功能接通。先完成独立单帧输出验收，再接媒体解码、预览，最后接导出。[当前 Preview](https://github.com/OpenCut-app/OpenCut/blob/e668010778568641babef2cc40be4703ae6916d6/apps/desktop/src/panels/preview.rs#L5-L19)、[当前 Inspector](https://github.com/OpenCut-app/OpenCut/blob/e668010778568641babef2cc40be4703ae6916d6/apps/desktop/src/panels/inspector.rs#L5-L22)。
5. **预览与导出调用同一颜色运算实现和同一参数顺序。** 显示转换与编码输出转换各有明确边界，不能让不同输入配置混用同一个含糊的“filter”。classic 的共享 CanvasRenderer 是可参考的调用结构；其 8-bit/sRGB 假定不应直接继承为新版专业颜色目标。
6. **保持可供上游审阅的粒度。** 第一份实现提案应只包含运算合同、依赖说明、测试输入/期望与一个最小模块。等上游媒体/渲染 API 确定，再做薄适配；不提前设计插件 ABI、通用节点运行时或完整编辑器内核。本地 fork 可持续推进，贡献窗口开放后再讨论提交上游。

## 实施前必须解决的风险

| 风险 | 当前证据 / 未知 | 需要的验收 |
|---|---|---|
| 色彩元数据 | 新版媒体 API 尚未存在；classic 数据模型和 exporter 缺显式颜色字段，见上文源码 | 同素材 input/output 的 primaries、transfer、matrix、range、bit depth 可查；元数据缺失有明确处理方式 |
| 精度 | classic 中间纹理固定 8-bit；新版目标尚未声明 | 首组 float 样例在 [0,2] 保留内部超白，按实验协议的限定绝对误差比较；负值/透明输入首期不支持。扩大域、高位深与 alpha 分别冻结规则 |
| 效果顺序 | classic clip/scene effects 位置不同；新版尚无效果模型 | 输入转换、曝光、混合、显示/输出转换固定顺序；零曝光为 identity；曝光正负往返在未裁剪域可复原 |
| 编码能力 | 新版只有 FFmpeg setup；classic 选择 CanvasSource 编码器但未实测 | 实测 Windows 的编码器、像素格式、文件元数据与回读结果；不把清单里的版本当作可用编码证明 |
| 性能 | classic 每个 effect pass 创建输出纹理并多处经 canvas；新版没有帧循环 | 固定素材/分辨率/帧率，测解码、颜色运算、上传/下载、显示和编码耗时及显存；先获得本机数字再承诺实时性 |
| 上游变化 | 新版 README 仍称架构设计中，暂不接受外部贡献 | 持续保留 upstream SHA 与本地差异；接口变化时更新证据，不保证被合并 |

性能风险的源码依据：classic [effects pass L177-L205](https://github.com/OpenCut-app/opencut-classic/blob/cf5e79e919144200294fb9fed22a222592a0aeea/rust/crates/effects/src/pipeline.rs#L177-L205)、[canvas 上传 L200-L226](https://github.com/OpenCut-app/opencut-classic/blob/cf5e79e919144200294fb9fed22a222592a0aeea/apps/web/src/services/renderer/compositor/wasm-compositor.ts#L200-L226)。这些只是潜在成本依据，没有对应本机性能数字。

## 待做运行验收清单

- [ ] 在实现阶段核验现有工具链，记录实际版本；运行新版现有 build/check 后记录失败或通过，区分环境错误与源码错误。
- [ ] 单帧 float 核心：零参数 identity、灰阶、色卡、渐变、[1,2] 内部超白和曝光往返；与明确的数学参考比较。负值/透明输入首期验证为明确不支持，后续扩展再单独验收。
- [ ] 颜色边界：至少一组有完整元数据的 SDR 测试输入；检查 decode 到工作空间、display transform、encode output transform。
- [ ] 同一时刻、同一参数比较预览 render 与导出编码前 render；编码后回读作为单独测试，容许有损编码误差但排查系统性色偏。
- [ ] 导出文件在外部播放器和回读工具中检验颜色标签、位深、格式、帧率与音画同步；没有导出链时明确保持该项未通过。
- [ ] 本机固定分辨率/帧率测性能及资源占用；独立模块通过不等于整套剪辑器可发行，也不等于达到 DaVinci Resolve 的画质或能力。

本报告完成的是新版参与路线的证据核查与最小技术提案。功能接入、画质验收、运行性能和上游合并仍待后续实施。
