"""Follow-ups page -- global follow-up list with filters and color coding."""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta

import customtkinter as ctk
import database as db
from export import export_follow_ups_csv


class FollowUpsTab(ctk.CTkFrame):
    def __init__(self, parent, conn, app):
        super().__init__(parent, fg_color="#F0F4F8")
        self.conn = conn
        self.app = app
        self._build_ui()

    def _build_ui(self):
        # ── Page header ────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=28, pady=(24, 4))

        header_left = ctk.CTkFrame(header, fg_color="transparent")
        header_left.pack(side="left")
        title_row = ctk.CTkFrame(header_left, fg_color="transparent")
        title_row.pack(anchor="w")
        ctk.CTkLabel(title_row, text="\u25F4",
                     font=ctk.CTkFont(size=20),
                     text_color="#2563EB").pack(side="left", padx=(0, 8))
        ctk.CTkLabel(title_row, text="Follow-ups",
                     font=ctk.CTkFont(size=22, weight="bold"),
                     text_color="#1E293B").pack(side="left")
        ctk.CTkLabel(header_left, text="Track and manage your follow-up tasks",
                     font=ctk.CTkFont(size=11),
                     text_color="#64748B").pack(anchor="w", pady=(2, 0))

        ctk.CTkButton(header, text="Export CSV", width=110, height=34,
                      corner_radius=8,
                      fg_color="#E2E8F0", hover_color="#CBD5E1",
                      text_color="#1E293B",
                      font=ctk.CTkFont(size=12),
                      command=self._export_csv).pack(side="right")

        # ── Filter bar ─────────────────────────────────────────────────
        filter_card = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=12,
                                   border_width=1, border_color="#E2E8F0")
        filter_card.pack(fill="x", padx=28, pady=(14, 0))

        filter_inner = ctk.CTkFrame(filter_card, fg_color="transparent")
        filter_inner.pack(fill="x", padx=16, pady=12)

        # Status
        ctk.CTkLabel(filter_inner, text="Status",
                     font=ctk.CTkFont(size=11),
                     text_color="#64748B").grid(row=0, column=0, sticky="w", padx=(0, 6))
        self.status_var = tk.StringVar(value="All")
        self.status_combo = ctk.CTkComboBox(
            filter_inner,
            values=["All", "Pending", "Completed", "Overdue"],
            variable=self.status_var,
            width=120, corner_radius=8,
            command=lambda _: self.refresh()
        )
        self.status_combo.grid(row=0, column=1, padx=(0, 18))

        # Type
        ctk.CTkLabel(filter_inner, text="Type",
                     font=ctk.CTkFont(size=11),
                     text_color="#64748B").grid(row=0, column=2, sticky="w", padx=(0, 6))
        self.type_var = tk.StringVar(value="All")
        self.type_combo = ctk.CTkComboBox(
            filter_inner,
            values=["All", "call", "email", "meeting"],
            variable=self.type_var,
            width=120, corner_radius=8,
            command=lambda _: self.refresh()
        )
        self.type_combo.grid(row=0, column=3, padx=(0, 18))

        # Date range
        ctk.CTkLabel(filter_inner, text="From",
                     font=ctk.CTkFont(size=11),
                     text_color="#64748B").grid(row=0, column=4, sticky="w", padx=(0, 6))
        self.from_var = tk.StringVar()
        ctk.CTkEntry(filter_inner, textvariable=self.from_var, width=110,
                     corner_radius=8,
                     placeholder_text="YYYY-MM-DD").grid(
            row=0, column=5, padx=(0, 12))

        ctk.CTkLabel(filter_inner, text="To",
                     font=ctk.CTkFont(size=11),
                     text_color="#64748B").grid(row=0, column=6, sticky="w", padx=(0, 6))
        self.to_var = tk.StringVar()
        ctk.CTkEntry(filter_inner, textvariable=self.to_var, width=110,
                     corner_radius=8,
                     placeholder_text="YYYY-MM-DD").grid(
            row=0, column=7, padx=(0, 12))

        ctk.CTkButton(filter_inner, text="Apply Dates", width=100, height=30,
                      corner_radius=6,
                      fg_color="#2563EB", hover_color="#1D4ED8",
                      font=ctk.CTkFont(size=11),
                      command=self.refresh).grid(row=0, column=8)

        # ── Treeview ───────────────────────────────────────────────────
        tree_frame = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=12,
                                  border_width=1, border_color="#E2E8F0")
        tree_frame.pack(fill="both", expand=True, padx=28, pady=(12, 20))

        tree_inner = tk.Frame(tree_frame, bg="#FFFFFF")
        tree_inner.pack(fill="both", expand=True, padx=4, pady=4)

        cols = ("customer_name", "due_date", "type", "status", "description")
        self.tree = ttk.Treeview(tree_inner, columns=cols, show="headings",
                                 selectmode="browse")

        col_widths = {"customer_name": 160, "due_date": 110, "type": 80,
                      "status": 90, "description": 280}
        for col in cols:
            self.tree.heading(col, text=col.replace("_", " ").title())
            self.tree.column(col, width=col_widths.get(col, 140), minwidth=60)

        # Color-coded row backgrounds for light theme
        self.tree.tag_configure("overdue",
                                background="#FEE2E2", foreground="#991B1B")
        self.tree.tag_configure("upcoming",
                                background="#FEF3C7", foreground="#92400E")
        self.tree.tag_configure("completed",
                                background="#F1F5F9", foreground="#94A3B8")
        self.tree.tag_configure("evenrow",
                                background="#FFFFFF", foreground="#1E293B")
        self.tree.tag_configure("oddrow",
                                background="#F1F5F9", foreground="#1E293B")

        scrollbar = ttk.Scrollbar(tree_inner, orient="vertical",
                                  command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(fill="both", expand=True, side="left")
        scrollbar.pack(fill="y", side="right")

        # Context menu
        self.menu = tk.Menu(self, tearoff=0,
                            bg="#FFFFFF", fg="#1E293B",
                            activebackground="#2563EB", activeforeground="#FFFFFF")
        self.menu.add_command(label="  Mark Completed",
                              command=self._mark_completed)
        self.menu.add_command(label="  Edit", command=self._edit)
        self.menu.add_separator()
        self.menu.add_command(label="  Delete", command=self._delete)
        self.menu.add_separator()
        self.menu.add_command(label="  Send Email", command=self._send_email)
        self.tree.bind("<Button-3>", self._show_menu)

    def refresh(self):
        date_from = self.from_var.get().strip() or None
        date_to = self.to_var.get().strip() or None

        follow_ups = db.get_all_follow_ups(
            self.conn,
            status=self.status_var.get(),
            type_=self.type_var.get(),
            date_from=date_from,
            date_to=date_to
        )

        today = datetime.now().strftime("%Y-%m-%d")
        upcoming_date = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")

        self.tree.delete(*self.tree.get_children())
        for idx, fu in enumerate(follow_ups):
            if fu["status"] == "completed":
                tag = "completed"
            elif fu["due_date"] < today:
                tag = "overdue"
            elif fu["due_date"] <= upcoming_date:
                tag = "upcoming"
            else:
                tag = "evenrow" if idx % 2 == 0 else "oddrow"
            self.tree.insert("", "end", iid=str(fu["id"]),
                             values=(fu["customer_name"], fu["due_date"],
                                     fu["type"], fu["status"],
                                     fu.get("description", "")),
                             tags=(tag,))

        self._current_follow_ups = follow_ups

    def _show_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.menu.post(event.x_root, event.y_root)

    def _get_selected_id(self):
        sel = self.tree.selection()
        if not sel:
            return None
        return int(sel[0])

    def _mark_completed(self):
        fid = self._get_selected_id()
        if fid:
            try:
                db.complete_follow_up(self.conn, fid)
                self.app.refresh_all_tabs()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to complete follow-up: {e}")

    def _edit(self):
        fid = self._get_selected_id()
        if fid:
            try:
                row = self.conn.execute(
                    "SELECT customer_id FROM follow_ups WHERE id=?",
                    (fid,)).fetchone()
                if row:
                    from tabs.customer_detail_tab import FollowUpDialog
                    FollowUpDialog(self, self.conn, row["customer_id"],
                                   follow_up_id=fid,
                                   on_save=lambda: self.app.refresh_all_tabs())
            except Exception as e:
                messagebox.showerror("Error", f"Failed to edit follow-up: {e}")

    def _delete(self):
        fid = self._get_selected_id()
        if fid and messagebox.askyesno("Confirm", "Delete this follow-up?"):
            try:
                db.delete_follow_up(self.conn, fid)
                self.app.refresh_all_tabs()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete follow-up: {e}")

    def _send_email(self):
        fid = self._get_selected_id()
        if fid:
            row = self.conn.execute(
                "SELECT f.*, c.email, c.name as customer_name "
                "FROM follow_ups f JOIN customers c ON f.customer_id = c.id "
                "WHERE f.id=?",
                (fid,)
            ).fetchone()
            if row:
                customer = db.get_customer(self.conn, row["customer_id"])
                if not customer:
                    messagebox.showwarning("Error", "Customer no longer exists.")
                    return
                from tabs.customer_detail_tab import ComposeEmailDialog
                ComposeEmailDialog(self, self.conn, customer)

    def _export_csv(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")])
        if filepath:
            follow_ups = getattr(self, "_current_follow_ups", [])
            if not follow_ups:
                follow_ups = db.get_all_follow_ups(self.conn)
            export_follow_ups_csv(follow_ups, filepath)
            messagebox.showinfo(
                "Export",
                f"Exported {len(follow_ups)} follow-ups to CSV.")
