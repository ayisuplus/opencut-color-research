# OpenCut 个性化调色剪辑器研究

项目编号：OC-COLOR-001。立项日期：2026-10-12（Asia/Shanghai）。

**项目已封存（2026-10-15）。** [封存记录与恢复入口](docs/archive-2026-10-15.md)。后续研究和产品实现暂停；下列未来计划保留为历史记录，待用户明确恢复后重新评估。

目标：参与 OpenCut 新主线的重写，研究专业调色的公开原理，开发有自己风格的开源剪辑器。DaVinci Resolve 是功能和效果参考；交付实现来自自主代码或许可证明确的开源组件。

## 当前状态

- 已确定：开发方向采用用户指定的 OpenCut 新主线。classic 只用于理解已有实现。
- 已完成：上游源码快照、功能研究、首期范围和验收设计。
- 封存时进度：阶段 1A 曝光定点研究已完成本轮近黑对照。正式浮点EXR累计60张。新近黑灰阶的−1/+1固定主模型最大中心及ROI通道误差1.788e−7，低于预定1e−6门；两档重放与中性恢复全图逐位一致，预测未改。固定无夹紧理想CPU候选在新输入上被排除，实际运行路径仍未绑定。005于2026-10-14核对的冻结getter/对象与23个原任务均匹配，009完成归档、008失败归档保留；完整公式尚未验收。
- 已完成 Resolve 21.1.1 升级、启动与原生 MCP 实测，21.1.1 / OCIO 2.5 快照已重新固定。封存前已在聊天中直接调用官方MCP工具；先前实验通过同一官方 server 的 stdio 直连进行。
- 已完成独立的 CDL 饱和度阳性对照：改动像素、非中性调色重放和中性恢复均有整幅像素核对；第三轮累计导出六张单帧 EXR。
- 尚未完成：HDR 完整 UI 换算及像素公式、新主线运行、调色功能接入、真实视频预览与导出、上游合入。
- 首期风格优先级仍待用户选择；“电影感调色与个人预设”仅为建议。

## 从这里开始

最新完成：[近黑新颜色原生对照](docs/research/hdr-near-black-native.md)、[独立审查](docs/reviews/hdr-near-black-native-review.md)、[输入与预测冻结](docs/research/hdr-near-black-preflight.md)、[素材重新链接补充协议](docs/research/hdr-near-black-relink-preflight.md)。封存前原拟下一项为高端／浮点输入协议，本次未启动。

上一轮：[三个未见曝光存储值的原生对照](docs/research/hdr-unseen-gains-native.md)、[独立审查](docs/reviews/hdr-unseen-gains-native-review.md)。历史[预测冻结](docs/research/hdr-unseen-gains-preflight.md)保持。前一轮：[白点适配与上传路径](docs/research/hdr-white-adaptation-and-upload.md)、[独立审查](docs/reviews/hdr-white-adaptation-review.md)。前序：[完整float32 GPU参考对照](docs/research/hdr-full-float32-gpu.md)、[GPU审查](docs/reviews/hdr-full-float32-gpu-review.md)、[HDR颜色转换链与sRGB残差](docs/research/hdr-color-transfer-chain.md)、[颜色链审查](docs/reviews/hdr-color-transfer-review.md)、[空分区曝光表与自有GPU采样](docs/research/hdr-table-and-sampler-precision.md)、[未见混色与空间复制的原生对照](docs/research/hdr-mixed-response.md)、[观测前冻结](docs/research/hdr-mixed-preflight.md)、[Global标量来源与精确零开关](docs/research/hdr-global-gain-binding.md)、[宿主查表路径与精度纠正](docs/research/hdr-host-table-path.md)、[参考值的同输入对照](docs/research/hdr-reference-context.md)、[静态内核与查表坐标候选](docs/research/hdr-static-texture-candidate.md)、[接近零的响应](docs/research/hdr-near-zero-response.md)、[黑场偏移字段校准](docs/research/hdr-black-offset-mapping.md)、[四帧像素对照](docs/research/hdr-black-offset-pixel-response.md)、[固定传递函数交叉检查](docs/research/hdr-asymmetric-domain-check.md)。

