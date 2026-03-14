"""Customer Detail page — 13-tab strategic account workbook with left nav."""

import re
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

import customtkinter as ctk
import database as db
from email_sender import load_smtp_config, send_email

from tabs.workbook.landing_page import LandingPage
from tabs.workbook.resources import ResourcesTab
from tabs.workbook.meeting_notes import MeetingNotesTab
from tabs.workbook.business_initiatives import BusinessInitiativesTab
from tabs.workbook.contact_development import ContactDevelopmentTab
from tabs.workbook.account_goals import AccountGoalsTab
from tabs.workbook.action_items import ActionItemsTab
from tabs.workbook.cph_report import CphReportTab
from tabs.workbook.hw_sw_landscape import HwSwLandscapeTab
from tabs.workbook.application_landscape import ApplicationLandscapeTab
from tabs.workbook.service_landscape import ServiceLandscapeTab
from tabs.workbook.tech_profile import TechProfileTab
from tabs.workbook.teamed_guidance import TeamedGuidanceTab

# Navigation structure: (section_label, [(key, display_name, TabClass), ...])
NAV_SECTIONS = [
    ("\u25A0  OVERVIEW", [
        ("landing",    "\u25A3  Dashboard",       LandingPage),
        ("resources",  "\u25CB  Team Resources",   ResourcesTab),
    ]),
    ("\u25C6  ENGAGEMENT", [
        ("meetings",   "\u25B7  Meeting Notes",    MeetingNotesTab),
        ("contacts",   "\u25C8  Contacts",         ContactDevelopmentTab),
        ("actions",    "\u2713  Action Items",     ActionItemsTab),
    ]),
    ("\u25B2  STRATEGY", [
        ("initiatives","\u25B8  Business Init.",   BusinessInitiativesTab),
        ("goals",      "\u2605  Goals",            AccountGoalsTab),
    ]),
    ("\u25C9  TECHNOLOGY", [
        ("hwsw",       "\u25A1  HW / SW",          HwSwLandscapeTab),
        ("apps",       "\u25CE  Applications",     ApplicationLandscapeTab),
        ("services",   "\u25C7  Services",         ServiceLandscapeTab),
        ("techprofile","\u2699  Tech Profile",     TechProfileTab),
    ]),
    ("\u25B6  FINANCIAL", [
        ("cph",        "\u25A8  CPH Report",       CphReportTab),
    ]),
    ("\u25CF  OTHER", [
        ("guidance",   "\u25BA  Guidance",         TeamedGuidanceTab),
    ]),
]


