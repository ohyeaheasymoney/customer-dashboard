"""Business Initiatives sub-tab — 6 sections of strategic content."""

import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk
import database as db
from tabs.workbook.base_subtab import BaseSubTab, COLORS

SECTIONS = [
    "Corporate Objectives",
    "Business Objectives",
    "Risks / Challenges",
    "Desired Outcomes",
    "Technology Priorities",
    "Proposed Solutions",
]


class BusinessInitiativesTab(BaseSubTab):
    def __init__(self, parent, conn, customer_id, app):
        super().__init__(parent, conn, customer_id, app)
        self._section_widgets = {}
        self._build_ui()

    def _build_ui(self):
        for section in SECTIONS:
            card = self.make_card()
            header = ctk.CTkFrame(card, fg_color="transparent")
            header.pack(fill="x", padx=18, pady=(14, 8))
            ctk.CTkLabel(header, text=section,
                         font=ctk.CTkFont(size=13, weight="bold"),
                         text_color=COLORS["text"]).pack(side="left")
            ctk.CTkButton(header, text="+ Add Item", width=90, height=28,
                          corner_radius=6,
                          font=ctk.CTkFont(size=11),
                          command=lambda s=section: self._add_item(s)).pack(
                side="right")

            ctk.CTkFrame(card, fg_color=COLORS["border"], height=1).pack(
                fill="x", padx=18)

            items_frame = ctk.CTkFrame(card, fg_color="transparent")
            items_frame.pack(fill="x", padx=18, pady=(8, 16))

            self._section_widgets[section] = items_frame

    def refresh(self):
        for section, frame in self._section_widgets.items():
            for w in frame.winfo_children():
                w.destroy()

            items = db.get_business_initiatives(self.conn, self.customer_id,
                                                section)
            if not items:
                ctk.CTkLabel(frame, text="No items yet",
                             font=ctk.CTkFont(size=11),
                             text_color=COLORS["text_dim"]).pack(
                    anchor="w", pady=4)
                continue

            for item in items:
                row = ctk.CTkFrame(frame, fg_color="transparent")
                row.pack(fill="x", pady=2)

                ctk.CTkLabel(row, text=item["content"],
                             font=ctk.CTkFont(size=12),
                             text_color=COLORS["text"],
                             wraplength=500, justify="left").pack(
                    side="left", fill="x", expand=True, anchor="w")

                ctk.CTkButton(row, text="Edit", width=50, height=24,
                              corner_radius=4,
                              font=ctk.CTkFont(size=10),
                              fg_color=COLORS["btn_secondary"],
                              hover_color=COLORS["btn_secondary_hover"],
                              command=lambda iid=item["id"], s=section, c=item["content"]: self._edit_item(iid, s, c)).pack(
                    side="right", padx=(4, 0))
                ctk.CTkButton(row, text="Del", width=40, height=24,
                              corner_radius=4,
                              font=ctk.CTkFont(size=10),
                              fg_color=COLORS["danger"],
                              hover_color=COLORS["danger_hover"],
                              command=lambda iid=item["id"]: self._delete_item(iid)).pack(
                    side="right", padx=(4, 0))

    def _add_item(self, section):
        InitiativeItemDialog(self, self.conn, self.customer_id, section,
                             on_save=self.refresh)

    def _edit_item(self, item_id, section, current_content):
        InitiativeItemDialog(self, self.conn, self.customer_id, section,
                             item_id=item_id, current_content=current_content,
                             on_save=self.refresh)

    def _delete_item(self, item_id):
        if self.confirm_delete("initiative item"):
            db.delete_business_initiative(self.conn, item_id)
            self.refresh()


class InitiativeItemDialog(ctk.CTkToplevel):
    def __init__(self, parent, conn, customer_id, section,
                 item_id=None, current_content="", on_save=None):
        super().__init__(parent)
        self.conn = conn
        self.customer_id = customer_id
        self.section = section
        self.item_id = item_id
        self.on_save = on_save

        self.title(f"{'Edit' if item_id else 'Add'} — {section}")
        self.geometry("500x260")
        self.resizable(False, False)
        self.after(100, self.grab_set)

        ctk.CTkLabel(self, text=section,
                     font=ctk.CTkFont(size=14, weight="bold")).pack(
            anchor="w", padx=24, pady=(20, 8))

        self.text = ctk.CTkTextbox(self, height=120,
                                   fg_color=COLORS["bg"],
                                   text_color=COLORS["text"],
                                   corner_radius=8, border_width=1,
                                   border_color=COLORS["border"],
                                   font=ctk.CTkFont(size=12))
        self.text.pack(fill="x", padx=24, pady=4)
        if current_content:
            self.text.insert("0.0", current_content)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=24, pady=(12, 16))
        ctk.CTkButton(btn_frame, text="Cancel", width=90,
                      fg_color=COLORS["btn_secondary"],
                      hover_color=COLORS["btn_secondary_hover"],
                      corner_radius=8, command=self.destroy).pack(
            side="right", padx=(8, 0))
        ctk.CTkButton(btn_frame, text="Save", width=90, corner_radius=8,
                      command=self._save).pack(side="right")

    def _save(self):
        content = self.text.get("0.0", "end").strip()
        if not content:
            messagebox.showwarning("Validation", "Content cannot be empty.",
                                   parent=self)
            return
        if self.item_id:
            db.update_business_initiative(self.conn, self.item_id, content)
        else:
            db.add_business_initiative(self.conn, self.customer_id,
                                       self.section, content)
        self.destroy()
        if self.on_save:
            self.on_save()
