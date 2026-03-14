"""Entry point -- creates CTk root window and launches the app."""

import sys
import os

# Fix X11 RENDER BadLength error on Linux
os.environ.setdefault("XLIB_SKIP_ARGB_VISUALS", "1")
# Force software rendering to avoid GPU-related X11 protocol issues
os.environ.setdefault("LIBGL_ALWAYS_SOFTWARE", "1")

# Add project directory to path so imports work
sys.path.insert(0, os.path.dirname(__file__))

import customtkinter as ctk

# Disable HiDPI scaling to avoid X11 RENDER errors on some Linux systems
ctk.deactivate_automatic_dpi_awareness()

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

from app import App


def main():
    root = ctk.CTk()
    root.title("Ajay's Customer Dashboard")
    root.geometry("1200x750")
    root.minsize(960, 640)

    # Force Tk scaling to 1.0 to prevent oversized glyph rendering
    root.tk.call("tk", "scaling", 1.0)

    App(root)

    root.mainloop()


if __name__ == "__main__":
    main()
