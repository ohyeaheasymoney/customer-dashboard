"""Service Landscape sub-tab — service contracts with incumbents."""

import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk
import database as db
from tabs.workbook.base_subtab import BaseSubTab, COLORS


class ServiceLandscapeTab(BaseSubTab):
    def __init__(self, parent, conn, customer_id, app):
        super().__init__(parent, conn, customer_id, app)
        self._build_ui()

    def _build_ui(self):
        card = self.make_card(pad_top=16)
        self.make_card_header(card, "Service Landscape", [
            ("+ Add Service", self._add, {}),
        ])

        cols = ("service", "incumbent", "contract_end", "annual_value", "notes")
        widths = {"service": 180, "incumbent": 140, "contract_end": 110,
                  "annual_value": 110, "notes": 200}
        self.tree, _ = self.make_treeview(card, cols, widths, height=18)

        self.tree.heading("annual_value", text="Annual Value")
        self.tree.heading("contract_end", text="Contract End")

        self.make_context_menu(self.tree, [
            ("Edit", self._edit),
            None,
            ("Delete", self._delete),
        ])

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        for idx, row in enumerate(
                db.get_service_landscape(self.conn, self.customer_id)):
            tag = "evenrow" if idx % 2 == 0 else "oddrow"
            av = row.get("annual_value", 0) or 0
            self.tree.insert("", "end", iid=str(row["id"]),
                             values=(row["service"], row["incumbent"],
                                     row["contract_end"],
                                     f"${av:,.0f}" if av else "",
                                     row["notes"]),
                             tags=(tag,))

    def _add(self):
        ServiceDialog(self, self.conn, self.customer_id, on_save=self.refresh)

    def _edit(self):
        sid = self.get_selected_id(self.tree, "service")
        if sid:
            ServiceDialog(self, self.conn, self.customer_id,
                          service_id=sid, on_save=self.refresh)

    def _delete(self):
        sid = self.get_selected_id(self.tree, "service")
        if sid and self.confirm_delete("service"):
            db.delete_service(self.conn, sid)
            self.refresh()


class ServiceDialog(ctk.CTkToplevel):
    def __init__(self, parent, conn, customer_id, service_id=None,
                 on_save=None):
        super().__init__(parent)
        self.conn = conn
        self.customer_id = customer_id
        self.service_id = service_id
        self.on_save = on_save

        self.title("Edit Service" if service_id else "New Service")
        self.geometry("480x380")
        self.resizable(False, False)
        self.after(100, self.grab_set)

        existing = None
        if service_id:
            row = conn.execute(
                "SELECT * FROM service_landscape WHERE id=?",
                (service_id,)).fetchone()
            if row:
                existing = dict(row)

        ctk.CTkLabel(self, text=self.title(),
                     font=ctk.CTkFont(size=16, weight="bold")).pack(
            anchor="w", padx=24, pady=(20, 12))

        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(fill="x", padx=24, pady=4)

        field_defs = [
            ("Service", "service"),
            ("Incumbent", "incumbent"),
            ("Contract End", "contract_end"),
            ("Annual Value ($)", "annual_value"),
            ("Notes", "notes"),
        ]
        self.entries = {}
        for i, (label, key) in enumerate(field_defs):
            ctk.CTkLabel(form, text=label, text_color=COLORS["text_dim"],
                         font=ctk.CTkFont(size=12)).grid(
                row=i, column=0, sticky="e", padx=(0, 14), pady=5)
            entry = ctk.CTkEntry(form, width=280, corner_radius=8)
            if key == "contract_end":
                entry.configure(placeholder_text="YYYY-MM-DD")
            if existing and existing.get(key) is not None:
                val = existing[key]
                if key == "annual_value":
                    val = str(int(val)) if val and val == int(val) else str(val or "")
                entry.insert(0, str(val))
            entry.grid(row=i, column=1, pady=5, sticky="ew")
            self.entries[key] = entry
        form.columnconfigure(1, weight=1)

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
        vals = {k: e.get().strip() for k, e in self.entries.items()}
        if not vals["service"]:
            messagebox.showwarning("Validation", "Service name is required.",
                                   parent=self)
            return

        try:
            vals["annual_value"] = float(vals["annual_value"]) if vals["annual_value"] else 0
        except ValueError:
            messagebox.showwarning("Validation", "Annual value must be a number.",
                                   parent=self)
            return

        if self.service_id:
            db.update_service(self.conn, self.service_id, **vals)
        else:
            db.add_service(self.conn, self.customer_id, **vals)

        self.destroy()
        if self.on_save:
            self.on_save()