class CustomerDetailTab(ctk.CTkFrame):
    def __init__(self, parent, conn, customer_id, app):
        super().__init__(parent, fg_color="#F0F4F8")
        self.conn = conn
        self.customer_id = customer_id
        self.app = app
        self._subtabs = {}
        self._nav_buttons = {}
        self._active_key = None
        self._build_ui()

    def _build_ui(self):
        # ── Header bar ─────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=0,
                              border_width=0)
        header.pack(fill="x", side="top")

        # Blue accent line at very top
        ctk.CTkFrame(header, fg_color="#2563EB", height=3,
                     corner_radius=0).pack(fill="x", side="top")

        header_inner = ctk.CTkFrame(header, fg_color="transparent")
        header_inner.pack(fill="x", padx=24, pady=(12, 12))

        # Left: avatar circle + name + subtitle
        left = ctk.CTkFrame(header_inner, fg_color="transparent")
        left.pack(side="left", fill="x", expand=True)

        left_row = ctk.CTkFrame(left, fg_color="transparent")
        left_row.pack(anchor="w")

        self.avatar_canvas = tk.Canvas(left_row, width=44, height=44,
                                        bg="#FFFFFF", highlightthickness=0)
        self.avatar_canvas.create_oval(2, 2, 42, 42, fill="#DBEAFE",
                                        outline="#93C5FD", width=2)
        self.avatar_canvas.create_text(22, 22, text="?", fill="#1E3A8A",
                                        font=("Helvetica", 16, "bold"))
        self.avatar_canvas.pack(side="left", padx=(0, 12))

        name_block = ctk.CTkFrame(left_row, fg_color="transparent")
        name_block.pack(side="left")

        self.name_label = ctk.CTkLabel(
            name_block, text="", font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#1E293B")
        self.name_label.pack(anchor="w")

        self.subtitle_label = ctk.CTkLabel(
            name_block, text="", font=ctk.CTkFont(size=11),
            text_color="#64748B")
        self.subtitle_label.pack(anchor="w", pady=(2, 0))

        # Right: action buttons
        right = ctk.CTkFrame(header_inner, fg_color="transparent")
        right.pack(side="right")

        ctk.CTkButton(
            right, text="Edit", width=80, height=34, corner_radius=8,
            fg_color="#F1F5F9", hover_color="#E2E8F0", text_color="#1E293B",
            font=ctk.CTkFont(size=12),
            border_width=1, border_color="#CBD5E1",
            command=self._edit_customer).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            right, text="Send Email", width=110, height=34, corner_radius=8,
            fg_color="#2563EB", hover_color="#1D4ED8",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._send_email).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            right, text="Close", width=80, height=34, corner_radius=8,
            fg_color="#FEE2E2", hover_color="#FECACA", text_color="#991B1B",
            font=ctk.CTkFont(size=12),
            command=self._close_tab).pack(side="left")

        # Bottom border on header
        ctk.CTkFrame(header, fg_color="#E2E8F0", height=1,
                     corner_radius=0).pack(fill="x", side="bottom")

        # ── Body: left nav + content ───────────────────────────────────
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True)

        # Left nav panel
        nav_panel = ctk.CTkFrame(body, fg_color="#FFFFFF", width=185,
                                 corner_radius=0)
        nav_panel.pack(side="left", fill="y")
        nav_panel.pack_propagate(False)

        # Right border on nav
        ctk.CTkFrame(nav_panel, fg_color="#E2E8F0", width=1,
                     corner_radius=0).pack(side="right", fill="y")

        nav_scroll = ctk.CTkScrollableFrame(nav_panel, fg_color="#FFFFFF",
                                            scrollbar_button_color="#CBD5E1",
                                            scrollbar_button_hover_color="#94A3B8")
        nav_scroll.pack(fill="both", expand=True, padx=0, pady=0)

        # Build nav sections
        for section_label, items in NAV_SECTIONS:
            ctk.CTkLabel(
                nav_scroll, text=section_label,
                font=ctk.CTkFont(size=9, weight="bold"),
                text_color="#94A3B8",
            ).pack(anchor="w", padx=16, pady=(14, 4))

            for key, display_name, TabClass in items:
                btn = ctk.CTkButton(
                    nav_scroll, text=display_name,
                    fg_color="transparent",
                    hover_color="#EFF6FF",
                    text_color="#475569",
                    anchor="w", height=34,
                    font=ctk.CTkFont(size=12),
                    corner_radius=6,
                    command=lambda k=key: self._show_subtab(k),
                )
                btn.pack(fill="x", padx=8, pady=1)
                self._nav_buttons[key] = btn

        # Content area
        self._content = ctk.CTkFrame(body, fg_color="#F0F4F8",
                                     corner_radius=0)
        self._content.pack(side="left", fill="both", expand=True)

        # Create all sub-tabs (stacked, hidden)
        for _section_label, items in NAV_SECTIONS:
            for key, _display_name, TabClass in items:
                subtab = TabClass(self._content, self.conn,
                                  self.customer_id, self.app)
                subtab.place(relx=0, rely=0, relwidth=1, relheight=1)
                subtab.lower()
                self._subtabs[key] = subtab

        # Show first tab
        self._show_subtab("landing")

    def _show_subtab(self, key):
        if key == self._active_key:
            return

        # Deactivate old
        if self._active_key and self._active_key in self._nav_buttons:
            self._nav_buttons[self._active_key].configure(
                fg_color="transparent", text_color="#475569",
                font=ctk.CTkFont(size=12))
        if self._active_key and self._active_key in self._subtabs:
            self._subtabs[self._active_key].lower()

        # Activate new
        self._active_key = key
        self._nav_buttons[key].configure(
            fg_color="#EFF6FF", text_color="#1D4ED8",
            font=ctk.CTkFont(size=12, weight="bold"))
        self._subtabs[key].lift()

    def refresh(self):
        customer = db.get_customer(self.conn, self.customer_id)
        if not customer:
            # Customer was deleted, close this tab
            self.after(100, lambda: self.app.close_customer_detail(self.customer_id))
            return

        self.name_label.configure(text=customer["name"])
        subtitle = (f"{customer['company']}  \u2022  {customer['category']}"
                    if customer["company"] else customer["category"])
        self.subtitle_label.configure(text=subtitle)

        # Update avatar initials
        parts = customer["name"].split()
        initials = (parts[0][0] + (parts[-1][0] if len(parts) > 1 else "")).upper()
        self.avatar_canvas.delete("all")
        self.avatar_canvas.create_oval(2, 2, 42, 42, fill="#DBEAFE",
                                        outline="#93C5FD", width=2)
        self.avatar_canvas.create_text(22, 22, text=initials, fill="#1E3A8A",
                                        font=("Helvetica", 14, "bold"))

        for subtab in self._subtabs.values():
            subtab.refresh()

    def _edit_customer(self):
        from tabs.customers_tab import CustomerDialog
        try:
            customer = db.get_customer(self.conn, self.customer_id)
            tags = db.get_customer_tags(self.conn, self.customer_id)
            CustomerDialog(self, self.conn, customer=customer, tags=tags,
                           on_save=lambda: self.app.refresh_all_tabs())
        except Exception as e:
            messagebox.showerror("Error", f"Failed to edit customer: {e}")

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
                     text_color="#64748B").grid(row=0, column=0, sticky="e",
                                                padx=(0, 14), pady=6)
        self.date_entry = ctk.CTkEntry(form, width=260, corner_radius=8,
                                        placeholder_text="YYYY-MM-DD")
        self.date_entry.insert(0,
                               existing["due_date"] if existing
                               else datetime.now().strftime("%Y-%m-%d"))
        self.date_entry.grid(row=0, column=1, pady=6, sticky="ew")

        ctk.CTkLabel(form, text="Type",
                     font=ctk.CTkFont(size=12),
                     text_color="#64748B").grid(row=1, column=0, sticky="e",
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
                     text_color="#64748B").grid(row=2, column=0, sticky="ne",
                                                padx=(0, 14), pady=6)
        self.desc_text = ctk.CTkTextbox(form, height=80,
                                         fg_color="#F8FAFC",
                                         text_color="#1E293B",
                                         font=ctk.CTkFont(size=12),
                                         corner_radius=8,
                                         border_width=1,
                                         border_color="#CBD5E1")
        self.desc_text.grid(row=2, column=1, pady=6, sticky="ew")
        if existing and existing["description"]:
            self.desc_text.insert("0.0", existing["description"])

        form.columnconfigure(1, weight=1)

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
                     text_color="#64748B").pack(anchor="w", padx=24, pady=(0, 12))

        # Form
        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=24, pady=4)

        ctk.CTkLabel(form, text="To",
                     font=ctk.CTkFont(size=12),
                     text_color="#64748B").grid(row=0, column=0, sticky="e",
                                                padx=(0, 14), pady=6)
        self.to_entry = ctk.CTkEntry(form, width=400, corner_radius=8)
        self.to_entry.insert(0, customer.get("email", ""))
        self.to_entry.grid(row=0, column=1, pady=6, sticky="ew")

        ctk.CTkLabel(form, text="Subject",
                     font=ctk.CTkFont(size=12),
                     text_color="#64748B").grid(row=1, column=0, sticky="e",
                                                padx=(0, 14), pady=6)
        self.subject_entry = ctk.CTkEntry(form, width=400, corner_radius=8,
                                           placeholder_text="Enter subject...")
        self.subject_entry.grid(row=1, column=1, pady=6, sticky="ew")

        ctk.CTkLabel(form, text="Body",
                     font=ctk.CTkFont(size=12),
                     text_color="#64748B").grid(row=2, column=0, sticky="ne",
                                                padx=(0, 14), pady=6)
        self.body_text = ctk.CTkTextbox(form, height=250,
                                         fg_color="#F8FAFC",
                                         text_color="#1E293B",
                                         font=ctk.CTkFont(size=12),
                                         corner_radius=8,
                                         border_width=1,
                                         border_color="#CBD5E1")
        self.body_text.grid(row=2, column=1, pady=6, sticky="nsew")

        form.columnconfigure(1, weight=1)
        form.rowconfigure(2, weight=1)

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=24, pady=(8, 16))
        ctk.CTkButton(btn_frame, text="Cancel", width=90,
                      fg_color="#E2E8F0", hover_color="#CBD5E1",
                      text_color="#1E293B",
                      corner_radius=8,
                      command=self.destroy).pack(side="right", padx=(8, 0))
        ctk.CTkButton(btn_frame, text="Send", width=90,
                      fg_color="#2563EB", hover_color="#1D4ED8",
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

        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', to):
            messagebox.showwarning("Validation", "Invalid email address.",
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
