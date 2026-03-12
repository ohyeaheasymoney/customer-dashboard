"""Entry point -- creates CTk root window and launches the app."""

import sys
import os

# Add project directory to path so imports work
sys.path.insert(0, os.path.dirname(__file__))

import customtkinter as ctk

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

from app import App


def main():
    root = ctk.CTk()
    root.title("Ajay's Customer Dashboard")
    root.geometry("1200x750")
    root.minsize(960, 640)

    App(root)

    root.mainloop()


if __name__ == "__main__":
    main()
