"""
services/analytics_service.py
Module 10: Analytics & Reports.
Reads from existing tables — no new tables needed.
All queries use parameterised SQL.
"""
from database.connection import get_connection


def _run(query, params=(), fetch=None):
    conn = get_connection()
    cur  = conn.cursor(dictionary=True)
    cur.execute(query, params)
    if fetch == "one":   result = cur.fetchone()
    elif fetch == "all": result = cur.fetchall()
    else:                conn.commit(); result = cur.lastrowid
    cur.close(); conn.close()
    return result


def _n(sql, params=()):
    r = _run(sql, params, fetch="one")
    return r["n"] if r else 0


# ── ADMIN: SYSTEM-WIDE KPIs ───────────────────────────────────────────────────

def get_system_kpis() -> dict:
    return {
        "total_users":       _n("SELECT COUNT(*) n FROM users"),
        "active_users":      _n("SELECT COUNT(*) n FROM users WHERE is_active=1"),
        "total_faculty":     _n("SELECT COUNT(*) n FROM users WHERE role='faculty'"),
        "total_students":    _n("SELECT COUNT(*) n FROM users WHERE role='student'"),
        "total_depts":       _n("SELECT COUNT(*) n FROM departments"),
        "total_papers":      _n("SELECT COUNT(*) n FROM papers"),
        "approved_papers":   _n("SELECT COUNT(*) n FROM papers WHERE status='approved'"),
        "pending_papers":    _n("SELECT COUNT(*) n FROM papers WHERE status='pending'"),
        "rejected_papers":   _n("SELECT COUNT(*) n FROM papers WHERE status='rejected'"),
        "total_downloads":   _n("SELECT COUNT(*) n FROM downloads"),
        "total_bookmarks":   _n("SELECT COUNT(*) n FROM bookmarks"),
        "unique_downloaders":_n("SELECT COUNT(DISTINCT user_id) n FROM downloads"),
    }


def get_papers_by_status() -> list:
    return _run("""
        SELECT status, COUNT(*) AS count
        FROM papers GROUP BY status ORDER BY count DESC
    """, fetch="all") or []


def get_papers_by_department() -> list:
    return _run("""
        SELECT d.dept_name, COUNT(p.paper_id) AS count
        FROM departments d
        LEFT JOIN papers p ON d.dept_id=p.dept_id AND p.status='approved'
        GROUP BY d.dept_id ORDER BY count DESC
    """, fetch="all") or []


def get_papers_by_year() -> list:
    return _run("""
        SELECT pub_year AS year, COUNT(*) AS count
        FROM papers WHERE status='approved' AND pub_year IS NOT NULL
        GROUP BY pub_year ORDER BY pub_year ASC
    """, fetch="all") or []


def get_papers_by_type() -> list:
    return _run("""
        SELECT paper_type, COUNT(*) AS count
        FROM papers WHERE status='approved' AND paper_type IS NOT NULL
        GROUP BY paper_type ORDER BY count DESC
    """, fetch="all") or []


def get_downloads_by_month() -> list:
    return _run("""
        SELECT DATE_FORMAT(downloaded_at,'%Y-%m') AS month, COUNT(*) AS count
        FROM downloads GROUP BY month ORDER BY month DESC LIMIT 12
    """, fetch="all") or []


def get_top_downloaded_papers(limit: int = 10) -> list:
    return _run("""
        SELECT p.paper_code, p.title, d.dept_name,
               p.pub_year, p.paper_type,
               COUNT(dl.download_id) AS download_count
        FROM papers p
        LEFT JOIN downloads   dl ON p.paper_id=dl.paper_id
        LEFT JOIN departments d  ON p.dept_id=d.dept_id
        WHERE p.status='approved'
        GROUP BY p.paper_id ORDER BY download_count DESC LIMIT %s
    """, (limit,), fetch="all") or []


def get_top_bookmarked_papers(limit: int = 10) -> list:
    return _run("""
        SELECT p.paper_code, p.title, d.dept_name,
               COUNT(bm.bookmark_id) AS bookmark_count
        FROM papers p
        LEFT JOIN bookmarks   bm ON p.paper_id=bm.paper_id
        LEFT JOIN departments d  ON p.dept_id=d.dept_id
        WHERE p.status='approved'
        GROUP BY p.paper_id ORDER BY bookmark_count DESC LIMIT %s
    """, (limit,), fetch="all") or []


def get_faculty_upload_stats() -> list:
    return _run("""
        SELECT u.full_name, d.dept_name,
               COUNT(p.paper_id)                                 AS total_papers,
               SUM(p.status='approved')                          AS approved,
               SUM(p.status='pending')                           AS pending,
               SUM(p.status IN ('rejected','changes_requested')) AS action_needed
        FROM users u
        LEFT JOIN papers      p ON u.user_id=p.uploaded_by
        LEFT JOIN departments d ON u.dept_id=d.dept_id
        WHERE u.role='faculty' AND u.is_active=1
        GROUP BY u.user_id ORDER BY total_papers DESC
    """, fetch="all") or []


def get_dept_download_stats() -> list:
    return _run("""
        SELECT d.dept_name, COUNT(dl.download_id) AS download_count
        FROM departments d
        LEFT JOIN papers    p  ON d.dept_id=p.dept_id
        LEFT JOIN downloads dl ON p.paper_id=dl.paper_id
        GROUP BY d.dept_id ORDER BY download_count DESC
    """, fetch="all") or []


