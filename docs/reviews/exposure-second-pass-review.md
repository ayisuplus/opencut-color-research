# 曝光研究第二轮独立对抗审查

日期：2026-10-12。审查者：独立子代理。范围：本轮研究材料、静态读取方法、已有工具与 SDK 记录、自有参考生成与验证；不验收 Resolve 原生 HDR 曝光或 OpenCut 产品功能。

**结论：发现 1 项 P2 验证缺口，主代理已修复，独立反例复验已关闭。当前材料可以保留为受限研究结果；阶段 1A 仍未通过，专用测试库、原生控件输入和真实帧对照仍未完成。**

## 检查方式与范围

只读检查了：

- `experiments/inspect-ocio-renderer-rtti.py`、`reference-exposure-grid.py`、`verify-exposure-reference.py`。
- 第二轮研究报告、结果摘要、两个参考 JSON，以及 README 与立项书 0.4。
- Git 忽略目录中的 RTTI/vtable 记录、三个 REA/Ghidra dossier、SDK 探测脚本与运行日志、进程归属记录。
- 固定 OCIO DLL 的原始 PE 字节、两个原文件及两个只读副本摘要、安装附带脚本组件的签名与摘要。

独立字节核对使用 Python 标准库，没有复用 RTTI 读取器的地址计算。参考反例仅在内存中修改 JSON，并执行验证器的检查部分，截断在结果写盘之前；正常 Python、assert 开启。本审查没有加载或执行目标 DLL、启动 Resolve、执行 SDK 探测、修改项目库、安装工具或提交 Git，仅新增本审查文件。

## 必要修改及闭环

### P2：验证器接受误标的负对照与工作范围 — 已关闭

原验证器 SHA-256 为 `922981364e2780d4120b7a16695048c225a8cd65f57bc53b3f722a5b768bea88`。它正确拒绝错误数值，却未检查负对照样本编号、操作标签及每个 case 的 `work_range`。

具体反例：保留全部真实数值，仅将 `negative_control.sample_id` 从 5 改为 9、将 `wrong_operation` 改为“native Resolve HDR Exposure output”，或将 +1 EV 的 `work_range` 改为 [0,1]，均仍通过。真实参考文件没有这些错误，但该验证结果不能阻止数据被错误命名或把内部白值 2 描述成已裁切。

建议最小修复：固定自有参考 scope、负对照编号和操作约定；根据已检查的全部工作 RGB 重新计算每个 case 的 min/max，并与范围字段核对。

主代理已完成这些断言，更新后的验证器 SHA-256 为 `5cd1f60711a00244a4c4070610e8f24167db9451f363e705685919c20cbacafc`，与公开 validation 中记录一致。独立复验结果：

| 内存样例 | 结果 |
|---|---|
| 未修改的真实数据 | 通过：144 个通道、48 个预览中心点，最大误差 4.440892098500626e-16 |
| scope 改称原生 Resolve HDR 输出 | 拒绝 |
| 错误对照替换为正确 +1 EV 数值 | 拒绝 |
| 错误对照替换为 [1,1,1] | 拒绝 |
| 负对照 sample_id 改为 9 | 拒绝 |
| 负对照操作标签改称原生输出 | 拒绝 |
| +1 EV 工作范围改为 [0,1] | 拒绝 |
| +1 EV 灰块工作值改为 [0.8,0.8,0.8] | 拒绝 |

无其他需修改的已证实问题。以下是已核对的事实与必须保留的证据边界。

## RTTI 定位与函数归属

固定 DLL 摘要仍为 `a1658f7bbe6193ce34f9f6dd4beaf5820c19a2455758c91a9bdb6d2ba5444478`。从 PE 头独立确认 AMD64、PE32+ 和首选映像基址 0x180000000。

原始字节与记录逐项一致：完整 TypeDescriptor 名称及前缀、COL 的 signature=1/offset=0/cdOffset=0/self-RVA、层级描述符、三个基类的 PMD=(0,-1,0)、COL 指针、非可执行段 vtable、全部 18 个可执行函数指针及各自前 16 字节。继承链为具体 renderer → ECRendererBase → OpCPU。

