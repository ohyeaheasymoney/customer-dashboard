"""Main App: sidebar navigation + content frame orchestration, menu bar."""

import os
import logging
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import customtkinter as ctk

import database as db
from backup import backup_database, restore_database
from email_sender import load_smtp_config, save_smtp_config, test_connection
from updater import get_version, check_for_updates, apply_update

from tabs.dashboard_tab import DashboardTab
from tabs.customers_tab import CustomersTab
from tabs.follow_ups_tab import FollowUpsTab
from tabs.customer_detail_tab import CustomerDetailTab

logging.basicConfig(
    filename=os.path.join(os.path.dirname(__file__), "app.log"),
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


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
        try:
            self.conn = db.get_connection(DB_PATH)
            db.init_db(self.conn)
            logger.info("Application started, database connected: %s", DB_PATH)
        except Exception as e:
            logger.error("Failed to open database: %s", e)
            messagebox.showerror("Database Error",
                f"Failed to open database:\n{e}\n\nTry restoring from a backup.")
            # Still create connection to empty DB so app doesn't crash
            self.conn = db.get_connection(":memory:")
            db.init_db(self.conn)

        # Close DB on window close
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

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

        # ── Lazy tab definitions (created on first show) ────────────
        self._tab_factories = {
            "dashboard": lambda: DashboardTab(self.content_frame, self.conn),
            "customers": lambda: CustomersTab(self.content_frame, self.conn, self),
            "follow_ups": lambda: FollowUpsTab(self.content_frame, self.conn, self),
        }
        self._tab_labels = {
            "dashboard": "\u25A3  Dashboard",
            "customers": "\u25A1  Customers",
            "follow_ups": "\u25F4  Follow-ups",
        }
        self.dashboard_tab = None
        self.customers_tab = None
        self.follow_ups_tab = None

        # Register nav buttons (but don't create tab widgets yet)
        for name in ("dashboard", "customers", "follow_ups"):
            self._register_nav_button(name, self._tab_labels[name])

        # Separator before detail tabs section
        self.detail_separator = None
        self.detail_section_label = None

        # Show dashboard by default (this will lazily create it)
        self.show_page("dashboard")

        # Keyboard shortcuts
        self.root.bind("<Control-n>", lambda e: self._shortcut_add_customer())
        self.root.bind("<Control-f>", lambda e: self._shortcut_focus_search())
        self.root.bind("<Escape>", lambda e: self._shortcut_close_detail())
        self.root.bind("<Control-d>", lambda e: self.show_page("dashboard"))
        self.root.bind("<Control-u>", lambda e: self._check_updates())

        # Overdue badge — update periodically
        self._overdue_badge_label = None
        self.after(500, self._update_overdue_badge)

    def _on_close(self):
        """Close DB connection and destroy the application window."""
        logger.info("Application shutting down.")
        try:
            self.conn.close()
        except Exception:
            pass
        self.root.destroy()

    def _update_all_connections(self):
        """Update conn reference in all tabs after a restore."""
        for tab in (self.dashboard_tab, self.customers_tab, self.follow_ups_tab):
            if tab is not None:
                tab.conn = self.conn
        for page_name in self.detail_tabs.values():
            if page_name in self.pages:
                self.pages[page_name].conn = self.conn

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

        # Quick search
        search_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        search_frame.pack(fill="x", padx=12, pady=(0, 10))
        self.sidebar_search = ctk.CTkEntry(
            search_frame, height=30, corner_radius=0,
            fg_color="#1E40AF", border_width=0,
            text_color="#FFFFFF",
            placeholder_text="Search customers...",
            placeholder_text_color="#60A5FA",
            font=ctk.CTkFont(size=11),
        )
        self.sidebar_search.pack(fill="x")
        self.sidebar_search.bind("<Return>", self._sidebar_search_go)

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

        ver_row = ctk.CTkFrame(bottom, fg_color="transparent")
        ver_row.pack(fill="x")
        ctk.CTkLabel(ver_row, text=f"\u2726  Ajay's CRM  v{get_version()}",
                     font=ctk.CTkFont(size=10),
                     text_color="#60A5FA").pack(side="left")

        # One-click update button
        self.update_btn = ctk.CTkButton(
            ver_row, text="\u2B06", width=26, height=22,
            corner_radius=4, fg_color="#1E40AF",
            hover_color="#2563EB", text_color="#93C5FD",
            font=ctk.CTkFont(size=11),
            command=self._check_updates
        )
        self.update_btn.pack(side="right")

        ctk.CTkLabel(bottom, text="Built with CustomTkinter",
                     font=ctk.CTkFont(size=9),
                     text_color="#3B82F6").pack(anchor="w", pady=(2, 0))

    def _build_content(self):
        """Build the content area."""
        self.content_frame = ctk.CTkFrame(self, fg_color=COLORS["content_bg"],
                                           corner_radius=0)
        self.content_frame.grid(row=0, column=1, sticky="nsew")

    def _register_nav_button(self, name, label):
        """Create a sidebar nav button without creating the tab widget."""
        nav_btn = ctk.CTkButton(
            self.nav_container, text=label,
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

    def _register_detail_page(self, name, frame, label):
        """Register a detail page with close button in sidebar."""
        self.pages[name] = frame
        frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        frame.lower()

        row_frame = ctk.CTkFrame(self.detail_nav_container, fg_color="transparent")
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

    def _ensure_tab(self, name):
        """Lazily create a tab widget if it hasn't been created yet."""
        if name in self.pages:
            return
        if name not in self._tab_factories:
            return
        tab = self._tab_factories[name]()
        self.pages[name] = tab
        tab.place(relx=0, rely=0, relwidth=1, relheight=1)
        tab.lower()
        # Store reference for refresh_all_tabs
        if name == "dashboard":
            self.dashboard_tab = tab
        elif name == "customers":
            self.customers_tab = tab
        elif name == "follow_ups":
            self.follow_ups_tab = tab

    def show_page(self, name):
        """Show the specified page and highlight its nav item."""
        # Lazily create the tab if needed
        self._ensure_tab(name)

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
        file_menu.add_command(label="  Check for Updates  (Ctrl+U)",
                              command=self._check_updates)
        file_menu.add_separator()
        file_menu.add_command(label="  Exit", command=self._on_close)

    def refresh_all_tabs(self):
        for tab in (self.dashboard_tab, self.customers_tab, self.follow_ups_tab):
            if tab is not None:
                tab.refresh()
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
            messagebox.showwarning("Not Found", "Customer no longer exists.")
            return

        # Show detail section separator/label if this is the first detail tab
        if not self.detail_tabs:
            self._show_detail_section()

        detail = CustomerDetailTab(self.content_frame, self.conn, customer_id, self)
        self._register_detail_page(page_name, detail, "\u25B8  " + customer["name"])
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

    # ── Keyboard shortcuts ──────────────────────────────────────────

    def _shortcut_add_customer(self):
        """Ctrl+N — open add customer dialog."""
        self.show_page("customers")
        if self.customers_tab:
            self.customers_tab._add_customer()

    def _shortcut_focus_search(self):
        """Ctrl+F — focus the sidebar search."""
        self.sidebar_search.focus_set()
        self.sidebar_search.select_range(0, "end")

    def _shortcut_close_detail(self):
        """Escape — close current detail tab or clear search."""
        if self.sidebar_search == self.root.focus_get():
            self.sidebar_search.delete(0, "end")
            self.root.focus_set()
            return
        if self.active_page and self.active_page.startswith("detail_"):
            cid = int(self.active_page.replace("detail_", ""))
            self.close_customer_detail(cid)

    def _sidebar_search_go(self, event=None):
        """Enter in sidebar search — switch to customers tab with query."""
        query = self.sidebar_search.get().strip()
        if not query:
            return
        self.show_page("customers")
        if self.customers_tab:
            self.customers_tab.search_var.set(query)
        self.sidebar_search.delete(0, "end")
        self.root.focus_set()

    # ── Overdue badge ────────────────────────────────────────────────

    def _update_overdue_badge(self):
        """Show overdue count badge on Follow-ups nav button."""
        try:
            stats = db.get_stats(self.conn)
            overdue = stats.get("overdue_follow_ups", 0)
        except Exception:
            overdue = 0

        fu_btn_info = self.nav_buttons.get("follow_ups")
        if fu_btn_info:
            btn = fu_btn_info["button"]
            if overdue > 0:
                btn.configure(text=f"\u25F4  Follow-ups  ({overdue})")
            else:
                btn.configure(text="\u25F4  Follow-ups")

        # Refresh every 60 seconds
        self.after(60000, self._update_overdue_badge)

    # ── Version updater ──────────────────────────────────────────────

    def _check_updates(self):
        """Check for updates and offer to apply them."""
        self.update_btn.configure(text="\u2026", state="disabled")
        self.root.update_idletasks()

        has_update, msg = check_for_updates()
        self.update_btn.configure(text="\u2B06", state="normal")

        if has_update:
            if messagebox.askyesno("Update Available",
                                    f"{msg}\n\nDownload and install update?"):
                success, result_msg = apply_update()
                if success:
                    messagebox.showinfo("Updated", result_msg)
                else:
                    messagebox.showerror("Update Failed", result_msg)
        else:
            messagebox.showinfo("Up to Date", msg)

    def _email_settings(self):
        SmtpSettingsDialog(self.root)

    def _backup(self):
        try:
            path = backup_database(DB_PATH, BACKUP_DIR)
            logger.info("Database backed up to: %s", path)
            messagebox.showinfo("Backup", f"Database backed up to:\n{path}")
        except Exception as e:
            logger.error("Backup failed: %s", e)
            messagebox.showerror("Backup Error", str(e))

    def _restore(self):
        filepath = filedialog.askopenfilename(
            initialdir=BACKUP_DIR,
            filetypes=[("SQLite Database", "*.db")],
            title="Select Backup to Restore"
        )
        if not filepath:
            return
        # Validate filepath is a .db file
        if not filepath.endswith('.db'):
            messagebox.showerror("Error", "Please select a valid .db file.")
            return
        if not messagebox.askyesno("Confirm Restore",
                                    "This will replace the current database with the selected backup.\nContinue?"):
            return
        try:
            self.conn.close()
            restore_database(filepath, DB_PATH)
            self.conn = db.get_connection(DB_PATH)
            # Verify integrity
            if not db.check_integrity(self.conn):
                messagebox.showwarning("Warning", "Restored database may be corrupted.")
            # Update conn references
            self._update_all_connections()
            # Close detail tabs
            for cid in list(self.detail_tabs.keys()):
                self.close_customer_detail(cid)
            self.refresh_all_tabs()
            logger.info("Database restored from: %s", filepath)
            messagebox.showinfo("Restore", "Database restored successfully.")
        except Exception as e:
            logger.error("Restore failed: %s", e)
            # Try to reconnect to original DB
            try:
                self.conn = db.get_connection(DB_PATH)
            except Exception:
                pass
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
            entry = ctk.CTkEntry(form, width=280, corner_radius=0,
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
