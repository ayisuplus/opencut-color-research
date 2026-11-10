# HDR近零曝光：独立复核

2026-10-13。独立审查覆盖输入grade、冻结六帧计划／原型、五份原生DRX读回、六张EXR与有限差分，以及随后明确标注的事后48通道参考值分析。审查者没有调用原生接口或新增渲染。

**结论：没有未关闭P1／P2。** 本轮资料支持有限点的共同偏移及条件参考值线索，不能宣布完整公式、数学不连续或内部旁路。已核对[研究报告](../research/hdr-near-zero-response.md)保留这些边界，并将事后估计与预先冻结观测分开。

## 输入、执行准入与原生读回

- 四份非零输入只有唯一Global `gainjz` 的float32载荷改变，精确为±2⁻¹⁰、±2⁻¹⁴。其他解压字节、外层XML及第二压缩Body不变，黑场偏移key不存在；严格解析错误为0。[独立输入验证](../../evidence/local/resolve-hdr-near-zero-20261013/analysis/independent-input-validation.json)。
- 准入时核对两份原型编译、嵌入快照与冻结计划一致、六份输入及夹具哈希、空输出／读回目录。原17项任务完整对象和新增ID集合受守卫保护；实际新增任务的目录、裸文件名、格式／尺寸／帧率和导出开关在启动前验证。计划上限六帧，零档和最终中性须匹配冻结RGB。[冻结计划](../../evidence/local/resolve-hdr-near-zero-20261013/analysis/frozen-near-zero-plan.json)。
- 五份原生DRX均绑定实际完成回执、来源及读回文件哈希；精确数值保留，只有零档省略零标量，所有其余参数及节点身份一致。Body0的`HasCorrection`一直为true，Body1一直为false；小档位工具列表None不能作为旁路证明。[独立原生读回验证](../../evidence/local/resolve-hdr-near-zero-20261013/analysis/independent-native-readback-validation.json)。

## 六帧独立复算

手工解析六张未压缩RGBFloat scanline EXR，核对结构、30fps、1920×1080及全部哈希；每帧6,220,800通道与OpenCV逐位一致。核对288个中心通道、测量统计、全图与灰阶／彩色分层的偶分量、奇分量、奇分量除步长、两尺度奇分量差，以及冻结BT.709候选预测／残差。BT.709另用独立标量公式，RMSE用分块平方和及`math.fsum`复算。

共553项检查通过，统计最大复算差为 `1.1102230246251565e−16`。独立比较所用 `1e−15` 只容纳算术实现舍入差，不是实验噪声模型或候选等价容差。[私有完整回执](../../evidence/local/resolve-hdr-near-zero-20261013/analysis/independent-near-zero-numeric.json)，SHA-256 `ff65bc04252d6ccba05effae55a3b4bf21ae8e72103a0a16a49fc93fbfea9069`。

两步长的全图中心偏离最大值均为 `0.0008299350738525391`；奇分量最大值分别为 `0.0003350377082824707` 和 `0.0000209808349609375`。`H_large−16H_small`最大绝对差为 `1.8477439880371094e−6`。这些值支持当前两尺度样本存在共同偏移，不能从有限点推导极限、真实阈值或严格线性。[公开六帧结果](../experiments/resolve-hdr-near-zero-result.json)的UTF-8／LF SHA-256为 `bd4bf5b3415b68ade48f64adcf4aed8dbc61edcf8d54c822a6a6b91808068f21`。

## 事后参考值分析

独立标量复算从小正负档估计的48个B值、正负来源差、零外推误差、四个目标档的预测／残差及灰彩分层。共488项检查通过，最大算术差 `2.710505431213761e−20`。四个目标的最大残差分别为 `1.5714196599514452e−7`、`1.3370635731924096e−7`、`2.9616989150049733e−7`、`9.256330435469806e−8`。[私有事后复算](../../evidence/local/resolve-hdr-near-zero-20261013/analysis/independent-nonzero-reference-validation.json)，SHA-256 `1e08c17002b4131c25e931d359214eec78d91309fdccd41ecc1bea45a1d53e23`。

该结果估计了48个样本依赖参考量，没有提供任意输入到B的函数。旧±1不参与B数值估计，但早已被观察过；不能称为盲测或前瞻留出。零外推仍不吻合。负B和超1值采用候选的代数延伸；保留微负值、局部抑制未选中幂分支warning、最终finite断言的处理一致，未偷偷裁切数据。[事后脚本](../../experiments/check-hdr-nonzero-reference.py)与[结果](../experiments/hdr-nonzero-reference-result.json)。

## 保留的限制

原生读回来自渲染前的抓取，最终恢复及端点RGB不审计全应用的隐含状态。该轮未新增HDR菜单或UI小数显示见证。大量同色块像素不是独立样本。Rec.709条件上的数值一致性不推广到sRGB、未知颜色、视频时域或物理EV。后续须研究B的输入来源并冻结新验证，而不是把这些估计参考量作为产品曝光公式。