# ── FACULTY: PERSONAL ANALYTICS ──────────────────────────────────────────────

def get_faculty_personal_stats(user_id: int) -> dict:
    return {
        "total_papers":    _n("SELECT COUNT(*) n FROM papers WHERE uploaded_by=%s",
                              (user_id,)),
        "approved":        _n("SELECT COUNT(*) n FROM papers WHERE uploaded_by=%s AND status='approved'",
                              (user_id,)),
        "pending":         _n("SELECT COUNT(*) n FROM papers WHERE uploaded_by=%s AND status='pending'",
                              (user_id,)),
        "action_needed":   _n("""SELECT COUNT(*) n FROM papers
                                 WHERE uploaded_by=%s
                                 AND status IN ('rejected','changes_requested')""",
                              (user_id,)),
        "total_downloads": _n("""SELECT COUNT(*) n FROM downloads dl
                                 JOIN papers p ON dl.paper_id=p.paper_id
                                 WHERE p.uploaded_by=%s""", (user_id,)),
        "total_bookmarks": _n("""SELECT COUNT(*) n FROM bookmarks bm
                                 JOIN papers p ON bm.paper_id=p.paper_id
                                 WHERE p.uploaded_by=%s""", (user_id,)),
    }


def get_faculty_paper_performance(user_id: int) -> list:
    return _run("""
        SELECT p.paper_code, p.title, p.status, p.pub_year,
               COUNT(DISTINCT dl.download_id) AS downloads,
               COUNT(DISTINCT bm.bookmark_id) AS bookmarks
        FROM papers p
        LEFT JOIN downloads dl ON p.paper_id=dl.paper_id
        LEFT JOIN bookmarks bm ON p.paper_id=bm.paper_id
        WHERE p.uploaded_by=%s
        GROUP BY p.paper_id ORDER BY downloads DESC
    """, (user_id,), fetch="all") or []


# ── STUDENT: PERSONAL ANALYTICS ──────────────────────────────────────────────

def get_student_personal_stats(user_id: int) -> dict:
    return {
        "total_downloads": _n("SELECT COUNT(*) n FROM downloads WHERE user_id=%s",
                              (user_id,)),
        "unique_papers":   _n("SELECT COUNT(DISTINCT paper_id) n FROM downloads WHERE user_id=%s",
                              (user_id,)),
        "total_bookmarks": _n("SELECT COUNT(*) n FROM bookmarks WHERE user_id=%s",
                              (user_id,)),
    }


def get_student_dept_breakdown(user_id: int) -> list:
    return _run("""
        SELECT d.dept_name, COUNT(dl.download_id) AS downloads
        FROM downloads dl
        JOIN papers      p ON dl.paper_id=p.paper_id
        JOIN departments d ON p.dept_id=d.dept_id
        WHERE dl.user_id=%s
        GROUP BY d.dept_id ORDER BY downloads DESC
    """, (user_id,), fetch="all") or []


def get_student_extended_stats(user_id: int) -> dict:
    total_dl = _n("SELECT COUNT(*) n FROM downloads WHERE user_id=%s", (user_id,))
    uniq_dl  = _n("SELECT COUNT(DISTINCT paper_id) n FROM downloads WHERE user_id=%s", (user_id,))
    total_bm = _n("SELECT COUNT(*) n FROM bookmarks WHERE user_id=%s", (user_id,))
    total_up = _n("SELECT COUNT(*) n FROM papers WHERE uploaded_by=%s", (user_id,))
    approved = _n("SELECT COUNT(*) n FROM papers WHERE uploaded_by=%s AND status='approved'", (user_id,))
    pending  = _n("SELECT COUNT(*) n FROM papers WHERE uploaded_by=%s AND status='pending'", (user_id,))
    return {
        "total_downloads": total_dl,
        "unique_papers": uniq_dl,
        "total_bookmarks": total_bm,
        "total_uploaded": total_up,
        "approved_papers": approved,
        "pending_papers": pending,
    }


def get_student_recent_downloads(user_id: int, limit: int = 6) -> list:
    return _run("""
        SELECT dl.download_id, dl.downloaded_at, p.paper_id, p.paper_code,
               p.title, p.pub_year, p.paper_type, p.research_area, d.dept_name,
               u.full_name AS uploader_name
        FROM downloads dl
        JOIN papers      p ON dl.paper_id = p.paper_id
        LEFT JOIN departments d ON p.dept_id = d.dept_id
        LEFT JOIN users       u ON p.uploaded_by = u.user_id
        WHERE dl.user_id = %s
        ORDER BY dl.downloaded_at DESC
        LIMIT %s
    """, (user_id, limit), fetch="all") or []


def get_student_domain_breakdown(user_id: int) -> list:
    return _run("""
        SELECT COALESCE(NULLIF(p.research_area, ''), 'General Research') AS domain, COUNT(*) AS count
        FROM downloads dl
        JOIN papers p ON dl.paper_id = p.paper_id
        WHERE dl.user_id = %s
        GROUP BY domain
        ORDER BY count DESC
        LIMIT 6
    """, (user_id,), fetch="all") or []
