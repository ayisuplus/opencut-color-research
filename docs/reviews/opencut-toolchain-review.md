# OpenCut 现有工具链探针独立审查

2026-10-13（Asia/Shanghai）。只读研究报告、公开摘要、私有命令回执与日志，并复核当前OpenCut Git状态、锁文件和manifest；仅写本文件。没有安装、网络查询、依赖源改动、构建重跑、启动应用或实现调色。

**结论：无must-fix；可作为现有环境的失败探针记录，不能标成锁定工具链、源码编译或应用运行验收通过。** 报告、JSON、README第19入口及立项书末段均保持这一边界。

## 证据绑定

| 对象 | SHA-256 |
|---|---|
| opencut-existing-toolchain-result.json | 9d9302fae18de586c8cb94eb9bdcc7ede1c1900e53d09e7bedcfaa559d05adbe |
| 私有 opencut-prereq-20261013/result.json | 5cf357c1b5b174f2db01a0b4d1b306b19951915c73731060bff53d0ad339d7b1 |
| cargo-version.stdout.txt | b6ef6807dd96d18b833474ad68e7a23a29e562a29c67afa71a59fb9a73df0068 |
| metadata-no-deps.stdout.txt | 95af938e8f90df993ed11632a309bdc2fbfa589d8749497a63b016433cfbfcb8 |
| desktop-check.stderr.txt | 9ea428109d1ac748db2ad609ef2351e707ded242211aed276caf564c57b41c62 |

私有result与公开private_probe_result_sha256相同；三个命令的全部六份stdout/stderr文件摘要、argv和退出码均匹配。没有把未执行步骤补成成功。研究报告SHA-256为 `ea2da6d772331acd12d10c09f37a8abbebe482dd7063a565062b448774c601dc`。

只读Git复核当前HEAD仍为 `e668010778568641babef2cc40be4703ae6916d6`、status为空，当前Cargo.lock摘要 `9c512116dc592f1df0da4ca53102d22da7126d932f41e50c7bb78831dc3a9323`与回执before/after一致。当前复核不替代完整文件系统审计；前后状态仍依据原始回执。

## 结果与错误归因

真实命令显式选择已安装stable-msvc Cargo；版本输出为1.96.0、exit0。当前`.prototools`固定Rust1.97.0、Bun1.3.11、moon2.3.3，均与摘要相同；该探针不是这些pin已使用或通过的证明。rustc、Bun1.3.14和Node24.15.0为主代理同轮CLI观察；本子代理核对三份Cargo回执，没有另重跑这些版本命令或把它们当成锁定版本验收。

`metadata --offline --locked --no-deps --format-version 1`退出0，输出单一opencut-desktop 0.1.0、edition2024、resolve=null，与当前manifest一致。只证明可读取manifest/workspace元数据；没有解析完整依赖图、检查Rust源码或启用被注释的crates成员。

`check --offline --locked -p opencut-desktop --target-dir <case-target>`退出101。原文是当前替换crates-io的`tuna`索引找不到`gpui`，失败归于此次离线依赖解析；不能据此判定OpenCut源码有类型错误、所有缓存都没有gpui，或改Rust版本便必然解决。离线错误附带的“去掉offline重试”建议没有被执行。源码check、链接、UI、解码、预览、导出、性能和调色接入都未验收。

web根目录及apps/web本地node_modules当前均未见，与记录一致；这不等于整台机器没有相关工具或缓存。moon/proto只限定当前PATH未找到，报告没有写成全机器未安装，也没有从当前Bun/Node版本推断上游CI兼容。

## 保留边界

目录探针、源码证据和真实应用运行分别记录。当前无须为这次离线失败改上游源码、依赖版本或机器源配置；后续锁定工具链与依赖获取须作为另一明确步骤验证。本次没有启动UI/web服务或提前开启自研调色，阶段1A与颜色公式的既有验收条件不变。
