"""Customer Detail page -- info, follow-ups, notes, activity log."""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

import customtkinter as ctk
import database as db
from email_sender import load_smtp_config, send_email


class CustomerDetailTab(ctk.CTkScrollableFrame):
    def __init__(self, parent, conn, customer_id, app):
        super().__init__(parent, fg_color="#1F2937")
        self.conn = conn
        self.customer_id = customer_id
        self.app = app
        self._build_ui()

    def _build_ui(self):
        # ── Header bar with name and action buttons ────────────────────
        header_card = ctk.CTkFrame(self, fg_color="#374151", corner_radius=12)
        header_card.pack(fill="x", padx=24, pady=(20, 0))

        header_inner = ctk.CTkFrame(header_card, fg_color="transparent")
        header_inner.pack(fill="x", padx=20, pady=16)

        # Left side: customer name + subtitle
        header_left = ctk.CTkFrame(header_inner, fg_color="transparent")
        header_left.pack(side="left", fill="x", expand=True)

        self.name_label = ctk.CTkLabel(header_left, text="",
                                        font=ctk.CTkFont(size=20, weight="bold"),
                                        text_color="#F9FAFB")
        self.name_label.pack(anchor="w")
        self.subtitle_label = ctk.CTkLabel(header_left, text="",
                                            font=ctk.CTkFont(size=12),
                                            text_color="#9CA3AF")
        self.subtitle_label.pack(anchor="w", pady=(2, 0))

        # Right side: action buttons
        header_right = ctk.CTkFrame(header_inner, fg_color="transparent")
        header_right.pack(side="right")
        ctk.CTkButton(header_right, text="Edit", width=70, height=32,
                      corner_radius=8,
                      fg_color="#374151", hover_color="#4B5563",
                      border_width=1, border_color="#4B5563",
                      command=self._edit_customer).pack(side="left", padx=(0, 6))
        ctk.CTkButton(header_right, text="Send Email", width=100, height=32,
                      corner_radius=8,
                      fg_color="#3B82F6", hover_color="#2563EB",
                      command=self._send_email).pack(side="left", padx=(0, 6))
        ctk.CTkButton(header_right, text="Close", width=70, height=32,
                      corner_radius=8,
                      fg_color="#EF4444", hover_color="#DC2626",
                      command=self._close_tab).pack(side="left")

        # ── Customer Info Card ─────────────────────────────────────────
        info_card = ctk.CTkFrame(self, fg_color="#374151", corner_radius=12)
        info_card.pack(fill="x", padx=24, pady=(12, 0))

        info_header = ctk.CTkFrame(info_card, fg_color="transparent")
        info_header.pack(fill="x", padx=18, pady=(14, 8))
        ctk.CTkLabel(info_header, text="Customer Information",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color="#F9FAFB").pack(anchor="w")

        sep = ctk.CTkFrame(info_card, fg_color="#4B5563", height=1)
        sep.pack(fill="x", padx=18)

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
                         text_color="#9CA3AF").grid(
                row=row, column=col, sticky="w", padx=(0, 8), pady=5)
            lbl = ctk.CTkLabel(info_grid, text="",
                               font=ctk.CTkFont(size=12),
                               text_color="#F9FAFB")
            lbl.grid(row=row, column=col + 1, sticky="w", padx=(0, 32), pady=5)
            self.info_labels[field_name.lower()] = lbl

        info_grid.columnconfigure(1, weight=1)
        info_grid.columnconfigure(3, weight=1)

        # ── Follow-ups Section ─────────────────────────────────────────
        fu_card = ctk.CTkFrame(self, fg_color="#374151", corner_radius=12)
        fu_card.pack(fill="x", padx=24, pady=(12, 0))

        fu_header = ctk.CTkFrame(fu_card, fg_color="transparent")
        fu_header.pack(fill="x", padx=18, pady=(14, 8))
        ctk.CTkLabel(fu_header, text="Follow-ups",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color="#F9FAFB").pack(side="left")
        ctk.CTkButton(fu_header, text="+ Add Follow-up", width=130, height=30,
                      corner_radius=6,
                      font=ctk.CTkFont(size=11),
                      command=self._add_follow_up).pack(side="right")

        sep2 = ctk.CTkFrame(fu_card, fg_color="#4B5563", height=1)
        sep2.pack(fill="x", padx=18)

        fu_tree_frame = tk.Frame(fu_card, bg="#374151")
        fu_tree_frame.pack(fill="x", padx=18, pady=(8, 16))

        cols = ("due_date", "type", "status", "description")
        self.fu_tree = ttk.Treeview(fu_tree_frame, columns=cols,
                                     show="headings", height=6)
        col_widths = {"due_date": 110, "type": 80, "status": 90, "description": 300}
        for col in cols:
            self.fu_tree.heading(col, text=col.replace("_", " ").title())
            self.fu_tree.column(col, width=col_widths.get(col, 130), minwidth=60)

        # Color-coded row backgrounds
        self.fu_tree.tag_configure("overdue",
                                    background="#7F1D1D", foreground="#FCA5A5")
        self.fu_tree.tag_configure("upcoming",
                                    background="#78350F", foreground="#FCD34D")
        self.fu_tree.tag_configure("completed",
                                    background="#1F2937", foreground="#6B7280")
        self.fu_tree.tag_configure("evenrow",
                                    background="#374151", foreground="#F9FAFB")
        self.fu_tree.tag_configure("oddrow",
                                    background="#2D3748", foreground="#F9FAFB")

        fu_scroll = ttk.Scrollbar(fu_tree_frame, orient="vertical",
                                   command=self.fu_tree.yview)
        self.fu_tree.configure(yscrollcommand=fu_scroll.set)
        self.fu_tree.pack(fill="x", side="left", expand=True)
        fu_scroll.pack(fill="y", side="right")

        fu_menu = tk.Menu(self, tearoff=0,
                          bg="#1F2937", fg="#F9FAFB",
                          activebackground="#3B82F6", activeforeground="#FFFFFF")
        fu_menu.add_command(label="  Mark Completed",
                            command=self._complete_follow_up)
        fu_menu.add_command(label="  Edit", command=self._edit_follow_up)
        fu_menu.add_separator()
        fu_menu.add_command(label="  Delete", command=self._delete_follow_up)
        self.fu_menu = fu_menu
        self.fu_tree.bind("<Button-3>", lambda e: self._show_fu_menu(e))

        # ── Notes Section ──────────────────────────────────────────────
        notes_card = ctk.CTkFrame(self, fg_color="#374151", corner_radius=12)
        notes_card.pack(fill="x", padx=24, pady=(12, 0))

        notes_header = ctk.CTkFrame(notes_card, fg_color="transparent")
        notes_header.pack(fill="x", padx=18, pady=(14, 8))
        ctk.CTkLabel(notes_header, text="Notes",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color="#F9FAFB").pack(side="left")

        sep3 = ctk.CTkFrame(notes_card, fg_color="#4B5563", height=1)
        sep3.pack(fill="x", padx=18)

        notes_body = ctk.CTkFrame(notes_card, fg_color="transparent")
        notes_body.pack(fill="x", padx=18, pady=(10, 16))

        self.notes_text = ctk.CTkTextbox(notes_body, height=140,
                                          fg_color="#1F2937",
                                          text_color="#F9FAFB",
                                          font=ctk.CTkFont(size=12),
                                          corner_radius=8)
        self.notes_text.pack(fill="x", pady=(0, 10))
        self.notes_text.configure(state="disabled")

        # New note input
        ctk.CTkLabel(notes_body, text="Add a note",
                     font=ctk.CTkFont(size=11),
                     text_color="#9CA3AF").pack(anchor="w")
        self.note_input = ctk.CTkTextbox(notes_body, height=70,
                                          fg_color="#1F2937",
                                          text_color="#F9FAFB",
                                          font=ctk.CTkFont(size=12),
                                          corner_radius=8,
                                          border_width=1,
                                          border_color="#4B5563")
        self.note_input.pack(fill="x", pady=(4, 0))

        note_btn_row = ctk.CTkFrame(notes_body, fg_color="transparent")
        note_btn_row.pack(fill="x", pady=(8, 0))
        ctk.CTkButton(note_btn_row, text="Add Note", width=100, height=32,
                      corner_radius=8,
                      command=self._add_note).pack(side="right")

        # ── Activity Log Section ───────────────────────────────────────
        log_card = ctk.CTkFrame(self, fg_color="#374151", corner_radius=12)
        log_card.pack(fill="x", padx=24, pady=(12, 20))

        log_header = ctk.CTkFrame(log_card, fg_color="transparent")
        log_header.pack(fill="x", padx=18, pady=(14, 8))
        ctk.CTkLabel(log_header, text="Activity Log",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color="#F9FAFB").pack(side="left")

        sep4 = ctk.CTkFrame(log_card, fg_color="#4B5563", height=1)
        sep4.pack(fill="x", padx=18)

        log_body = ctk.CTkFrame(log_card, fg_color="transparent")
        log_body.pack(fill="x", padx=18, pady=(10, 16))

        self.log_text = ctk.CTkTextbox(log_body, height=140,
                                        fg_color="#1F2937",
                                        text_color="#F9FAFB",
                                        font=ctk.CTkFont(size=12),
                                        corner_radius=8)
        self.log_text.pack(fill="x")
        self.log_text.configure(state="disabled")

    def refresh(self):
        customer = db.get_customer(self.conn, self.customer_id)
        if not customer:
            return

        tags = db.get_customer_tags(self.conn, self.customer_id)

        # Header
        self.name_label.configure(text=customer["name"])
        self.subtitle_label.configure(
            text=f"{customer['company']}  |  {customer['category']}"
            if customer["company"] else customer["category"])

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
        today = datetime.now().strftime("%Y-%m-%d")
        from datetime import timedelta
        upcoming_date = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")

        for idx, fu in enumerate(db.get_follow_ups_for_customer(
                self.conn, self.customer_id)):
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
        for note in db.get_notes_for_customer(self.conn, self.customer_id):
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

    def _show_fu_menu(self, event):
        item = self.fu_tree.identify_row(event.y)
        if item:
            self.fu_tree.selection_set(item)
            self.fu_menu.post(event.x_root, event.y_root)

    def _get_selected_fu_id(self):
        sel = self.fu_tree.selection()
        if not sel:
            messagebox.showwarning("No Selection",
                                    "Please select a follow-up.")
            return None
        return int(sel[0])

    def _add_follow_up(self):
        FollowUpDialog(self, self.conn, self.customer_id,
                       on_save=lambda: self.app.refresh_all_tabs())

    def _edit_follow_up(self):
        fid = self._get_selected_fu_id()
        if fid:
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
        if fid and messagebox.askyesno("Confirm", "Delete this follow-up?"):
            db.delete_follow_up(self.conn, fid)
            self.app.refresh_all_tabs()

    def _add_note(self):
        content = self.note_input.get("0.0", "end").strip()
        if content:
            db.add_note(self.conn, self.customer_id, content)
            self.note_input.delete("0.0", "end")
            self.app.refresh_all_tabs()

    def _edit_customer(self):
        from tabs.customers_tab import CustomerDialog
        customer = db.get_customer(self.conn, self.customer_id)
        tags = db.get_customer_tags(self.conn, self.customer_id)
        CustomerDialog(self, self.conn, customer=customer, tags=tags,
                       on_save=lambda: self.app.refresh_all_tabs())

    def _send_email(self):
        customer = db.get_customer(self.conn, self.customer_id)
        if customer:
            ComposeEmailDialog(self, self.conn, customer)

    def _close_tab(self):
        self.app.close_customer_detail(self.customer_id)


