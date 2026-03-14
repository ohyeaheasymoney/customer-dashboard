"""Tech Profile sub-tab — free-form text area."""

import customtkinter as ctk
import database as db
from tabs.workbook.base_subtab import BaseSubTab, COLORS


class TechProfileTab(BaseSubTab):
    def __init__(self, parent, conn, customer_id, app):
        super().__init__(parent, conn, customer_id, app)
        self._build_ui()

    def _build_ui(self):
        card = self.make_card(pad_top=16)
        self.make_card_header(card, "Technology Profile", [
            ("Save", self._save, {"fg_color": COLORS["primary"],
                                  "hover_color": COLORS["primary_hover"]}),
        ])

        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=18, pady=(10, 16))

        ctk.CTkLabel(body, text="Document the customer's technology environment, "
                     "architecture decisions, and infrastructure notes.",
                     font=ctk.CTkFont(size=11),
                     text_color=COLORS["text_dim"],
                     wraplength=600).pack(anchor="w", pady=(0, 8))

        self.text = ctk.CTkTextbox(body, height=500,
                                   fg_color=COLORS["bg"],
                                   text_color=COLORS["text"],
                                   corner_radius=0, border_width=1,
                                   border_color=COLORS["border"],
                                   font=ctk.CTkFont(size=12))
        self.text.pack(fill="both", expand=True)

    def refresh(self):
        data = db.get_text_section(self.conn, self.customer_id, "tech_profile")
        self.text.delete("0.0", "end")
        if data and data.get("content"):
            self.text.insert("0.0", data["content"])

    def _save(self):
        content = self.text.get("0.0", "end").strip()
        db.save_text_section(self.conn, self.customer_id,
                             "tech_profile", content)
        from tkinter import messagebox
        messagebox.showinfo("Saved", "Technology profile saved.")
