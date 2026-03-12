"""Customer Detail page — 13-tab strategic account workbook."""

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


class CustomerDetailTab(ctk.CTkFrame):
    def __init__(self, parent, conn, customer_id, app):
        super().__init__(parent, fg_color="#F0F4F8")
        self.conn = conn
        self.customer_id = customer_id
        self.app = app
        self._subtabs = {}
        self._build_ui()

    def _build_ui(self):
        # ── Header bar with name and action buttons ────────────────────
        header_card = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=12,
                                   border_width=1, border_color="#E2E8F0")
        header_card.pack(fill="x", padx=16, pady=(12, 0))

        header_inner = ctk.CTkFrame(header_card, fg_color="transparent")
        header_inner.pack(fill="x", padx=20, pady=14)

        # Left side: customer name + subtitle
        header_left = ctk.CTkFrame(header_inner, fg_color="transparent")
        header_left.pack(side="left", fill="x", expand=True)

        self.name_label = ctk.CTkLabel(header_left, text="",
                                        font=ctk.CTkFont(size=20, weight="bold"),
                                        text_color="#1E293B")
        self.name_label.pack(anchor="w")
        self.subtitle_label = ctk.CTkLabel(header_left, text="",
                                            font=ctk.CTkFont(size=12),
                                            text_color="#64748B")
        self.subtitle_label.pack(anchor="w", pady=(2, 0))

        # Right side: action buttons
        header_right = ctk.CTkFrame(header_inner, fg_color="transparent")
        header_right.pack(side="right")
        ctk.CTkButton(header_right, text="Edit", width=70, height=32,
                      corner_radius=8,
                      fg_color="#E2E8F0", hover_color="#CBD5E1",
                      text_color="#1E293B",
                      border_width=1, border_color="#CBD5E1",
                      command=self._edit_customer).pack(side="left", padx=(0, 6))
        ctk.CTkButton(header_right, text="Send Email", width=100, height=32,
                      corner_radius=8,
                      fg_color="#2563EB", hover_color="#1D4ED8",
                      command=self._send_email).pack(side="left", padx=(0, 6))
        ctk.CTkButton(header_right, text="Close", width=70, height=32,
                      corner_radius=8,
                      fg_color="#DC2626", hover_color="#B91C1C",
                      command=self._close_tab).pack(side="left")

        # ── Tabview with 13 sub-tabs ──────────────────────────────────
        self.tabview = ctk.CTkTabview(self, fg_color="#F0F4F8",
                                      segmented_button_fg_color="#E2E8F0",
                                      segmented_button_selected_color="#2563EB",
                                      segmented_button_selected_hover_color="#1D4ED8",
                                      segmented_button_unselected_color="#E2E8F0",
                                      segmented_button_unselected_hover_color="#CBD5E1",
                                      corner_radius=8)
        self.tabview.pack(fill="both", expand=True, padx=8, pady=(8, 8))

        # Define tabs in order
        tab_defs = [
            ("Landing", LandingPage),
            ("Resources", ResourcesTab),
            ("Meeting Notes", MeetingNotesTab),
            ("Business Init.", BusinessInitiativesTab),
            ("Contacts", ContactDevelopmentTab),
            ("Goals", AccountGoalsTab),
            ("Action Items", ActionItemsTab),
            ("CPH Report", CphReportTab),
            ("HW/SW", HwSwLandscapeTab),
            ("Applications", ApplicationLandscapeTab),
            ("Services", ServiceLandscapeTab),
            ("Tech Profile", TechProfileTab),
            ("Guidance", TeamedGuidanceTab),
        ]

        for tab_name, TabClass in tab_defs:
            tab_frame = self.tabview.add(tab_name)
            subtab = TabClass(tab_frame, self.conn, self.customer_id, self.app)
            subtab.pack(fill="both", expand=True)
            self._subtabs[tab_name] = subtab

        self.tabview.set("Landing")

    def refresh(self):
        # Update header
        customer = db.get_customer(self.conn, self.customer_id)
        if not customer:
            return

        self.name_label.configure(text=customer["name"])
        self.subtitle_label.configure(
            text=f"{customer['company']}  |  {customer['category']}"
            if customer["company"] else customer["category"])

        # Refresh all sub-tabs
        for subtab in self._subtabs.values():
            subtab.refresh()

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