class FollowUpDialog(ctk.CTkToplevel):
    """Dialog for adding/editing a follow-up."""

    def __init__(self, parent, conn, customer_id, follow_up_id=None,
                 on_save=None):
        super().__init__(parent)
        self.conn = conn
        self.customer_id = customer_id
        self.follow_up_id = follow_up_id
        self.on_save = on_save

        self.title("Edit Follow-up" if follow_up_id else "New Follow-up")
        self.geometry("460x360")
        self.resizable(False, False)
        self.after(100, self.grab_set)

        existing = None
        if follow_up_id:
            row = conn.execute("SELECT * FROM follow_ups WHERE id=?",
                               (follow_up_id,)).fetchone()
            if row:
                existing = dict(row)

        # Header
        ctk.CTkLabel(self,
                     text="Edit Follow-up" if follow_up_id else "New Follow-up",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(
            anchor="w", padx=24, pady=(20, 12))

        # Form
        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(fill="x", padx=24, pady=4)

        ctk.CTkLabel(form, text="Due Date",
                     font=ctk.CTkFont(size=12),
                     text_color="#9CA3AF").grid(row=0, column=0, sticky="e",
                                                padx=(0, 14), pady=6)
        self.date_entry = ctk.CTkEntry(form, width=260, corner_radius=8,
                                        placeholder_text="YYYY-MM-DD")
        self.date_entry.insert(0,
                               existing["due_date"] if existing
                               else datetime.now().strftime("%Y-%m-%d"))
        self.date_entry.grid(row=0, column=1, pady=6, sticky="ew")

        ctk.CTkLabel(form, text="Type",
                     font=ctk.CTkFont(size=12),
                     text_color="#9CA3AF").grid(row=1, column=0, sticky="e",
                                                padx=(0, 14), pady=6)
        self.type_var = tk.StringVar(
            value=existing["type"] if existing else "call")
        self.type_combo = ctk.CTkComboBox(
            form,
            values=["call", "email", "meeting"],
            variable=self.type_var,
            width=260, corner_radius=8
        )
        self.type_combo.grid(row=1, column=1, pady=6, sticky="ew")

        ctk.CTkLabel(form, text="Description",
                     font=ctk.CTkFont(size=12),
                     text_color="#9CA3AF").grid(row=2, column=0, sticky="ne",
                                                padx=(0, 14), pady=6)
        self.desc_text = ctk.CTkTextbox(form, height=80,
                                         fg_color="#1F2937",
                                         text_color="#F9FAFB",
                                         font=ctk.CTkFont(size=12),
                                         corner_radius=8,
                                         border_width=1,
                                         border_color="#4B5563")
        self.desc_text.grid(row=2, column=1, pady=6, sticky="ew")
        if existing and existing["description"]:
            self.desc_text.insert("0.0", existing["description"])

        form.columnconfigure(1, weight=1)

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=24, pady=(16, 16))
        ctk.CTkButton(btn_frame, text="Cancel", width=90,
                      fg_color="#374151", hover_color="#4B5563",
                      corner_radius=8,
                      command=self.destroy).pack(side="right", padx=(8, 0))
        ctk.CTkButton(btn_frame, text="Save", width=90,
                      corner_radius=8,
                      command=self._save).pack(side="right")

    def _save(self):
        date = self.date_entry.get().strip()
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            messagebox.showwarning("Validation",
                                    "Date must be YYYY-MM-DD format.",
                                    parent=self)
            return

        desc = self.desc_text.get("0.0", "end").strip()
        type_ = self.type_var.get()

        if self.follow_up_id:
            db.update_follow_up(self.conn, self.follow_up_id, date, type_, desc)
        else:
            db.add_follow_up(self.conn, self.customer_id, date, type_, desc)

        self.destroy()
        if self.on_save:
            self.on_save()


