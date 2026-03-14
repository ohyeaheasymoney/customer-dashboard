"""Account Goals sub-tab — moonshot + short/long term goals with status."""

import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk
import database as db
from tabs.workbook.base_subtab import BaseSubTab, COLORS

GOAL_STATUSES = ["Not Started", "In Progress", "On Track", "At Risk", "Complete"]


class AccountGoalsTab(BaseSubTab):
    def __init__(self, parent, conn, customer_id, app):
        super().__init__(parent, conn, customer_id, app)
        self._build_ui()

    def _build_ui(self):
        # ── Moonshot / Objectives card ─────────────────────────────────
        meta_card = self.make_card(pad_top=16)
        self.make_card_header(meta_card, "Moonshot Goal & Objectives", [
            ("Save", self._save_meta, {"fg_color": COLORS["primary"],
                                       "hover_color": COLORS["primary_hover"]}),
        ])

        meta_body = ctk.CTkFrame(meta_card, fg_color="transparent")
        meta_body.pack(fill="x", padx=18, pady=(10, 16))

        ctk.CTkLabel(meta_body, text="Moonshot Goal",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=COLORS["text_dim"]).pack(anchor="w")
        self.moonshot_text = ctk.CTkTextbox(meta_body, height=60,
                                            fg_color=COLORS["bg"],
                                            text_color=COLORS["text"],
                                            corner_radius=0, border_width=1,
                                            border_color=COLORS["border"],
                                            font=ctk.CTkFont(size=12))
        self.moonshot_text.pack(fill="x", pady=(4, 10))

        ctk.CTkLabel(meta_body, text="Key Objectives",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=COLORS["text_dim"]).pack(anchor="w")
        self.objectives_text = ctk.CTkTextbox(meta_body, height=60,
                                              fg_color=COLORS["bg"],
                                              text_color=COLORS["text"],
                                              corner_radius=0, border_width=1,
                                              border_color=COLORS["border"],
                                              font=ctk.CTkFont(size=12))
        self.objectives_text.pack(fill="x", pady=(4, 0))

        # ── Short-term Goals (3-6 months) ──────────────────────────────
        st_card = self.make_card()
        self.make_card_header(st_card, "Short-Term Goals (3-6 Months)", [
            ("+ Add Goal", lambda: self._add_goal("short"), {}),
        ])

        cols = ("goal", "status", "notes")
        widths = {"goal": 300, "status": 110, "notes": 250}
        self.short_tree, _ = self.make_treeview(st_card, cols, widths, height=6)
        self._setup_status_tags(self.short_tree)
        self.make_context_menu(self.short_tree, [
            ("Edit", lambda: self._edit_goal("short")),
            None,
            ("Delete", lambda: self._delete_goal("short")),
        ])

        # ── Long-term Goals (7-12 months) ──────────────────────────────
        lt_card = self.make_card()
        self.make_card_header(lt_card, "Long-Term Goals (7-12 Months)", [
            ("+ Add Goal", lambda: self._add_goal("long"), {}),
        ])
        self.long_tree, _ = self.make_treeview(lt_card, cols, widths, height=6)
        self._setup_status_tags(self.long_tree)
        self.make_context_menu(self.long_tree, [
            ("Edit", lambda: self._edit_goal("long")),
            None,
            ("Delete", lambda: self._delete_goal("long")),
        ])

    def _setup_status_tags(self, tree):
        tree.tag_configure("At Risk",
                           background="#FEE2E2", foreground="#991B1B")
        tree.tag_configure("Complete",
                           background="#D1FAE5", foreground="#065F46")

    def refresh(self):
        # Meta
        meta = db.get_goals_meta(self.conn, self.customer_id)
        self.moonshot_text.delete("0.0", "end")
        self.objectives_text.delete("0.0", "end")
        if meta:
            self.moonshot_text.insert("0.0", meta.get("moonshot", ""))
            self.objectives_text.insert("0.0", meta.get("objectives", ""))

        # Goals
        for term, tree in [("short", self.short_tree), ("long", self.long_tree)]:
            tree.delete(*tree.get_children())
            goals = db.get_account_goals(self.conn, self.customer_id, term)
            for idx, g in enumerate(goals):
                status = g.get("status", "Not Started")
                tag = status if status in ("At Risk", "Complete") else (
                    "evenrow" if idx % 2 == 0 else "oddrow")
                tree.insert("", "end", iid=str(g["id"]),
                            values=(g["goal"], g["status"], g["notes"]),
                            tags=(tag,))

    def _save_meta(self):
        moonshot = self.moonshot_text.get("0.0", "end").strip()
        objectives = self.objectives_text.get("0.0", "end").strip()
        db.upsert_goals_meta(self.conn, self.customer_id, moonshot, objectives)
        messagebox.showinfo("Saved", "Moonshot & objectives saved.")

    def _add_goal(self, term):
        GoalDialog(self, self.conn, self.customer_id, term,
                   on_save=self.refresh)

    def _edit_goal(self, term):
        tree = self.short_tree if term == "short" else self.long_tree
        gid = self.get_selected_id(tree, "goal")
        if gid:
            GoalDialog(self, self.conn, self.customer_id, term,
                       goal_id=gid, on_save=self.refresh)

    def _delete_goal(self, term):
        tree = self.short_tree if term == "short" else self.long_tree
        gid = self.get_selected_id(tree, "goal")
        if gid and self.confirm_delete("goal"):
            db.delete_account_goal(self.conn, gid)
            self.refresh()


