# 曝光研究第一轮独立对抗性审查

日期：2026-10-12（Asia/Shanghai）。范围：阶段 1A 的静态研究、PE 读取方法、Scripting SDK 边界、自有分析 fixture 与受控 PNG 输入。工具验收已按本轮真实记录复核；此报告不将阶段 1A 写成全部完成。

## 结论

本轮研究材料可交付，两个 P2 问题已修正并复验关闭，未发现需要停止当前静态研究的 P0/P1 问题。PE/SDK/PNG 输入和选定函数的原生工具链均有对应证据；真实曝光控件、应用解码、颜色管理和画面对照仍待验证，不能推成原生曝光公式已还原或阶段 1A 已全部完成。

## 实质问题与闭环

### EFR-01 [P2] 原始导入读取缺少明确格式及边界拒绝 — closed

初稿逐 20 字节读取时，没有拒绝非整除目录尺寸或目录内缺少全零终止项；固定 256/512 字节名称窗口未要求 NUL；固定 64 位 thunk 没有先限定 AMD64/PE32+，且 OCIO OriginalFirstThunk 为零时没有明确不支持。这些输入可能让损坏或不支持的格式仍生成似乎完整的计数。

修正采用限定范围的拒绝语义：只支持 AMD64/PE32+；描述符尺寸与终止均校验；RVA 窗口必须由同一文件节的原始数据完整支持；名称必须在窗口内终止；OCIO 的零 OriginalFirstThunk 直接拒绝，thunk 超出数量/文件范围而未终止时拒绝。普通 pefile 警告与 partial 标签保留。此修正不是通用 PE 格式验证器，也未补读所有模块的全部符号、延迟导入或主程序全部结构。

### EFR-02 [P2] 按名称 thunk 未拒绝 PE32+ 保留位 — closed

第一版修正仅检查 ordinal 保留位。具体内存反例：thunk 值为 0x80000000，同时存在可读的高 RVA 文件节及 NUL 终止名字；读取器曾接受该名字，但该值的 bit31 不符合 PE32+ 按名称导入字段。

