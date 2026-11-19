"""
services/registration_service.py
Student self-registration logic.

SECURITY: the role is hard-coded to "student" here. The registration page
never sends a role, so nobody can sign up as faculty or admin.
Faculty and admin accounts are still created only by the admin
(User Management page) or by database/seed.py.
"""
import re
from database.connection import get_connection
from auth.password import hash_password

STUDENT_ROLE = "student"          # <- the ONLY role self-registration can give
MIN_PASSWORD_LEN = 6              # same rule as the admin "Create User" form
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _email_taken(email: str) -> bool:
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT user_id FROM users WHERE email = %s", (email,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row is not None


def register_student(full_name: str, email: str, password: str,
                     confirm_password: str, dept_id=None,
                     phone: str = "") -> tuple[bool, str, int | None]:
    """
    Create a new STUDENT account.
    Returns (success, message, new_user_id).
    """
    full_name = (full_name or "").strip()
    email = (email or "").strip().lower()
    phone = (phone or "").strip()

    if not full_name:
        return False, "Full name is required.", None
    if not email:
        return False, "Email is required.", None
    if not _EMAIL_RE.match(email):
        return False, "Please enter a valid email address.", None
    if not password:
        return False, "Password is required.", None
    if len(password) < MIN_PASSWORD_LEN:
        return False, f"Password must be at least {MIN_PASSWORD_LEN} characters.", None
    if password != confirm_password:
        return False, "Passwords do not match.", None
    if _email_taken(email):
        return False, "This email is already registered. Try signing in.", None

    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("""
            INSERT INTO users
                (full_name, email, password_hash, role, dept_id,
                 phone, is_active, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, 1, NULL)
        """, (full_name, email, hash_password(password), STUDENT_ROLE,
              dept_id or None, phone or None))
        conn.commit()
        new_id = cur.lastrowid
    except Exception:
        conn.rollback()
        return False, "Could not create your account. Please try again.", None
    finally:
        cur.close()
        conn.close()

    # Email is best-effort and happens only after the account is committed.
    # A Brevo failure must never undo successful registration.
    try:
        from services.email_service import send_registration_email
        send_registration_email(full_name, email)
    except Exception:
        pass

    return True, "Account created! You can now sign in.", new_id
