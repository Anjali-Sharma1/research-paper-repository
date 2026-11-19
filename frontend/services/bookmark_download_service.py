"""
services/bookmark_download_service.py
Module 9: Bookmark & Download Tracking.
All queries parameterised — no SQL injection risk.
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


# ── DOWNLOADS ─────────────────────────────────────────────────────────────────

def record_download(paper_id: int, user_id: int):
    """One row per download — multiple downloads by same user allowed."""
    _run("INSERT INTO downloads (paper_id, user_id) VALUES (%s,%s)",
         (paper_id, user_id))


def get_my_downloads(user_id: int) -> list:
    return _run("""
        SELECT dl.download_id, dl.downloaded_at,
               p.paper_id, p.paper_code, p.title,
               p.pub_year, p.paper_type, p.file_name, p.file_path,
               d.dept_name, u.full_name AS uploader_name
        FROM downloads dl
        JOIN papers      p ON dl.paper_id  = p.paper_id
        LEFT JOIN departments d ON p.dept_id    = d.dept_id
        LEFT JOIN users       u ON p.uploaded_by = u.user_id
        WHERE dl.user_id = %s
        ORDER BY dl.downloaded_at DESC
    """, (user_id,), fetch="all") or []


def get_download_count(paper_id: int) -> int:
    row = _run("SELECT COUNT(*) AS n FROM downloads WHERE paper_id=%s",
               (paper_id,), fetch="one")
    return row["n"] if row else 0


def get_my_download_count(user_id: int) -> int:
    row = _run("SELECT COUNT(*) AS n FROM downloads WHERE user_id=%s",
               (user_id,), fetch="one")
    return row["n"] if row else 0


def get_most_downloaded(limit: int = 10) -> list:
    return _run("""
        SELECT p.paper_id, p.paper_code, p.title,
               p.pub_year, p.paper_type, d.dept_name,
               u.full_name AS uploader_name,
               COUNT(dl.download_id) AS download_count
        FROM papers p
        LEFT JOIN downloads   dl ON p.paper_id  = dl.paper_id
        LEFT JOIN departments d  ON p.dept_id   = d.dept_id
        LEFT JOIN users       u  ON p.uploaded_by= u.user_id
        WHERE p.status = 'approved'
        GROUP BY p.paper_id
        ORDER BY download_count DESC
        LIMIT %s
    """, (limit,), fetch="all") or []


# ── BOOKMARKS ─────────────────────────────────────────────────────────────────

def is_bookmarked(paper_id: int, user_id: int) -> bool:
    row = _run("""SELECT bookmark_id FROM bookmarks
                  WHERE paper_id=%s AND user_id=%s""",
               (paper_id, user_id), fetch="one")
    return row is not None


def add_bookmark(paper_id: int, user_id: int) -> tuple[bool, str]:
    if is_bookmarked(paper_id, user_id):
        return False, "Paper already bookmarked."
    _run("INSERT INTO bookmarks (paper_id, user_id) VALUES (%s,%s)",
         (paper_id, user_id))
    return True, "Paper bookmarked successfully."


def remove_bookmark(paper_id: int, user_id: int) -> tuple[bool, str]:
    if not is_bookmarked(paper_id, user_id):
        return False, "Bookmark not found."
    _run("DELETE FROM bookmarks WHERE paper_id=%s AND user_id=%s",
         (paper_id, user_id))
    return True, "Bookmark removed."


def toggle_bookmark(paper_id: int, user_id: int) -> tuple[bool, str, str]:
    """Returns (success, message, 'added'|'removed')."""
    if is_bookmarked(paper_id, user_id):
        ok, msg = remove_bookmark(paper_id, user_id)
        return ok, msg, "removed"
    ok, msg = add_bookmark(paper_id, user_id)
    return ok, msg, "added"


def get_my_bookmarks(user_id: int) -> list:
    return _run("""
        SELECT bm.bookmark_id, bm.created_at AS bookmarked_at,
               p.paper_id, p.paper_code, p.title,
               p.pub_year, p.paper_type, p.file_name, p.file_path,
               d.dept_name, u.full_name AS uploader_name
        FROM bookmarks bm
        JOIN papers      p ON bm.paper_id  = p.paper_id
        LEFT JOIN departments d ON p.dept_id    = d.dept_id
        LEFT JOIN users       u ON p.uploaded_by = u.user_id
        WHERE bm.user_id=%s AND p.status='approved'
        ORDER BY bm.created_at DESC
    """, (user_id,), fetch="all") or []


def get_my_bookmark_count(user_id: int) -> int:
    row = _run("SELECT COUNT(*) AS n FROM bookmarks WHERE user_id=%s",
               (user_id,), fetch="one")
    return row["n"] if row else 0


def get_bookmark_count(paper_id: int) -> int:
    row = _run("SELECT COUNT(*) AS n FROM bookmarks WHERE paper_id=%s",
               (paper_id,), fetch="one")
    return row["n"] if row else 0
