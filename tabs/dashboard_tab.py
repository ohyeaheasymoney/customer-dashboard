"""Dashboard page -- summary stats and matplotlib charts."""

import tkinter as tk
from tkinter import ttk
from datetime import datetime
from collections import defaultdict

import customtkinter as ctk
import database as db


class DashboardTab(ctk.CTkFrame):
    def __init__(self, parent, conn):
        super().__init__(parent, fg_color="#1F2937")
        self.conn = conn
        self._build_ui()

    def _build_ui(self):
        # ── Page header ────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=28, pady=(24, 4))
        ctk.CTkLabel(header, text="Dashboard",
                     font=ctk.CTkFont(size=22, weight="bold"),
                     text_color="#F9FAFB").pack(anchor="w")
        ctk.CTkLabel(header, text="Overview of your customer pipeline",
                     font=ctk.CTkFont(size=12),
                     text_color="#9CA3AF").pack(anchor="w", pady=(2, 0))

        # ── Stat cards row ─────────────────────────────────────────────
        self.stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.stats_frame.pack(fill="x", padx=26, pady=(18, 8))

        self.card_vars = {}
        cards = [
            ("Total Customers", "total_customers", "#3B82F6"),
            ("Pending",         "pending_follow_ups", "#F59E0B"),
            ("Overdue",         "overdue_follow_ups", "#EF4444"),
            ("Completed",       "completed_follow_ups", "#10B981"),
        ]
        for i, (label, key, accent) in enumerate(cards):
            self.stats_frame.columnconfigure(i, weight=1, uniform="card")
            card, var = self._make_stat_card(self.stats_frame, label, accent)
            card.grid(row=0, column=i, padx=6, pady=4, sticky="nsew")
            self.card_vars[key] = var

        # ── Charts area ────────────────────────────────────────────────
        self.charts_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.charts_frame.pack(fill="both", expand=True, padx=26, pady=(8, 20))

        self.canvas_widget = None

    def _make_stat_card(self, parent, label_text, accent_color):
        """Create a card with a colored left accent bar."""
        # Outer card frame
        card = ctk.CTkFrame(parent, fg_color="#374151", corner_radius=12)

        # Inner layout with accent stripe
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=0, pady=0)

        # Accent stripe on left
        stripe = ctk.CTkFrame(inner, fg_color=accent_color, width=4,
                               corner_radius=2)
        stripe.pack(side="left", fill="y", padx=(0, 0), pady=8)

        # Content area
        content = ctk.CTkFrame(inner, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=16, pady=14)

        value_var = tk.StringVar(value="0")
        ctk.CTkLabel(content, textvariable=value_var,
                     font=ctk.CTkFont(size=28, weight="bold"),
                     text_color="#F9FAFB").pack(anchor="w")
        ctk.CTkLabel(content, text=label_text,
                     font=ctk.CTkFont(size=11),
                     text_color="#9CA3AF").pack(anchor="w", pady=(4, 0))

        # Small colored dot indicator
        dot_frame = ctk.CTkFrame(content, fg_color="transparent")
        dot_frame.pack(anchor="w", pady=(8, 0))
        dot = tk.Canvas(dot_frame, width=8, height=8, bg="#374151",
                        highlightthickness=0)
        dot.create_oval(1, 1, 7, 7, fill=accent_color, outline=accent_color)
        dot.pack(side="left")
        ctk.CTkLabel(dot_frame, text=label_text.split()[0],
                     font=ctk.CTkFont(size=10),
                     text_color="#6B7280").pack(side="left", padx=(4, 0))

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
                         text_color="#9CA3AF",
                         font=ctk.CTkFont(size=11)).pack(pady=30)
            return

        bg_color = "#1F2937"
        surface = "#374151"
        text_color = "#F9FAFB"
        text_sec = "#9CA3AF"
        border = "#4B5563"

        fig = Figure(figsize=(11, 4), dpi=96, facecolor=bg_color)
        fig.subplots_adjust(left=0.06, right=0.97, top=0.88, bottom=0.18, wspace=0.30)

        chart_colors = {
            "pending": "#F59E0B",
            "completed": "#10B981",
            "company": "#3B82F6",
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
