# 小红书笔记发布 MCP 服务

基于 MCP（Model Context Protocol）协议的小红书笔记自动发布服务，通过 `uiautomator2` 控制 Android 手机，实现自动化发布小红书笔记。

## 功能特性

| 工具 | 说明 |
|------|------|
| `publish_note` | 发布完整的小红书笔记（图片+标题+正文+标签） |
| `push_image_to_phone` | 仅推送图片到手机相册 |
| `check_device_status` | 检查设备连接状态 |

## 技术栈

- **Python 3.10+**
- **MCP SDK** - `mcp.server.fastmcp.FastMCP`，使用 `streamable-http` 传输模式
- **uiautomator2** - Android UI 自动化控制
- **ADB** - Android Debug Bridge，用于推送图片到手机

## 架构

```
MCP Client (Claude/AI)
        │
        ▼
┌─────────────────────┐
│  MCP Server (:8000) │
│  streamable-http    │
├─────────────────────┤
│  publish_note()     │
│  adb_push_image()   │  ──► ADB ──► 手机 (192.168.1.136:15888)
│  push_content()     │  ──► uiautomator2 ──► 小红书 APP
└─────────────────────┘
```

## 工作流程

### 发布笔记 (`publish_note`)

```
1. 下载图片 → URL 下载到本地
2. ADB Push → 推送图片到手机 /sdcard/Pictures/
3. 媒体扫描 → 触发 MediaScanner 让相册识别新图片
4. 打开小红书 → app_start("com.xingin.xhs")
5. 点击 ➕ → 计算"市集"和"消息"之间的中心点，点击发布按钮
6. 从相册选择 → 选择刚推送的图片
7. 两次下一步 → 跳过图片编辑页
8. 填写标题 → set_text(title)
9. 填写正文 → 内容 + 标签拼接后写入
10. 发布笔记 → 点击"发布笔记"按钮
```

### 关键细节

- **升级弹窗处理**：每个操作步骤前都会调用 `reject_upgrade()`，自动关闭小红书的"发现新版本"弹窗
- **发布按钮定位**：通过"市集"和"消息"两个 Tab 的坐标计算 ➕ 按钮位置，兼容不同屏幕分辨率
- **图片命名**：使用 URL 的 MD5 哈希值作为文件名，避免重复下载

## 环境准备

### 1. 安装依赖

```bash
pip install "mcp[cli]" uiautomator2
```

### 2. 准备 Android 设备

```bash
# 确保手机开启 USB 调试，并连接到 ADB
adb connect 192.168.1.136:5555

# 初始化 uiautomator2（首次需要）
python -m uiautomator2 init
```

### 3. 修改设备地址

编辑 `mcp_server.py` 顶部的设备配置：

```python
did = "192.168.1.136:5555"  # 改为你的设备地址
```

## 启动服务

```bash
python mcp_server.py
```

启动后输出：

```
==================================================
🚀 启动小红书笔记发布MCP服务
==================================================

📱 连接设备: 192.168.1.136:5555
🌐 服务地址: http://0.0.0.0:8000
📡 MCP 端点: http://0.0.0.0:8000/mcp

🛠️ 可用工具:
  1. publish_note        - 发布小红书笔记
  2. push_image_to_phone - 推送图片到手机
  3. check_device_status - 检查设备状态
==================================================
```

## MCP 客户端配置

### Claude Desktop

在 `claude_desktop_config.json` 中添加：

```json
{
  "mcpServers": {
    "小红书笔记发布": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

### Cursor / 其他 MCP 客户端

连接端点：`http://localhost:8000/mcp`

## 使用示例

通过 AI 对话调用：

> 帮我发一条小红书笔记，标题是"布纳哈本2026岛节酒发布"，内容是关于这款威士忌的品鉴记录，图片用这个链接：https://example.com/whisky.jpg，标签带上 #威士忌 #有瓶酒APP

AI 会自动调用 `publish_note` 工具完成发布。

## 项目结构

```
xhs_mcp_u2/
├── mcp_server.py    # MCP 服务主文件
├── README.md        # 项目说明
└── requirements.txt # Python 依赖
```

## 注意事项

1. 手机需要保持屏幕常亮，建议开启开发者选项中的"保持唤醒状态"
2. 小红书 APP 需要提前登录
3. 网络环境需要能访问图片 URL（服务端下载图片后通过 ADB 推送）
4. 发布频率不宜过高，避免触发小红书风控