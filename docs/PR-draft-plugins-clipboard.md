# PR 草稿 — 发给上游 ZToolsCenter/ZTools-plugins

> 目标仓库：ZToolsCenter/ZTools-plugins
> 分支：`feat/clipboard-pin-screen`（fork：PepinoLatte/ZTools-plugins）
> 只改动 `plugins/clipboard`，1 个提交。

---

## 标题

```
feat: 剪贴板新增悬浮中转与悬浮剪贴板（对标 uTools）
```

## 描述（直接粘贴）

你好！参照 uTools 剪贴板 v4.3.2 的悬浮中转能力，为 clipboard 插件实现了
「悬浮中转站 + 悬浮剪贴板」两组功能，源码级实现（新增 PinScreen 组件与
usePinScreen 组合函数，入口按 `?way=` 分流，主界面零侵入），希望能回馈上游。

### 功能一：悬浮中转（常驻中转站窗口）

- 入口：侧边栏图钉按钮（钉当前活动记录）、记录右键菜单「悬浮中转」、
  特征码 `pindata`（选中文字/图片/文件 → 文本/图像/文件悬浮中转）
- 窗口：`createBrowserWindow` 创建的置顶、无边框、透明圆角小窗（右下角、
  宽 360、高 65% 工作区），**常驻复用**——已打开时再次钉入通过
  `webContents.send` 追加，不重复建窗
- 内容累积：钉住的多条内容以卡片列表共存，`collect/<hash>` 写入插件数据库
  **持久化**（重启不丢，对标 uTools collectPutDB）
- 每条记录：复制（同类型合并语义，与主面板一致）、删除（带确认弹窗，
  可勾选「不再弹出」）、**按住拖动**即转换为临时文件进入系统拖拽
  （文本→tmp txt、图片→png，对标 uTools convertDragFiles + startDrag）
- 双击任意条目 = 复制并粘贴到当前活动窗口

### 功能二：悬浮剪贴板（实时历史悬浮窗）

- 特征码 `pinscreen`（关键词「悬浮剪贴板 / 悬浮剪切板」）
- 3 秒轮询最近 100 条历史，支持关键词搜索
- 每条记录：钉住（加入中转站）、复制；点击条目 = 复制并粘贴到当前窗口
- 双页签设计：中转站 / 历史在同一窗口内切换，历史里看中的内容一键
  「钉住」进中转站

### 实现说明

- `src/main.js` 按 `?way=` 分流：悬浮模式渲染 `PinScreen.vue`，
  主界面代码路径零改动（悬浮窗口由 session 级 preload 提供 ztools API）
- `public/pin-preload.js`：子窗口 preload（`contextIsolation:false` 下提供
  fs 拖出转换与 `zt-pin-data` IPC 数据接收桥）
- `useSelection` 补充导出 `activeItem`，供图钉按钮定位当前活动记录
- 窗口定位：光标所在显示器右下角（对标 uTools），多显示器安全
- plugin.json 新增 `pindata` / `pinscreen` 两个特征码

### 测试情况

- `vite build` 通过；`node --test` 全部通过
- 实机验证：主面板图钉/右键钉住、窗口复用与追加、持久化重启恢复、
  文本/图片/文件三类内容渲染与复制、拖出、双击粘贴、悬浮剪贴板实时刷新

### 需要作者定夺的点

1. 中转站记录目前独立于「我的收藏」（collect/ 前缀），是否希望与收藏打通
2. 悬浮窗视觉是我按 uTools 风格写的深色玻璃样式，如需适配主题系统我可以调整
3. 删除确认的「不再弹出」记忆目前存 localStorage，如作者偏好走插件数据库可以改
