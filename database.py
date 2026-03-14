"""Database connection, schema initialization, and all CRUD functions."""

import re
import sqlite3
from datetime import datetime

# --- Constants / Enums ---
CATEGORIES = ("VIP", "Lead", "Active", "Inactive")
FOLLOW_UP_TYPES = ("call", "email", "meeting")
FOLLOW_UP_STATUSES = ("pending", "completed")

SCHEMA_VERSION = 2


def get_connection(db_path="customers.db"):
    """Create and return a database connection with foreign keys enabled."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.row_factory = sqlite3.Row
    return conn


# --- Input Validation Helpers ---

def validate_email(email):
    """Return True if *email* looks valid (or is empty/None, since it's optional)."""
    if not email:
        return True  # optional field
    return bool(re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email))


def validate_date(date_str):
    """Return True if *date_str* is a valid YYYY-MM-DD date string."""
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


# --- Integrity Check ---

def check_integrity(conn):
    """Run SQLite integrity check; return True when the database is healthy."""
    result = conn.execute("PRAGMA integrity_check").fetchone()
    return result[0] == "ok"


# --- Schema Initialization with Versioning ---

_ORIGINAL_SCHEMA = """
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

    CREATE TABLE IF NOT EXISTS account_resources (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL,
        role TEXT NOT NULL,
        name TEXT DEFAULT '',
        email TEXT DEFAULT '',
        phone TEXT DEFAULT '',
        FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS meeting_notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL,
        meeting_date TEXT NOT NULL,
        audience TEXT DEFAULT '',
        notes TEXT DEFAULT '',
        created_at TEXT NOT NULL,
        FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS business_initiatives (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL,
        section TEXT NOT NULL,
        content TEXT DEFAULT '',
        sort_order INTEGER DEFAULT 0,
        FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS contact_development (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        title TEXT DEFAULT '',
        relationship TEXT DEFAULT 'Unknown',
        influence TEXT DEFAULT 'Influencer',
        phone TEXT DEFAULT '',
        email TEXT DEFAULT '',
        notes TEXT DEFAULT '',
        FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS account_goals_meta (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL UNIQUE,
        moonshot TEXT DEFAULT '',
        objectives TEXT DEFAULT '',
        FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS account_goals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL,
        term TEXT NOT NULL DEFAULT 'short',
        goal TEXT DEFAULT '',
        status TEXT DEFAULT 'Not Started',
        notes TEXT DEFAULT '',
        FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS action_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL,
        what TEXT DEFAULT '',
        who TEXT DEFAULT '',
        how TEXT DEFAULT '',
        due_date TEXT DEFAULT '',
        status TEXT DEFAULT 'On Track',
        notes TEXT DEFAULT '',
        created_at TEXT NOT NULL,
        FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS cph_report (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL,
        category TEXT NOT NULL,
        month_1 REAL DEFAULT 0,
        month_2 REAL DEFAULT 0,
        month_3 REAL DEFAULT 0,
        month_4 REAL DEFAULT 0,
        month_5 REAL DEFAULT 0,
        month_6 REAL DEFAULT 0,
        month_7 REAL DEFAULT 0,
        month_8 REAL DEFAULT 0,
        month_9 REAL DEFAULT 0,
        month_10 REAL DEFAULT 0,
        month_11 REAL DEFAULT 0,
        month_12 REAL DEFAULT 0,
        FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS hw_sw_landscape (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL,
        category TEXT DEFAULT '',
        item TEXT DEFAULT '',
        vendor TEXT DEFAULT '',
        version TEXT DEFAULT '',
        qty INTEGER DEFAULT 0,
        support_status TEXT DEFAULT '',
        notes TEXT DEFAULT '',
        FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS application_landscape (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL,
        app_name TEXT DEFAULT '',
        criticality TEXT DEFAULT 'Standard',
        hosting TEXT DEFAULT '',
        owner TEXT DEFAULT '',
        opportunities TEXT DEFAULT '',
        notes TEXT DEFAULT '',
        FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS service_landscape (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL,
        service TEXT DEFAULT '',
        incumbent TEXT DEFAULT '',
        contract_end TEXT DEFAULT '',
        annual_value REAL DEFAULT 0,
        notes TEXT DEFAULT '',
        FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS account_text_sections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL,
        section TEXT NOT NULL,
        content TEXT DEFAULT '',
        updated_at TEXT,
        UNIQUE(customer_id, section),
        FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
    );
"""


