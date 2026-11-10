# HDR 曝光候选的输入域与一手公式

日期：2026-10-13。本文记录资料阅读子任务；未运行 Resolve、SDK 或目标二进制，未修改工程、grade、OpenCut 或样本数据。数值测量与原生实验由主任务另行记录。

当前可以固定并复算三种 RGB 传递函数候选：BT.709 OETF／其约定逆式、sRGB、纯 Gamma 2.4。三者各有明确来源，不能仅凭项目设置名称认定 Resolve HDR Global Exposure 内部采用其中一种。JzAzBz 有固定版本的公开实现，但输入绝对亮度、RGB→XYZ 的输入编码及曝光作用位置尚缺原生证据；因此只形成带显式假设的候选族。序列化字段名 gainjz 本身不证明原生算法采用论文的 JzAzBz。

## 1. 来源锁定与访问限界

| 来源 | 固定版本／定位 | 本轮实际取得的证据 |
| --- | --- | --- |
| ITU-R BT.709 | BT.709-6，2015-06；印刷第 3 页 item 1.2、1.3、1.4；第 4 页 item 3.1 | 官方 PDF：OETF、原色和 D65；规范公式的 L 域为 0…1。[PDF](https://www.itu.int/dms_pubrec/itu-r/rec/bt/R-REC-BT.709-6-201506-I!!PDF-E.pdf#page=5) |
| ITU-R BT.1886 | 2011-03；印刷第 2 页 Annex 1 | 官方 PDF：显示 EOTF、Gamma 2.4、白／黑亮度和 a、b 参数。[PDF](https://www.itu.int/dms_pubrec/itu-r/rec/bt/R-REC-BT.1886-0-201103-I!!PDF-E.pdf#page=4) |
| W3C CSS Color 4 | 2026-10-09 Candidate Recommendation Draft；§10.2、§19 | 官方固定发布稿：sRGB 分段传递函数及带符号延拓、D65 RGB↔XYZ 示例矩阵。§19 示例代码属于 informative，发布稿尚非最终 Recommendation。[§10.2](https://www.w3.org/TR/2026/CRD-css-color-4-20261009/#predefined-sRGB)、[§19](https://www.w3.org/TR/2026/CRD-css-color-4-20261009/#color-conversion-code) |
| Safdar 等原论文 | Muhammad Safdar、Guihua Cui、Youn Jin Kim、Ming Ronnier Luo，2017，Optics Express 25(13):15131–15151，DOI 10.1364/OE.25.015131 | 出版方目录可核对题名、作者和页码；原文 HTML／PDF 入口当前无法取得正文，未核对论文公式编号或逐式原文。[出版方目录](https://opg.optica.org/oe/issue.cfm?issue=13&volume=25)、[DOI](https://doi.org/10.1364/OE.25.015131) |
| Colour Science 源码 | v0.4.5；commit b7abc030184bfa4940a0cc4d73b5059ca7d39fa2 | 库自身原始源码可审计；jzazbz.py 声明 Safdar 2017 及另一个 Safdar 2021／ZCAM 分支。本报告只取前者。此源码是实现证据，不替代本轮未读到的论文正文。[文件开头和文献](https://github.com/colour-science/colour/blob/b7abc030184bfa4940a0cc4d73b5059ca7d39fa2/colour/models/jzazbz.py#L1-L22) |

Colour 的版本锁定经 annotated tag v0.4.5 解析至上述 commit；代码许可声明 BSD-3-Clause，可在同一 commit 的 [LICENSE](https://github.com/colour-science/colour/blob/b7abc030184bfa4940a0cc4d73b5059ca7d39fa2/LICENSE) 查核。本文不安装或调用该库。

论文访问已作有限尝试：DOI、出版方 HTML／PDF 入口及内置浏览器；HTML 返回 “Please wait”，PDF 取读失败，内置浏览器返回不可用。到此停止该检索分支，不以第三方教程替代论文正文。

## 2. 共用候选结构：假设与已知公式分开

令 C 为单个输出 EXR RGB **编码值**，E 为本实验输入的曝光档位数值，D 为约定解码函数，F 为约定编码函数。逐通道候选定义为：

$$
\widehat C_E=F\left(2^E\,D(C)\right).
$$

这里把 E 映射为线性域倍率 2^E，是待检验模型的定义，不是对 Resolve 的结论。对 baseline 的 48 个 RGB 编码样本使用同一函数，不能把 fixture 的“原设计线性 0.18”直接替代真实 EXR 编码值，也不能仅因容器为 FLOAT EXR 就认定存储值处在物理线性光域。

为了与超白 EXR 样本比较，候选不裁切到 0…1；BT.709 在 L>1 时继续代入高段公式属于本实验的代数延拓，超出了规范表的域。候选必须记录延拓和负数策略，不能默默 clamp、加黑位或做 gamut mapping。E=0 的编解码回环也须检查；分段舍入使少数接点值存在微小误差，不能宣称全实数域精确互逆。

## 3. BT.709：标准 OETF 与固定逆式约定

**已核对标准事实。** BT.709-6 item 1.2 的非负输入公式为：

$$
F_{709}(L)=
\begin{cases}
4.5L,&0\le L<0.018,\\
1.099L^{0.45}-0.099,&0.018\le L\le1.
\end{cases}
$$

L 是规范中的归一化图像亮度，V 是电信号；item 3.1 将这一非线性预校正用于原色信号。原色 R(x=.640,y=.330)、G(.300,.600)、B(.150,.060)，白点 D65(x=.3127,y=.3290)。[BT.709-6，印刷第 3 页 item 1.2–1.4／第 4 页 item 3.1](https://www.itu.int/dms_pubrec/itu-r/rec/bt/R-REC-BT.709-6-201506-I!!PDF-E.pdf#page=5)

**逆式固定实现。** Colour 的 BT.709 wrapper 直接调用 BT.601 的同常数函数。其逆函数分支阈值取：

$$
\tau=F_{709}(0.018)=1.099(0.018)^{0.45}-0.099
 =0.08124794403514046\ldots
$$

$$
D_{709,\mathrm{Colour}}(C)=
\begin{cases}
C/4.5,&C<\tau,\\
\left((C+0.099)/1.099\right)^{1/0.45},&C\ge\tau.
\end{cases}
$$

具体依据：[BT.709 wrapper L78、L120](https://github.com/colour-science/colour/blob/b7abc030184bfa4940a0cc4d73b5059ca7d39fa2/colour/models/rgb/transfer_functions/itur_bt_709.py#L78)、[实际 encode L86–90](https://github.com/colour-science/colour/blob/b7abc030184bfa4940a0cc4d73b5059ca7d39fa2/colour/models/rgb/transfer_functions/itur_bt_601.py#L86-L90)、[实际 decode L132–142](https://github.com/colour-science/colour/blob/b7abc030184bfa4940a0cc4d73b5059ca7d39fa2/colour/models/rgb/transfer_functions/itur_bt_601.py#L132-L142)。

接点低段极限为 4.5×.018=.081，高段起点为 τ，存在约 .000247944 的小间隙；这是上面固定舍入常数的直接计算结果。因此，简单使用 C<.081 的逆分支和这里的 Colour 约定不是完全相同的函数。规范正向公式没有给出该间隙内唯一严格逆值。不要把精化的连续 α／β 常数、.081 阈值和 .018／1.099 舍入常数组合成没有记录的“标准公式”。

本轮可复算候选固定为上面的 F709、D709,Colour，再将高段延拓到大于 1；非负 baseline 无需额外负数政策。若以后有负输入，先声明新的延拓规则并单独验证，不宣称 BT.709 表已规定。

## 4. sRGB：W3C 固定公式

**已核对官方定义。** 非负分量的解码与编码为：

$$
D_s(C)=
\begin{cases}
C/12.92,&C\le0.04045,\\
\left((C+0.055)/1.055\right)^{2.4},&C>0.04045,
\end{cases}
$$

$$
F_s(L)=
\begin{cases}
12.92L,&L\le0.0031308,\\
1.055L^{1/2.4}-0.055,&L>0.0031308.
\end{cases}
$$

W3C §10.2 给出解码及负值反射延拓；§19 的 lin_sRGB／gam_sRGB 给出双向代码：负值使用 sign(x)×正分支(|x|)，不会在这些转换函数内把结果截到 0…1。因此若采用此版本，负值和超范围行为也可明确固定。[W3C §10.2](https://www.w3.org/TR/2026/CRD-css-color-4-20261009/#predefined-sRGB)、[§19 lin_sRGB／gam_sRGB](https://www.w3.org/TR/2026/CRD-css-color-4-20261009/#color-conversion-code)

sRGB 的高段虽含指数 2.4，但同时含偏移 .055、比例 1.055 和线性低段；它不等于纯 Gamma 2.4。两个舍入阈值也不制造所有接点的精确数学互逆，应保留官方常数而非凭拟合擅自调整。

## 5. 纯 Gamma 2.4 与 BT.1886 的关系

**已核对官方事实。** BT.1886 Annex 1 的显示模型为：

$$
L=a\,[\max(V+b,0)]^\gamma,\quad \gamma=2.4,
$$

$$
a=\left(L_W^{1/\gamma}-L_B^{1/\gamma}\right)^\gamma,\qquad
b=\frac{L_B^{1/\gamma}}
        {L_W^{1/\gamma}-L_B^{1/\gamma}}.
$$

L 为 cd/m²；LW、LB 是白和黑的显示亮度。它描述显示 EOTF；BT.709 item 1.2 描述源端 OETF。[BT.1886，印刷第 2 页 Annex 1](https://www.itu.int/dms_pubrec/itu-r/rec/bt/R-REC-BT.1886-0-201103-I!!PDF-E.pdf#page=4)

**本实验候选。** 明确选择黑亮度为 0、归一化白亮度为 1 后，非负值模型才化为：

$$
D_g(C)=C^{2.4},\qquad F_g(L)=L^{1/2.4}.
$$

$$
\widehat C_E=C\,2^{E/2.4}\quad(C\ge0).
$$

这是纯幂候选；不要省略黑／白标定假设后将其称为任意显示条件下的完整 BT.1886，也不要称它为 BT.709 OETF 的逆式。原生 HDR 面板的 BlackOffset=0.000 是一个 UI 控件见证，不能据此证明物理显示的 LB=0。

## 6. JzAzBz 2017：固定实现的可复算转换

以下公式逐项核对的是 Colour 固定 commit 的 **Safdar 2017 实现**。原论文正文访问限制见第 1 节，因此不标注未读到的论文公式编号，也不将实现细节声称为逐式原文确认。

### 6.1 必须先指定 XYZ 的输入域

代码明确要求 D65 下的 XYZ，并使用绝对量型的 ST 2084 变体；底层函数的 C 以 cd/m² 为单位，固定峰值参数 10000。不能把相对 XYZ(Ywhite=1) 原样输入后又称其为既定绝对亮度。[jzazbz.py L169–208](https://github.com/colour-science/colour/blob/b7abc030184bfa4940a0cc4d73b5059ca7d39fa2/colour/models/jzazbz.py#L169-L208)、[st_2084.py L57–96](https://github.com/colour-science/colour/blob/b7abc030184bfa4940a0cc4d73b5059ca7d39fa2/colour/models/rgb/transfer_functions/st_2084.py#L57-L96)

若选 BT.709／sRGB 共同的原色和 D65，把 RGB 列向量 Rlin 通过 W3C 的矩阵转成相对 XYZ，再明确引入自由标定 W：

$$
\mathbf{XYZ}_{abs}=W\,M_{RGB\to XYZ}\,\mathbf{RGB}_{lin},
$$

$$
M_{RGB\to XYZ}=
\begin{bmatrix}
506752/1228815&87881/245763&12673/70218\\
87098/409605&175762/245763&12673/175545\\
7918/409605&87881/737289&1001167/1053270
\end{bmatrix}.
$$

这里采用普通矩阵乘列向量约定。白 RGB=(1,1,1) 的相对 Y=1；W 表示此相对白被指定为多少 cd/m²。这一 W 倍率桥接包含零黑亮度的简化，是我们的候选假设；还必须说明 RGBlin 来自哪一种解码。W3C 标准 sRGB 观看条件列有白 80、黑 .20 cd/m²，不能把这些显示条件直接当作 Resolve 内部标定；也不能把项目 workingLuminance/HDR mastering 数值自动等同于 W。[W3C §10.2 观看条件／原色](https://www.w3.org/TR/2026/CRD-css-color-4-20261009/#predefined-sRGB)、[§19 lin_sRGB_to_XYZ／XYZ_to_lin_sRGB](https://www.w3.org/TR/2026/CRD-css-color-4-20261009/#color-conversion-code)

### 6.2 前向转换

固定常数：

$$
b=1.15,\ g=0.66,\ d=-0.56,
d_0=1.6295499532821566\times10^{-11}.
$$

首先：

$$
X_p=bX-(b-1)Z,\quad Y_p=gY-(g-1)X,\quad Z_p=Z.
$$

$$
\begin{bmatrix}L\\M\\S\end{bmatrix}=
M_1\begin{bmatrix}X_p\\Y_p\\Z_p\end{bmatrix},\qquad
M_1=
\begin{bmatrix}
0.41478972&0.579999&0.0146480\\
-0.2015100&1.120649&0.0531008\\
-0.0166008&0.264800&0.6684799
\end{bmatrix}.
$$

[常数／M1，L72–103](https://github.com/colour-science/colour/blob/b7abc030184bfa4940a0cc4d73b5059ca7d39fa2/colour/models/jzazbz.py#L72-L103)、[预变换与 LMS，L249–257](https://github.com/colour-science/colour/blob/b7abc030184bfa4940a0cc4d73b5059ca7d39fa2/colour/models/jzazbz.py#L249-L257)

对每个非负锥响应 T 使用修改过指数的 PQ：

$$
Q(T)=\left(
 \frac{c_1+c_2(T/10000)^n}{1+c_3(T/10000)^n}
 \right)^p,
$$

$$
n=2610/16384,\quad
p=1.7(2523/32)=134.034375,\quad
c_1=3424/4096,\ c_2=2413/128,\ c_3=2392/128.
$$

p 取 Jz 实现的修改值，不是普通 ST 2084 的 2523/32。[Jz 修改指数 L75–76](https://github.com/colour-science/colour/blob/b7abc030184bfa4940a0cc4d73b5059ca7d39fa2/colour/models/jzazbz.py#L75-L76)、[PQ 常数 L44–50](https://github.com/colour-science/colour/blob/b7abc030184bfa4940a0cc4d73b5059ca7d39fa2/colour/models/rgb/transfer_functions/st_2084.py#L44-L50)、[PQ 计算 L120–130](https://github.com/colour-science/colour/blob/b7abc030184bfa4940a0cc4d73b5059ca7d39fa2/colour/models/rgb/transfer_functions/st_2084.py#L120-L130)

$$
\begin{bmatrix}I_z\\a_z\\b_z\end{bmatrix}
=M_2\begin{bmatrix}Q(L)\\Q(M)\\Q(S)\end{bmatrix},\quad
M_2=
\begin{bmatrix}
0.5&0.5&0\\
3.524&-4.066708&0.542708\\
0.199076&1.096799&-1.295875
\end{bmatrix},
$$

$$
J_z=\frac{(1+d)I_z}{1+dI_z}-d_0.
$$

[M2，L109–123](https://github.com/colour-science/colour/blob/b7abc030184bfa4940a0cc4d73b5059ca7d39fa2/colour/models/jzazbz.py#L109-L123)、[Jz，L428–439](https://github.com/colour-science/colour/blob/b7abc030184bfa4940a0cc4d73b5059ca7d39fa2/colour/models/jzazbz.py#L428-L439)

### 6.3 逆转换

令 j=Jz+d0：

$$
I_z=\frac{j}{1+d-dj},\qquad
\begin{bmatrix}L'\\M'\\S'\end{bmatrix}
=M_2^{-1}\begin{bmatrix}I_z\\a_z\\b_z\end{bmatrix}.
$$

对每个编码锥响应 q，在分母为正的有效域内：

$$
Q^{-1}(q)=10000
\left[
 \frac{\max(q^{1/p}-c_1,0)}
      {c_2-c_3q^{1/p}}
\right]^{1/n}.
$$

将其组成 LMS，经 M1逆矩阵获得 Xp,Yp,Zp，再复原：

$$
X=\frac{X_p+(b-1)Z_p}{b},\quad
Y=\frac{Y_p+(g-1)X}{g},\quad Z=Z_p.
$$

[Jz→Iz，L503–512](https://github.com/colour-science/colour/blob/b7abc030184bfa4940a0cc4d73b5059ca7d39fa2/colour/models/jzazbz.py#L503-L512)、[Iz/LMS/XYZ 逆变换，L346–360](https://github.com/colour-science/colour/blob/b7abc030184bfa4940a0cc4d73b5059ca7d39fa2/colour/models/jzazbz.py#L346-L360)、[PQ 逆式，L199–213](https://github.com/colour-science/colour/blob/b7abc030184bfa4940a0cc4d73b5059ca7d39fa2/colour/models/rgb/transfer_functions/st_2084.py#L199-L213)

这不是任意负 XYZ／负 Jz／奇异分母输入的保证。库的 signed-power 行为与上述非负公式域应区分；未来候选须记录无效域，不可悄悄裁切后宣称匹配原生。

## 7. Jz 的“曝光”仍有多项自由假设

颜色空间转换本身不替我们选择曝光算子。本轮可明确列出的候选分支为：

| 分支 | 明确定义 | 尚需假设 |
| --- | --- | --- |
| 线性域倍率 | RGB 解码后乘 2^E，再编码；也可先转绝对 XYZ，XYZ 三分量同乘 2^E 后逆转 | RGB 解码、色度矩阵、超范围策略。若 Jz 仅作一次前后互逆转换而不修改坐标，它不引入新的曝光模型。 |
| Jz 倍率 | Jz′=Jz×2^E，az、bz 固定，再用上面的逆式 | W、RGB 解码、在 Jz 而非 Iz 处作用、色度固定策略；倍率与 UI 的对应关系仍是假设。 |
| Jz 加法 | Jz′=Jz+kE，az、bz 固定，再逆转 | 上述假设加自由系数 k；还需有效域／负值政策。不能用逐色块不同 k 将拟合“做对”。 |

这些是研究设计提出的数学候选，并非从原论文或 Blackmagic 文档取得的 Resolve 曝光公式。修改 Iz 与修改 Jz 也不同；Global Sat=1.00 不证明原生一定保持 az、bz 数值不变。只有一个叫 gainjz 的字段以及 UI ±1 见证，无法决定 W、输入 transfer、Jz 增量／倍率、色度维护方式或中间 tone/gamut 操作。

## 8. 当前决策与下一步可验证边界

**可立即复算：** 使用同一 48 个 baseline EXR 编码样本，分别固定纯 Gamma 2.4、sRGB、BT.709(Colour 逆阈值约定)，比较 F(D(C)×2^E)。另保留直接编码值 C×2^E 作为单独候选。误差报告由主任务写，不将候选名称当作原生调用证据。

**Jz 分支有条件可复算：** 前向／逆向实现、矩阵和常数已有固定源码证据；须先声明 W、解码函数、Jz／Iz 操作和色度策略，做转换回环与有效域检查，才可以报告探索性数值。原论文逐式核对当前未完成；不再展开无界检索。

**尚不能得出的结论：** 这些转换公式与样本误差都不能独立证明 Resolve 使用 JzAzBz、物理线性 EV 或某一个公开标准函数；也不能由一个固定输入和项目上下文推出所有 palette 色彩空间／Gamma 下的实现。后续若变化输入域或原生上下文，需要与现有固定实验分开记录。
