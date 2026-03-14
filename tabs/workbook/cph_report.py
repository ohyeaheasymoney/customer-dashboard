"""CPH Report sub-tab — T12 financial spend across categories."""

import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk
import database as db
from tabs.workbook.base_subtab import BaseSubTab, COLORS


class CphReportTab(BaseSubTab):
    def __init__(self, parent, conn, customer_id, app):
        super().__init__(parent, conn, customer_id, app)
        self._build_ui()

    def _build_ui(self):
        card = self.make_card(pad_top=16)
        self.make_card_header(card, "CPH Report — Trailing 12-Month Spend", [
            ("+ Add Category", self._add, {}),
        ])

        # Wide treeview with 12 month columns
        cols = ("category",) + tuple(f"m{i}" for i in range(1, 13)) + ("total",)
        widths = {"category": 140}
        for i in range(1, 13):
            widths[f"m{i}"] = 75
        widths["total"] = 90

        self.tree, self._tree_frame = self.make_treeview(
            card, cols, widths, height=16)

        # Rename month headings
        for i in range(1, 13):
            self.tree.heading(f"m{i}", text=f"Month {i}")
        self.tree.heading("total", text="Total")

        self.tree.tag_configure("totals_row",
                                background="#DBEAFE", foreground="#1E3A8A")

        self.make_context_menu(self.tree, [
            ("Edit", self._edit),
            None,
            ("Delete", self._delete),
        ])

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        rows = db.get_cph_report(self.conn, self.customer_id)

        grand_totals = [0.0] * 12
        for idx, row in enumerate(rows):
            month_vals = [row.get(f"month_{i}", 0) or 0 for i in range(1, 13)]
            row_total = sum(month_vals)
            for j in range(12):
                grand_totals[j] += month_vals[j]

            display = [f"${v:,.0f}" if v else "" for v in month_vals]
            tag = "evenrow" if idx % 2 == 0 else "oddrow"
            self.tree.insert("", "end", iid=str(row["id"]),
                             values=(row["category"], *display,
                                     f"${row_total:,.0f}"),
                             tags=(tag,))

        # Totals row
        if rows:
            gt = sum(grand_totals)
            display = [f"${v:,.0f}" if v else "" for v in grand_totals]
            self.tree.insert("", "end", iid="totals",
                             values=("TOTAL", *display, f"${gt:,.0f}"),
                             tags=("totals_row",))

    def _add(self):
        CphRowDialog(self, self.conn, self.customer_id, on_save=self.refresh)

    def _edit(self):
        rid = self.get_selected_id(self.tree, "category")
        if rid:
            CphRowDialog(self, self.conn, self.customer_id,
                         row_id=rid, on_save=self.refresh)

    def _delete(self):
        sel = self.tree.selection()
        if not sel or sel[0] == "totals":
            return
        rid = int(sel[0])
        if self.confirm_delete("category row"):
            db.delete_cph_row(self.conn, rid)
            self.refresh()


class CphRowDialog(ctk.CTkToplevel):
    def __init__(self, parent, conn, customer_id, row_id=None, on_save=None):
        super().__init__(parent)
        self.conn = conn
        self.customer_id = customer_id
        self.row_id = row_id
        self.on_save = on_save

        self.title("Edit CPH Row" if row_id else "New CPH Category")
        self.geometry("560x500")
        self.resizable(False, False)
        self.after(100, self.grab_set)

        existing = None
        if row_id:
            row = conn.execute("SELECT * FROM cph_report WHERE id=?",
                               (row_id,)).fetchone()
            if row:
                existing = dict(row)

        ctk.CTkLabel(self, text=self.title(),
                     font=ctk.CTkFont(size=16, weight="bold")).pack(
            anchor="w", padx=24, pady=(20, 12))

        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=24, pady=4)

        ctk.CTkLabel(form, text="Category", text_color=COLORS["text_dim"],
                     font=ctk.CTkFont(size=12)).grid(
            row=0, column=0, sticky="e", padx=(0, 14), pady=5)
        self.cat_entry = ctk.CTkEntry(form, width=200, corner_radius=0)
        if existing:
            self.cat_entry.insert(0, existing["category"])
        self.cat_entry.grid(row=0, column=1, columnspan=3, pady=5, sticky="ew")

        self.month_entries = {}
        for i in range(1, 13):
            r = ((i - 1) // 3) + 1
            c = ((i - 1) % 3)
            label_col = c * 2
            entry_col = c * 2 + 1

            ctk.CTkLabel(form, text=f"Month {i}",
                         text_color=COLORS["text_dim"],
                         font=ctk.CTkFont(size=11)).grid(
                row=r, column=label_col, sticky="e", padx=(8, 6), pady=4)
            entry = ctk.CTkEntry(form, width=90, height=28, corner_radius=0,
                                 placeholder_text="0")
            if existing:
                val = existing.get(f"month_{i}", 0) or 0
                if val:
                    entry.insert(0, str(int(val) if val == int(val) else val))
            entry.grid(row=r, column=entry_col, pady=4, sticky="ew")
            self.month_entries[i] = entry

        for c in range(6):
            form.columnconfigure(c, weight=1 if c % 2 else 0)

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
        category = self.cat_entry.get().strip()
        if not category:
            messagebox.showwarning("Validation", "Category is required.",
                                   parent=self)
            return

        months = {}
        for i in range(1, 13):
            raw = self.month_entries[i].get().strip()
            try:
                months[f"month_{i}"] = float(raw) if raw else 0
            except ValueError:
                messagebox.showwarning("Validation",
                                       f"Month {i} must be a number.",
                                       parent=self)
                return

        if self.row_id:
            db.update_cph_row(self.conn, self.row_id, category, **months)
        else:
            db.add_cph_row(self.conn, self.customer_id, category, **months)

        self.destroy()
        if self.on_save:
            self.on_save()
