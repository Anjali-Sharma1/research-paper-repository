"""
services/dashboard_service.py
Module 4: Dashboard statistics queries.
Handles queries for Admin, Faculty, and Student dashboards.
Gracefully handles tables that don't exist yet (papers, downloads, bookmarks).
All queries are parameterised — no SQL injection risk.
"""
from database.connection import get_connection


def _run(query, params=(), fetch=None):
    conn = get_connection()
    cur  = conn.cursor(dictionary=True)
    cur.execute(query, params)
    if fetch == "one":
        result = cur.fetchone()
    elif fetch == "all":
        result = cur.fetchall()
    else:
        conn.commit()
        result = cur.lastrowid
    cur.close()
    conn.close()
    return result


def _safe_run(query, params=(), fetch=None, default=None):
    """
    Like _run() but returns default if the table doesn't exist yet.
    Used for papers/downloads/bookmarks which belong to future modules.
    """
    try:
        return _run(query, params, fetch)
    except Exception:
        return default


# ── ADMIN DASHBOARD STATS ─────────────────────────────────────────────────────

def get_admin_stats() -> dict:
    """
    All stats for Admin Dashboard.
    Returns zeros/empty for tables not yet created.
    """
    # User stats — from existing users table
    users = _run("SELECT role, is_active FROM users", fetch="all") or []
    total_users    = len(users)
    active_users   = sum(1 for u in users if u["is_active"])
    inactive_users = total_users - active_users
    total_faculty  = sum(1 for u in users if u["role"] == "faculty")
    total_students = sum(1 for u in users if u["role"] == "student")
    total_admins   = sum(1 for u in users if u["role"] == "admin")

    # Department stats — from existing departments table
    dept_row = _run("SELECT COUNT(*) AS n FROM departments", fetch="one")
    total_depts = dept_row["n"] if dept_row else 0

    # Paper stats — papers table created in Module 5
    paper_row = _safe_run("SELECT COUNT(*) AS n FROM papers", fetch="one")
    total_papers = paper_row["n"] if paper_row else None

    pending_row  = _safe_run(
        "SELECT COUNT(*) AS n FROM papers WHERE status='pending'", fetch="one")
    approved_row = _safe_run(
        "SELECT COUNT(*) AS n FROM papers WHERE status='approved'", fetch="one")
    rejected_row = _safe_run(
        "SELECT COUNT(*) AS n FROM papers WHERE status='rejected'", fetch="one")

    return {
        "total_users":    total_users,
        "active_users":   active_users,
        "inactive_users": inactive_users,
        "total_faculty":  total_faculty,
        "total_students": total_students,
        "total_admins":   total_admins,
        "total_depts":    total_depts,
        # None = table doesn't exist yet (show placeholder)
        "total_papers":   total_papers,
        "pending_papers": pending_row["n"]  if pending_row  else None,
        "approved_papers":approved_row["n"] if approved_row else None,
        "rejected_papers":rejected_row["n"] if rejected_row else None,
    }


def get_recent_activity(limit: int = 8) -> list:
    """Recent activity logs for Admin dashboard."""
    return _run("""
        SELECT l.action, l.entity, l.entity_id,
               l.created_at, u.full_name, u.role
        FROM activity_logs l
        LEFT JOIN users u ON l.user_id = u.user_id
        ORDER BY l.created_at DESC
        LIMIT %s
    """, (limit,), fetch="all") or []


def get_pending_papers_summary(limit: int = 5) -> list:
    """Recent pending papers for Admin quick-review section."""
    return _safe_run("""
        SELECT p.paper_id, p.paper_code, p.title,
               p.created_at, u.full_name AS uploader_name
        FROM papers p
        LEFT JOIN users u ON p.uploaded_by = u.user_id
        WHERE p.status = 'pending'
        ORDER BY p.created_at ASC
        LIMIT %s
    """, (limit,), fetch="all", default=[]) or []


# ── FACULTY DASHBOARD STATS ───────────────────────────────────────────────────

