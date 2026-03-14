"""Programmatic icon generation using Pillow (PIL).

Provides `get_icon(name, size, color)` which returns a CTkImage
built from simple geometric shapes drawn on a transparent background.
"""

from PIL import Image, ImageDraw
import customtkinter as ctk
import math

# Cache generated icons to avoid re-drawing
_icon_cache = {}


def _draw_dashboard(draw, s, color):
    """4 small squares in a 2x2 grid."""
    m = int(s * 0.15)  # margin
    gap = int(s * 0.1)  # gap between squares
    sq = (s - 2 * m - gap) // 2  # square size
    r = max(1, int(s * 0.06))  # corner radius

    positions = [
        (m, m),
        (m + sq + gap, m),
        (m, m + sq + gap),
        (m + sq + gap, m + sq + gap),
    ]
    for x, y in positions:
        draw.rounded_rectangle([x, y, x + sq, y + sq], radius=r, fill=color)


def _draw_customers(draw, s, color):
    """Person icon: circle head + body arc."""
    cx = s // 2
    # Head
    hr = int(s * 0.18)
    hy = int(s * 0.28)
    draw.ellipse([cx - hr, hy - hr, cx + hr, hy + hr], fill=color)
    # Body
    bw = int(s * 0.36)
    by = int(s * 0.52)
    bh = int(s * 0.34)
    draw.rounded_rectangle(
        [cx - bw, by, cx + bw, by + bh],
        radius=bw, fill=color
    )


def _draw_followups(draw, s, color):
    """Clock icon: circle with two hands."""
    m = int(s * 0.12)
    cx, cy = s // 2, s // 2
    r = s // 2 - m
    lw = max(1, int(s * 0.07))

    # Outer circle
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=lw)

    # Hour hand (pointing up-right, ~2 o'clock)
    hlen = int(r * 0.5)
    angle = math.radians(-60)
    hx = cx + int(hlen * math.cos(angle))
    hy = cy + int(hlen * math.sin(angle))
    draw.line([cx, cy, hx, hy], fill=color, width=lw)

    # Minute hand (pointing up)
    mlen = int(r * 0.7)
    mx = cx
    my = cy - mlen
    draw.line([cx, cy, mx, my], fill=color, width=lw)

    # Center dot
    dr = max(1, int(s * 0.06))
    draw.ellipse([cx - dr, cy - dr, cx + dr, cy + dr], fill=color)


def _draw_add(draw, s, color):
    """Plus icon in a circle."""
    m = int(s * 0.1)
    cx, cy = s // 2, s // 2
    r = s // 2 - m
    lw = max(1, int(s * 0.07))

    # Circle
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=lw)

    # Plus
    arm = int(r * 0.55)
    draw.line([cx - arm, cy, cx + arm, cy], fill=color, width=lw + 1)
    draw.line([cx, cy - arm, cx, cy + arm], fill=color, width=lw + 1)


def _draw_export(draw, s, color):
    """Arrow pointing up from a tray (upload/export)."""
    cx = s // 2
    lw = max(1, int(s * 0.08))
    m = int(s * 0.15)

    # Arrow shaft
    top = int(s * 0.15)
    bottom = int(s * 0.62)
    draw.line([cx, top, cx, bottom], fill=color, width=lw)

    # Arrow head
    ah = int(s * 0.18)
    draw.line([cx, top, cx - ah, top + ah], fill=color, width=lw)
    draw.line([cx, top, cx + ah, top + ah], fill=color, width=lw)

    # Tray (U shape at bottom)
    ty = int(s * 0.68)
    by = s - m
    draw.line([m, ty, m, by], fill=color, width=lw)
    draw.line([m, by, s - m, by], fill=color, width=lw)
    draw.line([s - m, by, s - m, ty], fill=color, width=lw)


def _draw_email(draw, s, color):
    """Envelope shape."""
    m = int(s * 0.12)
    lw = max(1, int(s * 0.07))
    left, right = m, s - m
    top, bottom = int(s * 0.22), int(s * 0.78)
    cx = s // 2

    # Rectangle
    draw.rounded_rectangle([left, top, right, bottom], radius=max(1, int(s * 0.05)),
                           outline=color, width=lw)
    # V flap
    draw.line([left, top, cx, int(s * 0.52)], fill=color, width=lw)
    draw.line([cx, int(s * 0.52), right, top], fill=color, width=lw)


def _draw_backup(draw, s, color):
    """Download/save icon: arrow down into tray."""
    cx = s // 2
    lw = max(1, int(s * 0.08))
    m = int(s * 0.15)

    # Arrow shaft (pointing down)
    top = int(s * 0.12)
    bottom = int(s * 0.55)
    draw.line([cx, top, cx, bottom], fill=color, width=lw)

    # Arrow head
    ah = int(s * 0.18)
    draw.line([cx, bottom, cx - ah, bottom - ah], fill=color, width=lw)
    draw.line([cx, bottom, cx + ah, bottom - ah], fill=color, width=lw)

    # Tray
    ty = int(s * 0.62)
    by = s - m
    draw.line([m, ty, m, by], fill=color, width=lw)
    draw.line([m, by, s - m, by], fill=color, width=lw)
    draw.line([s - m, by, s - m, ty], fill=color, width=lw)


