"""Dashboard page -- summary stats and matplotlib charts."""

import tkinter as tk
from datetime import datetime
from collections import defaultdict

import customtkinter as ctk
import database as db

_HAS_MATPLOTLIB = None


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
        banner_inner.pack(fill="x", padx=20, pady=16)

        # Greeting with time-of-day
        hour = datetime.now().hour
        if hour < 12:
            greeting, icon = "Good Morning", "\u2600"
        elif hour < 17:
            greeting, icon = "Good Afternoon", "\u263C"
        else:
            greeting, icon = "Good Evening", "\u263E"

        greeting_row = ctk.CTkFrame(banner_inner, fg_color="transparent")
        greeting_row.pack(anchor="w")
        ctk.CTkLabel(greeting_row, text=f"{icon}  {greeting}, Ajay!",
                     font=ctk.CTkFont(size=16, weight="bold"),
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
            ("Total Customers", "total_customers", "#2563EB", "#DBEAFE", "\u2302"),
            ("Pending",         "pending_follow_ups", "#D97706", "#FEF3C7", "\u25F7"),
            ("Overdue",         "overdue_follow_ups", "#DC2626", "#FEE2E2", "\u26A0"),
            ("Completed",       "completed_follow_ups", "#059669", "#D1FAE5", "\u2714"),
        ]
        for i, (label, key, accent, accent_light, sym) in enumerate(cards):
            self.stats_frame.columnconfigure(i, weight=1, uniform="card")
            card, var = self._make_stat_card(self.stats_frame, label, accent,
                                             accent_light, sym)
            card.grid(row=0, column=i, padx=6, pady=4, sticky="nsew")
            self.card_vars[key] = var

        # ── Chart period filter ───────────────────────────────────────
        chart_filter = ctk.CTkFrame(self, fg_color="transparent")
        chart_filter.pack(fill="x", padx=28, pady=(4, 0))
        ctk.CTkLabel(chart_filter, text="Chart Period:",
                     font=ctk.CTkFont(size=11),
                     text_color="#64748B").pack(side="left", padx=(0, 8))
        self.period_var = tk.StringVar(value="All Time")
        for period in ("3 Months", "6 Months", "12 Months", "All Time"):
            ctk.CTkButton(
                chart_filter, text=period, width=80, height=26,
                corner_radius=6,
                fg_color="#E2E8F0" if period != "All Time" else "#2563EB",
                hover_color="#CBD5E1" if period != "All Time" else "#1D4ED8",
                text_color="#1E293B" if period != "All Time" else "#FFFFFF",
                font=ctk.CTkFont(size=10),
                command=lambda p=period: self._set_period(p)
            ).pack(side="left", padx=2)

        # ── Charts area ────────────────────────────────────────────────
        self.charts_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.charts_frame.pack(fill="both", expand=True, padx=26, pady=(8, 20))
        self.canvas_widget = None

    def _make_stat_card(self, parent, label_text, accent_color,
                        accent_light="#EFF6FF", symbol="\u25CF"):
        """Compact stat card with colored accent bar."""
        card = ctk.CTkFrame(parent, fg_color="#FFFFFF", corner_radius=10,
                            border_width=1, border_color="#E2E8F0")

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True)

        # Accent stripe on left
        stripe = ctk.CTkFrame(inner, fg_color=accent_color, width=4,
                               corner_radius=2)
        stripe.pack(side="left", fill="y", pady=6)

        # Content area — compact padding
        content = ctk.CTkFrame(inner, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=14, pady=10)

        # Icon + label on top row
        top_row = ctk.CTkFrame(content, fg_color="transparent")
        top_row.pack(fill="x")

        icon_badge = ctk.CTkFrame(top_row, fg_color=accent_light,
                                   corner_radius=5, width=26, height=26)
        icon_badge.pack(side="left")
        icon_badge.pack_propagate(False)
        ctk.CTkLabel(icon_badge, text=symbol,
                     font=ctk.CTkFont(size=12),
                     text_color=accent_color).place(relx=0.5, rely=0.5,
                                                     anchor="center")

        ctk.CTkLabel(top_row, text=label_text,
                     font=ctk.CTkFont(size=11),
                     text_color="#64748B").pack(side="left", padx=(8, 0))

        # Big number
        value_var = tk.StringVar(value="0")
        ctk.CTkLabel(content, textvariable=value_var,
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color="#1E293B").pack(anchor="w", pady=(4, 0))

        return card, value_var

    def _set_period(self, period):
        """Update the chart period filter."""
        self.period_var.set(period)
        # Update button colors
        for widget in self.winfo_children():
            if isinstance(widget, ctk.CTkFrame):
                for child in widget.winfo_children():
                    if isinstance(child, ctk.CTkButton) and child.cget("text") in (
                            "3 Months", "6 Months", "12 Months", "All Time"):
                        if child.cget("text") == period:
                            child.configure(fg_color="#2563EB", text_color="#FFFFFF")
                        else:
                            child.configure(fg_color="#E2E8F0", text_color="#1E293B")
        self._draw_charts()

    def _get_period_months(self):
        """Return the number of months to show based on period filter."""
        p = self.period_var.get()
        if p == "3 Months":
            return 3
        elif p == "6 Months":
            return 6
        elif p == "12 Months":
            return 12
        return None  # All time

    def _check_matplotlib(self):
        global _HAS_MATPLOTLIB
        if _HAS_MATPLOTLIB is None:
            try:
                import matplotlib
                _HAS_MATPLOTLIB = True
            except ImportError:
                _HAS_MATPLOTLIB = False
        return _HAS_MATPLOTLIB

    def refresh(self):
        try:
            stats = db.get_stats(self.conn)
        except Exception:
            stats = {"total_customers": 0, "pending_follow_ups": 0,
                     "overdue_follow_ups": 0, "completed_follow_ups": 0}
        for key, var in self.card_vars.items():
            var.set(str(stats.get(key, 0)))
        self._draw_charts()

    def _draw_charts(self):
        if self.canvas_widget:
            self.canvas_widget.destroy()
            self.canvas_widget = None

        # Clear any old placeholder labels
        for w in self.charts_frame.winfo_children():
            w.destroy()

        if not self._check_matplotlib():
            ctk.CTkLabel(self.charts_frame,
                         text="Install matplotlib for charts:  pip install matplotlib",
                         text_color="#64748B",
                         font=ctk.CTkFont(size=11)).pack(pady=30)
            return

        try:
            import matplotlib
            matplotlib.use("Agg")
            from matplotlib.figure import Figure
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

            bg = "#F0F4F8"
            surface = "#FFFFFF"
            text_c = "#1E293B"
            text_s = "#94A3B8"
            border = "#E2E8F0"
            no_data_color = "#CBD5E1"

            # Get data (filtered by period)
            monthly = db.get_follow_ups_by_month(self.conn)
            months_data = defaultdict(lambda: {"pending": 0, "completed": 0})
            for row in monthly:
                months_data[row["month"]][row["status"]] += row["count"]

            # Filter by period
            period_n = self._get_period_months()
            if period_n and months_data:
                all_months = sorted(months_data.keys())
                cutoff = all_months[-period_n:] if len(all_months) > period_n else all_months
                months_data = {m: months_data[m] for m in cutoff}

            by_company = db.get_customers_by_company(self.conn)

            has_followup_data = bool(months_data)
            has_company_data = bool(by_company)

            # Also try to get category and growth data
            try:
                by_category = db.get_customers_by_category(self.conn)
            except Exception:
                by_category = []
            try:
                growth = db.get_customer_growth(self.conn)
                if period_n and growth:
                    growth = growth[-period_n:]
            except Exception:
                growth = []

            has_category_data = bool(by_category)
            has_growth_data = bool(growth)

            # Determine grid: 2x2 if we have enough data, else 1x2
            has_bottom_row = has_category_data or has_growth_data
            nrows = 2 if has_bottom_row else 1
            fig_height = 6.5 if has_bottom_row else 3.5
            fig = Figure(figsize=(9, fig_height), dpi=80, facecolor=bg)

            if has_bottom_row:
                fig.subplots_adjust(left=0.07, right=0.96, top=0.94, bottom=0.08,
                                    wspace=0.35, hspace=0.40)
            else:
                fig.subplots_adjust(left=0.07, right=0.96, top=0.88, bottom=0.18,
                                    wspace=0.35)

            def style_ax(ax):
                ax.set_facecolor(surface)
                ax.spines["top"].set_visible(False)
                ax.spines["right"].set_visible(False)
                ax.spines["left"].set_color(border)
                ax.spines["bottom"].set_color(border)
                ax.tick_params(colors=text_s, labelsize=8)
                ax.set_axisbelow(True)

            def no_data_message(ax, title):
                """Show a clean 'no data' placeholder."""
                ax.set_facecolor(surface)
                ax.spines["top"].set_visible(False)
                ax.spines["right"].set_visible(False)
                ax.spines["left"].set_visible(False)
                ax.spines["bottom"].set_visible(False)
                ax.set_xticks([])
                ax.set_yticks([])
                ax.set_title(title, fontsize=11, fontweight="bold",
                             color=text_c, pad=10)
                ax.text(0.5, 0.5, "No data yet", ha="center", va="center",
                        fontsize=13, color=no_data_color,
                        transform=ax.transAxes)

            # ── Chart 1: Follow-ups by Month ─────────────────────────
            ax1 = fig.add_subplot(nrows, 2, 1)
            if has_followup_data:
                style_ax(ax1)
                months = sorted(months_data.keys())
                pending_vals = [months_data[m]["pending"] for m in months]
                completed_vals = [months_data[m]["completed"] for m in months]
                x = range(len(months))
                bw = 0.35
                ax1.bar([v - bw/2 for v in x], pending_vals, width=bw,
                        label="Pending", color="#F59E0B", edgecolor="none",
                        zorder=3, alpha=0.85)
                ax1.bar([v + bw/2 for v in x], completed_vals, width=bw,
                        label="Completed", color="#10B981", edgecolor="none",
                        zorder=3, alpha=0.85)
                ax1.set_xticks(list(x))
                ax1.set_xticklabels([m[-5:] for m in months], rotation=30,
                                     fontsize=8, color=text_s)
                ax1.legend(fontsize=8, frameon=False, labelcolor=text_s)
                ax1.yaxis.grid(True, color=border, linewidth=0.5, zorder=0)
                # Force integer y-axis
                ax1.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True))
                ax1.set_title("Follow-ups by Month", fontsize=11,
                              fontweight="bold", color=text_c, pad=10)
            else:
                no_data_message(ax1, "Follow-ups by Month")

            # ── Chart 2: Customers by Company ────────────────────────
            ax2 = fig.add_subplot(nrows, 2, 2)
            if has_company_data:
                style_ax(ax2)
                companies = [r["company"][:20] for r in reversed(by_company)]
                counts = [r["count"] for r in reversed(by_company)]
                bars = ax2.barh(companies, counts, color="#3B82F6",
                                edgecolor="none", height=0.6, zorder=3, alpha=0.85)
                for bar, count in zip(bars, counts):
                    ax2.text(bar.get_width() + 0.15,
                             bar.get_y() + bar.get_height() / 2,
                             str(count), va="center", fontsize=9, color=text_s,
                             fontweight="bold")
                ax2.xaxis.grid(True, color=border, linewidth=0.5, zorder=0)
                ax2.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True))
                ax2.set_title("Customers by Company", fontsize=11,
                              fontweight="bold", color=text_c, pad=10)
            else:
                no_data_message(ax2, "Customers by Company")

            # ── Chart 3: Customers by Category (pie) ─────────────────
            if has_bottom_row:
                ax3 = fig.add_subplot(nrows, 2, 3)
                if has_category_data:
                    cat_colors = {
                        "VIP": "#8B5CF6", "Lead": "#3B82F6",
                        "Active": "#10B981", "Inactive": "#6B7280",
                    }
                    labels = [r["category"] for r in by_category]
                    sizes = [r["count"] for r in by_category]
                    colors = [cat_colors.get(l, "#94A3B8") for l in labels]

                    ax3.set_facecolor(surface)
                    wedges, texts, autotexts = ax3.pie(
                        sizes, labels=labels, colors=colors, autopct="%1.0f%%",
                        startangle=90, pctdistance=0.75,
                        wedgeprops=dict(width=0.45, edgecolor=surface, linewidth=2))
                    for t in texts:
                        t.set_fontsize(9)
                        t.set_color(text_c)
                    for t in autotexts:
                        t.set_fontsize(8)
                        t.set_color("white")
                        t.set_fontweight("bold")
                    ax3.set_title("Customers by Category", fontsize=11,
                                  fontweight="bold", color=text_c, pad=10)
                else:
                    no_data_message(ax3, "Customers by Category")

                # ── Chart 4: Customer Growth ─────────────────────────
                ax4 = fig.add_subplot(nrows, 2, 4)
                if has_growth_data:
                    style_ax(ax4)
                    g_months = [r["month"] for r in growth]
                    g_counts = [r["count"] for r in growth]
                    # Make cumulative
                    cumulative = []
                    total = 0
                    for c in g_counts:
                        total += c
                        cumulative.append(total)

                    ax4.fill_between(range(len(g_months)), cumulative,
                                     alpha=0.15, color="#3B82F6", zorder=2)
                    ax4.plot(range(len(g_months)), cumulative,
                             color="#3B82F6", linewidth=2.5, zorder=3,
                             marker="o", markersize=5)
                    ax4.set_xticks(range(len(g_months)))
                    ax4.set_xticklabels([m[-5:] for m in g_months],
                                         rotation=30, fontsize=8, color=text_s)
                    ax4.yaxis.grid(True, color=border, linewidth=0.5, zorder=0)
                    ax4.yaxis.set_major_locator(
                        matplotlib.ticker.MaxNLocator(integer=True))
                    ax4.set_title("Customer Growth", fontsize=11,
                                  fontweight="bold", color=text_c, pad=10)
                else:
                    no_data_message(ax4, "Customer Growth")

            canvas = FigureCanvasTkAgg(fig, master=self.charts_frame)
            canvas.draw()
            self.canvas_widget = canvas.get_tk_widget()
            self.canvas_widget.pack(fill="both", expand=True)

        except Exception as e:
            if self.canvas_widget:
                self.canvas_widget.destroy()
                self.canvas_widget = None
            ctk.CTkLabel(self.charts_frame,
                         text=f"Chart error: {e}",
                         text_color="#DC2626",
                         font=ctk.CTkFont(size=11)).pack(pady=20)