def get_faculty_stats(user_id: int) -> dict:
    """Stats for Faculty Dashboard — optimized single aggregation query."""
    row = _safe_run("""
        SELECT 
            COUNT(*) AS my_total,
            SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) AS my_pending,
            SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END) AS my_approved,
            SUM(CASE WHEN status IN ('rejected', 'changes_requested') THEN 1 ELSE 0 END) AS my_rejected
        FROM papers 
        WHERE uploaded_by = %s
    """, (user_id,), fetch="one") or {}

    notif_row = _safe_run(
        "SELECT COUNT(*) AS n FROM notifications WHERE user_id=%s AND is_read=0",
        (user_id,), fetch="one")

    return {
        "my_total":    int(row.get("my_total") or 0),
        "my_pending":  int(row.get("my_pending") or 0),
        "my_approved": int(row.get("my_approved") or 0),
        "my_rejected": int(row.get("my_rejected") or 0),
        "unread_notifs": int(notif_row["n"] if notif_row else 0),
    }


def get_faculty_recent_papers(user_id: int, limit: int = 5) -> list:
    """Faculty's own recently uploaded papers."""
    return _safe_run("""
        SELECT paper_id, paper_code, title, status, created_at
        FROM papers
        WHERE uploaded_by = %s
        ORDER BY created_at DESC
        LIMIT %s
    """, (user_id, limit), fetch="all", default=[]) or []


# ── STUDENT DASHBOARD STATS ───────────────────────────────────────────────────

def get_student_stats(user_id: int) -> dict:
    """Stats for Student Dashboard."""
    # Downloads — Module 9 table
    dl_row = _safe_run(
        "SELECT COUNT(*) AS n FROM downloads WHERE user_id=%s",
        (user_id,), fetch="one")
    # Bookmarks — Module 9 table
    bm_row = _safe_run(
        "SELECT COUNT(*) AS n FROM bookmarks WHERE user_id=%s",
        (user_id,), fetch="one")
    # Total approved papers available — Module 5 table
    ap_row = _safe_run(
        "SELECT COUNT(*) AS n FROM papers WHERE status='approved'",
        fetch="one")
    # Unread notifications
    notif_row = _run(
        "SELECT COUNT(*) AS n FROM notifications WHERE user_id=%s AND is_read=0",
        (user_id,), fetch="one")

    return {
        "my_downloads":    dl_row["n"] if dl_row else None,
        "my_bookmarks":    bm_row["n"] if bm_row else None,
        "available_papers":ap_row["n"] if ap_row else None,
        "unread_notifs":   notif_row["n"] if notif_row else 0,
    }


def get_recently_added_papers(limit: int = 5) -> list:
    """Most recently approved papers — for Student dashboard."""
    return _safe_run("""
        SELECT p.paper_id, p.paper_code, p.title,
               p.pub_year, p.paper_type, d.dept_name, p.created_at
        FROM papers p
        LEFT JOIN departments d ON p.dept_id = d.dept_id
        WHERE p.status = 'approved'
        ORDER BY p.created_at DESC
        LIMIT %s
    """, (limit,), fetch="all", default=[]) or []


def get_most_downloaded_papers(limit: int = 5) -> list:
    """Top downloaded papers — for Student dashboard."""
    return _safe_run("""
        SELECT p.paper_id, p.paper_code, p.title,
               COUNT(dl.download_id) AS download_count, d.dept_name
        FROM papers p
        LEFT JOIN downloads   dl ON p.paper_id  = dl.paper_id
        LEFT JOIN departments d  ON p.dept_id   = d.dept_id
        WHERE p.status = 'approved'
        GROUP BY p.paper_id
        ORDER BY download_count DESC
        LIMIT %s
    """, (limit,), fetch="all", default=[]) or []


def get_student_bookmarks(user_id: int, limit: int = 5) -> list:
    """Student's bookmarked papers."""
    return _safe_run("""
        SELECT p.paper_id, p.paper_code, p.title,
               p.pub_year, d.dept_name, b.created_at AS bookmarked_at
        FROM bookmarks b
        JOIN papers      p ON b.paper_id = p.paper_id
        LEFT JOIN departments d ON p.dept_id = d.dept_id
        WHERE b.user_id = %s AND p.status = 'approved'
        ORDER BY b.created_at DESC
        LIMIT %s
    """, (user_id, limit), fetch="all", default=[]) or []


def get_student_download_history(user_id: int, limit: int = 5) -> list:
    """Student's recent download history."""
    return _safe_run("""
        SELECT p.paper_id, p.paper_code, p.title,
               d.dept_name, dl.downloaded_at
        FROM downloads dl
        JOIN papers      p ON dl.paper_id = p.paper_id
        LEFT JOIN departments d ON p.dept_id = d.dept_id
        WHERE dl.user_id = %s
        ORDER BY dl.downloaded_at DESC
        LIMIT %s
    """, (user_id, limit), fetch="all", default=[]) or []
