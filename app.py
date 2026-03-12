"""Main App: sidebar navigation + content frame orchestration, menu bar."""

import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import customtkinter as ctk

import database as db
from backup import backup_database, restore_database
from email_sender import load_smtp_config, save_smtp_config, test_connection

from tabs.dashboard_tab import DashboardTab
from tabs.customers_tab import CustomersTab
from tabs.follow_ups_tab import FollowUpsTab
from tabs.customer_detail_tab import CustomerDetailTab


DB_PATH = os.path.join(os.path.dirname(__file__), "customers.db")
BACKUP_DIR = os.path.join(os.path.dirname(__file__), "backups")

# Color palette — white + royal-blue
COLORS = {
    "sidebar_bg": "#1E3A8A",
    "sidebar_hover": "#1E40AF",
    "sidebar_active": "#2563EB",
    "content_bg": "#F0F4F8",
    "card": "#FFFFFF",
    "primary": "#2563EB",
    "primary_hover": "#1D4ED8",
    "success": "#059669",
    "warning": "#D97706",
    "danger": "#DC2626",
    "text": "#1E293B",
    "text_dim": "#64748B",
    "border": "#CBD5E1",
}


def _configure_treeview_style():
    """Configure ttk.Treeview style to match the dark/modern theme."""
    style = ttk.Style()
    style.theme_use("clam")

    style.configure("Treeview",
                    background="#FFFFFF",
                    foreground="#1E293B",
                    fieldbackground="#FFFFFF",
                    borderwidth=0,
                    relief="flat",
                    rowheight=32,
                    font=("Helvetica", 10))
    style.configure("Treeview.Heading",
                    background="#EFF6FF",
                    foreground="#1E3A8A",
                    borderwidth=0,
                    relief="flat",
                    font=("Helvetica", 10, "bold"),
                    padding=(8, 6))
    style.map("Treeview",
              background=[("selected", "#2563EB")],
              foreground=[("selected", "#FFFFFF")])
    style.map("Treeview.Heading",
              background=[("active", "#DBEAFE")])

    style.configure("Vertical.TScrollbar",
                    background="#E2E8F0",
                    troughcolor="#F1F5F9",
                    borderwidth=0,
                    arrowsize=14)

    return style