def _draw_settings(draw, s, color):
    """Gear icon: circle with notches around it."""
    cx, cy = s // 2, s // 2
    lw = max(1, int(s * 0.07))

    # Inner circle
    ir = int(s * 0.18)
    draw.ellipse([cx - ir, cy - ir, cx + ir, cy + ir], outline=color, width=lw)

    # Outer notches (teeth)
    num_teeth = 8
    tooth_inner = int(s * 0.28)
    tooth_outer = int(s * 0.42)
    tooth_w = max(1, int(s * 0.1))

    for i in range(num_teeth):
        angle = math.radians(i * 360 / num_teeth)
        x1 = cx + int(tooth_inner * math.cos(angle))
        y1 = cy + int(tooth_inner * math.sin(angle))
        x2 = cx + int(tooth_outer * math.cos(angle))
        y2 = cy + int(tooth_outer * math.sin(angle))
        draw.line([x1, y1, x2, y2], fill=color, width=tooth_w)


def _draw_search(draw, s, color):
    """Magnifying glass."""
    lw = max(1, int(s * 0.08))
    # Circle part
    cr = int(s * 0.28)
    ccx, ccy = int(s * 0.4), int(s * 0.4)
    draw.ellipse([ccx - cr, ccy - cr, ccx + cr, ccy + cr], outline=color, width=lw)

    # Handle
    angle = math.radians(45)
    hx1 = ccx + int(cr * math.cos(angle))
    hy1 = ccy + int(cr * math.sin(angle))
    hlen = int(s * 0.28)
    hx2 = hx1 + int(hlen * math.cos(angle))
    hy2 = hy1 + int(hlen * math.sin(angle))
    draw.line([hx1, hy1, hx2, hy2], fill=color, width=lw + 1)


def _draw_close(draw, s, color):
    """X icon."""
    m = int(s * 0.22)
    lw = max(2, int(s * 0.1))
    draw.line([m, m, s - m, s - m], fill=color, width=lw)
    draw.line([s - m, m, m, s - m], fill=color, width=lw)


def _draw_sun(draw, s, color):
    """Sun shape for light mode."""
    cx, cy = s // 2, s // 2
    lw = max(1, int(s * 0.07))

    # Center circle
    cr = int(s * 0.18)
    draw.ellipse([cx - cr, cy - cr, cx + cr, cy + cr], fill=color)

    # Rays
    num_rays = 8
    ray_inner = int(s * 0.26)
    ray_outer = int(s * 0.42)
    for i in range(num_rays):
        angle = math.radians(i * 360 / num_rays)
        x1 = cx + int(ray_inner * math.cos(angle))
        y1 = cy + int(ray_inner * math.sin(angle))
        x2 = cx + int(ray_outer * math.cos(angle))
        y2 = cy + int(ray_outer * math.sin(angle))
        draw.line([x1, y1, x2, y2], fill=color, width=lw + 1)


def _draw_moon(draw, s, color):
    """Crescent moon for dark mode."""
    m = int(s * 0.12)
    # Full circle
    draw.ellipse([m, m, s - m, s - m], fill=color)
    # Cut-out circle (offset to the right) using transparent fill
    offset = int(s * 0.25)
    cut_r = int(s * 0.32)
    cut_cx = s // 2 + offset
    cut_cy = s // 2 - int(s * 0.1)
    draw.ellipse([cut_cx - cut_r, cut_cy - cut_r, cut_cx + cut_r, cut_cy + cut_r],
                 fill=(0, 0, 0, 0))


# Registry of drawing functions
_ICON_DRAWERS = {
    "dashboard": _draw_dashboard,
    "customers": _draw_customers,
    "followups": _draw_followups,
    "add": _draw_add,
    "export": _draw_export,
    "email": _draw_email,
    "backup": _draw_backup,
    "settings": _draw_settings,
    "search": _draw_search,
    "close": _draw_close,
    "sun": _draw_sun,
    "moon": _draw_moon,
}


def _hex_to_rgba(hex_color):
    """Convert '#RRGGBB' to (R, G, B, 255)."""
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (255,)


def get_icon(name, size=20, color="#FFFFFF"):
    """Return a CTkImage for the given icon name.

    Args:
        name: Icon name (e.g. 'dashboard', 'customers', 'add', etc.)
        size: Icon dimensions in pixels (square).
        color: Hex color string for the icon drawing.

    Returns:
        customtkinter.CTkImage instance, or None if name is unknown.
    """
    cache_key = (name, size, color)
    if cache_key in _icon_cache:
        return _icon_cache[cache_key]

    drawer = _ICON_DRAWERS.get(name)
    if drawer is None:
        return None

    # Use 2x resolution for crisp rendering, scaled down by CTkImage
    render_size = size * 2
    img = Image.new("RGBA", (render_size, render_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    rgba = _hex_to_rgba(color)
    drawer(draw, render_size, rgba)

    ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(size, size))
    _icon_cache[cache_key] = ctk_img
    return ctk_img
