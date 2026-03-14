"""Resources sub-tab — team roster with 15 roles (name/email/phone)."""

import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk
import database as db
from tabs.workbook.base_subtab import BaseSubTab, COLORS

TEAM_ROLES = [
    "Account Manager", "Account Executive", "Sales Director",
    "Solutions Engineer (SE)", "SE Manager", "Technical Architect",
    "Cloud Specialist", "Security Specialist", "Collaboration Specialist",
    "Data Center Specialist", "Networking Specialist",
    "Project Manager", "Customer Success Mgr", "Inside Sales Rep",
    "Executive Sponsor",
]


class ResourcesTab(BaseSubTab):
    def __init__(self, parent, conn, customer_id, app):
        super().__init__(parent, conn, customer_id, app)
        self._entries = {}
        self._row_ids = {}
        self._build_ui()

    def _build_ui(self):
        card = self.make_card(pad_top=16)
        self.make_card_header(card, "Account Team Resources", [
            ("Save All", self._save_all, {"fg_color": COLORS["primary"],
                                          "hover_color": COLORS["primary_hover"]}),
        ])

        grid = ctk.CTkFrame(card, fg_color="transparent")
        grid.pack(fill="x", padx=18, pady=(10, 16))

        # Column headers
        headers = ["Role", "Name", "Email", "Phone"]
        for col_idx, header in enumerate(headers):
            ctk.CTkLabel(grid, text=header,
                         font=ctk.CTkFont(size=11, weight="bold"),
                         text_color=COLORS["text_dim"]).grid(
                row=0, column=col_idx, sticky="w", padx=(0, 8), pady=(0, 6))

        for i, role in enumerate(TEAM_ROLES):
            row = i + 1
            # Alternating row color — visible entry backgrounds
            entry_bg = "#EFF6FF" if i % 2 == 0 else "#F1F5F9"
            label_color = "#F8FAFC" if i % 2 == 1 else "transparent"

            ctk.CTkLabel(grid, text=role,
                         font=ctk.CTkFont(size=11),
                         text_color=COLORS["text"],
                         fg_color=label_color,
                         corner_radius=4,
                         width=170, anchor="w").grid(
                row=row, column=0, sticky="w", padx=(0, 12), pady=2)

            name_entry = ctk.CTkEntry(grid, height=30, corner_radius=0,
                                      fg_color=entry_bg,
                                      border_color="#94A3B8",
                                      border_width=1,
                                      text_color=COLORS["text"],
                                      font=ctk.CTkFont(size=11))
            name_entry.grid(row=row, column=1, sticky="ew", padx=(0, 6), pady=2)

            email_entry = ctk.CTkEntry(grid, height=30, corner_radius=0,
                                       fg_color=entry_bg,
                                       border_color="#94A3B8",
                                       border_width=1,
                                       text_color=COLORS["text"],
                                       font=ctk.CTkFont(size=11))
            email_entry.grid(row=row, column=2, sticky="ew", padx=(0, 6), pady=2)

            phone_entry = ctk.CTkEntry(grid, height=30, corner_radius=0,
                                       fg_color=entry_bg,
                                       border_color="#94A3B8",
                                       border_width=1,
                                       text_color=COLORS["text"],
                                       font=ctk.CTkFont(size=11))
            phone_entry.grid(row=row, column=3, sticky="ew", padx=(0, 0), pady=2)

            self._entries[role] = (name_entry, email_entry, phone_entry)

        grid.columnconfigure(0, weight=0, minsize=170)
        grid.columnconfigure(1, weight=3)
        grid.columnconfigure(2, weight=3)
        grid.columnconfigure(3, weight=2)

    def refresh(self):
        # Clear all entries
        for role, (n, e, p) in self._entries.items():
            n.delete(0, "end")
            e.delete(0, "end")
            p.delete(0, "end")
        self._row_ids.clear()

        for res in db.get_account_resources(self.conn, self.customer_id):
            role = res["role"]
            if role in self._entries:
                n, e, p = self._entries[role]
                n.insert(0, res["name"] or "")
                e.insert(0, res["email"] or "")
                p.insert(0, res["phone"] or "")
                self._row_ids[role] = res["id"]

    def _save_all(self):
        for role, (n, e, p) in self._entries.items():
            name = n.get().strip()
            email = e.get().strip()
            phone = p.get().strip()
            rid = self._row_ids.get(role)

            if name or email or phone:
                db.upsert_account_resource(self.conn, self.customer_id,
                                           role, name, email, phone, rid)
            elif rid:
                # All fields cleared — delete the row
                db.delete_account_resource(self.conn, rid)

        messagebox.showinfo("Saved", "Team resources saved.")
        self.refresh()
