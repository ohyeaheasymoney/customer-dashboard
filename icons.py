"""Lightweight icon helper — uses Unicode text instead of Pillow rendering
to avoid X11 RENDER protocol errors on some Linux systems.

Provides `get_icon(name, size, color)` which returns None.
Sidebar/buttons should use text-based icons via the `text` parameter instead.
"""


# Icon text map — use these as button text prefixes
ICON_TEXT = {
    "dashboard": "\u25A6",   # ▦
    "customers": "\u25C8",   # ◈
    "followups": "\u25CE",   # ◎
    "add":       "\u002B",   # +
    "export":    "\u2B61",   # ⭡
    "email":     "\u2709",   # ✉
    "backup":    "\u2B73",   # ⭳
    "settings":  "\u2699",   # ⚙
    "search":    "\u2315",   # ⌕
    "close":     "\u2715",   # ✕
    "sun":       "\u2600",   # ☀
    "moon":      "\u263E",   # ☾
}


def get_icon(name, size=20, color="#FFFFFF"):
    """Return None — icons are handled via Unicode text to avoid X11 issues."""
    return None


def get_icon_text(name):
    """Return the Unicode character for the given icon name."""
    return ICON_TEXT.get(name, "")