def init_db(conn):
    """Create all tables if they don't exist, with schema versioning."""
    # Ensure the schema_version table exists
    conn.execute("CREATE TABLE IF NOT EXISTS schema_version (version INTEGER)")
    row = conn.execute("SELECT version FROM schema_version").fetchone()
    current = row["version"] if row else 0

    if current < 1:
        # Original schema
        conn.executescript(_ORIGINAL_SCHEMA)

    if current < 2:
        # Future migration slot -- add new columns/tables here using
        # try/except around ALTER TABLE to handle "already exists" gracefully.
        pass

    # Persist the version
    if current == 0:
        conn.execute("INSERT INTO schema_version (version) VALUES (?)", (SCHEMA_VERSION,))
    else:
        conn.execute("UPDATE schema_version SET version = ?", (SCHEMA_VERSION,))
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
    try:
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
    except Exception:
        conn.rollback()
        raise


def update_customer(conn, customer_id, name, company="", phone="", email="", category="Active", tag_names=None):
    try:
        conn.execute(
            "UPDATE customers SET name=?, company=?, phone=?, email=?, category=? WHERE id=?",
            (name, company, phone, email, category, customer_id)
        )
        if tag_names is not None:
            _set_customer_tags(conn, customer_id, tag_names)
        _log_activity(conn, customer_id, "edited", f"Customer '{name}' updated")
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def delete_customer(conn, customer_id):
    try:
        conn.execute("DELETE FROM customers WHERE id=?", (customer_id,))
        conn.commit()
    except Exception:
        conn.rollback()
        raise


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
    try:
        now = _now()
        cur = conn.execute(
            "INSERT INTO follow_ups (customer_id, due_date, type, status, description, created_at) VALUES (?, ?, ?, 'pending', ?, ?)",
            (customer_id, due_date, type_, description, now)
        )
        _log_activity(conn, customer_id, "follow_up_added",
                      f"Follow-up added: {type_} on {due_date}")
        conn.commit()
        return cur.lastrowid
    except Exception:
        conn.rollback()
        raise


def update_follow_up(conn, follow_up_id, due_date, type_="call", description=""):
    try:
        row = conn.execute("SELECT customer_id FROM follow_ups WHERE id=?", (follow_up_id,)).fetchone()
        if row:
            conn.execute(
                "UPDATE follow_ups SET due_date=?, type=?, description=? WHERE id=?",
                (due_date, type_, description, follow_up_id)
            )
            _log_activity(conn, row["customer_id"], "follow_up_edited",
                          f"Follow-up updated: {type_} on {due_date}")
            conn.commit()
    except Exception:
        conn.rollback()
        raise


def complete_follow_up(conn, follow_up_id):
    try:
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
    except Exception:
        conn.rollback()
        raise


def delete_follow_up(conn, follow_up_id):
    try:
        row = conn.execute("SELECT customer_id, type, due_date FROM follow_ups WHERE id=?", (follow_up_id,)).fetchone()
        if row:
            _log_activity(conn, row["customer_id"], "follow_up_deleted",
                          f"Follow-up deleted: {row['type']} on {row['due_date']}")
        conn.execute("DELETE FROM follow_ups WHERE id=?", (follow_up_id,))
        conn.commit()
    except Exception:
        conn.rollback()
        raise


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
    try:
        now = _now()
        conn.execute(
            "INSERT INTO notes (customer_id, content, created_at) VALUES (?, ?, ?)",
            (customer_id, content, now)
        )
        _log_activity(conn, customer_id, "note_added", f"Note added")
        conn.commit()
    except Exception:
        conn.rollback()
        raise


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


def get_customers_by_category(conn):
    """Return customer counts grouped by category."""
    rows = conn.execute("""
        SELECT category, COUNT(*) as count FROM customers
        GROUP BY category ORDER BY count DESC
    """).fetchall()
    return [dict(r) for r in rows]


def get_customer_growth(conn):
    """Return customer counts by month for the last 12 months."""
    rows = conn.execute("""
        SELECT strftime('%Y-%m', created_at) as month, COUNT(*) as count
        FROM customers
        WHERE created_at >= date('now', '-12 months')
        GROUP BY month
        ORDER BY month
    """).fetchall()
    return [dict(r) for r in rows]


