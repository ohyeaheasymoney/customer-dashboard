"""CSV and PDF export functions."""

import csv
from datetime import datetime


def export_customers_csv(customers, filepath):
    """Write customer list to CSV file."""
    if not customers:
        return
    fields = ["name", "company", "phone", "email", "category", "created_at"]
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for c in customers:
            writer.writerow(c)


def export_follow_ups_csv(follow_ups, filepath):
    """Write follow-up list to CSV file."""
    if not follow_ups:
        return
    fields = ["customer_name", "due_date", "type", "status", "description", "created_at", "completed_at"]
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for fu in follow_ups:
            writer.writerow(fu)


def export_customer_report_pdf(customer, follow_ups, notes, filepath):
    """Generate a PDF report for a single customer."""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
    except ImportError:
        raise ImportError("reportlab is required for PDF export. Install with: pip install reportlab")

    doc = SimpleDocTemplate(filepath, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    # Title
    elements.append(Paragraph(f"Customer Report: {customer['name']}", styles["Title"]))
    elements.append(Spacer(1, 12))

    # Customer info
    info_data = [
        ["Company", customer.get("company", "")],
        ["Phone", customer.get("phone", "")],
        ["Email", customer.get("email", "")],
        ["Category", customer.get("category", "")],
        ["Created", customer.get("created_at", "")],
    ]
    info_table = Table(info_data, colWidths=[100, 400])
    info_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 20))

    # Follow-ups
    if follow_ups:
        elements.append(Paragraph("Follow-ups", styles["Heading2"]))
        fu_data = [["Due Date", "Type", "Status", "Description"]]
        for fu in follow_ups:
            fu_data.append([fu["due_date"], fu["type"], fu["status"], fu.get("description", "")])
        fu_table = Table(fu_data, colWidths=[100, 80, 80, 240])
        fu_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("PADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(fu_table)
        elements.append(Spacer(1, 20))

    # Notes
    if notes:
        elements.append(Paragraph("Notes", styles["Heading2"]))
        for note in notes:
            elements.append(Paragraph(
                f"<b>{note['created_at']}</b>: {note['content']}", styles["Normal"]
            ))
            elements.append(Spacer(1, 6))

    # Footer
    elements.append(Spacer(1, 30))
    elements.append(Paragraph(
        f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles["Normal"]
    ))

    doc.build(elements)


def export_summary_pdf(stats, filepath):
    """Generate a PDF summary of dashboard stats."""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
    except ImportError:
        raise ImportError("reportlab is required for PDF export. Install with: pip install reportlab")

    doc = SimpleDocTemplate(filepath, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("Customer Dashboard Summary", styles["Title"]))
    elements.append(Spacer(1, 20))

    data = [
        ["Metric", "Value"],
        ["Total Customers", str(stats.get("total_customers", 0))],
        ["Pending Follow-ups", str(stats.get("pending_follow_ups", 0))],
        ["Overdue Follow-ups", str(stats.get("overdue_follow_ups", 0))],
        ["Completed Follow-ups", str(stats.get("completed_follow_ups", 0))],
    ]
    table = Table(data, colWidths=[250, 150])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("PADDING", (0, 0), (-1, -1), 8),
        ("FONTSIZE", (0, 0), (-1, -1), 12),
    ]))
    elements.append(table)

    elements.append(Spacer(1, 30))
    elements.append(Paragraph(
        f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles["Normal"]
    ))

    doc.build(elements)
