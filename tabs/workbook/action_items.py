"""Action Items sub-tab — What/Who/How/When tracker with status."""

import tkinter as tk
from tkinter import messagebox
from datetime import datetime

import customtkinter as ctk
import database as db
from tabs.workbook.base_subtab import BaseSubTab, COLORS

STATUSES = ["On Track", "In Jeopardy", "At Risk", "Complete"]


class ActionItemsTab(BaseSubTab):
    def __init__(self, parent, conn, customer_id, app):
        super().__init__(parent, conn, customer_id, app)
        self._build_ui()

    def _build_ui(self):
        card = self.make_card(pad_top=16)
        self.make_card_header(card, "Action Items", [
            ("+ Add Action", self._add, {}),
        ])

        cols = ("what", "who", "how", "due_date", "status", "notes")
        widths = {"what": 180, "who": 100, "how": 140,
                  "due_date": 100, "status": 100, "notes": 180}
        self.tree, _ = self.make_treeview(card, cols, widths, height=18)

        self.tree.tag_configure("On Track",
                                background="#D1FAE5", foreground="#065F46")
        self.tree.tag_configure("In Jeopardy",
                                background="#FEF3C7", foreground="#92400E")
        self.tree.tag_configure("At Risk",
                                background="#FEE2E2", foreground="#991B1B")
        self.tree.tag_configure("Complete",
                                background="#F1F5F9", foreground="#94A3B8")

        self.make_context_menu(self.tree, [
            ("Edit", self._edit),
            None,
            ("Delete", self._delete),
        ])

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        keys = ["what", "who", "how", "due_date", "status", "notes"]
        for idx, row in enumerate(
                db.get_action_items(self.conn, self.customer_id)):
            status = row.get("status", "On Track")
            tag = status if status in STATUSES else (
                "evenrow" if idx % 2 == 0 else "oddrow")
            vals = tuple(row[k] for k in keys)
            self.tree.insert("", "end", iid=str(row["id"]),
                             values=vals, tags=(tag,))

    def _add(self):
        ActionItemDialog(self, self.conn, self.customer_id,
                         on_save=self.refresh)

    def _edit(self):
        aid = self.get_selected_id(self.tree, "action item")
        if aid:
            ActionItemDialog(self, self.conn, self.customer_id,
                             item_id=aid, on_save=self.refresh)

    def _delete(self):
        aid = self.get_selected_id(self.tree, "action item")
        if aid and self.confirm_delete("action item"):
            db.delete_action_item(self.conn, aid)
            self.refresh()


class ActionItemDialog(ctk.CTkToplevel):
    def __init__(self, parent, conn, customer_id, item_id=None, on_save=None):
        super().__init__(parent)
        self.conn = conn
        self.customer_id = customer_id
        self.item_id = item_id
        self.on_save = on_save

        self.title("Edit Action Item" if item_id else "New Action Item")
        self.geometry("500x440")
        self.resizable(False, False)
        self.after(100, self.grab_set)

        existing = None
        if item_id:
            row = conn.execute("SELECT * FROM action_items WHERE id=?",
                               (item_id,)).fetchone()
            if row:
                existing = dict(row)

        ctk.CTkLabel(self, text=self.title(),
                     font=ctk.CTkFont(size=16, weight="bold")).pack(
            anchor="w", padx=24, pady=(20, 12))

        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=24, pady=4)

        self.entries = {}
        row_defs = [
            ("What", "what", "entry"),
            ("Who", "who", "entry"),
            ("How", "how", "entry"),
            ("Due Date", "due_date", "entry"),
            ("Status", "status", "combo"),
            ("Notes", "notes", "text"),
        ]
        for i, (label, key, ftype) in enumerate(row_defs):
            ctk.CTkLabel(form, text=label, text_color=COLORS["text_dim"],
                         font=ctk.CTkFont(size=12)).grid(
                row=i, column=0, sticky="ne" if ftype == "text" else "e",
                padx=(0, 14), pady=5)
            if ftype == "combo":
                var = tk.StringVar(
                    value=existing[key] if existing else "On Track")
                w = ctk.CTkComboBox(form, values=STATUSES, variable=var,
                                    width=300, corner_radius=8)
                self.entries[key] = var
            elif ftype == "text":
                w = ctk.CTkTextbox(form, height=80,
                                   fg_color=COLORS["bg"],
                                   text_color=COLORS["text"],
                                   corner_radius=8, border_width=1,
                                   border_color=COLORS["border"],
                                   font=ctk.CTkFont(size=12))
                if existing and existing.get(key):
                    w.insert("0.0", existing[key])
                self.entries[key] = w
            else:
                w = ctk.CTkEntry(form, width=300, corner_radius=8)
                if key == "due_date" and not existing:
                    w.configure(placeholder_text="YYYY-MM-DD")
                if existing and existing.get(key):
                    w.insert(0, existing[key])
                self.entries[key] = w
            w.grid(row=i, column=1, pady=5, sticky="ew")
        form.columnconfigure(1, weight=1)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=24, pady=(8, 16))
        ctk.CTkButton(btn_frame, text="Cancel", width=90,
                      fg_color=COLORS["btn_secondary"],
                      hover_color=COLORS["btn_secondary_hover"],
                      corner_radius=8, command=self.destroy).pack(
            side="right", padx=(8, 0))
        ctk.CTkButton(btn_frame, text="Save", width=90, corner_radius=8,
                      command=self._save).pack(side="right")

    def _save(self):
        def val(key):
            v = self.entries[key]
            if isinstance(v, tk.StringVar):
                return v.get()
            if isinstance(v, ctk.CTkTextbox):
                return v.get("0.0", "end").strip()
            return v.get().strip()

        what = val("what")
        if not what:
            messagebox.showwarning("Validation", "What is required.",
                                   parent=self)
            return

        kwargs = dict(what=what, who=val("who"), how=val("how"),
                      due_date=val("due_date"), status=val("status"),
                      notes=val("notes"))

        if self.item_id:
            db.update_action_item(self.conn, self.item_id, **kwargs)
        else:
            db.add_action_item(self.conn, self.customer_id, **kwargs)

        self.destroy()
        if self.on_save:
            self.on_save()
