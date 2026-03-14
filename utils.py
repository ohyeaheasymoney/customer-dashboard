"""Shared utility helpers."""

from datetime import datetime, timedelta


def relative_date(date_str):
    """Return a human-friendly relative date string like 'Due tomorrow' or '3 days overdue'."""
    try:
        due = datetime.strptime(date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return date_str

    today = datetime.now().date()
    diff = (due - today).days

    if diff == 0:
        return "Today"
    elif diff == 1:
        return "Tomorrow"
    elif diff == -1:
        return "Yesterday"
    elif diff > 1 and diff <= 7:
        return f"In {diff} days"
    elif diff > 7:
        return date_str
    elif diff < -1:
        return f"{-diff}d overdue"
    return date_str