class App(ctk.CTkFrame):
    """Main application with sidebar navigation and content area."""

    def __init__(self, root):
        super().__init__(root, fg_color="transparent")
        self.root = root
        self.pack(fill="both", expand=True)

        # Configure treeview style
        self._ttk_style = _configure_treeview_style()

        # Database
        self.conn = db.get_connection(DB_PATH)
        db.init_db(self.conn)

        # Menu bar
        self._build_menu()

        # ── Build layout ──────────────────────────────────────────────
        self.grid_columnconfigure(0, weight=0, minsize=220)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_content()

        # Track pages and nav items
        self.pages = {}         # name -> frame
        self.nav_buttons = {}   # name -> CTkButton
        self.detail_tabs = {}   # customer_id -> page_name
        self.active_page = None

        # ── Create core pages ─────────────────────────────────────────
        self.dashboard_tab = DashboardTab(self.content_frame, self.conn)
        self._register_page("dashboard", self.dashboard_tab, "\u25A3  Dashboard")

        self.customers_tab = CustomersTab(self.content_frame, self.conn, self)
        self._register_page("customers", self.customers_tab, "\u25A1  Customers")

        self.follow_ups_tab = FollowUpsTab(self.content_frame, self.conn, self)
        self._register_page("follow_ups", self.follow_ups_tab, "\u25F4  Follow-ups")

        # Separator before detail tabs section
        self.detail_separator = None
        self.detail_section_label = None

        # Show dashboard by default
        self.show_page("dashboard")

        # Initial refresh
        self.refresh_all_tabs()

    def _build_sidebar(self):
        """Build the sidebar navigation."""
        self.sidebar = ctk.CTkFrame(self, fg_color=COLORS["sidebar_bg"],
                                     corner_radius=0, width=220)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        # App logo/title
        title_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        title_frame.pack(fill="x", padx=16, pady=(20, 4))

        # Logo row: icon circle + text
        logo_row = ctk.CTkFrame(title_frame, fg_color="transparent")
        logo_row.pack(anchor="w")

        logo_circle = tk.Canvas(logo_row, width=38, height=38,
                                bg="#1E3A8A", highlightthickness=0)
        logo_circle.create_oval(2, 2, 36, 36, fill="#2563EB", outline="#3B82F6",
                                width=2)
        logo_circle.create_text(19, 19, text="AC", fill="#FFFFFF",
                                font=("Helvetica", 13, "bold"))
        logo_circle.pack(side="left", padx=(0, 10))

        logo_text = ctk.CTkFrame(logo_row, fg_color="transparent")
        logo_text.pack(side="left")
        ctk.CTkLabel(logo_text, text="Ajay's CRM",
                     font=ctk.CTkFont(size=17, weight="bold"),
                     text_color="#FFFFFF").pack(anchor="w")
        ctk.CTkLabel(logo_text, text="Customer Dashboard",
                     font=ctk.CTkFont(size=10),
                     text_color="#93C5FD").pack(anchor="w", pady=(1, 0))

        # Separator line
        sep = ctk.CTkFrame(self.sidebar, fg_color="#3B82F6", height=1)
        sep.pack(fill="x", padx=16, pady=(16, 12))

        # Section label
        ctk.CTkLabel(self.sidebar, text="  NAVIGATION",
                     font=ctk.CTkFont(size=9, weight="bold"),
                     text_color="#60A5FA").pack(fill="x", padx=16, pady=(0, 6), anchor="w")

        # Navigation buttons container
        self.nav_container = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.nav_container.pack(fill="x")

        # Detail tabs section (created dynamically)
        self.detail_nav_container = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.detail_nav_container.pack(fill="x")

        # Bottom section - version info
        bottom = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        bottom.pack(side="bottom", fill="x", padx=16, pady=(0, 16))

        ctk.CTkFrame(bottom, fg_color="#3B82F6", height=1).pack(
            fill="x", pady=(0, 10))
        ctk.CTkLabel(bottom, text="\u2726  Ajay's CRM  v2.0",
                     font=ctk.CTkFont(size=10),
                     text_color="#60A5FA").pack(anchor="w")
        ctk.CTkLabel(bottom, text="Built with CustomTkinter",
                     font=ctk.CTkFont(size=9),
                     text_color="#3B82F6").pack(anchor="w", pady=(2, 0))

    def _build_content(self):
        """Build the content area."""
        self.content_frame = ctk.CTkFrame(self, fg_color=COLORS["content_bg"],
                                           corner_radius=0)
        self.content_frame.grid(row=0, column=1, sticky="nsew")

    def _register_page(self, name, frame, label, is_detail=False):
        """Register a page and create its sidebar nav button."""
        self.pages[name] = frame
        # Place frame but hide it
        frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        frame.lower()

        container = self.detail_nav_container if is_detail else self.nav_container

        if is_detail:
            # For detail tabs, create a frame with button + close button
            row_frame = ctk.CTkFrame(container, fg_color="transparent")
            row_frame.pack(fill="x", padx=8, pady=1)

            nav_btn = ctk.CTkButton(
                row_frame, text=label,
                fg_color="transparent",
                hover_color=COLORS["sidebar_hover"],
                text_color="#DBEAFE",
                anchor="w", height=36,
                font=ctk.CTkFont(size=12),
                corner_radius=6,
                command=lambda n=name: self.show_page(n)
            )
            nav_btn.pack(side="left", fill="x", expand=True)

            # Close button
            cid = int(name.replace("detail_", ""))
            close_btn = ctk.CTkButton(
                row_frame, text="\u2715", width=28, height=28,
                fg_color="transparent",
                hover_color="#DC2626",
                text_color="#93C5FD",
                font=ctk.CTkFont(size=11),
                corner_radius=4,
                command=lambda c=cid: self.close_customer_detail(c)
            )
            close_btn.pack(side="right", padx=(0, 4))

            self.nav_buttons[name] = {"button": nav_btn, "frame": row_frame}
        else:
            nav_btn = ctk.CTkButton(
                container, text=label,
                fg_color="transparent",
                hover_color=COLORS["sidebar_hover"],
                text_color="#DBEAFE",
                anchor="w", height=40,
                font=ctk.CTkFont(size=13),
                corner_radius=6,
                command=lambda n=name: self.show_page(n)
            )
            nav_btn.pack(fill="x", padx=8, pady=1)
            self.nav_buttons[name] = {"button": nav_btn}

    def show_page(self, name):
        """Show the specified page and highlight its nav item."""
        if name not in self.pages:
            return

        # Deactivate old nav button
        if self.active_page and self.active_page in self.nav_buttons:
            old_btn = self.nav_buttons[self.active_page]["button"]
            old_btn.configure(fg_color="transparent", text_color="#DBEAFE")

        # Hide old page
        if self.active_page and self.active_page in self.pages:
            self.pages[self.active_page].lower()

        # Activate new nav button
        self.active_page = name
        new_btn = self.nav_buttons[name]["button"]
        new_btn.configure(fg_color=COLORS["sidebar_active"], text_color="#FFFFFF")

        # Show page
        self.pages[name].lift()

        # Refresh the page
        page = self.pages[name]
        if hasattr(page, "refresh"):
            page.refresh()

    def _build_menu(self):
        menubar = tk.Menu(self.root, bg="#FFFFFF", fg="#1E293B",
                          activebackground="#2563EB", activeforeground="#FFFFFF",
                          relief="flat", borderwidth=0)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0,
                            bg="#FFFFFF", fg="#1E293B",
                            activebackground="#2563EB", activeforeground="#FFFFFF")
        menubar.add_cascade(label="  File  ", menu=file_menu)
        file_menu.add_command(label="  Email Settings...", command=self._email_settings)
        file_menu.add_separator()
        file_menu.add_command(label="  Backup Database", command=self._backup)
        file_menu.add_command(label="  Restore from Backup...", command=self._restore)
        file_menu.add_separator()
        file_menu.add_command(label="  Exit", command=self.root.quit)

    def refresh_all_tabs(self):
        self.dashboard_tab.refresh()
        self.customers_tab.refresh()
        self.follow_ups_tab.refresh()
        for cid, page_name in list(self.detail_tabs.items()):
            if page_name in self.pages:
                page = self.pages[page_name]
                if page.winfo_exists():
                    page.refresh()

    def open_customer_detail(self, customer_id):
        page_name = f"detail_{customer_id}"
        if page_name in self.pages:
            page = self.pages[page_name]
            if page.winfo_exists():
                self.show_page(page_name)
                return

        customer = db.get_customer(self.conn, customer_id)
        if not customer:
            return

        # Show detail section separator/label if this is the first detail tab
        if not self.detail_tabs:
            self._show_detail_section()

        detail = CustomerDetailTab(self.content_frame, self.conn, customer_id, self)
        self._register_page(page_name, detail, "\u25B8  " + customer["name"], is_detail=True)
        self.detail_tabs[customer_id] = page_name
        self.show_page(page_name)
        detail.refresh()

    def _show_detail_section(self):
        """Show the 'OPEN CUSTOMERS' section header in sidebar."""
        if self.detail_separator:
            return
        self.detail_separator = ctk.CTkFrame(
            self.detail_nav_container, fg_color="#3B82F6", height=1
        )
        self.detail_separator.pack(fill="x", padx=16, pady=(12, 4))

        self.detail_section_label = ctk.CTkLabel(
            self.detail_nav_container, text="  \u25C8  OPEN ACCOUNTS",
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color="#60A5FA"
        )
        self.detail_section_label.pack(fill="x", padx=16, pady=(0, 4), anchor="w")

    def _hide_detail_section(self):
        """Hide the detail section header if no detail tabs remain."""
        if self.detail_separator:
            self.detail_separator.destroy()
            self.detail_separator = None
        if self.detail_section_label:
            self.detail_section_label.destroy()
            self.detail_section_label = None

    def close_customer_detail(self, customer_id):
        page_name = f"detail_{customer_id}"
        if customer_id in self.detail_tabs:
            del self.detail_tabs[customer_id]

        if page_name in self.pages:
            page = self.pages.pop(page_name)
            if page.winfo_exists():
                page.destroy()

        if page_name in self.nav_buttons:
            nav = self.nav_buttons.pop(page_name)
            if "frame" in nav:
                nav["frame"].destroy()
            else:
                nav["button"].destroy()

        # If we were viewing this page, switch to dashboard
        if self.active_page == page_name:
            self.show_page("dashboard")

        # Hide detail section if no more detail tabs
        if not self.detail_tabs:
            self._hide_detail_section()

    def _email_settings(self):
        SmtpSettingsDialog(self.root)

    def _backup(self):
        try:
            path = backup_database(DB_PATH, BACKUP_DIR)
            messagebox.showinfo("Backup", f"Database backed up to:\n{path}")
        except Exception as e:
            messagebox.showerror("Backup Error", str(e))

    def _restore(self):
        filepath = filedialog.askopenfilename(
            initialdir=BACKUP_DIR,
            filetypes=[("SQLite Database", "*.db")],
            title="Select Backup to Restore"
        )
        if not filepath:
            return
        if not messagebox.askyesno("Confirm Restore",
                                    "This will replace the current database with the selected backup.\nContinue?"):
            return
        try:
            self.conn.close()
            restore_database(filepath, DB_PATH)
            self.conn = db.get_connection(DB_PATH)
            # Update connection references in all tabs
            self.dashboard_tab.conn = self.conn
            self.customers_tab.conn = self.conn
            self.follow_ups_tab.conn = self.conn
            # Close all detail tabs
            for cid in list(self.detail_tabs.keys()):
                self.close_customer_detail(cid)
            self.refresh_all_tabs()
            messagebox.showinfo("Restore", "Database restored successfully.")
        except Exception as e:
            messagebox.showerror("Restore Error", str(e))