1. [立项书](docs/project-brief.md)：目标、范围、交付顺序和成功标准。
2. [达芬奇调色研究](docs/research/resolve-color.md)：公开能力、实现原理和未知事项。
3. [OpenCut 源码可行性](docs/research/opencut-feasibility.md)：固定版本、实际承载能力和接入风险。
4. [实验协议](docs/experiments/color-protocol.md)：如何证明计算正确、预览与导出一致。
5. [上游提案草案](docs/upstream-proposal.md)：可供后续讨论的最小贡献。
6. [独立对抗审查](docs/reviews/adversarial-review.md)：发现的问题和处理记录。
7. [曝光研究第一轮](docs/research/resolve-exposure-first-pass.md)：本机静态发现、工具验证和仍需实测的问题。
8. [原生工具验证](docs/experiments/rea-native-verification.json) 与 [测试库准备](docs/experiments/resolve-test-library.md)：已通过的工具检查和下一轮画面对照入口。
9. [曝光研究第二轮](docs/research/resolve-exposure-second-pass.md)：三个颜色域的像素函数、SDK 实测、参考输出和停止边界。
10. [真实工程准备](docs/research/resolve-project-preparation.md)：隔离库、SDK 创建工程与素材导入，以及下一步颜色设置确认。
11. [Resolve 21.1.1 升级](docs/research/resolve-21-1-upgrade.md)：安装来源、离线备份、独立审查与原生 MCP 的验证范围。
12. [原生导出第三轮](docs/research/resolve-native-neutral-third-pass.md)：六帧像素测量、中性/非中性调色重放及恢复；[OCIO 2.5 / HDR 数据结构](docs/research/ocio-25-and-native-grade-api.md)记录公开公式与定点静态发现，[独立审查](docs/reviews/resolve-native-neutral-review.md)记录验证范围及已关闭问题。
13. [HDR 参数映射](docs/research/hdr-global-parameter-mapping.md)：人工显示点、精确候选与原生读回；[官方操作域与上下文](docs/research/hdr-exposure-official-domain.md)、[校准与执行审查](docs/reviews/hdr-mapping-review.md)分别记录资料依据与准入限制。
14. [HDR 原生对照第四轮](docs/research/resolve-hdr-global-fourth-pass.md)：六帧浮点像素结果、零档重复与中性恢复、直接 EXR 通道缩放候选的反例；[校准及执行记录](docs/experiments/resolve-hdr-calibration-result.json)与[像素结果](docs/experiments/resolve-hdr-global-grid-result.json)保留摘要和测量范围。尚未证明完整曝光公式。
15. [HDR 操作域第五轮](docs/research/resolve-hdr-domain-fifth-pass.md)：固定候选、七帧 Gamma 配置对照及保存重载差异；[一手公式](docs/research/hdr-exposure-domain-primary-models.md)、[数据](docs/experiments/resolve-hdr-gamma-conditions-result.json)、[配置探针](docs/experiments/resolve-hdr-setting-probes-result.json)与[独立审查](docs/reviews/hdr-domain-review.md)记录已确认及未知的边界。
16. [HDR 上下文第六轮 A](docs/research/resolve-hdr-context-sixth-pass.md)：官方设置职责、005 的显式关闭重开及完整快照恢复；[第六轮 B](docs/research/resolve-hdr-context-sixth-pass-b.md)完成八帧和五份严格读回，记录配置响应、调色重放及仍有残差的候选。
17. [HDR sRGB配对第七轮](docs/research/resolve-hdr-srgb-seventh-pass.md)：五帧、三份严格读回与[三档数据](docs/experiments/resolve-hdr-srgb-pair-result.json)；零档省略字段后默认0，原Rec.709的非零档近4关系不能推广到新条件。
18. [HDR接口缺口](docs/research/resolve-hdr-api-gap.md)：实际查询官方14项MCP工具、Graph声明及注册脚本窗口，尚未取得005菜单状态；待一次人工确认，实验结果保留。
19. [OpenCut工具链探针](docs/research/opencut-existing-toolchain.md)：现有Rust1.96的元数据读取成功，离线桌面check因当前索引缺gpui而未通过；锁定工具链及运行尚待验收。

## 源码快照

`opencut/` 是独立 Git 仓库，已从 https://github.com/OpenCut-app/OpenCut.git 克隆。固定上游 main 基线：`e668010778568641babef2cc40be4703ae6916d6`，本地工作分支：`research/color-foundation`。立项仓库不重复收录上游代码；基线见 [upstream-lock.json](upstream-lock.json)。

上游当前主线尚在重写，也尚未开放外部贡献。我们可以本地研究和制作贡献候选；外部合并需遵循届时的贡献规则。[上游说明](https://github.com/OpenCut-app/OpenCut/blob/e668010778568641babef2cc40be4703ae6916d6/README.md)

## 可运行的研究演示

在本项目根目录中运行：

```powershell
node experiments/linear-exposure.mjs
python experiments/make-exposure-inputs.py
python experiments/reference-exposure-grid.py
python experiments/verify-exposure-reference.py
```

这些程序生成自有输入、线性曝光参考，并进行独立数值与预览回读检查。它们不代表已复现达芬奇，也不代表 OpenCut 已具备调色功能。