# --- Account Resources ---

def get_account_resources(conn, customer_id):
    rows = conn.execute(
        "SELECT * FROM account_resources WHERE customer_id=? ORDER BY role",
        (customer_id,)).fetchall()
    return [dict(r) for r in rows]


def upsert_account_resource(conn, customer_id, role, name="", email="", phone="", resource_id=None):
    if resource_id:
        conn.execute(
            "UPDATE account_resources SET role=?, name=?, email=?, phone=? WHERE id=?",
            (role, name, email, phone, resource_id))
    else:
        conn.execute(
            "INSERT INTO account_resources (customer_id, role, name, email, phone) VALUES (?,?,?,?,?)",
            (customer_id, role, name, email, phone))
    conn.commit()


def delete_account_resource(conn, resource_id):
    conn.execute("DELETE FROM account_resources WHERE id=?", (resource_id,))
    conn.commit()


# --- Meeting Notes ---

def get_meeting_notes(conn, customer_id):
    rows = conn.execute(
        "SELECT * FROM meeting_notes WHERE customer_id=? ORDER BY meeting_date DESC",
        (customer_id,)).fetchall()
    return [dict(r) for r in rows]


def add_meeting_note(conn, customer_id, meeting_date, audience="", notes=""):
    now = _now()
    cur = conn.execute(
        "INSERT INTO meeting_notes (customer_id, meeting_date, audience, notes, created_at) VALUES (?,?,?,?,?)",
        (customer_id, meeting_date, audience, notes, now))
    conn.commit()
    return cur.lastrowid


def update_meeting_note(conn, note_id, meeting_date, audience="", notes=""):
    conn.execute(
        "UPDATE meeting_notes SET meeting_date=?, audience=?, notes=? WHERE id=?",
        (meeting_date, audience, notes, note_id))
    conn.commit()


def delete_meeting_note(conn, note_id):
    conn.execute("DELETE FROM meeting_notes WHERE id=?", (note_id,))
    conn.commit()


# --- Business Initiatives ---

def get_business_initiatives(conn, customer_id, section=None):
    if section:
        rows = conn.execute(
            "SELECT * FROM business_initiatives WHERE customer_id=? AND section=? ORDER BY sort_order",
            (customer_id, section)).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM business_initiatives WHERE customer_id=? ORDER BY section, sort_order",
            (customer_id,)).fetchall()
    return [dict(r) for r in rows]


def add_business_initiative(conn, customer_id, section, content="", sort_order=0):
    cur = conn.execute(
        "INSERT INTO business_initiatives (customer_id, section, content, sort_order) VALUES (?,?,?,?)",
        (customer_id, section, content, sort_order))
    conn.commit()
    return cur.lastrowid


def update_business_initiative(conn, item_id, content="", sort_order=0):
    conn.execute(
        "UPDATE business_initiatives SET content=?, sort_order=? WHERE id=?",
        (content, sort_order, item_id))
    conn.commit()


def delete_business_initiative(conn, item_id):
    conn.execute("DELETE FROM business_initiatives WHERE id=?", (item_id,))
    conn.commit()


# --- Contact Development ---

def get_contacts(conn, customer_id):
    rows = conn.execute(
        "SELECT * FROM contact_development WHERE customer_id=? ORDER BY name",
        (customer_id,)).fetchall()
    return [dict(r) for r in rows]


def add_contact(conn, customer_id, name, title="", relationship="Unknown",
                influence="Influencer", phone="", email="", notes=""):
    cur = conn.execute(
        "INSERT INTO contact_development (customer_id, name, title, relationship, influence, phone, email, notes) VALUES (?,?,?,?,?,?,?,?)",
        (customer_id, name, title, relationship, influence, phone, email, notes))
    conn.commit()
    return cur.lastrowid


def update_contact(conn, contact_id, name, title="", relationship="Unknown",
                   influence="Influencer", phone="", email="", notes=""):
    conn.execute(
        "UPDATE contact_development SET name=?, title=?, relationship=?, influence=?, phone=?, email=?, notes=? WHERE id=?",
        (name, title, relationship, influence, phone, email, notes, contact_id))
    conn.commit()