class SmtpSettingsDialog(ctk.CTkToplevel):
    """SMTP settings configuration dialog."""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Email Settings (SMTP)")
        self.geometry("500x420")
        self.resizable(False, False)
        self.after(100, self.grab_set)

        # Header
        ctk.CTkLabel(self, text="SMTP Configuration",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(
            anchor="w", padx=24, pady=(20, 2))
        ctk.CTkLabel(self, text="Configure your email server settings",
                     font=ctk.CTkFont(size=12),
                     text_color="#64748B").pack(anchor="w", padx=24, pady=(0, 12))

        # Form
        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(fill="x", padx=24, pady=4)

        config = load_smtp_config()

        fields = [
            ("SMTP Server", "smtp_server"),
            ("Port", "smtp_port"),
            ("Username", "username"),
            ("Password", "password"),
            ("Sender Name", "sender_name"),
        ]
        self.entries = {}
        for i, (label, key) in enumerate(fields):
            ctk.CTkLabel(form, text=label,
                         font=ctk.CTkFont(size=12),
                         text_color="#64748B").grid(
                row=i, column=0, padx=(0, 16), pady=6, sticky="e")
            entry = ctk.CTkEntry(form, width=280, corner_radius=8,
                                  placeholder_text=f"Enter {label.lower()}...")
            if key == "password":
                entry.configure(show="*")
            entry.insert(0, str(config.get(key, "")))
            entry.grid(row=i, column=1, pady=6, sticky="ew")
            self.entries[key] = entry
        form.columnconfigure(1, weight=1)

        # Presets
        row = len(fields)
        ctk.CTkLabel(form, text="Presets",
                     font=ctk.CTkFont(size=12),
                     text_color="#64748B").grid(
            row=row, column=0, padx=(0, 16), pady=6, sticky="e")
        preset_frame = ctk.CTkFrame(form, fg_color="transparent")
        preset_frame.grid(row=row, column=1, pady=6, sticky="w")
        ctk.CTkButton(preset_frame, text="Gmail", width=80, height=30,
                      corner_radius=6,
                      fg_color="#E2E8F0", hover_color="#CBD5E1", text_color="#1E293B",
                      command=lambda: self._preset("smtp.gmail.com", "587")).pack(
            side="left", padx=(0, 6))
        ctk.CTkButton(preset_frame, text="Outlook", width=80, height=30,
                      corner_radius=6,
                      fg_color="#E2E8F0", hover_color="#CBD5E1", text_color="#1E293B",
                      command=lambda: self._preset("smtp.office365.com", "587")).pack(
            side="left")

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=24, pady=(20, 16))
        ctk.CTkButton(btn_frame, text="Cancel", width=90,
                      fg_color="#E2E8F0", hover_color="#CBD5E1", text_color="#1E293B",
                      corner_radius=8,
                      command=self.destroy).pack(side="right", padx=(8, 0))
        ctk.CTkButton(btn_frame, text="Save", width=90,
                      corner_radius=8,
                      command=self._save).pack(side="right", padx=(8, 0))
        ctk.CTkButton(btn_frame, text="Test Connection", width=130,
                      fg_color="#E2E8F0", hover_color="#CBD5E1", text_color="#1E293B",
                      corner_radius=8,
                      command=self._test).pack(side="right")

    def _preset(self, server, port):
        self.entries["smtp_server"].delete(0, "end")
        self.entries["smtp_server"].insert(0, server)
        self.entries["smtp_port"].delete(0, "end")
        self.entries["smtp_port"].insert(0, port)

    def _get_config(self):
        return {key: entry.get() for key, entry in self.entries.items()}

    def _test(self):
        config = self._get_config()
        success, msg = test_connection(config)
        if success:
            messagebox.showinfo("Test", msg, parent=self)
        else:
            messagebox.showerror("Test", msg, parent=self)

    def _save(self):
        save_smtp_config(self._get_config())
        messagebox.showinfo("Saved", "SMTP settings saved.", parent=self)
        self.destroy()