class ComposeEmailDialog(ctk.CTkToplevel):
    """Email composition dialog."""

    def __init__(self, parent, conn, customer):
        super().__init__(parent)
        self.conn = conn
        self.customer = customer

        self.title("Compose Email")
        self.geometry("560x500")
        self.after(100, self.grab_set)

        # Header
        ctk.CTkLabel(self, text="Compose Email",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(
            anchor="w", padx=24, pady=(20, 2))
        ctk.CTkLabel(self, text=f"To {customer.get('name', '')}",
                     font=ctk.CTkFont(size=12),
                     text_color="#9CA3AF").pack(anchor="w", padx=24, pady=(0, 12))

        # Form
        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=24, pady=4)

        ctk.CTkLabel(form, text="To",
                     font=ctk.CTkFont(size=12),
                     text_color="#9CA3AF").grid(row=0, column=0, sticky="e",
                                                padx=(0, 14), pady=6)
        self.to_entry = ctk.CTkEntry(form, width=400, corner_radius=8)
        self.to_entry.insert(0, customer.get("email", ""))
        self.to_entry.grid(row=0, column=1, pady=6, sticky="ew")

        ctk.CTkLabel(form, text="Subject",
                     font=ctk.CTkFont(size=12),
                     text_color="#9CA3AF").grid(row=1, column=0, sticky="e",
                                                padx=(0, 14), pady=6)
        self.subject_entry = ctk.CTkEntry(form, width=400, corner_radius=8,
                                           placeholder_text="Enter subject...")
        self.subject_entry.grid(row=1, column=1, pady=6, sticky="ew")

        ctk.CTkLabel(form, text="Body",
                     font=ctk.CTkFont(size=12),
                     text_color="#9CA3AF").grid(row=2, column=0, sticky="ne",
                                                padx=(0, 14), pady=6)
        self.body_text = ctk.CTkTextbox(form, height=250,
                                         fg_color="#1F2937",
                                         text_color="#F9FAFB",
                                         font=ctk.CTkFont(size=12),
                                         corner_radius=8,
                                         border_width=1,
                                         border_color="#4B5563")
        self.body_text.grid(row=2, column=1, pady=6, sticky="nsew")

        form.columnconfigure(1, weight=1)
        form.rowconfigure(2, weight=1)

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=24, pady=(8, 16))
        ctk.CTkButton(btn_frame, text="Cancel", width=90,
                      fg_color="#374151", hover_color="#4B5563",
                      corner_radius=8,
                      command=self.destroy).pack(side="right", padx=(8, 0))
        ctk.CTkButton(btn_frame, text="Send", width=90,
                      corner_radius=8,
                      command=self._send).pack(side="right")

    def _send(self):
        config = load_smtp_config()
        if not config.get("smtp_server"):
            messagebox.showwarning(
                "Email Settings",
                "Please configure SMTP settings first (File > Email Settings).",
                parent=self)
            return

        to = self.to_entry.get().strip()
        subject = self.subject_entry.get().strip()
        body = self.body_text.get("0.0", "end").strip()

        if not to or not subject:
            messagebox.showwarning("Validation",
                                    "To and Subject are required.",
                                    parent=self)
            return

        success, msg = send_email(config, to, subject, body)
        if success:
            from database import _log_activity, _now
            _log_activity(self.conn, self.customer["id"], "email_sent",
                          f"Email sent to {to}: {subject}")
            self.conn.commit()
            messagebox.showinfo("Email", msg, parent=self)
            self.destroy()
        else:
            messagebox.showerror("Email Error", msg, parent=self)