def delete_contact(conn, contact_id):
    conn.execute("DELETE FROM contact_development WHERE id=?", (contact_id,))
    conn.commit()


# --- Account Goals ---

def get_goals_meta(conn, customer_id):
    row = conn.execute(
        "SELECT * FROM account_goals_meta WHERE customer_id=?",
        (customer_id,)).fetchone()
    return dict(row) if row else None


def upsert_goals_meta(conn, customer_id, moonshot="", objectives=""):
    existing = get_goals_meta(conn, customer_id)
    if existing:
        conn.execute(
            "UPDATE account_goals_meta SET moonshot=?, objectives=? WHERE customer_id=?",
            (moonshot, objectives, customer_id))
    else:
        conn.execute(
            "INSERT INTO account_goals_meta (customer_id, moonshot, objectives) VALUES (?,?,?)",
            (customer_id, moonshot, objectives))
    conn.commit()


def get_account_goals(conn, customer_id, term=None):
    if term:
        rows = conn.execute(
            "SELECT * FROM account_goals WHERE customer_id=? AND term=? ORDER BY id",
            (customer_id, term)).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM account_goals WHERE customer_id=? ORDER BY term, id",
            (customer_id,)).fetchall()
    return [dict(r) for r in rows]


def add_account_goal(conn, customer_id, term="short", goal="", status="Not Started", notes=""):
    cur = conn.execute(
        "INSERT INTO account_goals (customer_id, term, goal, status, notes) VALUES (?,?,?,?,?)",
        (customer_id, term, goal, status, notes))
    conn.commit()
    return cur.lastrowid


def update_account_goal(conn, goal_id, goal="", status="Not Started", notes=""):
    conn.execute(
        "UPDATE account_goals SET goal=?, status=?, notes=? WHERE id=?",
        (goal, status, notes, goal_id))
    conn.commit()


def delete_account_goal(conn, goal_id):
    conn.execute("DELETE FROM account_goals WHERE id=?", (goal_id,))
    conn.commit()


# --- Action Items ---

def get_action_items(conn, customer_id):
    rows = conn.execute(
        "SELECT * FROM action_items WHERE customer_id=? ORDER BY due_date",
        (customer_id,)).fetchall()
    return [dict(r) for r in rows]


def add_action_item(conn, customer_id, what="", who="", how="", due_date="", status="On Track", notes=""):
    now = _now()
    cur = conn.execute(
        "INSERT INTO action_items (customer_id, what, who, how, due_date, status, notes, created_at) VALUES (?,?,?,?,?,?,?,?)",
        (customer_id, what, who, how, due_date, status, notes, now))
    conn.commit()
    return cur.lastrowid


def update_action_item(conn, item_id, what="", who="", how="", due_date="", status="On Track", notes=""):
    conn.execute(
        "UPDATE action_items SET what=?, who=?, how=?, due_date=?, status=?, notes=? WHERE id=?",
        (what, who, how, due_date, status, notes, item_id))
    conn.commit()


def delete_action_item(conn, item_id):
    conn.execute("DELETE FROM action_items WHERE id=?", (item_id,))
    conn.commit()


# --- CPH Report ---

def get_cph_report(conn, customer_id):
    rows = conn.execute(
        "SELECT * FROM cph_report WHERE customer_id=? ORDER BY category",
        (customer_id,)).fetchall()
    return [dict(r) for r in rows]


