"""Meeting Notes sub-tab — date/audience/notes log."""

import tkinter as tk
from tkinter import messagebox
from datetime import datetime

import customtkinter as ctk
import database as db
from tabs.workbook.base_subtab import BaseSubTab, COLORS


class MeetingNotesTab(BaseSubTab):
    def __init__(self, parent, conn, customer_id, app):
        super().__init__(parent, conn, customer_id, app)
        self._build_ui()

    def _build_ui(self):
        card = self.make_card(pad_top=16)
        self.make_card_header(card, "Meeting Notes", [
            ("+ Add Meeting Note", self._add, {}),
        ])

        cols = ("meeting_date", "audience", "notes")
        widths = {"meeting_date": 110, "audience": 180, "notes": 400}
        self.tree, _ = self.make_treeview(card, cols, widths, height=18)

        self.make_context_menu(self.tree, [
            ("Edit", self._edit),
            None,
            ("Delete", self._delete),
        ])

    def refresh(self):
        rows = db.get_meeting_notes(self.conn, self.customer_id)
        self.insert_rows(self.tree, rows, "id",
                         ["meeting_date", "audience", "notes"])

    def _add(self):
        MeetingNoteDialog(self, self.conn, self.customer_id,
                          on_save=self.refresh)

    def _edit(self):
        nid = self.get_selected_id(self.tree, "meeting note")
        if nid:
            MeetingNoteDialog(self, self.conn, self.customer_id,
                              note_id=nid, on_save=self.refresh)

    def _delete(self):
        nid = self.get_selected_id(self.tree, "meeting note")
        if nid and self.confirm_delete("meeting note"):
            db.delete_meeting_note(self.conn, nid)
            self.refresh()


class MeetingNoteDialog(ctk.CTkToplevel):
    def __init__(self, parent, conn, customer_id, note_id=None, on_save=None):
        super().__init__(parent)
        self.conn = conn
        self.customer_id = customer_id
        self.note_id = note_id
        self.on_save = on_save

        self.title("Edit Meeting Note" if note_id else "New Meeting Note")
        self.geometry("520x400")
        self.resizable(False, False)
        self.after(100, self.grab_set)

        existing = None
        if note_id:
            row = conn.execute("SELECT * FROM meeting_notes WHERE id=?",
                               (note_id,)).fetchone()
            if row:
                existing = dict(row)

        ctk.CTkLabel(self, text=self.title(),
                     font=ctk.CTkFont(size=16, weight="bold")).pack(
            anchor="w", padx=24, pady=(20, 12))

        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=24, pady=4)

        ctk.CTkLabel(form, text="Date", text_color=COLORS["text_dim"],
                     font=ctk.CTkFont(size=12)).grid(
            row=0, column=0, sticky="e", padx=(0, 14), pady=6)
        self.date_entry = ctk.CTkEntry(form, width=260, corner_radius=8,
                                       placeholder_text="YYYY-MM-DD")
        self.date_entry.insert(0, existing["meeting_date"] if existing
                               else datetime.now().strftime("%Y-%m-%d"))
        self.date_entry.grid(row=0, column=1, pady=6, sticky="ew")

        ctk.CTkLabel(form, text="Audience", text_color=COLORS["text_dim"],
                     font=ctk.CTkFont(size=12)).grid(
            row=1, column=0, sticky="e", padx=(0, 14), pady=6)
        self.audience_entry = ctk.CTkEntry(form, width=260, corner_radius=8,
                                           placeholder_text="Who attended...")
        if existing and existing["audience"]:
            self.audience_entry.insert(0, existing["audience"])
        self.audience_entry.grid(row=1, column=1, pady=6, sticky="ew")

        ctk.CTkLabel(form, text="Notes", text_color=COLORS["text_dim"],
                     font=ctk.CTkFont(size=12)).grid(
            row=2, column=0, sticky="ne", padx=(0, 14), pady=6)
        self.notes_text = ctk.CTkTextbox(form, height=160,
                                         fg_color=COLORS["bg"],
                                         text_color=COLORS["text"],
                                         corner_radius=8, border_width=1,
                                         border_color=COLORS["border"],
                                         font=ctk.CTkFont(size=12))
        self.notes_text.grid(row=2, column=1, pady=6, sticky="nsew")
        if existing and existing["notes"]:
            self.notes_text.insert("0.0", existing["notes"])
        form.columnconfigure(1, weight=1)
        form.rowconfigure(2, weight=1)

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
        date = self.date_entry.get().strip()
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            messagebox.showwarning("Validation", "Date must be YYYY-MM-DD.",
                                   parent=self)
            return
        audience = self.audience_entry.get().strip()
        notes = self.notes_text.get("0.0", "end").strip()

        if self.note_id:
            db.update_meeting_note(self.conn, self.note_id, date, audience, notes)
        else:
            db.add_meeting_note(self.conn, self.customer_id, date, audience, notes)

        self.destroy()
        if self.on_save:
            self.on_save()
