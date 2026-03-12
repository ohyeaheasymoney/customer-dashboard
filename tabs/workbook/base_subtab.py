"""Base class for all workbook sub-tabs with shared styling helpers."""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

import customtkinter as ctk

# Shared color constants — white + royal-blue theme
COLORS = {
    "bg": "#F0F4F8",
    "card": "#FFFFFF",
    "card_alt": "#F1F5F9",
    "border": "#E2E8F0",
    "border_strong": "#CBD5E1",
    "text": "#1E293B",
    "text_dim": "#64748B",
    "text_muted": "#94A3B8",
    "primary": "#2563EB",
    "primary_hover": "#1D4ED8",
    "primary_light": "#EFF6FF",
    "success": "#059669",
    "warning": "#D97706",
    "danger": "#DC2626",
    "danger_hover": "#B91C1C",
    "btn_secondary": "#F1F5F9",
    "btn_secondary_hover": "#E2E8F0",
    "input_bg": "#F8FAFC",
}


class BaseSubTab(ctk.CTkScrollableFrame):
    """Base class for workbook sub-tabs providing common helpers."""

    def __init__(self, parent, conn, customer_id, app):
        super().__init__(parent, fg_color=COLORS["bg"],
                         scrollbar_button_color="#CBD5E1",
                         scrollbar_button_hover_color="#94A3B8")
        self.conn = conn
        self.customer_id = customer_id
        self.app = app

    def refresh(self):
        """Override in subclass to reload data."""
        pass

    # ── UI Helpers ──────────────────────────────────────────────────

    def make_card(self, parent=None, pad_top=12):
        """Create a styled card frame with subtle border."""
        p = parent or self
        card = ctk.CTkFrame(p, fg_color=COLORS["card"], corner_radius=10,
                            border_width=1, border_color=COLORS["border"])
        card.pack(fill="x", padx=16, pady=(pad_top, 0))
        return card

    def make_card_header(self, card, title, buttons=None):
        """Add a header row with title and optional buttons to a card."""
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(16, 10))

        # Title with subtle accent dot
        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.pack(side="left")
        ctk.CTkLabel(title_frame, text="\u25CF",
                     font=ctk.CTkFont(size=8),
                     text_color=COLORS["primary"]).pack(side="left",
                                                         padx=(0, 8))
        ctk.CTkLabel(title_frame, text=title,
                     font=ctk.CTkFont(size=15, weight="bold"),
                     text_color=COLORS["text"]).pack(side="left")

        if buttons:
            for text, cmd, kwargs in buttons:
                kw = {
                    "width": 120, "height": 32, "corner_radius": 8,
                    "font": ctk.CTkFont(size=12),
                    "fg_color": COLORS["primary"],
                    "hover_color": COLORS["primary_hover"],
                }
                kw.update(kwargs)
                ctk.CTkButton(header, text=text, command=cmd, **kw).pack(
                    side="right", padx=(8, 0))

        # Separator
        ctk.CTkFrame(card, fg_color=COLORS["border"], height=1).pack(
            fill="x", padx=20)
        return header

    def make_treeview(self, card, columns, col_widths, height=10):
        """Create a styled treeview inside a card with scrollbar."""
        frame = tk.Frame(card, bg="#FFFFFF")
        frame.pack(fill="both", expand=True, padx=20, pady=(10, 18))

        tree = ttk.Treeview(frame, columns=columns, show="headings",
                            height=height)
        for col in columns:
            heading = col.replace("_", " ").title()
            tree.heading(col, text=heading)
            tree.column(col, width=col_widths.get(col, 120), minwidth=50)

        tree.tag_configure("evenrow",
                           background="#FFFFFF", foreground="#1E293B")
        tree.tag_configure("oddrow",
                           background="#F8FAFC", foreground="#1E293B")

        scroll = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        tree.pack(fill="both", expand=True, side="left")
        scroll.pack(fill="y", side="right")

        return tree, frame

    def make_context_menu(self, tree, items):
        """Create a right-click context menu for a treeview."""
        menu = tk.Menu(self, tearoff=0,
                       bg="#FFFFFF", fg=COLORS["text"],
                       activebackground=COLORS["primary"],
                       activeforeground="#FFFFFF",
                       font=("Helvetica", 10))
        for item in items:
            if item is None:
                menu.add_separator()
            else:
                label, cmd = item
                menu.add_command(label=f"  {label}", command=cmd)

        def show_menu(event):
            row = tree.identify_row(event.y)
            if row:
                tree.selection_set(row)
                menu.post(event.x_root, event.y_root)

        tree.bind("<Button-3>", show_menu)
        return menu

    def get_selected_id(self, tree, label="item"):
        """Get selected treeview item id as int, or None with warning."""
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("No Selection",
                                   f"Please select a {label}.")
            return None
        return int(sel[0])

    def confirm_delete(self, label="item"):
        """Show a delete confirmation dialog."""
        return messagebox.askyesno("Confirm Delete",
                                   f"Delete this {label}?")

    def insert_rows(self, tree, rows, id_key="id", value_keys=None):
        """Clear and re-insert rows into a treeview with alternating colors."""
        tree.delete(*tree.get_children())
        for idx, row in enumerate(rows):
            tag = "evenrow" if idx % 2 == 0 else "oddrow"
            vals = tuple(row[k] for k in value_keys) if value_keys else tuple(row.values())
            tree.insert("", "end", iid=str(row[id_key]), values=vals, tags=(tag,))