def add_cph_row(conn, customer_id, category, **months):
    vals = {f"month_{i}": months.get(f"month_{i}", 0) for i in range(1, 13)}
    conn.execute(
        "INSERT INTO cph_report (customer_id, category, month_1,month_2,month_3,month_4,month_5,month_6,month_7,month_8,month_9,month_10,month_11,month_12) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (customer_id, category, *[vals[f"month_{i}"] for i in range(1, 13)]))
    conn.commit()


def update_cph_row(conn, row_id, category, **months):
    vals = {f"month_{i}": months.get(f"month_{i}", 0) for i in range(1, 13)}
    conn.execute(
        "UPDATE cph_report SET category=?, month_1=?,month_2=?,month_3=?,month_4=?,month_5=?,month_6=?,month_7=?,month_8=?,month_9=?,month_10=?,month_11=?,month_12=? WHERE id=?",
        (category, *[vals[f"month_{i}"] for i in range(1, 13)], row_id))
    conn.commit()


def delete_cph_row(conn, row_id):
    conn.execute("DELETE FROM cph_report WHERE id=?", (row_id,))
    conn.commit()


# --- HW/SW Landscape ---

def get_hw_sw_landscape(conn, customer_id):
    rows = conn.execute(
        "SELECT * FROM hw_sw_landscape WHERE customer_id=? ORDER BY category, item",
        (customer_id,)).fetchall()
    return [dict(r) for r in rows]


def add_hw_sw_item(conn, customer_id, category="", item="", vendor="", version="", qty=0, support_status="", notes=""):
    cur = conn.execute(
        "INSERT INTO hw_sw_landscape (customer_id, category, item, vendor, version, qty, support_status, notes) VALUES (?,?,?,?,?,?,?,?)",
        (customer_id, category, item, vendor, version, qty, support_status, notes))
    conn.commit()
    return cur.lastrowid


def update_hw_sw_item(conn, item_id, category="", item="", vendor="", version="", qty=0, support_status="", notes=""):
    conn.execute(
        "UPDATE hw_sw_landscape SET category=?, item=?, vendor=?, version=?, qty=?, support_status=?, notes=? WHERE id=?",
        (category, item, vendor, version, qty, support_status, notes, item_id))
    conn.commit()


def delete_hw_sw_item(conn, item_id):
    conn.execute("DELETE FROM hw_sw_landscape WHERE id=?", (item_id,))
    conn.commit()


def seed_hw_sw_landscape(conn, customer_id):
    """Pre-seed ~50 common technology items for a new customer if none exist."""
    existing = get_hw_sw_landscape(conn, customer_id)
    if existing:
        return
    template = [
        ("Servers", "Physical Servers", "", "", 0, "", ""),
        ("Servers", "Virtual Servers", "", "", 0, "", ""),
        ("Servers", "Blade Chassis", "", "", 0, "", ""),
        ("Storage", "SAN", "", "", 0, "", ""),
        ("Storage", "NAS", "", "", 0, "", ""),
        ("Storage", "Backup Appliance", "", "", 0, "", ""),
        ("Storage", "Object Storage", "", "", 0, "", ""),
        ("Networking", "Core Switches", "", "", 0, "", ""),
        ("Networking", "Access Switches", "", "", 0, "", ""),
        ("Networking", "Routers", "", "", 0, "", ""),
        ("Networking", "Firewalls", "", "", 0, "", ""),
        ("Networking", "Load Balancers", "", "", 0, "", ""),
        ("Networking", "Wireless Controllers", "", "", 0, "", ""),
        ("Networking", "Wireless APs", "", "", 0, "", ""),
        ("Networking", "SD-WAN", "", "", 0, "", ""),
        ("Security", "Next-Gen Firewall", "", "", 0, "", ""),
        ("Security", "IDS/IPS", "", "", 0, "", ""),
        ("Security", "SIEM", "", "", 0, "", ""),
        ("Security", "EDR/XDR", "", "", 0, "", ""),
        ("Security", "NAC", "", "", 0, "", ""),
        ("Security", "Email Security", "", "", 0, "", ""),
        ("Security", "Web Proxy", "", "", 0, "", ""),
        ("Security", "PAM", "", "", 0, "", ""),
        ("Security", "MFA/IAM", "", "", 0, "", ""),
        ("Compute", "Hypervisor Platform", "", "", 0, "", ""),
        ("Compute", "Container Platform", "", "", 0, "", ""),
        ("Compute", "VDI", "", "", 0, "", ""),
        ("Compute", "HCI", "", "", 0, "", ""),
        ("Cloud", "IaaS", "", "", 0, "", ""),
        ("Cloud", "PaaS", "", "", 0, "", ""),
        ("Cloud", "SaaS", "", "", 0, "", ""),
        ("Cloud", "DRaaS", "", "", 0, "", ""),
        ("Cloud", "BaaS", "", "", 0, "", ""),
        ("Collaboration", "Email Platform", "", "", 0, "", ""),
        ("Collaboration", "UC Platform", "", "", 0, "", ""),
        ("Collaboration", "Video Conferencing", "", "", 0, "", ""),
        ("Collaboration", "Contact Center", "", "", 0, "", ""),
        ("Collaboration", "Team Messaging", "", "", 0, "", ""),
        ("Database", "RDBMS", "", "", 0, "", ""),
        ("Database", "NoSQL", "", "", 0, "", ""),
        ("OS", "Windows Server", "", "", 0, "", ""),
        ("OS", "Linux (RHEL/Ubuntu)", "", "", 0, "", ""),
        ("Management", "Monitoring", "", "", 0, "", ""),
        ("Management", "ITSM/Ticketing", "", "", 0, "", ""),
        ("Management", "Config Management", "", "", 0, "", ""),
        ("Management", "Patch Management", "", "", 0, "", ""),
        ("Endpoint", "Desktops", "", "", 0, "", ""),
        ("Endpoint", "Laptops", "", "", 0, "", ""),
        ("Endpoint", "Mobile Devices", "", "", 0, "", ""),
        ("Endpoint", "Printers/MFPs", "", "", 0, "", ""),
    ]
    for cat, itm, vendor, ver, qty, status, notes in template:
        conn.execute(
            "INSERT INTO hw_sw_landscape (customer_id, category, item, vendor, version, qty, support_status, notes) VALUES (?,?,?,?,?,?,?,?)",
            (customer_id, cat, itm, vendor, ver, qty, status, notes))
    conn.commit()


# --- Application Landscape ---

def get_application_landscape(conn, customer_id):
    rows = conn.execute(
        "SELECT * FROM application_landscape WHERE customer_id=? ORDER BY app_name",
        (customer_id,)).fetchall()
    return [dict(r) for r in rows]


def add_application(conn, customer_id, app_name="", criticality="Standard", hosting="", owner="", opportunities="", notes=""):
    cur = conn.execute(
        "INSERT INTO application_landscape (customer_id, app_name, criticality, hosting, owner, opportunities, notes) VALUES (?,?,?,?,?,?,?)",
        (customer_id, app_name, criticality, hosting, owner, opportunities, notes))
    conn.commit()
    return cur.lastrowid


def update_application(conn, app_id, app_name="", criticality="Standard", hosting="", owner="", opportunities="", notes=""):
    conn.execute(
        "UPDATE application_landscape SET app_name=?, criticality=?, hosting=?, owner=?, opportunities=?, notes=? WHERE id=?",
        (app_name, criticality, hosting, owner, opportunities, notes, app_id))
    conn.commit()


def delete_application(conn, app_id):
    conn.execute("DELETE FROM application_landscape WHERE id=?", (app_id,))
    conn.commit()


# --- Service Landscape ---

def get_service_landscape(conn, customer_id):
    rows = conn.execute(
        "SELECT * FROM service_landscape WHERE customer_id=? ORDER BY service",
        (customer_id,)).fetchall()
    return [dict(r) for r in rows]


def add_service(conn, customer_id, service="", incumbent="", contract_end="", annual_value=0, notes=""):
    cur = conn.execute(
        "INSERT INTO service_landscape (customer_id, service, incumbent, contract_end, annual_value, notes) VALUES (?,?,?,?,?,?)",
        (customer_id, service, incumbent, contract_end, annual_value, notes))
    conn.commit()
    return cur.lastrowid


def update_service(conn, service_id, service="", incumbent="", contract_end="", annual_value=0, notes=""):
    conn.execute(
        "UPDATE service_landscape SET service=?, incumbent=?, contract_end=?, annual_value=?, notes=? WHERE id=?",
        (service, incumbent, contract_end, annual_value, notes, service_id))
    conn.commit()


def delete_service(conn, service_id):
    conn.execute("DELETE FROM service_landscape WHERE id=?", (service_id,))
    conn.commit()


# --- Account Text Sections (Tech Profile & Guidance) ---

def get_text_section(conn, customer_id, section):
    row = conn.execute(
        "SELECT * FROM account_text_sections WHERE customer_id=? AND section=?",
        (customer_id, section)).fetchone()
    return dict(row) if row else None


def save_text_section(conn, customer_id, section, content=""):
    now = _now()
    conn.execute(
        "INSERT INTO account_text_sections (customer_id, section, content, updated_at) VALUES (?,?,?,?) "
        "ON CONFLICT(customer_id, section) DO UPDATE SET content=?, updated_at=?",
        (customer_id, section, content, now, content, now))
    conn.commit()
