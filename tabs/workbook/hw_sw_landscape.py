"""HW/SW Landscape sub-tab — ~50-row technology landscape (pre-seeded)."""

import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk
import database as db
from tabs.workbook.base_subtab import BaseSubTab, COLORS


class HwSwLandscapeTab(BaseSubTab):
    def __init__(self, parent, conn, customer_id, app):
        super().__init__(parent, conn, customer_id, app)
        self._build_ui()

    def _build_ui(self):
        card = self.make_card(pad_top=16)
        self.make_card_header(card, "HW / SW Technology Landscape", [
            ("+ Add Item", self._add, {}),
            ("Seed Template", self._seed, {
                "fg_color": COLORS["btn_secondary"],
                "hover_color": COLORS["btn_secondary_hover"]}),
        ])

        cols = ("category", "item", "vendor", "version",
                "qty", "support_status", "notes")
        widths = {"category": 110, "item": 140, "vendor": 110,
                  "version": 80, "qty": 50, "support_status": 100, "notes": 160}
        self.tree, _ = self.make_treeview(card, cols, widths, height=22)

        self.make_context_menu(self.tree, [
            ("Edit", self._edit),
            None,
            ("Delete", self._delete),
        ])

    def refresh(self):
        rows = db.get_hw_sw_landscape(self.conn, self.customer_id)
        self.insert_rows(self.tree, rows, "id",
                         ["category", "item", "vendor", "version",
                          "qty", "support_status", "notes"])

    def _seed(self):
        db.seed_hw_sw_landscape(self.conn, self.customer_id)
        self.refresh()

    def _add(self):
        HwSwDialog(self, self.conn, self.customer_id, on_save=self.refresh)

    def _edit(self):
        iid = self.get_selected_id(self.tree, "item")
        if iid:
            HwSwDialog(self, self.conn, self.customer_id,
                       item_id=iid, on_save=self.refresh)

    def _delete(self):
        iid = self.get_selected_id(self.tree, "item")
        if iid and self.confirm_delete("technology item"):
            db.delete_hw_sw_item(self.conn, iid)
            self.refresh()


class HwSwDialog(ctk.CTkToplevel):
    def __init__(self, parent, conn, customer_id, item_id=None, on_save=None):
        super().__init__(parent)
        self.conn = conn
        self.customer_id = customer_id
        self.item_id = item_id
        self.on_save = on_save

        self.title("Edit Item" if item_id else "New Technology Item")
        self.geometry("480x440")
        self.resizable(False, False)
        self.after(100, self.grab_set)

        existing = None
        if item_id:
            row = conn.execute("SELECT * FROM hw_sw_landscape WHERE id=?",
                               (item_id,)).fetchone()
            if row:
                existing = dict(row)

        ctk.CTkLabel(self, text=self.title(),
                     font=ctk.CTkFont(size=16, weight="bold")).pack(
            anchor="w", padx=24, pady=(20, 12))

        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(fill="x", padx=24, pady=4)

        field_defs = [
            ("Category", "category"), ("Item", "item"),
            ("Vendor", "vendor"), ("Version", "version"),
            ("Qty", "qty"), ("Support Status", "support_status"),
            ("Notes", "notes"),
        ]
        self.entries = {}
        for i, (label, key) in enumerate(field_defs):
            ctk.CTkLabel(form, text=label, text_color=COLORS["text_dim"],
                         font=ctk.CTkFont(size=12)).grid(
                row=i, column=0, sticky="e", padx=(0, 14), pady=5)
            entry = ctk.CTkEntry(form, width=280, corner_radius=8)
            if existing and existing.get(key) is not None:
                entry.insert(0, str(existing[key]))
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
        try:
            vals["qty"] = int(vals["qty"]) if vals["qty"] else 0
        except ValueError:
            messagebox.showwarning("Validation", "Qty must be a number.",
                                   parent=self)
            return

        if self.item_id:
            db.update_hw_sw_item(self.conn, self.item_id, **vals)
        else:
            db.add_hw_sw_item(self.conn, self.customer_id, **vals)

        self.destroy()
        if self.on_save:
            self.on_save()
