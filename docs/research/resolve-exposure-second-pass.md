# 曝光研究第二轮：像素函数、SDK 实测与参考输出

日期：2026-10-12。阶段 1A 继续进行。本轮按用户要求自主推进，不再等待教学操作。已有安装及项目数据保留；分析用固定副本，SDK 探测使用本机附带的脚本工具。

本文件保留第二轮的历史范围。用户随后已创建专用库，Lua 已创建测试工程并导入素材；当前进展见 [真实工程准备](resolve-project-preparation.md)。

**已从创建入口追到 OCIO 库中三个像素处理候选函数，并用官方 Lua 连接了 Resolve 21.0.0.47。专用测试库和原生 HDR 曝光画面对照仍未完成。** 自有数值参考已生成并验证，不能作为 Resolve 导出结果。

## 从类型信息到实际函数

目标为第一轮固定的 `OpenColorIO_2_4.dll` 副本，SHA-256 `a1658f7bbe6193ce34f9f6dd4beaf5820c19a2455758c91a9bdb6d2ba5444478`。解析对象是文件字节，没有加载或执行这份库副本。

[RTTI 读取脚本](../../experiments/inspect-ocio-renderer-rtti.py) 核查了 AMD64 PE32+、文件支持的地址范围、完整类型名、MSVC x64 Complete Object Locator 的 signature/self-RVA、继承描述符和六个可执行段函数指针。根据锁定的公开源码虚函数顺序，把 slot 1 推断为 `apply`；这不是从原始符号表取得的方法名。[官方 OpCPU 声明](https://github.com/AcademySoftwareFoundation/OpenColorIO/blob/2831d2547d133b326c6e9a09726ceeb7fe46f997/src/OpenColorIO/Op.h#L34-L51)、[LLVM 的 COL 结构实现](https://github.com/llvm/llvm-project/blob/llvmorg-20.1.8/clang/lib/CodeGen/MicrosoftCXXABI.cpp#L3903-L3916)。

| 推断的类 | TypeDescriptor RVA | COL RVA | vtable RVA | slot 1 首选 VA | Ghidra 函数体 / 指令数 |
|---|---|---|---|---|---|
| ECLinearRenderer | `0x4455c0` | `0x3b84b8` | `0x384720` | `0x180154180` | 1036 字节 / 228 |
| ECVideoRenderer | `0x445660` | `0x3b85c8` | `0x384790` | `0x180154dd0` | 1052 字节 / 231 |
| ECLogarithmicRenderer | `0x445700` | `0x3b86d8` | `0x384800` | `0x1801549b0` | 460 字节 / 116 |

这里的 VA = 首选映像基址 `0x180000000` + RVA，不是本机运行时地址。Linear / Video 的 `.pdata` 匹配只覆盖入口的 31 字节片段；表中大小来自 Ghidra FunctionManager 的 body AddressSet，不能把该片段长度当成完整函数长度。

REA 6.4.0 + Ghidra 12.1.4 对三个候选的分析均成功返回。原始 dossier 保留在 Git 忽略的 `evidence/local/resolve-exposure-20261012/analysis/`；安全摘要、精确 body 范围、证据 ID 和原始 JSON 哈希见 [第二轮结果](../experiments/exposure-second-pass-result.json)。Linear 和 Video 的 `native_value_flow.truncated` 均为 true，Log 为 false。汇编与反编译视图支持下面的局部分支解释；不能据此声称取得全部 P-code/def-use、原始 C++ 类型或完整宿主调用图。

## 能够支持的数值解释

将 RGB 输入记作 x，曝光参数为 E。只讨论 contrast × gamma 经最低值约束、转换成 float 后恰为 1 的分支：

| 库中的候选 | 本机静态观察 | 与公开公式的对应 |
|---|---|---|
| Linear | `powf` 的底数为 2，结果用于 RGB 乘法；alpha 槽复制 | x × 2^E |
| Video | 第二次幂计算的指数约为 0.5464481；结果用于 RGB 乘法；alpha 槽复制 | x × (2^E)^(1/1.83) |
| Log | 从对象读取每档步长、pivot；RGB 乘加后恢复 alpha 槽 | 当有效 contrast 为 1 时，数学上化为 x + E × step |

对应公开源码固定在 OpenColorIO v2.4.0 的 commit `2831d2547d133b326c6e9a09726ceeb7fe46f997`。[CPU 实现](https://github.com/AcademySoftwareFoundation/OpenColorIO/blob/2831d2547d133b326c6e9a09726ceeb7fe46f997/src/OpenColorIO/ops/exposurecontrast/ExposureContrastOpCPU.cpp)、[参数与颜色域说明](https://github.com/AcademySoftwareFoundation/OpenColorIO/blob/2831d2547d133b326c6e9a09726ceeb7fe46f997/src/OpenColorIO/ops/exposurecontrast/ExposureContrastOpData.h)。公开 tag 不是厂商 DLL 的构建证明；本轮只确认这些局部运算与公开实现相符。

Video 的幂常数是特定 OETF 近似，不是通用 sRGB 解码。Log 的 step 可配置；公开默认值 0.088 不能代替某个 Resolve 项目的实际参数。Log 的非中性 contrast 分支还包含 pivot 和 contrast 的乘加；浮点执行顺序也不保证与化简式逐位一致。本轮没有动态测试负值、超白、alpha、contrast 非中性分支或 SIMD 近似误差。

**仍未建立 Resolve 的 HDR Global Exposure 控件到这三个函数的调用关系。** 第一轮的 OCIO 直接导入和本轮的库函数分析不能证明达芬奇原生曝光轮使用 OCIO，更不能概括整个专业调色引擎。

## SDK 运行验证

本机 SDK 明确支持 `-nogui`。启动前确认没有 Resolve 进程；研究创建一个隐藏的无界面实例，只请求只读查询，退出时核验 PID、可执行路径、启动时间和默认未命名工程，再调用官方 `Resolve.Quit()`。已确认研究进程退出。[本机 SDK headless 说明](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/README.txt:76>)。

安装附带的 `fuscript.exe` 和 `fusionscript.dll` Authenticode 状态均为 Valid；它们的哈希已记入第二轮结果。该签名核查不证明被修改过的 Resolve 整体安装完整性。

| 实际探测 | 结果与限度 |
|---|---|
| Python 3.12.0 / 3.11.9 / 3.9.25，均为 64-bit | 三者都在 SDK 导入阶段的 native extension `create_module` 出现 access violation；尚未进入 `scriptapp`。3.12 在 Resolve headless 运行时重复探测仍失败。原因未定位，不能归咎于某一个 Python 版本 |
| 官方 `fuscript.exe -l lua` | 成功连接 `bmd.scriptapp("Resolve")`，运行版本返回 21.0.0.47；因此 SDK 并非整体不可用 |
| 项目管理器只读查询 | 1 个已连接 Disk 库，当前库不是 `OC_COLOR_001_TEST`，当前工程为默认未命名工程 |
| `CreateDatabase` / `CreateProjectLibrary` 属性 | 在该项目管理器对象上均为 nil；阳性对照 `GetDatabaseList` 为 function，随机不存在方法为 nil。只证明这两个精确入口未暴露，不能推广成全部未文档化 API 均不存在 |

没有请求 `CreateProject`、`SetCurrentDatabase`、`SaveProject`、grade 修改或渲染。`project-library/` 仍为空，空目录不是实际数据库。原生 HDR Exposure setter 仍未在官方 SDK 声明中找到。`CreateProject` 在当前库里建工程，不能实现本次需要的库隔离。[官方安装 SDK 的数据库接口](<C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting/README.txt:116>)、[既有 SDK 边界记录](resolve-exposure-sdk-boundary.md)。

本轮没有 UI 自动化。当前工具不提供 Windows 原生界面操作，浏览器无法创建 Resolve 本地项目库。没有通过手写数据库、修改库连接配置或把 CDL/LUT 输出当成原生 HDR 控件来补齐缺失证据。

收尾时再次核验 `Resolve.exe`、`OpenColorIO_2_4.dll` 的原文件与只读副本；四个摘要均与第一轮固定值相同。原软件这两个文件未改动，OpenCut 嵌套仓库仍在固定基线且无改动。此检查不等于对应用启动产生的缓存、日志或整个用户数据库做了字节级审计。

## 自有画面对照参考

[参考生成器](../../experiments/reference-exposure-grid.py) 读取第一轮固定的 16 色块输入与量化后代码值，生成 −1、0、+1 EV 的 48 组工作 RGB，以及三张仅供观看的 8-bit sRGB 预览。曝光公式只用于明确约定的线性域；sRGB 解码/编码依据 [W3C 转换公式](https://www.w3.org/TR/css-color-4/#color-conversion-code)。代码没有调用 Resolve 或加载 OCIO。

| 输入 18% 灰块实际线性值 | −1 EV | 0 EV | +1 EV | 错误的编码值翻倍、再解码 |
|---|---|---|---|---|
| 0.18000033259998335 | 0.09000016629999168 | 0.18000033259998335 | 0.3600006651999667 | 0.8331083550727032 |

工作数值保存在 [参考结果](../experiments/exposure-reference-result.json)；预览保存在 `experiments/output/exposure-reference/`，只有显示时才裁切到 [0,1]。+1 档白块的工作值为 2，预览值为 255；这是本项目参考代码的行为，没有测得 Resolve 的超白保留行为。

[独立验证器](../../experiments/verify-exposure-reference.py) 用 Decimal 50 位精度逐项检查 144 个通道，并检查输入 PNG 的 CRC、位深和全部色块像素、48 个预览取样点和错误操作的差异。float64 与独立 Decimal 预期的最大误差为 `4.440892098500626e-16`。这是参考数据正确性验证，不是原生处理函数的浮点或画质验收。[验证结果](../experiments/exposure-reference-validation.json)

复现自有参考：

```powershell
python experiments/reference-exposure-grid.py
python experiments/verify-exposure-reference.py
```

这些脚本复用本机已有 NumPy / Pillow，无需新增依赖；输入不存在时先运行 `python experiments/make-exposure-inputs.py`。

## 本轮停止位置

库函数定点静态分析、Lua SDK 连通性、数值参考已得到可复核结果。专用库创建、原生控件设置、颜色管理配置和实际帧导出仍缺少可验证的操作入口。本轮在此结束受控研究，保留真实原生曝光实验为未完成项；阶段 1A 不宣布通过，阶段 1B 不据此声称复现达芬奇。

后续解锁条件是可用的 Windows 原生界面控制，或经过验证的官方隔离建库及原生 grade 输入途径。拿到真正由指定原生控件生成的 DRX 后，可研究 SDK 重放与单帧导出，但须核查具体控件、颜色设置、grade 应用状态和真实导出文件位深。产品实现继续依据公开原理和自有代码，不搬运本机反编译文本。

[第二轮独立对抗审查](../reviews/exposure-second-pass-review.md) 已核对原始字节、常量、SDK 摘要和数值参考。发现的一项 P2 标签/范围验证缺口已修复；真实样例通过，七个伪造反例被拒绝。该审查不验收原生 HDR 曝光或产品功能。
