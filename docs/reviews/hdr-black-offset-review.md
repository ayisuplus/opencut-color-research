# HDR Black Offset 独立审查

2026-10-13。范围：UI单点与原生字段差分、恢复读回、四帧执行准入和完成后的像素复算。审查者未调用原生Resolve接口。

**结论：没有未关闭P1／P2。** 准入时发现一个P2：首次新增任务只校验codec和帧范围，缺少实际输出目标及完整视频配置守卫。主执行者在启动前补齐精确目录、裸文件名、1920×1080、30fps、EXR、无alpha／音频及单片段模式，并冻结参考RGB哈希和停止条件；再次审查通过。[冻结计划](../../evidence/local/resolve-hdr-black-offset-20261013/analysis/frozen-pixel-plan.json)、[准入原型](../../evidence/local/resolve-hdr-black-offset-20261013/runtime/prototype-add-first-job.py:38)。

## 已验证

- **字段差分：** 修改后只新增 `0x86000303` generic float Parameter，值为float32 `0.009999999776482582`；原7项Parameter原始／canonical字节不变，Global曝光仍精确1。按key对齐避免数组位置移动造成假差异。去时间戳并移除唯一新增项后，完整VersionBody一致；严格解析错误全为0。[严格差分回执](../../evidence/local/resolve-hdr-black-offset-20261013/analysis/independent-black-offset-delta.json)。
- **恢复：** 校准后的中性DRX与冻结源相比，参数和去时间戳完整Body一致，无HDR分支和新增黑位key。[恢复回执](../../evidence/local/resolve-hdr-black-offset-20261013/analysis/independent-black-offset-restored.json)。
- **四帧数值：** 独立手工scanline读取4张新EXR及2张旧参照，核对哈希、RGBFloat／尺寸／帧率／无压缩、全部192个新中心通道、测量误差和48个中心差值。每张新帧6,220,800通道与OpenCV逐位相同。全幅RMSE另用分块平方和及`math.fsum`归并复算，与公开统计无差异。[独立数值回执](../../evidence/local/resolve-hdr-black-offset-20261013/analysis/independent-black-offset-numeric.json)。
- **结果边界：** 新基线与旧Rec.709 +1整幅RGB一致，重复基线逐位一致，中性恢复与旧中性逐位一致；实际新增4个独立任务ID，完成状态、计划和最终回执绑定一致。原任务保护依赖原生执行守卫及最终回执，不将这些布尔记录解释为审核了程序的所有隐含状态。

独立检查共391项通过。公开结果UTF-8／LF SHA-256为 `cc41cf511f39a2813dd229e91644cf9e650f79e3434e6d2ed4efc1ed2e1c675b`；独立数值回执SHA-256为 `b40fbfb8b57f7b8792cc650290968a71910eb7550fb7088f0f8994ebe354181a`。

## 结论措辞审查

全幅改变4,795,200个通道，最大绝对差 `0.0007291585206985474`，RMSE `0.00026293217175667996`，最小有符号差 `−2.682208730675484e−7`。采样灰阶ID0–4的正响应明显大于ID5–9约10⁻⁷量级的差值；可表述为**本夹具中暗灰响应更大，变化不是最终EXR全通道统一加0.01**。不能把这一有限样本扩展为任意素材的阈值／完整曲线，或认定微小负差必为噪声。[全部实测采样](../experiments/resolve-hdr-black-offset-result.json)。

已核对[比较脚本](../../experiments/compare-hdr-black-offset.py)和[像素报告](../research/hdr-black-offset-pixel-response.md)：输入原生grade在重放前通过严格验证，但没有逐帧渲染后DRX读回；新增grade应用后的HDR菜单没有人工重查；夹具SHA验证发生在本轮渲染后。上述限制均须保留。此次没有测量线性光量，没有建立任意黑位数值换算，也没有解释此前sRGB残差或完整Global曝光算法。
