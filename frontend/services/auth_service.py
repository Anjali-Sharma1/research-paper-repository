"""
services/auth_service.py
Module 2: Authentication backend.
Handles: authenticate_user(), session creation, logout, role checking.
Keeps ALL auth logic here — login.py only calls these functions.
"""
import streamlit as st
from database.connection import get_connection
from auth.password import verify_password


# ── Session state keys used across the entire project ─────────────────────────
# Every module must use these exact keys — do not change them.
SESSION_KEYS = {
    "is_logged_in": False,
    "user_id":      None,
    "user_name":    "",
    "user_role":    "",
    "user_email":   "",
    "dept_id":      None,
}


def init_session():
    """Call once at app startup to set default session values."""
    for key, default in SESSION_KEYS.items():
        if key not in st.session_state:
            st.session_state[key] = default


def authenticate_user(email: str, password: str) -> tuple[bool, str, dict | None]:
    """
    Verify credentials against MySQL.

    Returns:
        (True,  "",          user_dict)  — success
        (False, error_msg,  None)        — failure

    Checks in order:
      1. Email exists in users table
      2. Account is active (is_active = 1)
      3. Password hash matches (bcrypt)
    """
    if not email.strip() or not password.strip():
        return False, "Email and password are required.", None

    conn = get_connection()
    cur  = conn.cursor(dictionary=True)
    cur.execute(
        "SELECT * FROM users WHERE email = %s",
        (email.strip().lower(),)
    )
    user = cur.fetchone()
    cur.close()
    conn.close()

    # Step 1: email check
    if not user:
        return False, "No account found with that email address.", None

    # Step 2: active check — done BEFORE password to avoid timing hints
    if not user["is_active"]:
        return False, "Your account has been deactivated. Contact the administrator.", None

    # Step 3: password check
    if not verify_password(password, user["password_hash"]):
        return False, "Incorrect password. Please try again.", None

    return True, "", user


def create_session(user: dict):
    """
    Populate session state after successful login.
    Called by auth/login.py after authenticate_user() returns True.
    """
    st.session_state["is_logged_in"] = True
    st.session_state["user_id"]      = user["user_id"]
    st.session_state["user_name"]    = user["full_name"]
    st.session_state["user_role"]    = user["role"]
    st.session_state["user_email"]   = user["email"]
    st.session_state["dept_id"]      = user["dept_id"]


def clear_session():
    """
    Wipe all session state keys on logout.
    Called by auth/logout.py.
    """
    for key in SESSION_KEYS:
        st.session_state[key] = SESSION_KEYS[key]


def update_last_login(user_id: int):
    """Update last_login timestamp in users table."""
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute(
        "UPDATE users SET last_login = NOW() WHERE user_id = %s",
        (user_id,)
    )
    conn.commit()
    cur.close()
    conn.close()


def log_activity(user_id: int, action: str,
                 entity: str = None, entity_id: int = None):
    """Delegate to notification_service.log() — Module 11."""
    from services.notification_service import log as _log
    _log(user_id, action, entity, entity_id)


def get_unread_count(user_id: int) -> int:
    """Delegate to notification_service — Module 11."""
    from services.notification_service import get_unread_count as _uc
    return _uc(user_id)


def require_role(*allowed_roles: str):
    """
    Role guard — call at top of any protected page.
    Stops execution immediately if role not allowed.

    Usage:
        from services.auth_service import require_role
        require_role("admin")
        require_role("faculty", "admin")
    """
    if not st.session_state.get("is_logged_in"):
        st.error("You must be logged in.")
        st.stop()
    role = st.session_state.get("user_role", "")
    if role not in allowed_roles:
        st.error(f"Access denied. Required role: {' or '.join(allowed_roles)}.")
        st.stop()
