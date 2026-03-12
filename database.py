"""Database connection, schema initialization, and all CRUD functions."""

import sqlite3
from datetime import datetime


def get_connection(db_path="customers.db"):
    """Create and return a database connection with foreign keys enabled."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn):
    """Create all tables if they don't exist."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            company TEXT DEFAULT '',
            phone TEXT DEFAULT '',
            email TEXT DEFAULT '',
            category TEXT DEFAULT 'Active',
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS follow_ups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            due_date TEXT NOT NULL,
            type TEXT NOT NULL DEFAULT 'call',
            status TEXT NOT NULL DEFAULT 'pending',
            description TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            completed_at TEXT,
            FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        );

        CREATE TABLE IF NOT EXISTS customer_tags (
            customer_id INTEGER NOT NULL,
            tag_id INTEGER NOT NULL,
            PRIMARY KEY (customer_id, tag_id),
            FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
            FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            detail TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
        );
    """)
    conn.commit()


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _log_activity(conn, customer_id, action, detail=""):
    conn.execute(
        "INSERT INTO activity_log (customer_id, action, detail, created_at) VALUES (?, ?, ?, ?)",
        (customer_id, action, detail, _now())
    )


# --- Customers ---

def add_customer(conn, name, company="", phone="", email="", category="Active", tag_names=None):
    now = _now()
    cur = conn.execute(
        "INSERT INTO customers (name, company, phone, email, category, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (name, company, phone, email, category, now)
    )
    customer_id = cur.lastrowid
    if tag_names:
        _set_customer_tags(conn, customer_id, tag_names)
    _log_activity(conn, customer_id, "created", f"Customer '{name}' created")
    conn.commit()
    return customer_id


def update_customer(conn, customer_id, name, company="", phone="", email="", category="Active", tag_names=None):
    conn.execute(
        "UPDATE customers SET name=?, company=?, phone=?, email=?, category=? WHERE id=?",
        (name, company, phone, email, category, customer_id)
    )
    if tag_names is not None:
        _set_customer_tags(conn, customer_id, tag_names)
    _log_activity(conn, customer_id, "edited", f"Customer '{name}' updated")
    conn.commit()


def delete_customer(conn, customer_id):
    conn.execute("DELETE FROM customers WHERE id=?", (customer_id,))
    conn.commit()


def get_customer(conn, customer_id):
    row = conn.execute("SELECT * FROM customers WHERE id=?", (customer_id,)).fetchone()
    if row:
        return dict(row)
    return None


def get_all_customers(conn):
    rows = conn.execute("SELECT * FROM customers ORDER BY name").fetchall()
    return [dict(r) for r in rows]


def search_customers(conn, text="", category="All", tag_name="All", company="All"):
    query = "SELECT DISTINCT c.* FROM customers c"
    joins = []
    conditions = []
    params = []

    if tag_name and tag_name != "All":
        joins.append("JOIN customer_tags ct ON c.id = ct.customer_id JOIN tags t ON ct.tag_id = t.id")
        conditions.append("t.name = ?")
        params.append(tag_name)

    if joins:
        query += " " + " ".join(joins)

    if text:
        conditions.append("(c.name LIKE ? OR c.company LIKE ? OR c.email LIKE ?)")
        like = f"%{text}%"
        params.extend([like, like, like])

    if category and category != "All":
        conditions.append("c.category = ?")
        params.append(category)

    if company and company != "All":
        conditions.append("c.company = ?")
        params.append(company)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY c.name"
    rows = conn.execute(query, params).fetchall()
    return [dict(r) for r in rows]


def get_all_companies(conn):
    rows = conn.execute("SELECT DISTINCT company FROM customers WHERE company != '' ORDER BY company").fetchall()
    return [r["company"] for r in rows]


# --- Tags ---

def _set_customer_tags(conn, customer_id, tag_names):
    conn.execute("DELETE FROM customer_tags WHERE customer_id=?", (customer_id,))
    for tname in tag_names:
        tname = tname.strip()
        if not tname:
            continue
        conn.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (tname,))
        tag_row = conn.execute("SELECT id FROM tags WHERE name=?", (tname,)).fetchone()
        conn.execute("INSERT OR IGNORE INTO customer_tags (customer_id, tag_id) VALUES (?, ?)",
                      (customer_id, tag_row["id"]))


def get_customer_tags(conn, customer_id):
    rows = conn.execute(
        "SELECT t.name FROM tags t JOIN customer_tags ct ON t.id = ct.tag_id WHERE ct.customer_id=? ORDER BY t.name",
        (customer_id,)
    ).fetchall()
    return [r["name"] for r in rows]


def get_all_tags(conn):
    rows = conn.execute("SELECT name FROM tags ORDER BY name").fetchall()
    return [r["name"] for r in rows]


# --- Follow-ups ---

def add_follow_up(conn, customer_id, due_date, type_="call", description=""):
    now = _now()
    cur = conn.execute(
        "INSERT INTO follow_ups (customer_id, due_date, type, status, description, created_at) VALUES (?, ?, ?, 'pending', ?, ?)",
        (customer_id, due_date, type_, description, now)
    )
    _log_activity(conn, customer_id, "follow_up_added",
                  f"Follow-up added: {type_} on {due_date}")
    conn.commit()
    return cur.lastrowid


def update_follow_up(conn, follow_up_id, due_date, type_="call", description=""):
    row = conn.execute("SELECT customer_id FROM follow_ups WHERE id=?", (follow_up_id,)).fetchone()
    if row:
        conn.execute(
            "UPDATE follow_ups SET due_date=?, type=?, description=? WHERE id=?",
            (due_date, type_, description, follow_up_id)
        )
        _log_activity(conn, row["customer_id"], "follow_up_edited",
                      f"Follow-up updated: {type_} on {due_date}")
        conn.commit()


def complete_follow_up(conn, follow_up_id):
    now = _now()
    row = conn.execute("SELECT customer_id, type, due_date FROM follow_ups WHERE id=?", (follow_up_id,)).fetchone()
    if row:
        conn.execute(
            "UPDATE follow_ups SET status='completed', completed_at=? WHERE id=?",
            (now, follow_up_id)
        )
        _log_activity(conn, row["customer_id"], "status_changed",
                      f"Follow-up marked completed: {row['type']} on {row['due_date']}")
        conn.commit()


def delete_follow_up(conn, follow_up_id):
    row = conn.execute("SELECT customer_id, type, due_date FROM follow_ups WHERE id=?", (follow_up_id,)).fetchone()
    if row:
        _log_activity(conn, row["customer_id"], "follow_up_deleted",
                      f"Follow-up deleted: {row['type']} on {row['due_date']}")
    conn.execute("DELETE FROM follow_ups WHERE id=?", (follow_up_id,))
    conn.commit()


def get_follow_ups_for_customer(conn, customer_id):
    rows = conn.execute(
        "SELECT * FROM follow_ups WHERE customer_id=? ORDER BY due_date", (customer_id,)
    ).fetchall()
    return [dict(r) for r in rows]


def get_all_follow_ups(conn, status="All", type_="All", date_from=None, date_to=None):
    query = """
        SELECT f.*, c.name as customer_name
        FROM follow_ups f JOIN customers c ON f.customer_id = c.id
    """
    conditions = []
    params = []

    if status == "Overdue":
        today = datetime.now().strftime("%Y-%m-%d")
        conditions.append("f.status = 'pending' AND f.due_date < ?")
        params.append(today)
    elif status and status != "All":
        conditions.append("f.status = ?")
        params.append(status.lower())

    if type_ and type_ != "All":
        conditions.append("f.type = ?")
        params.append(type_.lower())

    if date_from:
        conditions.append("f.due_date >= ?")
        params.append(date_from)

    if date_to:
        conditions.append("f.due_date <= ?")
        params.append(date_to)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY f.due_date"
    rows = conn.execute(query, params).fetchall()
    return [dict(r) for r in rows]


# --- Notes ---

def add_note(conn, customer_id, content):
    now = _now()
    conn.execute(
        "INSERT INTO notes (customer_id, content, created_at) VALUES (?, ?, ?)",
        (customer_id, content, now)
    )
    _log_activity(conn, customer_id, "note_added", f"Note added")
    conn.commit()


def get_notes_for_customer(conn, customer_id):
    rows = conn.execute(
        "SELECT * FROM notes WHERE customer_id=? ORDER BY created_at DESC", (customer_id,)
    ).fetchall()
    return [dict(r) for r in rows]


# --- Activity Log ---

def get_activity_log(conn, customer_id):
    rows = conn.execute(
        "SELECT * FROM activity_log WHERE customer_id=? ORDER BY created_at DESC", (customer_id,)
    ).fetchall()
    return [dict(r) for r in rows]


# --- Stats ---

def get_stats(conn):
    today = datetime.now().strftime("%Y-%m-%d")
    total = conn.execute("SELECT COUNT(*) as c FROM customers").fetchone()["c"]
    pending = conn.execute("SELECT COUNT(*) as c FROM follow_ups WHERE status='pending'").fetchone()["c"]
    overdue = conn.execute(
        "SELECT COUNT(*) as c FROM follow_ups WHERE status='pending' AND due_date < ?", (today,)
    ).fetchone()["c"]
    completed = conn.execute("SELECT COUNT(*) as c FROM follow_ups WHERE status='completed'").fetchone()["c"]
    return {
        "total_customers": total,
        "pending_follow_ups": pending,
        "overdue_follow_ups": overdue,
        "completed_follow_ups": completed,
    }


def get_follow_ups_by_month(conn):
    """Return follow-up counts grouped by month for the last 6 months."""
    rows = conn.execute("""
        SELECT strftime('%Y-%m', due_date) as month, status, COUNT(*) as count
        FROM follow_ups
        WHERE due_date >= date('now', '-6 months')
        GROUP BY month, status
        ORDER BY month
    """).fetchall()
    return [dict(r) for r in rows]


def get_customers_by_company(conn, limit=10):
    """Return customer counts by company, top N."""
    rows = conn.execute("""
        SELECT company, COUNT(*) as count FROM customers
        WHERE company != ''
        GROUP BY company ORDER BY count DESC LIMIT ?
    """, (limit,)).fetchall()
    return [dict(r) for r in rows]
