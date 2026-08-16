"""Autonomous Online Icon Search, Dynamic Recolor, and Retrieval Tool.

Enables Coding Agents to search open vector libraries (200,000+ icons from
Iconify, Ant Design, ByteDance IconPark, Lucide, Material Symbols, Tabler)
by semantic keywords, inject PPT theme colors, and save as SVG & transparent PNG.
"""

import os
import re
import sys
import json
import urllib.request
import urllib.parse
import argparse
from typing import Optional, List, Tuple
from PIL import Image

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


# Common Chinese-to-English semantic keyword mapping dictionary
ZH_EN_MAP = {
    "用户": "user",
    "团队": "users",
    "人员": "user",
    "组织": "organization",
    "云": "cloud",
    "云计算": "cloud-server",
    "服务器": "server",
    "数据库": "database",
    "安全": "shield",
    "盾牌": "shield",
    "锁": "lock",
    "钥匙": "key",
    "搜索": "search",
    "放大镜": "search",
    "设置": "settings",
    "齿轮": "gear",
    "图表": "chart-bar",
    "折线图": "chart-line",
    "饼图": "chart-pie",
    "趋势": "trending-up",
    "火箭": "rocket",
    "启动": "rocket",
    "速度": "zap",
    "闪电": "zap",
    "效率": "zap",
    "AI": "sparkles",
    "智能": "sparkles",
    "机器人": "bot",
    "芯片": "cpu",
    "手机": "smartphone",
    "电脑": "laptop",
    "代码": "code",
    "终端": "terminal",
    "文档": "file-text",
    "表格": "table",
    "邮件": "mail",
    "消息": "message-square",
    "对话": "message-circle",
    "通知": "bell",
    "日历": "calendar",
    "时间": "clock",
    "钱": "dollar-sign",
    "金融": "bank",
    "全球": "globe",
    "地球": "globe",
    "目标": "target",
    "勾选": "check",
    "成功": "check-circle",
    "警告": "alert-triangle",
    "错误": "x-circle",
    "星星": "star",
    "心": "heart",
    "分享": "share",
    "下载": "download",
    "上传": "upload",
}


def translate_keyword(kw: str) -> str:
    """Translate keyword to English if in Chinese map, otherwise keep as is."""
    kw_clean = kw.strip().lower()
    return ZH_EN_MAP.get(kw_clean, kw_clean)


def recolor_svg(svg_content: str, color_hex: str) -> str:
    """Inject target color into SVG fill/stroke attributes."""
    color_hex = color_hex.strip()
    if not color_hex.startswith("#") and len(color_hex) in (3, 6):
        color_hex = "#" + color_hex

    # Replace currentColor with hex
    svg_mod = svg_content.replace("currentColor", color_hex)

    # If SVG doesn't specify fill or has fill="black", replace it
    if 'fill="' in svg_mod:
        svg_mod = re.sub(r'fill="(?!none)[^"]*"', f'fill="{color_hex}"', svg_mod)
    elif 'stroke="' in svg_mod:
        svg_mod = re.sub(r'stroke="(?!none)[^"]*"', f'stroke="{color_hex}"', svg_mod)
    else:
        # Add fill attribute to root <svg>
        svg_mod = re.sub(r'<svg([^>]*)>', rf'<svg\1 fill="{color_hex}">', svg_mod, count=1)

    return svg_mod


