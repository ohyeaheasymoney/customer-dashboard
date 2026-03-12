"""Dashboard page -- summary stats and matplotlib charts."""

import tkinter as tk
from tkinter import ttk
from datetime import datetime
from collections import defaultdict

import customtkinter as ctk
import database as db


class DashboardTab(ctk.CTkFrame):
    def __init__(self, parent, conn):
        super().__init__(parent, fg_color="#F0F4F8")
        self.conn = conn
        self._build_ui()

    def _build_ui(self):
        # ── Welcome banner ────────────────────────────────────────────
        banner = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=12,
                              border_width=1, border_color="#E2E8F0")
        banner.pack(fill="x", padx=28, pady=(24, 0))

        banner_inner = ctk.CTkFrame(banner, fg_color="transparent")
        banner_inner.pack(fill="x", padx=20, pady=18)

        # Greeting with time-of-day
        hour = datetime.now().hour
        if hour < 12:
            greeting = "Good Morning"
            icon = "\u2600"   # sun
        elif hour < 17:
            greeting = "Good Afternoon"
            icon = "\u263C"   # sun with rays
        else:
            greeting = "Good Evening"
            icon = "\u263E"   # moon

        greeting_row = ctk.CTkFrame(banner_inner, fg_color="transparent")
        greeting_row.pack(anchor="w")

        ctk.CTkLabel(greeting_row, text=f"{icon}  {greeting}, Ajay!",
                     font=ctk.CTkFont(size=20, weight="bold"),
                     text_color="#1E293B").pack(side="left")

        ctk.CTkLabel(banner_inner,
                     text="Here\u2019s your customer pipeline at a glance.",
                     font=ctk.CTkFont(size=12),
                     text_color="#64748B").pack(anchor="w", pady=(4, 0))

        # Date badge on right
        date_badge = ctk.CTkFrame(banner_inner, fg_color="#EFF6FF",
                                   corner_radius=8)
        date_badge.place(relx=1.0, rely=0.5, anchor="e")
        today_str = datetime.now().strftime("%A, %b %d, %Y")
        ctk.CTkLabel(date_badge, text=f"  \u25A3  {today_str}  ",
                     font=ctk.CTkFont(size=11),
                     text_color="#2563EB").pack(padx=8, pady=6)

        # ── Stat cards row ─────────────────────────────────────────────
        self.stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.stats_frame.pack(fill="x", padx=26, pady=(14, 8))

        self.card_vars = {}
        cards = [
            ("Total Customers", "total_customers", "#2563EB", "#DBEAFE", "\u25A1"),
            ("Pending",         "pending_follow_ups", "#D97706", "#FEF3C7", "\u25F4"),
            ("Overdue",         "overdue_follow_ups", "#DC2626", "#FEE2E2", "\u25B2"),
            ("Completed",       "completed_follow_ups", "#059669", "#D1FAE5", "\u2713"),
        ]
        for i, (label, key, accent, accent_light, icon) in enumerate(cards):
            self.stats_frame.columnconfigure(i, weight=1, uniform="card")
            card, var = self._make_stat_card(self.stats_frame, label, accent,
                                             accent_light, icon)
            card.grid(row=0, column=i, padx=6, pady=4, sticky="nsew")
            self.card_vars[key] = var

        # ── Charts area ────────────────────────────────────────────────
        self.charts_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.charts_frame.pack(fill="both", expand=True, padx=26, pady=(8, 20))

        self.canvas_widget = None

    def _make_stat_card(self, parent, label_text, accent_color,
                        accent_light="#EFF6FF", icon="\u25CF"):
        """Create a card with a colored accent bar and icon."""
        card = ctk.CTkFrame(parent, fg_color="#FFFFFF", corner_radius=12,
                            border_width=1, border_color="#E2E8F0")

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=0, pady=0)

        # Accent stripe on left
        stripe = ctk.CTkFrame(inner, fg_color=accent_color, width=4,
                               corner_radius=2)
        stripe.pack(side="left", fill="y", padx=(0, 0), pady=8)

        # Content area
        content = ctk.CTkFrame(inner, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=16, pady=14)

        # Top row: icon badge
        icon_badge = ctk.CTkFrame(content, fg_color=accent_light,
                                   corner_radius=6, width=32, height=32)
        icon_badge.pack(anchor="w", pady=(0, 8))
        icon_badge.pack_propagate(False)
        ctk.CTkLabel(icon_badge, text=icon,
                     font=ctk.CTkFont(size=14),
                     text_color=accent_color).place(relx=0.5, rely=0.5,
                                                     anchor="center")

        value_var = tk.StringVar(value="0")
        ctk.CTkLabel(content, textvariable=value_var,
                     font=ctk.CTkFont(size=28, weight="bold"),
                     text_color="#1E293B").pack(anchor="w")
        ctk.CTkLabel(content, text=label_text,
                     font=ctk.CTkFont(size=11),
                     text_color="#64748B").pack(anchor="w", pady=(2, 0))

        return card, value_var

    def refresh(self):
        stats = db.get_stats(self.conn)
        for key, var in self.card_vars.items():
            var.set(str(stats.get(key, 0)))
        self._draw_charts()

    def _draw_charts(self):
        # Clear old chart
        if self.canvas_widget:
            self.canvas_widget.destroy()
            self.canvas_widget = None

        try:
            import matplotlib
            matplotlib.use("Agg")
            from matplotlib.figure import Figure
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        except ImportError:
            ctk.CTkLabel(self.charts_frame,
                         text="Install matplotlib for charts:  pip install matplotlib",
                         text_color="#64748B",
                         font=ctk.CTkFont(size=11)).pack(pady=30)
            return

        bg_color = "#F0F4F8"
        surface = "#FFFFFF"
        text_color = "#1E293B"
        text_sec = "#64748B"
        border = "#E2E8F0"

        fig = Figure(figsize=(11, 4), dpi=96, facecolor=bg_color)
        fig.subplots_adjust(left=0.06, right=0.97, top=0.88, bottom=0.18, wspace=0.30)

        chart_colors = {
            "pending": "#D97706",
            "completed": "#059669",
            "company": "#2563EB",
        }

        # ── Chart 1: Follow-ups over time ──────────────────────────────
        ax1 = fig.add_subplot(121)
        ax1.set_facecolor(surface)
        monthly = db.get_follow_ups_by_month(self.conn)
        months_data = defaultdict(lambda: {"pending": 0, "completed": 0})
        for row in monthly:
            months_data[row["month"]][row["status"]] += row["count"]

        if months_data:
            months = sorted(months_data.keys())
            pending_vals = [months_data[m]["pending"] for m in months]
            completed_vals = [months_data[m]["completed"] for m in months]
            x = range(len(months))
            bar_width = 0.38
            x_pending = [v - bar_width / 2 for v in x]
            x_completed = [v + bar_width / 2 for v in x]
            ax1.bar(x_pending, pending_vals, width=bar_width, label="Pending",
                    color=chart_colors["pending"], edgecolor="none", zorder=3,
                    alpha=0.85)
            ax1.bar(x_completed, completed_vals, width=bar_width, label="Completed",
                    color=chart_colors["completed"], edgecolor="none", zorder=3,
                    alpha=0.85)
            ax1.set_xticks(list(x))
            ax1.set_xticklabels(months, rotation=40, fontsize=8, color=text_sec)
            ax1.legend(fontsize=8, frameon=False, labelcolor=text_sec)

        ax1.set_title("Follow-ups by Month", fontsize=11, fontweight="bold",
                       color=text_color, pad=10)
        ax1.spines["top"].set_visible(False)
        ax1.spines["right"].set_visible(False)
        ax1.spines["left"].set_color(border)
        ax1.spines["bottom"].set_color(border)
        ax1.tick_params(colors=text_sec, labelsize=8)
        ax1.yaxis.grid(True, color=border, linewidth=0.5, zorder=0)
        ax1.set_axisbelow(True)

        # ── Chart 2: Customers by company ──────────────────────────────
        ax2 = fig.add_subplot(122)
        ax2.set_facecolor(surface)
        by_company = db.get_customers_by_company(self.conn)
        if by_company:
            companies = [r["company"][:22] for r in reversed(by_company)]
            counts = [r["count"] for r in reversed(by_company)]
            bars = ax2.barh(companies, counts, color=chart_colors["company"],
                            edgecolor="none", height=0.6, zorder=3, alpha=0.85)
            for bar, count in zip(bars, counts):
                ax2.text(bar.get_width() + 0.2, bar.get_y() + bar.get_height() / 2,
                         str(count), va="center", fontsize=8, color=text_sec)

        ax2.set_title("Customers by Company", fontsize=11, fontweight="bold",
                       color=text_color, pad=10)
        ax2.spines["top"].set_visible(False)
        ax2.spines["right"].set_visible(False)
        ax2.spines["left"].set_color(border)
        ax2.spines["bottom"].set_color(border)
        ax2.tick_params(colors=text_sec, labelsize=8)
        ax2.xaxis.grid(True, color=border, linewidth=0.5, zorder=0)
        ax2.set_axisbelow(True)

        canvas = FigureCanvasTkAgg(fig, master=self.charts_frame)
        canvas.draw()
        self.canvas_widget = canvas.get_tk_widget()
        self.canvas_widget.pack(fill="both", expand=True)
