# HDR静态与纹理坐标候选独立审查

2026-10-13（Asia/Shanghai）。本子代理只读静态提取物、清单、公开模型/数据/报告和宿主分析失败回执；独立标量复算，不调用Resolve/MCP/SDK、执行目标/PTX/cubin、安装或新增渲染。只写本审查及忽略目录中的私有带行号摘要，没有向公开文件复制完整私有kernel或把它用于OpenCut实现。

**结论：无未关闭P1/P2；静态线索与离线模型可作为事后候选记录，完整算法仍未证明。** N=1024、工作亮度代理、纹理定义及实际运行连接未验收；残差下降与零档失败都如实保存。REA宿主请求实际超时失败，不能计为宿主分析成功。

## 固定证据与修复

| 当前对象 | SHA-256 |
|---|---|
| check-hdr-texture-coordinate-candidate.py | b3aacf8f02ed0d8ff7d4d2bb6e99893bf9a462dba3730ed148bd34dba81939c0 |
| hdr-texture-coordinate-candidate.json | d21d3e26f94280f9eb98474e2f0bd3ab0c4a6911958ebbc402fa98a815af5d95 |
| hdr-static-candidate-evidence.json | f890bfb02323acdb11d3024bf485d4c9d894f437293df6e7226646b7c186a92f |
| hdr-static-texture-candidate.md | b318f13b74091fc80653f711065447b9a219f049df8c2e57dcafff156d505410 |
| 私有独立静态摘要 | 50f4c3d85e84130ce73b969aa0e7e58d1b6e8c77c762072180c96ad14d7d735b |

初始提取清单将LF文本摘要当作未注明口径的文件摘要，而entry/module实际为CRLF。发现后已明确raw/utf8_lf两种口径，双方摘要分别与真实文件匹配，行号不变。cuobjdump的function选项未限制PTX输出，原始dump实际覆盖全部sm120模块，之后才截取entry与所属模块；报告没有把约48.8MB原始输出描述为单函数。

本子代理读完1521行entry并核所用常量和控制条件，未审全部48946行模块、重新扫描主程序或重哈希大型总dump。完整字段/行号算术摘要保留在私有 `evidence/local/resolve-hdr-reference-origin-20261013/analysis/independent-hdr-candidate-static-review.md`。公开元数据与该摘要hash相同；字段偏移和完整私有变换没有迁入本报告。

四个序列化RIP相对字节候选的位移目标算术与元数据一致；这个核对不验证所有字节的真实指令边界，也不把展开信息范围等同于完整函数或实际运行xref。类型名称、sm120和本机GPU信息只支持候选定位，不证明当前Global调色选择了该PTX而非cubin/其它通路。

## 公开候选的独立算术核对

脚本只读取冻结near-zero、旧第四轮数据和公开BT.709候选函数。三个source的UTF-8/LF摘要均匹配；near-zero的F0样本与旧neutral-before逐对象相同。脚本从F0直接解码、计算共同亮度代理和纹理坐标，没有再拟合48个逐色块B。N=1024明确是看到残差后的离散假设，因此仍是同批数据的事后一致性检查，不是预设独立验证或新样本验证。

线性纹理的半texel坐标及8位小数权重有公开依据。[NVIDIA CUDA12.8.1 Linear Filtering](https://docs.nvidia.com/cuda/archive/12.8.1/cuda-c-programming-guide/index.html#linear-filtering)。内部区间、normalized/linear、端点表假设下，x=N·u−0.5给出t=q+q/(N−1)+E；中心表是消除该斜率偏差的反例。脚本确实分别构造端点理想、端点最近1/256权重、中心理想三方案，并显式clip两个纹理索引；不是把内部连续幂式无限外推到端点。

本子代理以独立JavaScript标量式从F0重算三方案、六个非零档及三次零档外推。864个非零预测通道逐值差为0；包括max/RMSE/48计数的全部统计最大复算差5.421010862427522e−20。该检查不重新解码EXR或验证近零实验的全部原生恢复过程；输入依据已发布数据及其固定摘要。

| 方案 | 旧−1最大误差 | 旧+1最大误差 | 零档外推最大误差 |
|---|---:|---:|---:|
| 1024端点理想 | 5.359470395e−6 | 9.921009968e−6 | 0.0008292995999588104 |
| 端点最近1/256权重 | 7.403240795e−6 | 1.383988362e−5 | 0.0008316346365420113 |
| 中心理想 | 6.074872683e−4 | 1.133742271e−3 | 4.440892098500626e−16 |

四个近零非零档也参与同样复算。权重量化未改善旧±1误差；端点方案零外推失败，脚本没有用事后零旁路替换该反例。近零共同参考值与真实F0不能因非零模型较接近而改称相同，预测零档不能替代实际HDR-zero数据。

工作Y=100×加权decode709(RGB)、权重0.2126/0.7152/0.0722、identity-log-plus-E表、normalized/linear/clamp sampler都是假设。报告没有把导出G直接称为内部Y，也没有把编码Y′的权重运算当作线性Y；ITU-R BT.2087只作为公开线性颜色变换背景，不能替代实际host矩阵。该标准发布页及CUDA语义已检查，本次未重新审阅ITU PDF的全部矩阵章节。

## 宿主分析失败及剩余边界

REA回执SHA-256 `a2bfaefb73e5d8d24ed7e25c5c4fb2620efcad88e3382e9ab08a4802a4aedc26`，错误为provider_timeout，operation=procedure_pseudo_code、timeout_ms=600000；独立退出回执为exit1，与公开metadata相同。没有可用宿主反编译。owned Java终止是主代理进程观察，本子代理没有重新操作/查询进程；报告已从进行中更新为实际失败，没有把请求启动冒充成功。

当前没有新增原生帧，near-zero公开输入的累计数为42，报告没有因静态/模型计算增加计数。仍缺host表width、端点/中心构造、实际上传值、filter/normalized/address设置、输入工作域、const/texture与gainjz映射、同一处理条件下的实际调用。最近权重取值仅是一种算术方案，非完整PTX/GPU模拟或已恢复硬件舍入规则；近似指令、float32纹理内容、矩阵精度、边界及噪声也未独立确定。

本轮支持继续查证候选机制，不支持认定Resolve存在采样缺陷、表长已测得1024、物理EV已确认或OpenCut应采用这条公式。静态私有资料和公开自主假设保持各自来源，完整曝光规格目标未完成。
