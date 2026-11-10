# HDR 颜色上下文：当前官方接口缺口

2026-10-13。在第七轮32张测量帧完成后，进一步只读查询本机官方MCP工具目录、21.1.1 API声明以及当前脚本窗口。没有设置Gamma、应用grade、创建窗口或渲染任务。

**结果：当前安装所公开的查询接口，没有找到直接读取HDR palette「色彩空间」「Gamma」选中项的getter。** 官方MCP状态查询确认Resolve运行中，版本21.1.1；完整构建号仍以第七轮SDK断言21.1.1.10为准。

实际 `tools/list` 返回14项，包括API/文档查询、run_script、DCTL/LUT工具；没有直接菜单或界面截图工具。`search_scripting_api` 在主API中查询 `HDR|gamma|palette`，返回项目/时间线Gamma、HDR母版/监看及导出GammaTag等字段。这些字段不是HDR菜单选中项。另取得Graph的完整11个方法声明；GetToolsInNode读取使用中的工具名称，不能据它判断HDR的色彩空间/Gamma。

UI查询返回 `UIManager.FindWindow/FindWindows`。官方目录说明ui_api用于Fusion脚本界面；声明提供按ID查找窗口，没有提供Resolve调色菜单的对象或ID。依据已经读取的声明，通过官方沙箱run_script调用 `resolve.Fusion().UIManager.FindWindows()`，在003为活动工程、idle时返回0个窗口。没有猜测原生控件ID、发送窗口事件或使用Windows界面自动化。查询前后ProjectSettings和任务列表相等；没有据此声称全应用状态不变。

这个0值只描述当时的查询结果，不证明所有原生窗口不可访问，也不排除未公开接口。它没有取得005的菜单状态。原003两个「使用时间线」的人工见证不能直接充当005的见证；DRX未知int参数也不能当作菜单枚举。

[脱敏查询摘要](../experiments/resolve-hdr-api-gap-result.json)记录实际工具名、Graph方法、模式、查询范围及原始回执哈希；详细返回与脚本保存在忽略目录。该缺口不使32张实验帧失效，但限制继续解释Gamma响应和固定完整公式。

后续人工确认已完成：助手切到专用副本EXPO_005_HDR_CONTEXT后，用户确认两个菜单均为「使用时间线」。这补齐当前中性Rec.709状态的观察；官方菜单getter缺口仍在，不能据此回填过去各次渲染的界面状态。[005菜单见证](resolve-hdr-005-menu-witness.md)
