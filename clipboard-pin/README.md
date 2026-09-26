# 剪贴板「悬浮中转 + 悬浮剪贴板」补丁工具

对标 uTools 剪贴板 v4.3.2 的悬浮中转能力，为本机安装的 clipboard 插件
（clipboard-1.3.2）提供的注入式补丁工具。**这是个人使用的过渡方案**——
正式形态是以源码方式向 ZToolsCenter/ZTools-plugins 的 plugins/clipboard
贡献功能（见 docs/PR-draft.md 的预告部分）。

## 功能清单（与 uTools 对标）

| 功能       | 说明                                                                  |
| ---------- | --------------------------------------------------------------------- |
| 中转站窗口 | 常驻复用、右下角 360px、置顶、无边框透明圆角                          |
| 内容累积   | 多条钉住内容共存于一个窗口，collect/<hash> 持久化（重启不丢）         |
| 交互       | 双击条目=复制并粘贴到当前活动窗口；文本点击展开/收起                  |
| 拖出       | 按住条目拖动即进入系统拖拽（文本→临时 txt、图片→png）                 |
| 历史       | 「历史」页签实时浏览剪贴板历史，可搜索，逐条「钉住」加入中转站        |
| 特征码     | pindata：选中文字/图片/文件→悬浮中转；pinscreen：关键词「悬浮剪贴板」 |
| 入口       | 剪贴板侧边栏图钉按钮、记录右键菜单「悬浮中转」                        |

## 使用

```bash
python clipboard-pin/patch-clipboard-pin.py
```

- 脚本可重复执行：检测到旧补丁会自动从原始备份重打最新版
- 需要本机 node（脚本会优先用 PATH 里的，回退 D:\Software_Data\nodejs）
- 打完后重启 ZTools 生效

## 文件说明

| 文件                   | 作用                                                    |
| ---------------------- | ------------------------------------------------------- |
| patch-clipboard-pin.py | 补丁主脚本（解包→注入→校验→重打包→同步注册表）          |
| pin.html               | 悬浮窗页面（中转站 + 历史双页签）                       |
| pin-preload.js         | 子窗口 preload（fs 拖出转换 + 父窗口 IPC 数据接收）     |
| update-registry.js     | 把 pindata/pinscreen 特征码同步进插件注册表并清指令缓存 |
| \_asar_req.js          | node 调用 @electron/asar 的解包/打包桥                  |

## 回滚

`~/.ztools/plugins/clipboard-1.3.2-a0321049.asar.pre-pin.bak` 复制回原文件。