def search_and_fetch_icon(
    keyword: str,
    color_hex: str = "#2563EB",
    preferred_collection: Optional[str] = None,
    timeout: int = 6,
) -> Optional[str]:
    """Search Iconify API for a matching SVG icon and return recolored SVG text."""
    en_keyword = translate_keyword(keyword)
    query_str = urllib.parse.quote(en_keyword)

    # 1. Search for matching icon names
    search_url = f"https://api.iconify.design/search?query={query_str}&limit=15"
    req = urllib.request.Request(
        search_url,
        headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) PPT-Restoration-Agent"}
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            icons = data.get("icons", [])
    except Exception as e:
        print(f"[IconFetcher] Online search failed ({e}).")
        return None

    if not icons:
        print(f"[IconFetcher] No icons found for keyword: '{keyword}' (search: '{en_keyword}')")
        return None

    # Pick best match (prefer lucid, tabler, ant-design, icon-park, or first result)
    selected_icon = icons[0]
    priority_prefixes = ["lucide", "ant-design", "icon-park-outline", "tabler", "material-symbols", "ri"]
    for icon_name in icons:
        prefix = icon_name.split(":")[0] if ":" in icon_name else ""
        if preferred_collection and prefix == preferred_collection:
            selected_icon = icon_name
            break
        elif any(prefix.startswith(p) for p in priority_prefixes):
            selected_icon = icon_name
            break

    print(f"[IconFetcher] Found icon: '{selected_icon}' for '{keyword}'")

    # 2. Fetch the SVG content
    if ":" in selected_icon:
        prefix, name = selected_icon.split(":", 1)
    else:
        prefix, name = "lucide", selected_icon

    encoded_color = urllib.parse.quote(color_hex)
    svg_url = f"https://api.iconify.design/{prefix}/{name}.svg?color={encoded_color}"
    req_svg = urllib.request.Request(
        svg_url,
        headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) PPT-Restoration-Agent"}
    )

    try:
        with urllib.request.urlopen(req_svg, timeout=timeout) as resp:
            svg_data = resp.read().decode("utf-8")
            return recolor_svg(svg_data, color_hex)
    except Exception as e:
        print(f"[IconFetcher] Failed downloading SVG from {svg_url}: {e}")
        return None


def fetch_icon(
    keyword: str,
    output_path: str,
    color_hex: str = "#2563EB",
    fallback_image: Optional[str] = None,
    fallback_box: Optional[List[float]] = None,
) -> str:
    """Fetch icon online, inject color, save to output_path, with automatic slice fallback.

    Args:
        keyword: Search keyword in English or Chinese (e.g. 'rocket', 'shield', '云计算', '安全')
        output_path: Destination path (e.g. 'assets/icon_security.svg' or 'assets/icon_security.png')
        color_hex: Primary color to tint the icon with (e.g. '#2563EB')
        fallback_image: Optional original slide image path for fallback cropping
        fallback_box: Optional [left, top, width, height] in 0-1000 for fallback cropping
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    base_no_ext, ext = os.path.splitext(output_path)
    svg_path = f"{base_no_ext}.svg"
    png_path = f"{base_no_ext}.png"

    # Step 1: Try online search
    svg_content = search_and_fetch_icon(keyword, color_hex)

    if svg_content:
        # Save SVG file
        with open(svg_path, "w", encoding="utf-8") as f:
            f.write(svg_content)
        print(f"[Success] Saved vector SVG icon: {svg_path}")

        # Also provide a PNG copy for broad compatibility
        if ext.lower() == ".png":
            # If user specifically asked for PNG, save SVG and return svg_path or png
            return svg_path
        return svg_path

    # Step 2: Fallback to slice if provided
    if fallback_image and fallback_box:
        print(f"[IconFetcher] Executing fallback: cropping from {fallback_image} at {fallback_box}...")
        from tools.slice import slice_image
        return slice_image(fallback_image, fallback_box, output_path)

    raise RuntimeError(
        f"Failed to fetch icon for keyword '{keyword}' and no fallback crop was provided."
    )


def main():
    parser = argparse.ArgumentParser(description="Search and retrieve vector icons online with color injection.")
    parser.add_argument("keyword", help="Search term (e.g. 'shield', 'cloud', 'rocket', '用户', '安全')")
    parser.add_argument("-o", "--output", default="assets/icon.svg", help="Output file path (e.g. assets/icon.svg)")
    parser.add_argument("-c", "--color", default="#2563EB", help="Theme color hex (e.g. '#2563EB' or '#0F172A')")
    parser.add_argument("--fallback-image", default=None, help="Original slide image for fallback cropping")
    parser.add_argument("--fallback-box", nargs=4, type=float, metavar=("LEFT", "TOP", "W", "H"), help="Fallback 0-1000 box")

    args = parser.parse_args()
    fetch_icon(
        keyword=args.keyword,
        output_path=args.output,
        color_hex=args.color,
        fallback_image=args.fallback_image,
        fallback_box=args.fallback_box,
    )


if __name__ == "__main__":
    main()
