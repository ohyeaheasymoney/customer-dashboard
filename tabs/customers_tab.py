"""Customers page -- customer list with search, filters, add/edit/delete."""

import re
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import customtkinter as ctk

import database as db
from export import export_customers_csv, export_customer_report_pdf


class CustomersTab(ctk.CTkFrame):
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
        ctk.CTkLabel(title_row, text="\u25A1",
                     font=ctk.CTkFont(size=20),
                     text_color="#2563EB").pack(side="left", padx=(0, 8))
        ctk.CTkLabel(title_row, text="Customers",
                     font=ctk.CTkFont(size=22, weight="bold"),
                     text_color="#1E293B").pack(side="left")
        ctk.CTkLabel(header_left, text="Manage your customer accounts",
                     font=ctk.CTkFont(size=11),
                     text_color="#64748B").pack(anchor="w", pady=(2, 0))

        # Action buttons in header
        btn_group = ctk.CTkFrame(header, fg_color="transparent")
        btn_group.pack(side="right")
        ctk.CTkButton(btn_group, text="+ Add Customer",
                      corner_radius=8, height=34,
                      fg_color="#2563EB", hover_color="#1D4ED8",
                      font=ctk.CTkFont(size=12, weight="bold"),
                      command=self._add_customer).pack(side="left", padx=(0, 8))
        ctk.CTkButton(btn_group, text="Export CSV",
                      corner_radius=8, height=34,
                      fg_color="#E2E8F0", hover_color="#CBD5E1",
                      text_color="#1E293B",
                      font=ctk.CTkFont(size=12),
                      command=self._export_csv).pack(side="left", padx=(0, 8))
        ctk.CTkButton(btn_group, text="Export PDF",
                      corner_radius=8, height=34,
                      fg_color="#E2E8F0", hover_color="#CBD5E1",
                      text_color="#1E293B",
                      font=ctk.CTkFont(size=12),
                      command=self._export_pdf).pack(side="left")

        # ── Search / Filter bar ────────────────────────────────────────
        filter_card = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=12,
                                   border_width=1, border_color="#E2E8F0")
        filter_card.pack(fill="x", padx=28, pady=(14, 0))

        filter_inner = ctk.CTkFrame(filter_card, fg_color="transparent")
        filter_inner.pack(fill="x", padx=16, pady=12)

        # Search
        ctk.CTkLabel(filter_inner, text="Search",
                     font=ctk.CTkFont(size=11),
                     text_color="#64748B").grid(row=0, column=0, sticky="w", padx=(0, 6))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.refresh())
        search_entry = ctk.CTkEntry(filter_inner, textvariable=self.search_var,
                                     width=180, corner_radius=8,
                                     placeholder_text="Search customers...")
        search_entry.grid(row=0, column=1, padx=(0, 18), sticky="ew")

        # Category
        ctk.CTkLabel(filter_inner, text="Category",
                     font=ctk.CTkFont(size=11),
                     text_color="#64748B").grid(row=0, column=2, sticky="w", padx=(0, 6))
        self.cat_var = tk.StringVar(value="All")
        self.cat_combo = ctk.CTkComboBox(
            filter_inner,
            values=["All", "VIP", "Lead", "Active", "Inactive"],
            variable=self.cat_var,
            width=120, corner_radius=8,
            command=lambda _: self.refresh()
        )
        self.cat_combo.grid(row=0, column=3, padx=(0, 18))

        # Tag
        ctk.CTkLabel(filter_inner, text="Tag",
                     font=ctk.CTkFont(size=11),
                     text_color="#64748B").grid(row=0, column=4, sticky="w", padx=(0, 6))
        self.tag_var = tk.StringVar(value="All")
        self.tag_combo = ctk.CTkComboBox(
            filter_inner,
            values=["All"],
            variable=self.tag_var,
            width=140, corner_radius=8,
            command=lambda _: self.refresh()
        )
        self.tag_combo.grid(row=0, column=5, padx=(0, 18))

        # Company
        ctk.CTkLabel(filter_inner, text="Company",
                     font=ctk.CTkFont(size=11),
                     text_color="#64748B").grid(row=0, column=6, sticky="w", padx=(0, 6))
        self.company_var = tk.StringVar(value="All")
        self.company_combo = ctk.CTkComboBox(
            filter_inner,
            values=["All"],
            variable=self.company_var,
            width=160, corner_radius=8,
            command=lambda _: self.refresh()
        )
        self.company_combo.grid(row=0, column=7)

        filter_inner.columnconfigure(1, weight=1)

        # ── Treeview ───────────────────────────────────────────────────
        tree_frame = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=12,
                                  border_width=1, border_color="#E2E8F0")
        tree_frame.pack(fill="both", expand=True, padx=28, pady=(12, 20))

        tree_inner = tk.Frame(tree_frame, bg="#FFFFFF")
        tree_inner.pack(fill="both", expand=True, padx=4, pady=4)

        cols = ("name", "company", "phone", "email", "category", "tags")
        self.tree = ttk.Treeview(tree_inner, columns=cols, show="headings",
                                 selectmode="browse")

        col_widths = {"name": 160, "company": 140, "phone": 120,
                      "email": 180, "category": 90, "tags": 160}
        for col in cols:
            self.tree.heading(col, text=col.replace("_", " ").title(),
                              command=lambda c=col: self._sort_column(c))
            self.tree.column(col, width=col_widths.get(col, 120), minwidth=60)

        # Alternating row colors for light theme
        self.tree.tag_configure("evenrow", background="#FFFFFF", foreground="#1E293B")
        self.tree.tag_configure("oddrow", background="#F1F5F9", foreground="#1E293B")

        scrollbar = ttk.Scrollbar(tree_inner, orient="vertical",
                                  command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(fill="both", expand=True, side="left")
        scrollbar.pack(fill="y", side="right")

        self.tree.bind("<Double-1>", self._on_double_click)

        # Context menu
        self.menu = tk.Menu(self, tearoff=0,
                            bg="#FFFFFF", fg="#1E293B",
                            activebackground="#2563EB", activeforeground="#FFFFFF")
        self.menu.add_command(label="  Open Detail", command=self._open_detail)
        self.menu.add_command(label="  Edit", command=self._edit_customer)
        self.menu.add_separator()
        self.menu.add_command(label="  Delete", command=self._delete_customer)
        self.tree.bind("<Button-3>", self._show_menu)

        self._sort_col = None
        self._sort_reverse = False

    def _sort_column(self, col):
        if self._sort_col == col:
            self._sort_reverse = not self._sort_reverse
        else:
            self._sort_col = col
            self._sort_reverse = False
        self.refresh()

    def refresh(self):
        # Update filter combos
        tags = ["All"] + db.get_all_tags(self.conn)
        self.tag_combo.configure(values=tags)
        companies = ["All"] + db.get_all_companies(self.conn)
        self.company_combo.configure(values=companies)

        customers = db.search_customers(
            self.conn,
            text=self.search_var.get(),
            category=self.cat_var.get(),
            tag_name=self.tag_var.get(),
            company=self.company_var.get()
        )

        # Add tags to each customer
        for c in customers:
            c["tags"] = ", ".join(db.get_customer_tags(self.conn, c["id"]))

        # Sort
        if self._sort_col:
            customers.sort(key=lambda x: (x.get(self._sort_col, "") or "").lower(),
                           reverse=self._sort_reverse)

        self.tree.delete(*self.tree.get_children())
        for idx, c in enumerate(customers):
            row_tag = "evenrow" if idx % 2 == 0 else "oddrow"
            self.tree.insert("", "end", iid=str(c["id"]),
                             values=(c["name"], c["company"], c["phone"],
                                     c["email"], c["category"], c["tags"]),
                             tags=(row_tag,))

    def _get_selected_id(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("No Selection", "Please select a customer.")
            return None
        return int(sel[0])

    def _on_double_click(self, event):
        self._open_detail()

    def _open_detail(self):
        cid = self._get_selected_id()
        if cid:
            self.app.open_customer_detail(cid)

    def _show_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.menu.post(event.x_root, event.y_root)

    def _add_customer(self):
        CustomerDialog(self, self.conn, on_save=self._after_save)

    def _edit_customer(self):
        cid = self._get_selected_id()
        if cid:
            customer = db.get_customer(self.conn, cid)
            tags = db.get_customer_tags(self.conn, cid)
            CustomerDialog(self, self.conn, customer=customer, tags=tags,
                           on_save=self._after_save)

    def _delete_customer(self):
        cid = self._get_selected_id()
        if cid:
            if messagebox.askyesno("Confirm Delete",
                                    "Delete this customer and all related data?"):
                db.delete_customer(self.conn, cid)
                self.app.close_customer_detail(cid)
                self.app.refresh_all_tabs()

    def _after_save(self):
        self.app.refresh_all_tabs()

    def _export_csv(self):
        filepath = filedialog.asksaveasfilename(defaultextension=".csv",
                                                 filetypes=[("CSV files", "*.csv")])
        if filepath:
            try:
                customers = db.search_customers(
                    self.conn, text=self.search_var.get(),
                    category=self.cat_var.get(), tag_name=self.tag_var.get(),
                    company=self.company_var.get()
                )
                export_customers_csv(customers, filepath)
                messagebox.showinfo("Export",
                                    f"Exported {len(customers)} customers to CSV.")
            except (IOError, PermissionError) as e:
                messagebox.showerror("Export Error", f"Failed to export CSV: {e}")

    def _export_pdf(self):
        cid = self._get_selected_id()
        if not cid:
            messagebox.showinfo("Export PDF",
                                "Select a customer to export their report.")
            return
        filepath = filedialog.asksaveasfilename(defaultextension=".pdf",
                                                 filetypes=[("PDF files", "*.pdf")])
        if filepath:
            try:
                customer = db.get_customer(self.conn, cid)
                follow_ups = db.get_follow_ups_for_customer(self.conn, cid)
                notes = db.get_notes_for_customer(self.conn, cid)
                export_customer_report_pdf(customer, follow_ups, notes, filepath)
                messagebox.showinfo("Export", "PDF report exported.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export PDF: {e}")


class CustomerDialog(ctk.CTkToplevel):
    """Modal dialog for adding/editing a customer."""

    def __init__(self, parent, conn, customer=None, tags=None, on_save=None):
        super().__init__(parent)
        self.conn = conn
        self.customer = customer
        self.on_save = on_save

        self.title("Edit Customer" if customer else "New Customer")
        self.geometry("480x560")
        self.resizable(False, False)
        self.after(100, self.grab_set)

        # Header
        ctk.CTkLabel(self,
                     text="Edit Customer" if customer else "New Customer",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(
            anchor="w", padx=24, pady=(20, 2))
        ctk.CTkLabel(self,
                     text="Update the details below" if customer else "Fill in the customer details",
                     font=ctk.CTkFont(size=12),
                     text_color="#64748B").pack(anchor="w", padx=24, pady=(0, 12))

        # Form
        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(fill="x", padx=24, pady=4)

        fields = [("Name", "name"), ("Company", "company"),
                  ("Phone", "phone"), ("Email", "email")]
        self.entries = {}
        for i, (label, key) in enumerate(fields):
            ctk.CTkLabel(form, text=label,
                         font=ctk.CTkFont(size=12),
                         text_color="#64748B").grid(
                row=i, column=0, padx=(0, 14), pady=6, sticky="e")
            entry = ctk.CTkEntry(form, width=280, corner_radius=8,
                                  placeholder_text=f"Enter {label.lower()}...")
            entry.insert(0, customer.get(key, "") if customer else "")
            entry.grid(row=i, column=1, pady=6, sticky="ew")
            self.entries[key] = entry

        # Category
        row = len(fields)
        ctk.CTkLabel(form, text="Category",
                     font=ctk.CTkFont(size=12),
                     text_color="#64748B").grid(
            row=row, column=0, padx=(0, 14), pady=6, sticky="e")
        self.cat_var = tk.StringVar(
            value=customer.get("category", "Active") if customer else "Active")
        self.cat_combo = ctk.CTkComboBox(
            form,
            values=["VIP", "Lead", "Active", "Inactive"],
            variable=self.cat_var,
            width=280, corner_radius=8
        )
        self.cat_combo.grid(row=row, column=1, pady=6, sticky="ew")

        form.columnconfigure(1, weight=1)

        # Tags section
        tag_section = ctk.CTkFrame(self, fg_color="transparent")
        tag_section.pack(fill="x", padx=24, pady=(12, 4))

        ctk.CTkLabel(tag_section, text="Tags",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color="#64748B").pack(anchor="w")

        tag_input_row = ctk.CTkFrame(tag_section, fg_color="transparent")
        tag_input_row.pack(fill="x", pady=(6, 4))
        self.tag_entry_widget = ctk.CTkEntry(tag_input_row, width=180,
                                              corner_radius=8,
                                              placeholder_text="Enter tag...")
        self.tag_entry_widget.pack(side="left", padx=(0, 6))
        ctk.CTkButton(tag_input_row, text="Add", width=60, height=30,
                      corner_radius=6,
                      fg_color="#2563EB", hover_color="#1D4ED8",
                      command=self._add_tag).pack(side="left", padx=(0, 4))
        ctk.CTkButton(tag_input_row, text="Remove", width=70, height=30,
                      corner_radius=6,
                      fg_color="#E2E8F0", hover_color="#CBD5E1",
                      text_color="#1E293B",
                      command=self._remove_tag).pack(side="left")

        list_frame = tk.Frame(tag_section, bg="#F8FAFC")
        list_frame.pack(fill="x", pady=(4, 0))
        self.tag_listbox = tk.Listbox(list_frame, height=4, bg="#F8FAFC",
                                       fg="#1E293B",
                                       selectbackground="#2563EB",
                                       selectforeground="#FFFFFF",
                                       relief="flat", borderwidth=4,
                                       font=("Helvetica", 10))
        self.tag_listbox.pack(fill="x")
        if tags:
            for t in tags:
                self.tag_listbox.insert("end", t)

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=24, pady=(16, 16))
        ctk.CTkButton(btn_frame, text="Cancel", width=90,
                      fg_color="#E2E8F0", hover_color="#CBD5E1",
                      text_color="#1E293B",
                      corner_radius=8,
                      command=self.destroy).pack(side="right", padx=(8, 0))
        ctk.CTkButton(btn_frame, text="Save", width=90,
                      fg_color="#2563EB", hover_color="#1D4ED8",
                      corner_radius=8,
                      command=self._save).pack(side="right")

    def _add_tag(self):
        tag = self.tag_entry_widget.get().strip()
        if tag and tag not in self.tag_listbox.get(0, "end"):
            self.tag_listbox.insert("end", tag)
        self.tag_entry_widget.delete(0, "end")

    def _remove_tag(self):
        sel = self.tag_listbox.curselection()
        if sel:
            self.tag_listbox.delete(sel[0])

    def _save(self):
        name = self.entries["name"].get().strip()
        if not name:
            messagebox.showwarning("Validation", "Name is required.", parent=self)
            return

        email = self.entries["email"].get().strip()
        if email and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            messagebox.showwarning("Validation", "Invalid email format.", parent=self)
            return

        tag_names = list(self.tag_listbox.get(0, "end"))
        kwargs = {
            "name": name,
            "company": self.entries["company"].get().strip(),
            "phone": self.entries["phone"].get().strip(),
            "email": email,
            "category": self.cat_var.get(),
            "tag_names": tag_names,
        }

        try:
            if self.customer:
                db.update_customer(self.conn, self.customer["id"], **kwargs)
            else:
                db.add_customer(self.conn, **kwargs)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save customer: {e}", parent=self)
            return

        self.destroy()
        if self.on_save:
            self.on_save()
