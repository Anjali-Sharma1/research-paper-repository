"""
auth/password.py
bcrypt helper functions — used by auth_service.py and user_service.py.
Module 2.
"""
import bcrypt


def hash_password(plain: str) -> str:
    """Hash a plain-text password. Returns decoded string for MySQL storage."""
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    """Check plain password against stored bcrypt hash."""
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False