| 类候选 | TypeDescriptor RVA | COL RVA | vtable RVA | slot 1 指针位置 RVA | slot 1 函数 RVA |
|---|---|---|---|---|---|
| ECLinearRenderer | 0x4455c0 | 0x3b84b8 | 0x384720 | 0x384728 | 0x154180 |
| ECVideoRenderer | 0x445660 | 0x3b85c8 | 0x384790 | 0x384798 | 0x154dd0 |
| ECLogarithmicRenderer | 0x445700 | 0x3b86d8 | 0x384800 | 0x384808 | 0x1549b0 |

六槽方法顺序来自 [固定源码 OpCPU](https://github.com/AcademySoftwareFoundation/OpenColorIO/blob/2831d2547d133b326c6e9a09726ceeb7fe46f997/src/OpenColorIO/Op.h#L34-L51) 与 [ECRendererBase](https://github.com/AcademySoftwareFoundation/OpenColorIO/blob/2831d2547d133b326c6e9a09726ceeb7fe46f997/src/OpenColorIO/ops/exposurecontrast/ExposureContrastOpCPU.cpp#L20-L41)；COL 字段与 [固定版本 LLVM 实现](https://github.com/llvm/llvm-project/blob/llvmorg-20.1.8/clang/lib/CodeGen/MicrosoftCXXABI.cpp#L3903-L3916) 相符。已直接核对 raw 文件的实际行号，网页阅读器折叠空行后的行号不作为 GitHub 锚点依据。

因此 slot 1 可保留为 apply 候选，不能称其方法名来自原始导出符号，也不能以公开 tag 证明厂商采用同一源码或构建选项。VA 是首选映像基址加 RVA，不是本机运行地址。

本案异常目录为 102264 字节，可整除 12，共 8522 条非零记录；独立核对未发现重复 begin，begin<end，起止与 unwind 地址均有对应原始节字节。RTTI 脚本不构成通用 PE 验证器；其固定哈希输入限制必须保留。

## 函数范围、截断与数值观察

三个 dossier 的完整 SHA-256、证据 ID、body AddressSet、指令数量和截断标记均与 [公开结果摘要](../experiments/exposure-second-pass-result.json) 一致，raw 与 normalized 视图一致。

| 候选 | .pdata 精确入口片段 | Ghidra body 字节数 | 指令数 | native_value_flow.truncated |
|---|---|---|---|---|
| Linear | 31 字节 | 1036 | 228 | true |
| Video | 31 字节 | 1052 | 231 | true |
| Log | 460 字节 | 460 | 116 | false |

Linear/Video 的 .pdata 只覆盖入口片段，不能充当完整函数；Ghidra body 是工具恢复的范围，也不是原始源码边界证明。两者 value-flow 均标明至少省略 1 个 operation，Video 另记录 22 个已知省略 edge。Log 未截断也不代表已解决跨函数别名、虚调用或全部原始类型。

独立从固定字节读出 2.0、1.0 和 Video 幂常数的 float32 值 0.5464481115341187；三次相对 CALL 均指向 RVA 0x3124ba，其间接跳转对应 IAT RVA 0x329860，声明导入名为 powf。结合局部汇编与反编译视图，可以支持报告中中性有效 contrast 分支的 RGB 乘法解释。Linear/Video 该分支出现第 4 通道复制；Log 出现乘加后的第 4 通道恢复。未将这些伪代码复制入公开报告。

[公开 CPU 实现](https://github.com/AcademySoftwareFoundation/OpenColorIO/blob/2831d2547d133b326c6e9a09726ceeb7fe46f997/src/OpenColorIO/ops/exposurecontrast/ExposureContrastOpCPU.cpp) 与 [参数说明](https://github.com/AcademySoftwareFoundation/OpenColorIO/blob/2831d2547d133b326c6e9a09726ceeb7fe46f997/src/OpenColorIO/ops/exposurecontrast/ExposureContrastOpData.h) 支持这些受限数学对应；Video 的 1/1.83 是特定曲线近似，Log 步长可配置。对象成员名称与曝光/contrast/gamma 的类型归属仍含源码对应推断，恢复的无参签名或临时变量类型不能当作真实 ABI。

报告已正确限定 float 转换后有效 contrast 恰为 1；Log 中性化简式不是逐位浮点等价承诺。本轮没有直接调用固定副本中的三个候选，也没有进行受控动态验证；未观测 headless 宿主内部是否调用这些候选。因此，负值、超白、alpha、非中性 contrast、SIMD 误差、参数 setter 和真实调用路径均未验收。库内导入与候选函数存在，不能证明 Resolve HDR Global Exposure 使用它们。

## SDK 运行记录与副作用边界

逐项重算了公开摘要所指的 Lua stdout、方法表面 stdout，以及四组 Python stdout/stderr 哈希，均匹配。

Python 3.12.0、3.11.9、3.9.25 的日志均止于 before_sdk_import，stderr 均记录 create_module 阶段 access violation；有 headless 实例时的 3.12 重试仍相同。没有证据定位根因，不能推断全部 Python 环境都不兼容。

官方 Lua 记录明确显示 connected=true、版本 21.0.0.47、library_count=1、Disk、test_library_current=false、project_open=true；方法表面记录显示默认未命名工程。它足以反驳“Python 导入崩溃，所以整个 SDK 都不可用”，也不能把默认工程等同于专用隔离库。

CreateDatabase/CreateProjectLibrary 两个精确属性为 nil，已有方法为 function、随机不存在方法为 nil；结论只适用于这次查询的对象与两个名称，不能推广至全部未文档化方法。Lua 只读脚本与 Python 探测源码未请求建工程、换库、保存、grade 或渲染；Python exception 捕获不能兜住原生 access violation，现有材料未声称能兜住。

研究归属记录包含独立 PID、路径、启动与退出确认，官方 Quit 日志存在；审查时只读进程查询没有匹配的 Resolve 进程或该 PID。仅核对现存记录与当前状态，没有重演启动、退出或 SDK 调用。安装附带 fuscript.exe/fusionscript.dll 的 Authenticode 状态均为 Valid，完整摘要与公开结果匹配；这不证明被修改过的整个安装可信。

两个原文件及两个只读副本的完整摘要与第一轮 manifest 一致，副本只读；OpenCut HEAD 仍为 e668010778568641babef2cc40be4703ae6916d6 且工作副本 clean。空 project-library 目录属实，但不是已创建的数据库。“未请求项目修改”与“应用启动/退出从未写过缓存、日志或用户库”必须区分，报告已保留这一边界。

## 自有参考的证据限度

按独立 Decimal 50 位精度重算全部 144 个工作通道。输入通过原始 PNG 字节核对 CRC、16-bit RGB 头、sRGB 标记、解压行及全部色块像素，没有将 Pillow 的 8-bit RGB 读入当作 16-bit 数值检查。三个观看预览按文件摘要与 48 个中心点回读核对。

参考使用量化后的代码值，18% 灰实际线性值为 0.18000033259998335；−1/0/+1 EV 对应 0.09000016629999168、0.18000033259998335、0.3600006651999667。负对照为编码值先翻倍并裁切、再解码，得到 0.8331083550727032。工作白值 2 保留于表格，只有观看预览裁切为 255。

这些结果只验证自有 float64 sRGB 参考及其文件一致性：不是 Resolve/OCIO 执行结果，不是 native f32 容差、真实视频编码、预览/导出一致性或审美验收。预览仅检查中心点；没有宣称对其全部像素逐点回读。参考报告、README 与立项书均保留了这些限度。

## 保留的未完成项

- 专用项目库与测试工程实际隔离；当前库不是测试库。
- 原生 HDR Exposure 参数的可验证输入途径、控件值语义与颜色管理设置。
- 原生旁路和参数变化的重复帧导出、位深/数值比较、宿主调用关系。
- 实际负值、超白、alpha、非中性参数、原生浮点及视频误差实验。
- OpenCut 新主线运行、调色接入、真实预览/导出与上游合入。

后续可以继续研究可用入口；上述条件未具备前，不能宣布阶段 1A 已通过、阶段 1B 已实现或“达芬奇原生曝光已复现”。本轮当前停止位置符合已观察到的证据边界。