class GoalDialog(ctk.CTkToplevel):
    def __init__(self, parent, conn, customer_id, term,
                 goal_id=None, on_save=None):
        super().__init__(parent)
        self.conn = conn
        self.customer_id = customer_id
        self.term = term
        self.goal_id = goal_id
        self.on_save = on_save

        label = "Short-Term" if term == "short" else "Long-Term"
        self.title(f"{'Edit' if goal_id else 'New'} {label} Goal")
        self.geometry("480x340")
        self.resizable(False, False)
        self.after(100, self.grab_set)

        existing = None
        if goal_id:
            row = conn.execute("SELECT * FROM account_goals WHERE id=?",
                               (goal_id,)).fetchone()
            if row:
                existing = dict(row)

        ctk.CTkLabel(self, text=self.title(),
                     font=ctk.CTkFont(size=16, weight="bold")).pack(
            anchor="w", padx=24, pady=(20, 12))

        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(fill="x", padx=24, pady=4)

        ctk.CTkLabel(form, text="Goal", text_color=COLORS["text_dim"],
                     font=ctk.CTkFont(size=12)).grid(
            row=0, column=0, sticky="e", padx=(0, 14), pady=6)
        self.goal_entry = ctk.CTkEntry(form, width=300, corner_radius=0)
        if existing:
            self.goal_entry.insert(0, existing["goal"])
        self.goal_entry.grid(row=0, column=1, pady=6, sticky="ew")

        ctk.CTkLabel(form, text="Status", text_color=COLORS["text_dim"],
                     font=ctk.CTkFont(size=12)).grid(
            row=1, column=0, sticky="e", padx=(0, 14), pady=6)
        self.status_var = tk.StringVar(
            value=existing["status"] if existing else "Not Started")
        ctk.CTkComboBox(form, values=GOAL_STATUSES,
                        variable=self.status_var,
                        width=300, corner_radius=0).grid(
            row=1, column=1, pady=6, sticky="ew")

        ctk.CTkLabel(form, text="Notes", text_color=COLORS["text_dim"],
                     font=ctk.CTkFont(size=12)).grid(
            row=2, column=0, sticky="ne", padx=(0, 14), pady=6)
        self.notes_text = ctk.CTkTextbox(form, height=80,
                                         fg_color=COLORS["bg"],
                                         text_color=COLORS["text"],
                                         corner_radius=0, border_width=1,
                                         border_color=COLORS["border"],
                                         font=ctk.CTkFont(size=12))
        self.notes_text.grid(row=2, column=1, pady=6, sticky="ew")
        if existing and existing.get("notes"):
            self.notes_text.insert("0.0", existing["notes"])
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
        goal = self.goal_entry.get().strip()
        if not goal:
            messagebox.showwarning("Validation", "Goal is required.",
                                   parent=self)
            return
        status = self.status_var.get()
        notes = self.notes_text.get("0.0", "end").strip()

        if self.goal_id:
            db.update_account_goal(self.conn, self.goal_id, goal, status, notes)
        else:
            db.add_account_goal(self.conn, self.customer_id, self.term,
                                goal, status, notes)

        self.destroy()
        if self.on_save:
            self.on_save()
