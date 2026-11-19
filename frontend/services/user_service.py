"""
services/user_service.py
Module 3: Complete user management business logic.
Admin operations + self-service profile operations.
All DB queries use parameterised format — no SQL injection.
"""
from database.connection import get_connection
from auth.password import hash_password, verify_password


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


# ── READ ──────────────────────────────────────────────────────────────────────

def get_all_users() -> list:
    return _run("""
        SELECT u.user_id, u.full_name, u.email, u.role,
               u.phone, u.is_active, u.created_at, u.last_login,
               d.dept_name,
               c.full_name AS created_by_name
        FROM users u
        LEFT JOIN departments d ON u.dept_id    = d.dept_id
        LEFT JOIN users       c ON u.created_by = c.user_id
        ORDER BY u.created_at DESC
    """, fetch="all") or []


def get_user(user_id: int) -> dict | None:
    return _run("""
        SELECT u.*, d.dept_name
        FROM users u
        LEFT JOIN departments d ON u.dept_id = d.dept_id
        WHERE u.user_id = %s
    """, (user_id,), fetch="one")


def email_exists(email: str, exclude_id: int = None) -> bool:
    if exclude_id:
        row = _run(
            "SELECT user_id FROM users WHERE email=%s AND user_id!=%s",
            (email.strip().lower(), exclude_id), fetch="one")
    else:
        row = _run(
            "SELECT user_id FROM users WHERE email=%s",
            (email.strip().lower(),), fetch="one")
    return row is not None


# ── ADMIN: CREATE / EDIT / DEACTIVATE ─────────────────────────────────────────

def create_user(full_name: str, email: str, password: str,
                role: str, dept_id, phone: str,
                created_by: int) -> tuple[bool, str]:
    if not full_name.strip():
        return False, "Full name is required."
    if not email.strip():
        return False, "Email is required."
    if not password.strip():
        return False, "Password is required."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."
    if email_exists(email):
        return False, "This email address is already registered."
    if role not in ("admin", "faculty", "student"):
        return False, "Invalid role selected."

    _run("""
        INSERT INTO users
            (full_name, email, password_hash, role, dept_id,
             phone, is_active, created_by)
        VALUES (%s, %s, %s, %s, %s, %s, 1, %s)
    """, (full_name.strip(), email.strip().lower(),
          hash_password(password), role,
          dept_id or None, phone.strip() or None, created_by))
    return True, f"User '{full_name.strip()}' created successfully."


def update_user(user_id: int, full_name: str, role: str,
                dept_id, phone: str) -> tuple[bool, str]:
    if not full_name.strip():
        return False, "Full name is required."
    if role not in ("admin", "faculty", "student"):
        return False, "Invalid role."
    _run("""
        UPDATE users
        SET full_name=%s, role=%s, dept_id=%s,
            phone=%s, updated_at=NOW()
        WHERE user_id=%s
    """, (full_name.strip(), role, dept_id or None,
          phone.strip() or None, user_id))
    return True, "User updated successfully."


def toggle_active(user_id: int) -> tuple[bool, str]:
    user = get_user(user_id)
    if not user:
        return False, "User not found."
    new_state = 0 if user["is_active"] else 1
    _run("UPDATE users SET is_active=%s WHERE user_id=%s",
         (new_state, user_id))
    state_str = "activated" if new_state else "deactivated"
    return True, f"User {state_str} successfully."


def admin_reset_password(user_id: int,
                         new_password: str) -> tuple[bool, str]:
    if len(new_password) < 6:
        return False, "Password must be at least 6 characters."
    _run("""
        UPDATE users SET password_hash=%s, updated_at=NOW()
        WHERE user_id=%s
    """, (hash_password(new_password), user_id))
    return True, "Password reset successfully."


# ── SELF-SERVICE: profile + password ─────────────────────────────────────────

def update_own_profile(user_id: int, full_name: str,
                       phone: str) -> tuple[bool, str]:
    if not full_name.strip():
        return False, "Full name cannot be empty."
    _run("""
        UPDATE users SET full_name=%s, phone=%s, updated_at=NOW()
        WHERE user_id=%s
    """, (full_name.strip(), phone.strip() or None, user_id))
    return True, "Profile updated successfully."


def change_own_password(user_id: int, old_pw: str,
                        new_pw: str,
                        confirm_pw: str) -> tuple[bool, str]:
    if not old_pw or not new_pw or not confirm_pw:
        return False, "All password fields are required."
    if new_pw != confirm_pw:
        return False, "New passwords do not match."
    if len(new_pw) < 6:
        return False, "New password must be at least 6 characters."
    user = get_user(user_id)
    if not user:
        return False, "User not found."
    if not verify_password(old_pw, user["password_hash"]):
        return False, "Current password is incorrect."
    _run("""
        UPDATE users SET password_hash=%s, updated_at=NOW()
        WHERE user_id=%s
    """, (hash_password(new_pw), user_id))
    return True, "Password changed successfully."


# ── NOTIFICATIONS helper (used by other modules) ──────────────────────────────

def log_action(user_id: int, action: str,
               entity: str = None, entity_id: int = None):
    """Delegate to notification_service.log() — Module 11."""
    from services.notification_service import log as _log
    _log(user_id, action, entity, entity_id)


def get_activity_logs(limit: int = 100) -> list:
    return _run("""
        SELECT l.*, u.full_name AS user_name, u.role
        FROM activity_logs l
        LEFT JOIN users u ON l.user_id = u.user_id
        ORDER BY l.created_at DESC
        LIMIT %s
    """, (limit,), fetch="all") or []


def unread_count(user_id: int) -> int:
    row = _run("""
        SELECT COUNT(*) AS n FROM notifications
        WHERE user_id=%s AND is_read=0
    """, (user_id,), fetch="one")
    return row["n"] if row else 0


def get_notifications(user_id: int) -> list:
    return _run("""
        SELECT * FROM notifications
        WHERE user_id=%s ORDER BY created_at DESC LIMIT 50
    """, (user_id,), fetch="all") or []


def mark_all_read(user_id: int):
    _run("UPDATE notifications SET is_read=1 WHERE user_id=%s",
         (user_id,))
