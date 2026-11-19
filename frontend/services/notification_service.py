"""
services/notification_service.py
Module 11: Unified notification and activity log service.

Consolidates all notification/logging logic into one place.
All other modules import from here instead of scattering
_send_notification / log_activity / log_action across files.

Existing calls in paper_service.py / auth_service.py / user_service.py
continue to work — this module is the canonical implementation.
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


# ═══════════════════════════════════════════════════════════════════
# ACTIVITY LOGS
# ═══════════════════════════════════════════════════════════════════

def log(user_id: int, action: str,
        entity: str = None, entity_id: int = None):
    """
    Record one system action in activity_logs.
    Canonical logging function — all modules should call this.
    Safe to call from anywhere; never raises an exception to the caller.
    """
    try:
        _run("""
            INSERT INTO activity_logs (user_id, action, entity, entity_id)
            VALUES (%s, %s, %s, %s)
        """, (user_id, action, entity, entity_id))
    except Exception:
        pass  # logging must never break the main flow


def get_logs(limit: int = 100,
             user_id: int = None,
             action_filter: str = None) -> list:
    """
    Fetch activity logs.
    user_id=None  → all logs (Admin view)
    user_id=int   → only that user's logs
    action_filter → partial match on action column
    """
    sql = """
        SELECT l.log_id, l.action, l.entity, l.entity_id,
               l.created_at, u.full_name AS user_name, u.role
        FROM activity_logs l
        LEFT JOIN users u ON l.user_id = u.user_id
        WHERE 1=1
    """
    params = []

    if user_id is not None:
        sql += " AND l.user_id = %s"; params.append(user_id)

    if action_filter and action_filter.strip():
        sql += " AND l.action LIKE %s"
        params.append(f"%{action_filter.strip()}%")

    sql += " ORDER BY l.created_at DESC LIMIT %s"
    params.append(limit)

    return _run(sql, params, fetch="all") or []


def get_log_summary() -> dict:
    """Quick counts for admin dashboard / reports."""
    def n(sql): r = _run(sql, fetch="one"); return r["n"] if r else 0
    return {
        "total_logins":    n("SELECT COUNT(*) n FROM activity_logs WHERE action='login'"),
        "total_uploads":   n("SELECT COUNT(*) n FROM activity_logs WHERE action='upload_paper'"),
        "total_approvals": n("SELECT COUNT(*) n FROM activity_logs WHERE action='approve_paper'"),
        "total_downloads": n("SELECT COUNT(*) n FROM activity_logs WHERE action='download_paper'"),
        "total_actions":   n("SELECT COUNT(*) n FROM activity_logs"),
    }


# ═══════════════════════════════════════════════════════════════════
# NOTIFICATIONS
# ═══════════════════════════════════════════════════════════════════

def notify(user_id: int, message: str, link: str = None):
    """
    Send an in-app notification to one user.
    Canonical notification function — replaces _send_notification().
    Safe to call from anywhere; never raises an exception to the caller.
    """
    try:
        _run("""
            INSERT INTO notifications (user_id, message, link)
            VALUES (%s, %s, %s)
        """, (user_id, message, link))
    except Exception:
        pass


def notify_role(role: str, message: str, link: str = None):
    """Broadcast a notification to all active users of a given role."""
    users = _run("""
        SELECT user_id FROM users WHERE role=%s AND is_active=1
    """, (role,), fetch="all") or []
    for u in users:
        notify(u["user_id"], message, link)


def get_notifications(user_id: int, unread_only: bool = False) -> list:
    """Fetch notifications for one user, newest first."""
    sql = """
        SELECT notif_id, message, link, is_read, created_at
        FROM notifications
        WHERE user_id = %s
    """
    params = [user_id]
    if unread_only:
        sql += " AND is_read = 0"
    sql += " ORDER BY created_at DESC LIMIT 50"
    return _run(sql, params, fetch="all") or []


def get_unread_count(user_id: int) -> int:
    row = _run("""
        SELECT COUNT(*) AS n FROM notifications
        WHERE user_id=%s AND is_read=0
    """, (user_id,), fetch="one")
    return row["n"] if row else 0


def mark_read(notif_id: int, user_id: int):
    """Mark one notification as read (only if it belongs to this user)."""
    _run("""
        UPDATE notifications SET is_read=1
        WHERE notif_id=%s AND user_id=%s
    """, (notif_id, user_id))


def mark_all_read(user_id: int):
    """Mark all of a user's notifications as read."""
    _run("UPDATE notifications SET is_read=1 WHERE user_id=%s",
         (user_id,))


def delete_notification(notif_id: int, user_id: int):
    """Delete one notification (only if it belongs to this user)."""
    _run("DELETE FROM notifications WHERE notif_id=%s AND user_id=%s",
         (notif_id, user_id))


def delete_all_read(user_id: int):
    """Remove already-read notifications to keep inbox tidy."""
    _run("DELETE FROM notifications WHERE user_id=%s AND is_read=1",
         (user_id,))
