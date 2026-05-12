# -*- encoding: utf-8 -*-
import time
import uiautomator2 as u2
from urllib.request import urlretrieve
from hashlib import md5
from pathlib import Path
import subprocess
from typing import Optional, List
import os

from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent, ImageContent

# 设备配置
did = "192.168.1.136:5555"
d = u2.connect(did)

# 创建 FastMCP 实例
mcp = FastMCP(
    name="小红书笔记发布服务",
    host="0.0.0.0",
    port=8000,
)


def reject_upgrade():
    if d.xpath('//*[@text="发现新版本"]').exists:
        d.xpath('//*[@text="稍后再说"]').click()

    time.sleep(5)


def adb_push_image(url: str, device_serial: str = did) -> bool:
    phone_path = "/sdcard/Pictures/"

    img_ext = Path(url).suffix
    if not img_ext:
        # 兼容没有后缀的图片 url
        img_ext = ".jpg"

    img_name = md5(url.encode('utf-8')).hexdigest() + img_ext

    try:
        urlretrieve(url, img_name)
    except Exception as e:
        print("使用 urlretrive 下载图片失败", str(e), "\n")
        False
    push_cmd = ["adb", "-s", device_serial, "push", img_name, phone_path]

    try:
        result = subprocess.run(
            push_cmd, check=True, capture_output=True, text=True, encoding="utf-8")
        print("推送成功：", result.stdout)

        scan_cmd = [
            "adb", "-s", device_serial, "shell", "am", "broadcast",
            "-a", "android.intent.action.MEDIA_SCANNER_SCAN_FILE",
            "-d", f"file://{phone_path}"
        ]
        subprocess.run(scan_cmd, check=True, capture_output=True,
                       text=True, encoding="utf-8")
        print("媒体库刷新成功")

        if os.path.exists(img_name):
            os.remove(img_name)

        return True
    except subprocess.CalledProcessError as e:
        print("命令执行失败：", e.stderr)
        return False


def push_content(title: str, content: str, tags: list, pic_url: str) -> dict:
    try:
        reject_upgrade()
    except Exception as e:
        print("跳过升级异常: ", str(e), "\n")

    img_success = adb_push_image(pic_url)
    if not img_success:
        return {"success": False, "message": "推送图片失败"}

    current_app = d.app_current().get("package", "")
    if current_app != "com.xingin.xhs":
        d.app_start("com.xingin.xhs")
        time.sleep(3)

    try:
        reject_upgrade()
    except Exception as e:
        print("跳过升级异常: ", str(e), "\n")

    try:
        x = d.device_info.get("displayWidth", 0)
        x1, y1 = d(text="市集").center()
        x2, y2 = d(text="消息").center()
        x = x if x > 0 else abs(x1 - x2) + x1
        y = y1
        print(x, y)
        d.click(x, y)
        time.sleep(2)
    except Exception as e:
        return {"success": False, "message": "点击➕按钮异常", "error": str(e)}

    try:
        reject_upgrade()
    except Exception as e:
        print("跳过升级异常: ", str(e), "\n")

    try:
        d.xpath('//*[@text="从相册选择"]').click()
        time.sleep(5)
    except Exception as e:
        return {"success": False, "message": "点击从相册选择图片异常", "error": str(e)}

    try:
        reject_upgrade()
    except Exception as e:
        print("跳过升级异常: ", str(e), "\n")

    try:
        d.xpath('(//android.widget.ImageView)[4]').click()
        time.sleep(5)
    except Exception as e:
        return {"success": False, "message": "选择第一张图片异常", "error": str(e)}

    try:
        reject_upgrade()
    except Exception as e:
        print("跳过升级异常: ", str(e), "\n")

    try:
        d.xpath('//*[@content-desc="下一步"]').click()
        time.sleep(5)
    except Exception as e:
        return {"success": False, "message": "选择图片后的下一步异常", "error": str(e)}

    try:
        reject_upgrade()
    except Exception as e:
        print("跳过升级异常: ", str(e), "\n")

    try:
        d.xpath('//*[@text="下一步"]').click()
        time.sleep(5)
    except Exception as e:
        return {"success": False, "message": "图片编辑页点击下一步异常", "error": str(e)}

    try:
        reject_upgrade()
    except Exception as e:
        print("跳过升级异常: ", str(e), "\n")

    try:
        d.xpath('//*[@text="添加标题"]').set_text(title)
        time.sleep(1)
    except Exception as e:
        return {"success": False, "message": "输入标题异常", "error": str(e)}

    try:
        reject_upgrade()
    except Exception as e:
        print("跳过升级异常: ", str(e), "\n")

    full_text = content + "\n\n" + " ".join(tags)

    try:
        d.xpath('(//android.view.ViewGroup)[3]').set_text(full_text)
        time.sleep(1)
    except Exception as e:
        return {"success": False, "message": "输入正文异常", "error": str(e)}

    try:
        reject_upgrade()
    except Exception as e:
        print("跳过升级异常: ", str(e), "\n")

    try:
        d.xpath('//*[@text="完成"]').click_exists(timeout=3)
    except Exception:
        pass

    try:
        reject_upgrade()
    except Exception as e:
        print("跳过升级异常: ", str(e), "\n")

    try:
        d.xpath('//*[@text="发布笔记"]').click()
        time.sleep(3)
        return {"success": True, "message": f"笔记发布成功！\n标题: {title}\n标签: {', '.join(tags)}"}
    except Exception as e:
        return {"success": False, "message": "点击发布笔记按钮异常", "error": str(e)}