之后增加 0x7fffffff80000000 掩码检查；同一反例现在明确拒绝。read_backed 的 size/delta 和 read_name 的可用字节范围亦显式检查，越原始节范围的名字从非预期的负长度异常改为准确的不支持错误。格式依据：[Microsoft Import Lookup Table](https://learn.microsoft.com/en-us/windows/win32/debug/pe-format#import-lookup-table)。

## 独立复验

未运行完整研究脚本来重写私有 inventory。对最新脚本的 helper 与描述符读取块做内存隔离探针，不导入 SDK、不加载目标 DLL、不改副本。结果如下：

| 探针 | 预期与实测 |
|---|---|
| 合法按名称控制 | 接受 |
| 合法 ordinal 控制 | 接受 |
| 缺全零描述符终止项 | 拒绝 |
| 目录尺寸不是 20 的倍数 | 拒绝 |
| 模块名无 NUL | 拒绝 |
| 符号名无 NUL | 拒绝 |
| OCIO OriginalFirstThunk 为零 | 拒绝 |
| ordinal 保留位非零 | 拒绝 |
| 按名称 bit31 非零 | 拒绝 |
| PE32/非 AMD64 | 拒绝 |
| 名字超过原始节支持范围 | 拒绝 |
| thunk 到研究上限仍无终止 | 拒绝 |

12 项结果均符合预期。这些是读取逻辑的有限边界探针，不是 pefile 全部节映射、所有畸形 PE 或操作系统加载器的验证。

另用 Python 标准库独立读取实际副本的 PE/节头与文件支持 RVA，没有依赖 pefile 的导入结果：

| 对象 | 格式 | 导入目录尺寸 | 非零描述符 | 目录终止 | 当前 OCIO 查找表 |
|---|---|---:|---:|---|---|
| Resolve.exe | AMD64 PE32+ | 2940 | 146 | 范围内全零终止 | 57 项，全有终止 |
| OpenColorIO_2_4.dll | AMD64 PE32+ | 380 | 18 | 范围内全零终止 | 该目录未声明目标 OCIO 库 |

实际 OCIO 57 项的名称与 IAT RVA、目标描述符 RVA 与私有 seeds 完全一致；这些 IAT 窗口有文件支持。原始文件与副本分别重算 SHA-256，均匹配 target-manifest，副本属性为只读。解析器主程序仅得到 75 个普通导入模块并有 33 条警告，文档准确保留 partial；没有把差额补丁说成全程序验证。

## SDK 与因果结论

只读核查安装附带 README、CHANGELOG、loader 源码和批量样例；三份 SDK 文件 SHA 与报告一致。公开列出的 API 有 SetCDL、Graph LUT/grade 等入口，没有声明原生 Exposure/HDR Exposure setter。“未找到声明”不能推成运行时绝不存在其他接口。

CreateProject 位于当前项目库；它不能自动提供隔离库。DaVinciResolveScript.py 的导入会尝试加载 fusionscript，不能当作纯文本文档运行。批量样例顶层最终调用 DeleteAllRenderJobs，并处理当前工程的所有 timeline；没有执行这些样例、导入 loader 或调用 SDK。

DRX 重放和帧导出只是条件性计划，原生控件、设置重放、测试库隔离和真实输出均未实测。API 返回成功、PNG/TIF 扩展名、缩略图或 SetCDL 数值不能代替高位深原生曝光真值。

已声明 OCIO 依赖、IAT 入口、曝光相关文字和库导出只能提供静态候选；不能证明运行调用，也不能证明 Resolve 原生曝光轮使用 ExposureContrast。RAW、primary 和 HDR 控件仍需要分别研究；文件版本资源不能证明修改版安装的官方真实性。

## 受控 PNG 输入核查

未用 Pillow 的 RGB 读取作为 16 位数值证据。直接解析 PNG 签名、IHDR、所有 chunk 的 CRC，拼接并解压 IDAT，以大端 16 位样本读取中心像素和全部 16 个色块面积；另用 50 位 Decimal 精度独立计算 sRGB 编码、舍入与解码。[PNG 规范](https://www.w3.org/TR/png-3/#7Integers-and-byte-order)规定多字节样本采用大端顺序。

实测输入为 1920×1080、RGB color type 2、16-bit、非交错、所有行 filter 0、sRGB intent 0，无 alpha/tRNS。公开与输出目录 manifest 一致，PNG 大小与 SHA 一致；16 个 patch 的实际码值均匹配 manifest 和独立量化参考。独立 realized 值与 manifest 的最大差为约 2.22e-16。

关键 0.18 灰块中心是 (720,405)，三通道实际整数均为 30235，对应 realized linear RGB 约 0.18000033259998335；后续比较应使用此实际值。8-bit preview 的头、CRC、摘要也匹配，仍仅供观看。

没有由此验证 Resolve 导入、sRGB tag 处理、项目颜色转换或原生曝光输出。输入只有非负、无超白的不透明 SDR 色块，不能充当 HDR、负值、alpha 或连续梯度验收。

## 工具证据

工具相关待复验项已按实际证据关闭。结论限于本轮 Ghidra 与两项选定函数静态分析，不等于 REA 全部能力、所有 provider 或 Codex MCP 集成都已配置。

| 层次 | 独立核对的证据 | 判定 |
|---|---|---|
| REA 包 | 本地 package.json 为 rea-agents 6.4.0，repository 指向 morluto/rea，许可证 MIT | 固定包身份可核对；安装脚本禁用、CLI 退出码取自主代理执行记录 |
| Ghidra 包 | 实际 archive 为 569649598 字节，完整 SHA-256 为 ddac49f903da9d5bac833e5cc79395098b9c33cfd3279be5f31bd00387d2d4db，与官方 release 公布值相同；隔离安装目录存在 | 版本/整包身份通过 |
| doctor | 明确的 Ghidra/自有 DLL 范围内 healthy=true，11 项 scope_checks 全部 ok；providerVersion=12.1.4 | 指定范围就绪通过；environment_healthy=false，不能宣称全环境健康 |
| 自有 Rust fixture | 输入 DLL 摘要、源码摘要、完整 5 字节函数、编译器汇编与 Ghidra 输出一致 | 已知源码的静态 smoke 通过 |
| OCIO 创建入口 | 输入摘要、PE 导出 RVA、非 forwarder 属性、211 字节文件支持范围及实际 provider 结果一致 | 选定函数真实分析通过；像素算法与 Resolve 调用未验证 |
| inspect_artifact / managed 分类 | 分别是静态 artifact graph 与无 CLI 目录的 managed 否定分类 | 未拿它们代替上述原生分析验收 |

官方 package 身份依据：[Ghidra 12.1.4 release](https://github.com/NationalSecurityAgency/ghidra/releases/tag/Ghidra_12.1.4_build)。主代理先分析自有 fixture，再分析 OCIO，符合受控验证顺序。

自有 DLL 的 SHA-256 为 d71274261d45595237ca5f3fb1ca0bf762cf684cf04a7993bc445dd85cf40407。独立按文件支持 RVA 读取入口字节，结果为 F3 0F 58 C0 C3，与 ADDSS/RET、5 字节函数体及编译器输出相符；源函数为 f32 乘二。Evidence ID 为 ev_bf3a3b986566ef9cc96bec9052c47f0e417bb86ad72826662ff787c68fc1a06c，value flow 未截断。没有运行此 DLL 的函数或用它证明数值/视频性能。

OCIO 的真实结果为 ExposureContrastTransform::Create，RVA 0x2b4380，首选静态 VA 0x1802b4380，Evidence ID 为 ev_373f433d69415c47a7236bdd47b9fc1ea60f8278ac9778ef2b78c1380e04a9c6；provider 为 Ghidra 12.1.4，完整连续函数范围报告为 211 字节，汇编记录 50 条，value flow 未截断。独立读取 PE 导出表确认同一 RVA 且不是导出转发字符串；输入摘要与已固定 DLL 相同。

它是对象创建入口，没有提供像素 RGB 到输出 RGB 的曝光公式。恢复的共享指针函数签名与伪代码的返回/隐藏寄存器表达不一致，另有折叠类型标签；这些不能认证原始 C++ 类型、ABI、变量或类身份。本报告不复制该私有伪代码，也不把函数名当作原生 HDR 控件的调用证据。

公开工具汇总的四份 raw_evidence 文件摘要和 fixture 源码摘要均独立重算匹配。CLI 正常退出状态来自执行记录；随后只读观察 java/javaw/node/cmd/decompile 的本项目范围及 Resolve 进程，未见残留。再次完整读取两个原文件与副本，四份 SHA-256 均仍匹配原 manifest；自有 DLL 的分析后摘要也匹配。过程未终止其他应用。

补充阅读了公开 OCIO v2.4.0 factory/CPU linear 源码：报告所述中性对比度/gamma 分支的 RGB 曝光倍数与 alpha 保留可由公开源码支持，但不能由命名空间证明本机 DLL 的精确源码 tag，也没有证明 Resolve 原生控件采用该分支。[公开 CPU 实现](https://github.com/AcademySoftwareFoundation/OpenColorIO/blob/v2.4.0/src/OpenColorIO/ops/exposurecontrast/ExposureContrastOpCPU.cpp#L143-L166)

已核对 REA 6.4.0 NativeUiObservation 的 Mach-O 入口限制；它不能为本次 Windows 曝光轮提供界面自动设置路径。新测试库说明准确标记尚未执行，并将库创建与 CreateProject 分开；没有把生成输入、拟选控件或导出计划当成实测。用户暂无专用测试库，真实画面对照仍需要建立并确认隔离上下文。

## 范围、发布与剩余证据

本审查没有安装/下载工具、编译或执行目标、导入 SDK、读取用户项目库或认证资料；只写此报告。tools、evidence/local、experiments/output 均由 Git 忽略。公开材料没有复制私有反编译代码或用户素材，完整私有工具输出应继续保留在忽略目录。

剩余证据包括：特定 UI 控件到像素处理函数的对应、隔离测试库与项目、图像解码/颜色配置、受控参数档位、无损/高位深导出及输入输出数学关系。原生 provider 的本轮两项指定函数验证已通过，不再列为未验证。不能把尚未就绪的环节补写成功；最终“为何好用/画质如何”的产品和观感结论也不能由这一轮静态计数推出。


本轮复验读取脚本 SHA-256：ee82a29a61a5653457dc72cab23444bf0a2cb462015674c170cc2b376895b89b；PNG 生成器 SHA-256：b796a11b8084ed473f4f1f08c2e1980a3b3c05ce762ec729f8b306047d1437c7。代码、原始证据和摘要之间的对应仍需在后续版本变更时重新核对。
