"""Landing Page sub-tab — customer info, follow-ups, notes, activity log."""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta

import customtkinter as ctk
import database as db
from tabs.workbook.base_subtab import BaseSubTab, COLORS


class LandingPage(BaseSubTab):
    def __init__(self, parent, conn, customer_id, app):
        super().__init__(parent, conn, customer_id, app)
        self._build_ui()

    def _build_ui(self):
        # ── Quick Stats Row ────────────────────────────────────────────
        stats_row = ctk.CTkFrame(self, fg_color="transparent")
        stats_row.pack(fill="x", padx=16, pady=(16, 0))

        self._stat_vars = {}
        stat_defs = [
            ("Follow-ups", "follow_ups", "#2563EB", "\u25F4"),
            ("Overdue", "overdue", "#DC2626", "\u25B2"),
            ("Notes", "notes", "#059669", "\u25A3"),
            ("Actions", "actions", "#D97706", "\u2713"),
        ]
        for i, (label, key, color, icon) in enumerate(stat_defs):
            stats_row.columnconfigure(i, weight=1, uniform="stat")
            pill = ctk.CTkFrame(stats_row, fg_color="#FFFFFF",
                                corner_radius=10, border_width=1,
                                border_color=COLORS["border"])
            pill.grid(row=0, column=i, padx=4, sticky="ew")

            pill_inner = ctk.CTkFrame(pill, fg_color="transparent")
            pill_inner.pack(padx=14, pady=10)

            ctk.CTkLabel(pill_inner, text=icon,
                         font=ctk.CTkFont(size=13),
                         text_color=color).pack(side="left", padx=(0, 6))
            var = tk.StringVar(value="0")
            ctk.CTkLabel(pill_inner, textvariable=var,
                         font=ctk.CTkFont(size=16, weight="bold"),
                         text_color=COLORS["text"]).pack(side="left",
                                                          padx=(0, 6))
            ctk.CTkLabel(pill_inner, text=label,
                         font=ctk.CTkFont(size=11),
                         text_color=COLORS["text_dim"]).pack(side="left")
            self._stat_vars[key] = var

        # ── Customer Info Card ─────────────────────────────────────────
        info_card = self.make_card(pad_top=12)
        self.make_card_header(info_card, "Customer Information")

        info_grid = ctk.CTkFrame(info_card, fg_color="transparent")
        info_grid.pack(fill="x", padx=18, pady=(10, 16))

        self.info_labels = {}
        fields = [
            ("Name", 0, 0), ("Company", 0, 2), ("Phone", 1, 0),
            ("Email", 1, 2), ("Category", 2, 0), ("Tags", 2, 2),
            ("Created", 3, 0),
        ]
        for field_name, row, col in fields:
            ctk.CTkLabel(info_grid, text=field_name,
                         font=ctk.CTkFont(size=11),
                         text_color=COLORS["text_dim"]).grid(
                row=row, column=col, sticky="w", padx=(0, 8), pady=5)
            lbl = ctk.CTkLabel(info_grid, text="",
                               font=ctk.CTkFont(size=12),
                               text_color=COLORS["text"])
            lbl.grid(row=row, column=col + 1, sticky="w", padx=(0, 32), pady=5)
            self.info_labels[field_name.lower()] = lbl
        info_grid.columnconfigure(1, weight=1)
        info_grid.columnconfigure(3, weight=1)

        # ── Follow-ups Section ─────────────────────────────────────────
        fu_card = self.make_card()
        self.make_card_header(fu_card, "Follow-ups", [
            ("+ Add Follow-up", self._add_follow_up, {}),
        ])

        cols = ("due_date", "type", "status", "description")
        widths = {"due_date": 110, "type": 80, "status": 90, "description": 300}
        self.fu_tree, _ = self.make_treeview(fu_card, cols, widths, height=6)

        self.fu_tree.tag_configure("overdue",
                                   background="#FEE2E2", foreground="#991B1B")
        self.fu_tree.tag_configure("upcoming",
                                   background="#FEF3C7", foreground="#92400E")
        self.fu_tree.tag_configure("completed",
                                   background="#F1F5F9", foreground="#94A3B8")

        self.make_context_menu(self.fu_tree, [
            ("Mark Completed", self._complete_follow_up),
            ("Edit", self._edit_follow_up),
            None,
            ("Delete", self._delete_follow_up),
        ])

        # ── Notes Section ──────────────────────────────────────────────
        notes_card = self.make_card()
        self.make_card_header(notes_card, "Notes")

        notes_body = ctk.CTkFrame(notes_card, fg_color="transparent")
        notes_body.pack(fill="x", padx=20, pady=(10, 18))

        self.notes_text = ctk.CTkTextbox(notes_body, height=140,
                                         fg_color=COLORS["bg"],
                                         text_color=COLORS["text"],
                                         font=ctk.CTkFont(size=12),
                                         corner_radius=8)
        self.notes_text.pack(fill="x", pady=(0, 10))
        self.notes_text.configure(state="disabled")

        ctk.CTkLabel(notes_body, text="Add a note",
                     font=ctk.CTkFont(size=11),
                     text_color=COLORS["text_dim"]).pack(anchor="w")
        self.note_input = ctk.CTkTextbox(notes_body, height=70,
                                         fg_color=COLORS["bg"],
                                         text_color=COLORS["text"],
                                         font=ctk.CTkFont(size=12),
                                         corner_radius=8,
                                         border_width=1,
                                         border_color=COLORS["border"])
        self.note_input.pack(fill="x", pady=(4, 0))

        note_btn_row = ctk.CTkFrame(notes_body, fg_color="transparent")
        note_btn_row.pack(fill="x", pady=(8, 0))
        ctk.CTkButton(note_btn_row, text="Add Note", width=100, height=32,
                      corner_radius=8,
                      command=self._add_note).pack(side="right")

        # ── Activity Log Section ───────────────────────────────────────
        log_card = self.make_card()
        self.make_card_header(log_card, "Activity Log")

        log_body = ctk.CTkFrame(log_card, fg_color="transparent")
        log_body.pack(fill="x", padx=18, pady=(10, 16))

        self.log_text = ctk.CTkTextbox(log_body, height=140,
                                       fg_color=COLORS["bg"],
                                       text_color=COLORS["text"],
                                       font=ctk.CTkFont(size=12),
                                       corner_radius=8)
        self.log_text.pack(fill="x")
        self.log_text.configure(state="disabled")

    def refresh(self):
        customer = db.get_customer(self.conn, self.customer_id)
        if not customer:
            return

        # Update quick stats
        follow_ups = db.get_follow_ups_for_customer(self.conn, self.customer_id)
        today = datetime.now().strftime("%Y-%m-%d")
        n_fu = len(follow_ups)
        n_overdue = sum(1 for fu in follow_ups
                        if fu["status"] != "completed" and fu["due_date"] < today)
        notes = db.get_notes_for_customer(self.conn, self.customer_id)
        n_notes = len(notes)
        try:
            actions = db.get_action_items(self.conn, self.customer_id)
            n_actions = len(actions)
        except Exception:
            n_actions = 0

        self._stat_vars["follow_ups"].set(str(n_fu))
        self._stat_vars["overdue"].set(str(n_overdue))
        self._stat_vars["notes"].set(str(n_notes))
        self._stat_vars["actions"].set(str(n_actions))

        tags = db.get_customer_tags(self.conn, self.customer_id)

        # Info labels
        self.info_labels["name"].configure(text=customer["name"])
        self.info_labels["company"].configure(text=customer["company"] or "-")
        self.info_labels["phone"].configure(text=customer["phone"] or "-")
        self.info_labels["email"].configure(text=customer["email"] or "-")
        self.info_labels["category"].configure(text=customer["category"])
        self.info_labels["tags"].configure(
            text=", ".join(tags) if tags else "(none)")
        self.info_labels["created"].configure(text=customer["created_at"])

        # Follow-ups
        self.fu_tree.delete(*self.fu_tree.get_children())
        upcoming_date = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
        for idx, fu in enumerate(follow_ups):
            if fu["status"] == "completed":
                tag = "completed"
            elif fu["due_date"] < today:
                tag = "overdue"
            elif fu["due_date"] <= upcoming_date:
                tag = "upcoming"
            else:
                tag = "evenrow" if idx % 2 == 0 else "oddrow"
            self.fu_tree.insert("", "end", iid=str(fu["id"]),
                                values=(fu["due_date"], fu["type"],
                                        fu["status"], fu["description"]),
                                tags=(tag,))

        # Notes
        self.notes_text.configure(state="normal")
        self.notes_text.delete("0.0", "end")
        for note in notes:
            self.notes_text.insert("end", f"{note['created_at']}\n")
            self.notes_text.insert("end", f"{note['content']}\n\n")
        self.notes_text.configure(state="disabled")

        # Activity log
        self.log_text.configure(state="normal")
        self.log_text.delete("0.0", "end")
        for entry in db.get_activity_log(self.conn, self.customer_id):
            self.log_text.insert("end",
                                 f"{entry['created_at']}  {entry['action']}  {entry['detail']}\n")
        self.log_text.configure(state="disabled")

    # ── Follow-up actions ──────────────────────────────────────────

    def _get_selected_fu_id(self):
        return self.get_selected_id(self.fu_tree, "follow-up")

    def _add_follow_up(self):
        from tabs.customer_detail_tab import FollowUpDialog
        FollowUpDialog(self, self.conn, self.customer_id,
                       on_save=lambda: self.app.refresh_all_tabs())

    def _edit_follow_up(self):
        fid = self._get_selected_fu_id()
        if fid:
            from tabs.customer_detail_tab import FollowUpDialog
            FollowUpDialog(self, self.conn, self.customer_id,
                           follow_up_id=fid,
                           on_save=lambda: self.app.refresh_all_tabs())

    def _complete_follow_up(self):
        fid = self._get_selected_fu_id()
        if fid:
            db.complete_follow_up(self.conn, fid)
            self.app.refresh_all_tabs()

    def _delete_follow_up(self):
        fid = self._get_selected_fu_id()
        if fid and self.confirm_delete("follow-up"):
            db.delete_follow_up(self.conn, fid)
            self.app.refresh_all_tabs()

    def _add_note(self):
        content = self.note_input.get("0.0", "end").strip()
        if content:
            db.add_note(self.conn, self.customer_id, content)
            self.note_input.delete("0.0", "end")
            self.app.refresh_all_tabs()
