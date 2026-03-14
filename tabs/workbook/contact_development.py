"""Contact Development sub-tab — relationship matrix."""

import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk
import database as db
from tabs.workbook.base_subtab import BaseSubTab, COLORS

RELATIONSHIPS = ["Supporter", "Questionable", "Non-Supporter", "Unknown"]
INFLUENCES = ["Decision Maker", "Influencer", "Coach", "End User"]


class ContactDevelopmentTab(BaseSubTab):
    def __init__(self, parent, conn, customer_id, app):
        super().__init__(parent, conn, customer_id, app)
        self._build_ui()

    def _build_ui(self):
        card = self.make_card(pad_top=16)
        self.make_card_header(card, "Contact Development", [
            ("+ Add Contact", self._add, {}),
        ])

        cols = ("name", "title", "relationship", "influence",
                "phone", "email", "notes")
        widths = {"name": 120, "title": 120, "relationship": 110,
                  "influence": 110, "phone": 100, "email": 150, "notes": 150}
        self.tree, _ = self.make_treeview(card, cols, widths, height=18)

        # Color-code by relationship
        self.tree.tag_configure("Supporter",
                                background="#D1FAE5", foreground="#065F46")
        self.tree.tag_configure("Questionable",
                                background="#FEF3C7", foreground="#92400E")
        self.tree.tag_configure("Non-Supporter",
                                background="#FEE2E2", foreground="#991B1B")

        self.make_context_menu(self.tree, [
            ("Edit", self._edit),
            None,
            ("Delete", self._delete),
        ])

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        keys = ["name", "title", "relationship", "influence",
                "phone", "email", "notes"]
        for idx, row in enumerate(db.get_contacts(self.conn, self.customer_id)):
            rel = row.get("relationship", "Unknown")
            tag = rel if rel in ("Supporter", "Questionable", "Non-Supporter") else (
                "evenrow" if idx % 2 == 0 else "oddrow")
            vals = tuple(row[k] for k in keys)
            self.tree.insert("", "end", iid=str(row["id"]),
                             values=vals, tags=(tag,))

    def _add(self):
        ContactDialog(self, self.conn, self.customer_id, on_save=self.refresh)

    def _edit(self):
        cid = self.get_selected_id(self.tree, "contact")
        if cid:
            ContactDialog(self, self.conn, self.customer_id,
                          contact_id=cid, on_save=self.refresh)

    def _delete(self):
        cid = self.get_selected_id(self.tree, "contact")
        if cid and self.confirm_delete("contact"):
            db.delete_contact(self.conn, cid)
            self.refresh()


class ContactDialog(ctk.CTkToplevel):
    def __init__(self, parent, conn, customer_id, contact_id=None,
                 on_save=None):
        super().__init__(parent)
        self.conn = conn
        self.customer_id = customer_id
        self.contact_id = contact_id
        self.on_save = on_save

        self.title("Edit Contact" if contact_id else "New Contact")
        self.geometry("480x480")
        self.resizable(False, False)
        self.after(100, self.grab_set)

        existing = None
        if contact_id:
            row = conn.execute(
                "SELECT * FROM contact_development WHERE id=?",
                (contact_id,)).fetchone()
            if row:
                existing = dict(row)

        ctk.CTkLabel(self, text=self.title(),
                     font=ctk.CTkFont(size=16, weight="bold")).pack(
            anchor="w", padx=24, pady=(20, 12))

        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=24, pady=4)

        fields = [
            ("Name", "name", "entry"),
            ("Title", "title", "entry"),
            ("Relationship", "relationship", "combo"),
            ("Influence", "influence", "combo"),
            ("Phone", "phone", "entry"),
            ("Email", "email", "entry"),
            ("Notes", "notes", "entry"),
        ]
        self.entries = {}
        for i, (label, key, ftype) in enumerate(fields):
            ctk.CTkLabel(form, text=label, text_color=COLORS["text_dim"],
                         font=ctk.CTkFont(size=12)).grid(
                row=i, column=0, sticky="e", padx=(0, 14), pady=5)
            if ftype == "combo":
                values = RELATIONSHIPS if key == "relationship" else INFLUENCES
                var = tk.StringVar(value=existing[key] if existing else values[-1])
                w = ctk.CTkComboBox(form, values=values, variable=var,
                                    width=260, corner_radius=0)
                self.entries[key] = var
            else:
                w = ctk.CTkEntry(form, width=260, corner_radius=0)
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

        name = val("name")
        if not name:
            messagebox.showwarning("Validation", "Name is required.",
                                   parent=self)
            return

        kwargs = dict(
            name=name, title=val("title"),
            relationship=val("relationship"), influence=val("influence"),
            phone=val("phone"), email=val("email"), notes=val("notes"),
        )

        if self.contact_id:
            db.update_contact(self.conn, self.contact_id, **kwargs)
        else:
            db.add_contact(self.conn, self.customer_id, **kwargs)

        self.destroy()
        if self.on_save:
            self.on_save()
