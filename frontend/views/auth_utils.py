"""
auth_utils.py
Shared helpers for the Registration & Login system:
- password hashing (salted SHA-256, stdlib only — no extra dependency risk)
- field validation (email, employee ID, password policy)
- lightweight CSV-backed user store (swap for a real DB in production)
"""

import os
import re
import csv
import hashlib
import secrets
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
USERS_CSV = os.path.join(DATA_DIR, "users.csv")

FIELDNAMES = [
    "full_name", "email", "employee_id", "department", "designation",
    "salt", "password_hash", "created_on", "is_active", "role",
]

DEPARTMENTS = ["CSE", "ECE", "ME", "CE", "EE", "IT", "Other"]
DESIGNATIONS = ["Professor", "Associate Professor", "Assistant Professor", "Faculty", "Student"]

ROLES = ["Admin", "Guide", "Researcher"]
DESIGNATION_ROLES = {
    "Professor": "Guide",
    "Associate Professor": "Guide",
    "Assistant Professor": "Researcher",
    "Faculty": "Researcher",
    "Student": "Researcher",
}

PERSONAL_EMAIL_DOMAINS = {"gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "icloud.com", "rediffmail.com"}

EMAIL_REGEX = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")
EMPLOYEE_ID_REGEX = re.compile(r"^[A-Za-z0-9\-\/]{4,15}$")


# --------------------------------------------------------------------------
# STORAGE
# --------------------------------------------------------------------------
def default_role(designation):
    return DESIGNATION_ROLES.get(designation, "Researcher")


def ensure_store():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(USERS_CSV):
        with open(USERS_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()
        return
    migrate_store()


def migrate_store():
    """Bring an older users.csv up to the current FIELDNAMES without losing rows.
    The very first account becomes Admin so the console always has an owner."""
    with open(USERS_CSV, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames and set(FIELDNAMES).issubset(reader.fieldnames):
            return
        rows = list(reader)

    for index, row in enumerate(rows):
        row.setdefault("role", "")
        if not row["role"]:
            row["role"] = "Admin" if index == 0 else default_role(row.get("designation", ""))

    write_users(rows)


def write_users(rows):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(USERS_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in FIELDNAMES})


def load_users():
    ensure_store()
    with open(USERS_CSV, "r", newline="", encoding="utf-8") as f:
        users = list(csv.DictReader(f))
    for user in users:
        if not user.get("role"):
            user["role"] = default_role(user.get("designation", ""))
    return users


def save_user(row):
    ensure_store()
    row.setdefault("role", default_role(row.get("designation", "")))
    with open(USERS_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writerow(row)


def update_user(email, changes):
    """Apply field changes to one account. Returns the updated row, or None."""
    email = email.strip().lower()
    users = load_users()
    updated = None
    for user in users:
        if user["email"].strip().lower() == email:
            user.update({k: v for k, v in changes.items() if k in FIELDNAMES})
            updated = user
    if updated:
        write_users(users)
    return updated


def delete_user(email):
    email = email.strip().lower()
    users = load_users()
    remaining = [u for u in users if u["email"].strip().lower() != email]
    if len(remaining) == len(users):
        return False
    write_users(remaining)
    return True


def set_user_password(email, new_password):
    salt, digest = hash_password(new_password)
    return update_user(email, {"salt": salt, "password_hash": digest})


def find_user_by_email(email):
    email = email.strip().lower()
    for u in load_users():
        if u["email"].strip().lower() == email:
            return u
    return None


def find_user_by_employee_id(employee_id):
    eid = employee_id.strip().lower()
    for u in load_users():
        if u["employee_id"].strip().lower() == eid:
            return u
    return None


# --------------------------------------------------------------------------
# PASSWORD HASHING (salted SHA-256 via stdlib hashlib/secrets)
# --------------------------------------------------------------------------
def hash_password(password, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return salt, digest


def verify_password(password, salt, expected_hash):
    _, digest = hash_password(password, salt)
    return secrets.compare_digest(digest, expected_hash)


# --------------------------------------------------------------------------
# VALIDATION
# --------------------------------------------------------------------------
def validate_full_name(name):
    name = name.strip()
    if len(name) < 3:
        return "Full name must be at least 3 characters."
    if not re.match(r"^[A-Za-z][A-Za-z .'\-]*$", name):
        return "Full name should contain only letters, spaces, and . ' -"
    return None


def validate_email(email):
    email = email.strip()
    if not EMAIL_REGEX.match(email):
        return "Please enter a valid email address.", False
    domain = email.split("@")[-1].lower()
    if domain in PERSONAL_EMAIL_DOMAINS:
        return "This looks like a personal email. An institutional email (e.g. name@college.edu) is recommended.", True
    return None, True


def validate_employee_id(eid):
    eid = eid.strip()
    if not EMPLOYEE_ID_REGEX.match(eid):
        return "Employee/Roll ID must be 4–15 characters (letters, numbers, - or / only)."
    return None


def password_strength(password):
    """Returns (score 0-4, label, list_of_unmet_rules)."""
    rules = {
        "At least 8 characters": len(password) >= 8,
        "At least one uppercase letter": bool(re.search(r"[A-Z]", password)),
        "At least one number": bool(re.search(r"[0-9]", password)),
        "At least one special character (!@#$…)": bool(re.search(r"[^A-Za-z0-9]", password)),
    }
    score = sum(rules.values())
    labels = {0: "Very Weak", 1: "Weak", 2: "Fair", 3: "Good", 4: "Strong"}
    unmet = [r for r, ok in rules.items() if not ok]
    return score, labels[score], unmet


def validate_password_policy(password):
    score, _, unmet = password_strength(password)
    if score < 4:
        return "Password does not meet all requirements: " + "; ".join(unmet)
    return None