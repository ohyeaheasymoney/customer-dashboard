"""Application Landscape sub-tab — critical business apps."""

import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk
import database as db
from tabs.workbook.base_subtab import BaseSubTab, COLORS

CRITICALITIES = ["Mission Critical", "Business Critical", "Standard", "Low"]


class ApplicationLandscapeTab(BaseSubTab):
    def __init__(self, parent, conn, customer_id, app):
        super().__init__(parent, conn, customer_id, app)
        self._build_ui()

    def _build_ui(self):
        card = self.make_card(pad_top=16)
        self.make_card_header(card, "Application Landscape", [
            ("+ Add Application", self._add, {}),
        ])

        cols = ("app_name", "criticality", "hosting", "owner",
                "opportunities", "notes")
        widths = {"app_name": 140, "criticality": 120, "hosting": 110,
                  "owner": 100, "opportunities": 160, "notes": 160}
        self.tree, _ = self.make_treeview(card, cols, widths, height=18)

        self.tree.heading("app_name", text="Application")

        self.tree.tag_configure("Mission Critical",
                                background="#FEE2E2", foreground="#991B1B")
        self.tree.tag_configure("Business Critical",
                                background="#FEF3C7", foreground="#92400E")

        self.make_context_menu(self.tree, [
            ("Edit", self._edit),
            None,
            ("Delete", self._delete),
        ])

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        keys = ["app_name", "criticality", "hosting", "owner",
                "opportunities", "notes"]
        for idx, row in enumerate(
                db.get_application_landscape(self.conn, self.customer_id)):
            crit = row.get("criticality", "Standard")
            tag = crit if crit in ("Mission Critical", "Business Critical") else (
                "evenrow" if idx % 2 == 0 else "oddrow")
            vals = tuple(row[k] for k in keys)
            self.tree.insert("", "end", iid=str(row["id"]),
                             values=vals, tags=(tag,))

    def _add(self):
        AppDialog(self, self.conn, self.customer_id, on_save=self.refresh)

    def _edit(self):
        aid = self.get_selected_id(self.tree, "application")
        if aid:
            AppDialog(self, self.conn, self.customer_id,
                      app_id=aid, on_save=self.refresh)

    def _delete(self):
        aid = self.get_selected_id(self.tree, "application")
        if aid and self.confirm_delete("application"):
            db.delete_application(self.conn, aid)
            self.refresh()


class AppDialog(ctk.CTkToplevel):
    def __init__(self, parent, conn, customer_id, app_id=None, on_save=None):
        super().__init__(parent)
        self.conn = conn
        self.customer_id = customer_id
        self.app_id = app_id
        self.on_save = on_save

        self.title("Edit Application" if app_id else "New Application")
        self.geometry("480x420")
        self.resizable(False, False)
        self.after(100, self.grab_set)

        existing = None
        if app_id:
            row = conn.execute(
                "SELECT * FROM application_landscape WHERE id=?",
                (app_id,)).fetchone()
            if row:
                existing = dict(row)

        ctk.CTkLabel(self, text=self.title(),
                     font=ctk.CTkFont(size=16, weight="bold")).pack(
            anchor="w", padx=24, pady=(20, 12))

        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(fill="x", padx=24, pady=4)

        field_defs = [
            ("Application", "app_name", "entry"),
            ("Criticality", "criticality", "combo"),
            ("Hosting", "hosting", "entry"),
            ("Owner", "owner", "entry"),
            ("Opportunities", "opportunities", "entry"),
            ("Notes", "notes", "entry"),
        ]
        self.entries = {}
        for i, (label, key, ftype) in enumerate(field_defs):
            ctk.CTkLabel(form, text=label, text_color=COLORS["text_dim"],
                         font=ctk.CTkFont(size=12)).grid(
                row=i, column=0, sticky="e", padx=(0, 14), pady=5)
            if ftype == "combo":
                var = tk.StringVar(
                    value=existing[key] if existing else "Standard")
                w = ctk.CTkComboBox(form, values=CRITICALITIES, variable=var,
                                    width=280, corner_radius=8)
                self.entries[key] = var
            else:
                w = ctk.CTkEntry(form, width=280, corner_radius=8)
                if existing and existing.get(key):
                    w.insert(0, existing[key])
                self.entries[key] = w
            w.grid(row=i, column=1, pady=5, sticky="ew")
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
        def val(key):
            v = self.entries[key]
            return v.get().strip() if hasattr(v, 'get') and callable(getattr(v, 'get')) else v.get()

        app_name = val("app_name")
        if not app_name:
            messagebox.showwarning("Validation", "Application name is required.",
                                   parent=self)
            return

        kwargs = dict(app_name=app_name, criticality=val("criticality"),
                      hosting=val("hosting"), owner=val("owner"),
                      opportunities=val("opportunities"), notes=val("notes"))

        if self.app_id:
            db.update_application(self.conn, self.app_id, **kwargs)
        else:
            db.add_application(self.conn, self.customer_id, **kwargs)

        self.destroy()
        if self.on_save:
            self.on_save()
