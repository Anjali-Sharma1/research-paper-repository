"""
services/department_service.py
Module 3: Department management business logic.
All department DB operations in one place.
Admin-only write operations. All roles can read.
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


def get_all_departments() -> list:
    """Return all departments with user and paper counts."""
    return _run("""
        SELECT
            d.*,
            (SELECT COUNT(*) FROM users  WHERE dept_id = d.dept_id) AS user_count,
            (SELECT COUNT(*) FROM papers WHERE dept_id = d.dept_id
             LIMIT 1) AS paper_count
        FROM departments d
        ORDER BY d.dept_name
    """, fetch="all") or []


def get_all_departments_simple() -> list:
    """Return id + name only — for dropdowns."""
    return _run(
        "SELECT dept_id, dept_name FROM departments ORDER BY dept_name",
        fetch="all"
    ) or []


def get_department(dept_id: int) -> dict | None:
    return _run(
        "SELECT * FROM departments WHERE dept_id = %s",
        (dept_id,), fetch="one"
    )


def dept_name_exists(dept_name: str, exclude_id: int = None) -> bool:
    if exclude_id:
        row = _run(
            "SELECT dept_id FROM departments WHERE dept_name=%s AND dept_id!=%s",
            (dept_name.strip(), exclude_id), fetch="one"
        )
    else:
        row = _run(
            "SELECT dept_id FROM departments WHERE dept_name=%s",
            (dept_name.strip(),), fetch="one"
        )
    return row is not None


def dept_code_exists(dept_code: str, exclude_id: int = None) -> bool:
    if exclude_id:
        row = _run(
            "SELECT dept_id FROM departments WHERE dept_code=%s AND dept_id!=%s",
            (dept_code.strip().upper(), exclude_id), fetch="one"
        )
    else:
        row = _run(
            "SELECT dept_id FROM departments WHERE dept_code=%s",
            (dept_code.strip().upper(),), fetch="one"
        )
    return row is not None


def create_department(dept_name: str, dept_code: str,
                      hod_name: str) -> tuple[bool, str]:
    if not dept_name.strip():
        return False, "Department name is required."
    if not dept_code.strip():
        return False, "Department code is required."
    if dept_name_exists(dept_name):
        return False, f"Department name '{dept_name}' already exists."
    if dept_code_exists(dept_code):
        return False, f"Department code '{dept_code.upper()}' already exists."

    _run("""
        INSERT INTO departments (dept_name, dept_code, hod_name)
        VALUES (%s, %s, %s)
    """, (dept_name.strip(), dept_code.strip().upper(),
          hod_name.strip() or None))
    return True, f"Department '{dept_name}' created successfully."


def update_department(dept_id: int, dept_name: str,
                      dept_code: str, hod_name: str) -> tuple[bool, str]:
    if not dept_name.strip():
        return False, "Department name is required."
    if not dept_code.strip():
        return False, "Department code is required."
    if dept_name_exists(dept_name, exclude_id=dept_id):
        return False, f"Department name '{dept_name}' is already used."
    if dept_code_exists(dept_code, exclude_id=dept_id):
        return False, f"Department code '{dept_code.upper()}' is already used."

    _run("""
        UPDATE departments
        SET dept_name=%s, dept_code=%s, hod_name=%s
        WHERE dept_id=%s
    """, (dept_name.strip(), dept_code.strip().upper(),
          hod_name.strip() or None, dept_id))
    return True, "Department updated successfully."


def can_delete_department(dept_id: int) -> tuple[bool, str]:
    """
    A department can only be deleted if no users and no papers are linked to it.
    Returns (can_delete, reason_if_not).
    """
    user_count = _run(
        "SELECT COUNT(*) AS n FROM users WHERE dept_id=%s",
        (dept_id,), fetch="one"
    )
    if user_count and user_count["n"] > 0:
        return False, f"Cannot delete: {user_count['n']} user(s) belong to this department."

    # papers table may not exist yet (added in Module 5) — handle gracefully
    try:
        paper_count = _run(
            "SELECT COUNT(*) AS n FROM papers WHERE dept_id=%s",
            (dept_id,), fetch="one"
        )
        if paper_count and paper_count["n"] > 0:
            return False, f"Cannot delete: {paper_count['n']} paper(s) belong to this department."
    except Exception:
        pass  # papers table doesn't exist yet

    return True, ""


def delete_department(dept_id: int) -> tuple[bool, str]:
    can, reason = can_delete_department(dept_id)
    if not can:
        return False, reason
    _run("DELETE FROM departments WHERE dept_id=%s", (dept_id,))
    return True, "Department deleted successfully."
