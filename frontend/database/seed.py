"""
database/seed.py
Creates test departments and test users for Module 2 testing.
Passwords are properly bcrypt-hashed.

Run ONCE after schema.sql:
    python database/seed.py

Default test logins:
    admin@rprms.edu     / Admin@123
    faculty@rprms.edu   / Faculty@123   (testerrprms@gmail.com  / RPRMS@1998)
    student@rprms.edu   / Student@123   (Marnus215@gmail.com  / Marnus215)
"""
import bcrypt
import sys
import os

# allow import of database/connection.py from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_connection


def hash_pw(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def run():
    conn = get_connection()
    cur  = conn.cursor()

    print("Creating departments...")
    departments = [
        ("Master of Computer Applications", "MCA",       "Dr. A. Sharma"),
        ("Bachelor of Technology - CSE",    "BTECH-CSE", "Dr. B. Verma"),
        ("Master of Business Administration","MBA",      "Dr. C. Gupta"),
        ("Electronics & Communication Engineering", "ECE", "Dr. D. K. Singh"),
        ("Information Technology", "IT", "Dr. R. K. Mishra"),
        ("Artificial Intelligence & Data Science", "AI-DS", "Dr. S. K. Nair"),
        ("Mechanical Engineering", "ME", "Dr. P. K. Joshi"),
        ("Electrical & Electronics Engineering", "EEE", "Dr. M. S. Rao"),
        ("Civil Engineering", "CE", "Dr. H. K. Verma"),
        ("Biotechnology & Bioinformatics", "BT", "Dr. N. T. Pillai"),
    ]
    for dept_name, dept_code, hod in departments:
        cur.execute("""
            INSERT IGNORE INTO departments (dept_name, dept_code, hod_name)
            VALUES (%s, %s, %s)
        """, (dept_name, dept_code, hod))
    conn.commit()

    # get dept_id for MCA
    cur.execute("SELECT dept_id FROM departments WHERE dept_code='MCA'")
    row = cur.fetchone()
    mca_id = row[0] if row else None

    print("Creating test users...")

    # ── ADMIN ──────────────────────────────────────────────────────────────────
    cur.execute("""
        INSERT IGNORE INTO users
            (full_name, email, password_hash, role, is_active)
        VALUES (%s, %s, %s, 'admin', 1)
    """, ("System Admin", "admin@rprms.edu", hash_pw("Admin@123")))

    # ── FACULTY ────────────────────────────────────────────────────────────────
    cur.execute("""
        INSERT IGNORE INTO users
            (full_name, email, password_hash, role, dept_id, is_active)
        VALUES (%s, %s, %s, 'faculty', %s, 1)
    """, ("Dr. Priya Mehta", "faculty@rprms.edu", hash_pw("Faculty@123"), mca_id))

    # ── STUDENT ────────────────────────────────────────────────────────────────
    cur.execute("""
        INSERT IGNORE INTO users
            (full_name, email, password_hash, role, dept_id, is_active)
        VALUES (%s, %s, %s, 'student', %s, 1)
    """, ("Anjali Sharma", "student@rprms.edu", hash_pw("Student@123"), mca_id))

    # ── INACTIVE USER (for testing inactive block) ──────────────────────────────
    cur.execute("""
        INSERT IGNORE INTO users
            (full_name, email, password_hash, role, is_active)
        VALUES (%s, %s, %s, 'student', 0)
    """, ("Inactive User", "inactive@rprms.edu", hash_pw("Test@123")))

    conn.commit()
    cur.close()
    conn.close()

    print("\n✅  Seed complete!")
    print("─" * 40)
    print("Test logins:")
    print("  Admin:    admin@rprms.edu     / Admin@123")
    print("  Faculty:  faculty@rprms.edu   / Faculty@123")
    print("  Student:  student@rprms.edu   / Student@123")
    print("  Inactive: inactive@rprms.edu  / Test@123  (should be blocked)")
    print("─" * 40)


if __name__ == "__main__":
    run()