@mcp.tool()
async def publish_note(title: str, content: str, tags: List[str], pic_url: str) -> List[TextContent]:
    """发布小红书笔记

    Args:
        title: 笔记标题
        content: 笔记正文内容
        tags: 标签列表，如["#威士忌", "#品鉴"]
        pic_url: 图片URL地址
    """
    try:
        result = push_content(title, content, tags, pic_url)
        if result["success"]:
            text = f"✅ 笔记发布成功！\n\n📝 标题: {title}\n📄 内容: {content[:50]}...\n🏷️ 标签: {', '.join(tags)}\n🖼️ 图片: {pic_url}"
        else:
            text = f"❌ 笔记发布失败\n\n错误信息: {result['message']}\n详细错误: {result.get('error', '无')}"
    except Exception as e:
        text = f"❌ 发布笔记时发生异常: {str(e)}"

    return [TextContent(type="text", text=text)]


@mcp.tool()
async def push_image_to_phone(image_url: str) -> List[TextContent]:
    """只推送图片到手机（不发布笔记）

    Args:
        image_url: 图片URL地址
    """
    try:
        success = adb_push_image(image_url)
        if success:
            text = f"✅ 图片推送成功！\n\n🖼️ 图片URL: {image_url}\n📂 手机路径: /sdcard/Pictures/"
        else:
            text = f"❌ 图片推送失败\n\n🖼️ 图片URL: {image_url}"
    except Exception as e:
        text = f"❌ 推送图片时发生异常: {str(e)}"

    return [TextContent(type="text", text=text)]


@mcp.tool()
async def check_device_status() -> List[TextContent]:
    """检查设备连接状态"""
    try:
        result = subprocess.run(
            ["adb", "-s", did, "get-state"], capture_output=True, text=True, timeout=5)
        adb_state = result.stdout.strip()
        current_app = d.app_current().get("package", "未知")
        device_info = d.device_info

        text = f"📱 设备状态\n\n🔗 设备ID: {did}\n📶 ADB状态: {adb_state}\n📦 当前应用: {current_app}\n📋 设备型号: {device_info.get('productName', '未知')}"
    except Exception as e:
        text = f"❌ 检查设备状态失败: {str(e)}"

    return [TextContent(type="text", text=text)]


if __name__ == "__main__":
    print("=" * 50)
    print("🚀 启动小红书笔记发布MCP服务")
    print("=" * 50)
    print(f"\n📱 连接设备: {did}")
    print(f"🌐 服务地址: http://0.0.0.0:8000")
    print(f"📡 MCP 端点: http://0.0.0.0:8000/mcp")
    print("\n🛠️ 可用工具:")
    print("  1. publish_note        - 发布小红书笔记")
    print("  2. push_image_to_phone - 推送图片到手机")
    print("  3. check_device_status - 检查设备状态")
    print("=" * 50)

    # streamable-http 模式
    mcp.run(transport="streamable-http")
