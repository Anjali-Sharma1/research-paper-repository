"""
services/paper_service.py
Module 5: Paper Upload & Metadata business logic.
Handles validation, file saving, paper_code generation, DB insert.
All queries are parameterised. Uploaded_by always comes from session — never user input.
"""
import os
import re
import datetime
from database.connection import get_connection

UPLOAD_DIR   = "uploads/papers"
MAX_MB       = 20
ALLOWED_MIME = "application/pdf"
PAPER_TYPES  = ["journal", "conference", "thesis", "book_chapter", "other"]

os.makedirs(UPLOAD_DIR, exist_ok=True)


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


# ── VALIDATION ────────────────────────────────────────────────────────────────

def validate_pdf_file(uploaded_file) -> tuple[bool, str]:
    """Validate the uploaded Streamlit file object."""
    if uploaded_file is None:
        return False, "Please select a PDF file to upload."
    if uploaded_file.type != ALLOWED_MIME:
        return False, "Only PDF files are accepted. Please upload a .pdf file."
    size_mb = uploaded_file.size / (1024 * 1024)
    if size_mb > MAX_MB:
        return False, f"File is too large ({size_mb:.1f} MB). Maximum allowed is {MAX_MB} MB."
    return True, ""


def validate_metadata(title: str, abstract: str, dept_id,
                      pub_year: int) -> tuple[bool, str]:
    """Validate paper metadata fields."""
    if not title.strip():
        return False, "Paper title is required."
    if len(title.strip()) < 5:
        return False, "Paper title is too short (minimum 5 characters)."
    if not abstract or not abstract.strip():
        return False, "Abstract is required."
    if len(abstract.strip()) < 20:
        return False, "Abstract is too short (minimum 20 characters)."
    if not dept_id:
        return False, "Please select a department."
    current_year = datetime.date.today().year
    if pub_year < 1990 or pub_year > current_year:
        return False, f"Publication year must be between 1990 and {current_year}."
    return True, ""


def title_exists(title: str) -> bool:
    """Check if a paper with the same title already exists."""
    row = _run(
        "SELECT paper_id FROM papers WHERE LOWER(title) = LOWER(%s) LIMIT 1",
        (title.strip(),), fetch="one"
    )
    return row is not None


# ── PAPER CODE GENERATION ─────────────────────────────────────────────────────

def generate_paper_code(paper_id: int) -> str:
    """
    Generate human-readable paper code after INSERT.
    Format: RPRMS-YYYY-NNNN  e.g. RPRMS-2025-0001
    """
    year = datetime.date.today().year
    return f"RPRMS-{year}-{paper_id:04d}"


# ── FILE SAVING ───────────────────────────────────────────────────────────────

def _safe_filename(original_name: str, paper_id: int) -> str:
    """
    Build a safe filename using paper_id to avoid conflicts.
    Strips unsafe characters. Always ends with .pdf.
    Example: RPRMS_2025_0001.pdf
    """
    base = re.sub(r"[^\w\-]", "_", os.path.splitext(original_name)[0])
    base = base[:50].strip("_")  # limit length
    return f"RPRMS_{datetime.date.today().year}_{paper_id:04d}_{base}.pdf"


def save_pdf_file(uploaded_file, paper_id: int) -> tuple[str, str, int]:
    """
    Save the uploaded PDF to uploads/papers/.
    Returns (safe_filename, file_path, file_size_bytes).
    """
    safe_name = _safe_filename(uploaded_file.name, paper_id)
    file_path = os.path.join(UPLOAD_DIR, safe_name)
    file_bytes = uploaded_file.getvalue()
    with open(file_path, "wb") as f:
        f.write(file_bytes)
    return safe_name, file_path, len(file_bytes)


# ── DATABASE OPERATIONS ───────────────────────────────────────────────────────

def create_paper(title: str, abstract: str, keywords: str,
                 research_area: str, guide_name: str,
                 dept_id: int, pub_year: int, paper_type: str,
                 uploaded_by: int, uploaded_file) -> tuple[bool, str, dict | None]:
    """
    Full paper creation pipeline:
      1. Validate metadata
      2. Validate PDF file
      3. Check duplicate title
      4. INSERT paper row with placeholder file info
      5. Generate paper_code from new paper_id
      6. Save PDF file using paper_id in filename
      7. UPDATE paper row with real file info and paper_code
      8. Return (success, message, paper_dict)

    uploaded_by MUST come from session_state — never from user input.
    """
    # Step 1: validate metadata
    ok, err = validate_metadata(title, abstract, dept_id, pub_year)
    if not ok:
        return False, err, None

    # Step 2: validate file
    ok, err = validate_pdf_file(uploaded_file)
    if not ok:
        return False, err, None

    # Step 3: duplicate title check
    if title_exists(title):
        return False, "A paper with this title already exists in the system.", None

    # Step 4: INSERT with placeholder — get paper_id first
    paper_id = _run("""
        INSERT INTO papers
            (paper_code, title, abstract, keywords, research_area,
             guide_name, dept_id, pub_year, paper_type, uploaded_by,
             file_name, file_path, file_size, status)
        VALUES
            (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'pending')
    """, (
        "TEMP",                        # placeholder — updated below
        title.strip(),
        abstract.strip(),
        keywords.strip()       or None,
        research_area.strip()  or None,
        guide_name.strip()     or None,
        dept_id,
        pub_year,
        paper_type,
        uploaded_by,           # ← from session, never user input
        "TEMP",                # placeholder file_name
        "TEMP",                # placeholder file_path
        0                      # placeholder file_size
    ))

    # Step 5: generate paper_code
    paper_code = generate_paper_code(paper_id)

    # Step 6: save PDF to disk
    file_name, file_path, file_size = save_pdf_file(uploaded_file, paper_id)

    # Step 7: UPDATE with real values
    _run("""
        UPDATE papers
        SET paper_code=%s, file_name=%s, file_path=%s, file_size=%s
        WHERE paper_id=%s
    """, (paper_code, file_name, file_path, file_size, paper_id))

    paper = get_paper_by_id(paper_id)

    # Step 8: record version 1 (Module 7 — safe if table not yet created)
    try:
        _create_version_record(
            paper_id, 1, file_name, file_path,
            file_size, uploaded_by, 'Initial upload')
    except Exception:
        pass  # paper_versions table created in Module 7

    # Confirm submission by email only after the paper is saved successfully.
    # Email errors must not affect the successful paper upload.
    try:
        from services.email_service import send_submission_email
        if paper:
            send_submission_email(
                paper.get("uploader_name", ""),
                paper.get("uploader_email", ""),
                paper,
            )
    except Exception:
        pass

    return True, f"Paper uploaded successfully! Paper ID: {paper_code}", paper


def get_paper_by_id(paper_id: int) -> dict | None:
    return _run("""
        SELECT p.*, d.dept_name, u.full_name AS uploader_name,
               u.email AS uploader_email
        FROM papers p
        LEFT JOIN departments d ON p.dept_id    = d.dept_id
        LEFT JOIN users       u ON p.uploaded_by = u.user_id
        WHERE p.paper_id = %s
    """, (paper_id,), fetch="one")


def get_papers_by_uploader(user_id: int) -> list:
    """All papers uploaded by a specific faculty member."""
    return _run("""
        SELECT p.paper_id, p.paper_code, p.title, p.status,
               p.pub_year, p.paper_type, p.created_at,
               d.dept_name
        FROM papers p
        LEFT JOIN departments d ON p.dept_id = d.dept_id
        WHERE p.uploaded_by = %s
        ORDER BY p.created_at DESC
    """, (user_id,), fetch="all") or []


def get_all_papers_admin() -> list:
    """All papers for Admin view."""
    return _run("""
        SELECT p.paper_id, p.paper_code, p.title, p.status,
               p.pub_year, p.paper_type, p.created_at,
               d.dept_name, u.full_name AS uploader_name
        FROM papers p
        LEFT JOIN departments d ON p.dept_id    = d.dept_id
        LEFT JOIN users       u ON p.uploaded_by = u.user_id
        ORDER BY p.created_at DESC
    """, fetch="all") or []


def get_paper_types() -> list:
    return PAPER_TYPES


# ── MODULE 6: APPROVAL WORKFLOW ───────────────────────────────────────────────

VALID_STATUSES = ("pending", "approved", "rejected", "changes_requested")


def get_pending_papers() -> list:
    """All papers with status=pending for Admin review queue."""
    return _run("""
        SELECT p.paper_id, p.paper_code, p.title, p.status,
               p.pub_year, p.paper_type, p.created_at,
               p.research_area, p.guide_name,
               d.dept_name, u.full_name AS uploader_name
        FROM papers p
        LEFT JOIN departments d ON p.dept_id    = d.dept_id
        LEFT JOIN users       u ON p.uploaded_by = u.user_id
        WHERE p.status = 'pending'
        ORDER BY p.created_at ASC
    """, fetch="all") or []


def get_paper_status_history(paper_id: int) -> list:
    """Full audit trail for a specific paper."""
    return _run("""
        SELECT h.history_id, h.old_status, h.new_status,
               h.comments, h.changed_at,
               u.full_name AS reviewer_name, u.role
        FROM paper_status_history h
        LEFT JOIN users u ON h.changed_by = u.user_id
        WHERE h.paper_id = %s
        ORDER BY h.changed_at DESC
    """, (paper_id,), fetch="all") or []


def _record_status_change(paper_id: int, old_status: str,
                          new_status: str, changed_by: int,
                          comments: str = ""):
    """Insert one row into paper_status_history."""
    _run("""
        INSERT INTO paper_status_history
            (paper_id, old_status, new_status, changed_by, comments)
        VALUES (%s, %s, %s, %s, %s)
    """, (paper_id, old_status, new_status, changed_by,
          comments.strip() or None))


def _send_notification(user_id: int, message: str):
    """Delegate to notification_service.notify() — Module 11."""
    from services.notification_service import notify as _notify
    _notify(user_id, message)


def _update_paper_status(paper_id: int, new_status: str,
                         reviewer_id: int, comments: str) -> tuple[bool, str]:
    """
    Core status-change function.
    Validates transition, updates papers table, records history, notifies faculty.
    """
    if new_status not in VALID_STATUSES:
        return False, f"Invalid status: {new_status}"

    paper = get_paper_by_id(paper_id)
    if not paper:
        return False, "Paper not found."

    old_status = paper["status"]
    if old_status == new_status:
        return False, f"Paper is already {new_status}."

    # Approved papers cannot be re-approved or rejected without going
    # back to pending first (enforced here — not just in UI)
    if old_status == "approved" and new_status == "rejected":
        return False, "An approved paper cannot be directly rejected. " \
                      "Request changes first."

    # Update papers table
    _run("""
        UPDATE papers
        SET status=%s, updated_at=NOW()
        WHERE paper_id=%s
    """, (new_status, paper_id))

    # Record in history
    _record_status_change(paper_id, old_status, new_status,
                          reviewer_id, comments)

    # Notify the uploader
    status_messages = {
        "approved":          f"Your paper '{paper['title'][:60]}' has been APPROVED.",
        "rejected":          f"Your paper '{paper['title'][:60]}' has been REJECTED. "
                             f"Comment: {comments or 'No comment provided.'}",
        "changes_requested": f"Changes requested for '{paper['title'][:60]}'. "
                             f"Comment: {comments or 'Please review and resubmit.'}",
    }
    if new_status in status_messages:
        _send_notification(paper["uploaded_by"], status_messages[new_status])

    # Send a matching email after the status/history operations succeed.
    # This is best-effort: mail failures do not roll back the decision.
    if new_status in ("approved", "rejected", "changes_requested"):
        try:
            from services.email_service import send_review_email
            send_review_email(
                paper.get("uploader_name", ""),
                paper.get("uploader_email", ""),
                paper,
                new_status,
                comments or "",
            )
        except Exception:
            pass

    return True, f"Paper status updated to '{new_status}'."


def approve_paper(paper_id: int, reviewer_id: int,
                  comments: str = "") -> tuple[bool, str]:
    """Approve a paper. Only admin can call this. Also triggers QR generation."""
    result = _update_paper_status(paper_id, "approved", reviewer_id, comments)
    if result[0]:
        # Auto-generate QR code on approval — Module 12
        try:
            paper = get_paper_by_id(paper_id)
            if paper:
                from services.qr_service import get_or_create_qr
                get_or_create_qr(paper_id, paper["paper_code"])
        except Exception:
            pass  # QR generation failure must never block approval
    return result


def reject_paper(paper_id: int, reviewer_id: int,
                 comments: str) -> tuple[bool, str]:
    """Reject a paper. Comment is required."""
    if not comments.strip():
        return False, "A comment is required when rejecting a paper."
    return _update_paper_status(paper_id, "rejected", reviewer_id, comments)


def request_changes(paper_id: int, reviewer_id: int,
                    comments: str) -> tuple[bool, str]:
    """Request changes. Comment is required."""
    if not comments.strip():
        return False, "Please describe what changes are needed."
    return _update_paper_status(paper_id, "changes_requested",
                                reviewer_id, comments)


# ── MODULE 7: PAPER VERSION MANAGEMENT ───────────────────────────────────────

def _get_next_version_no(paper_id: int) -> int:
    """Get the next version number for a paper."""
    row = _run("""
        SELECT MAX(version_no) AS max_ver
        FROM paper_versions
        WHERE paper_id = %s
    """, (paper_id,), fetch="one")
    return (row["max_ver"] or 0) + 1 if row else 1


def _create_version_record(paper_id: int, version_no: int,
                           file_name: str, file_path: str,
                           file_size: int, uploaded_by: int,
                           change_notes: str = ""):
    """Insert one row into paper_versions."""
    _run("""
        INSERT INTO paper_versions
            (paper_id, version_no, file_name, file_path,
             file_size, uploaded_by, change_notes)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (paper_id, version_no, file_name, file_path,
          file_size, uploaded_by, change_notes.strip() or None))


def record_initial_version(paper_id: int, file_name: str,
                           file_path: str, file_size: int,
                           uploaded_by: int):
    """
    Called right after create_paper() succeeds.
    Records version 1 for the initial upload.
    """
    _create_version_record(
        paper_id, 1, file_name, file_path,
        file_size, uploaded_by, "Initial upload")


def get_paper_versions(paper_id: int) -> list:
    """All versions for a paper, newest first."""
    return _run("""
        SELECT pv.version_id, pv.version_no, pv.file_name,
               pv.file_path, pv.file_size, pv.change_notes,
               pv.uploaded_at, u.full_name AS uploader_name
        FROM paper_versions pv
        LEFT JOIN users u ON pv.uploaded_by = u.user_id
        WHERE pv.paper_id = %s
        ORDER BY pv.version_no DESC
    """, (paper_id,), fetch="all") or []


def get_version_by_id(version_id: int) -> dict | None:
    """Single version record."""
    return _run("""
        SELECT pv.*, u.full_name AS uploader_name
        FROM paper_versions pv
        LEFT JOIN users u ON pv.uploaded_by = u.user_id
        WHERE pv.version_id = %s
    """, (version_id,), fetch="one")


def upload_new_version(paper_id: int, uploaded_file,
                       uploaded_by: int,
                       change_notes: str) -> tuple[bool, str, dict | None]:
    """
    Faculty re-uploads a paper after 'changes_requested'.
    Steps:
      1. Validate paper exists and belongs to this user
      2. Validate status allows re-upload (changes_requested only)
      3. Validate the new PDF file
      4. Save new file to disk
      5. Insert new version row
      6. Update papers table (new file info + status back to pending)
      7. Record status change in paper_status_history
      8. Notify admin
    Returns (success, message, paper_dict)
    """
    # 1. Fetch paper and verify ownership
    paper = get_paper_by_id(paper_id)
    if not paper:
        return False, "Paper not found.", None
    if paper["uploaded_by"] != uploaded_by:
        return False, "You are not the uploader of this paper.", None

    # 2. Only allow re-upload when changes were requested
    if paper["status"] != "changes_requested":
        return False, (
            f"Re-upload is only allowed when status is 'changes_requested'. "
            f"Current status: {paper['status']}."), None

    # 3. Validate new file
    ok, err = validate_pdf_file(uploaded_file)
    if not ok:
        return False, err, None

    if not change_notes.strip():
        return False, "Please describe what changes you made.", None

    # 4. Save new file with version number in filename
    next_ver = _get_next_version_no(paper_id)
    safe_name = _safe_filename(uploaded_file.name, paper_id)
    # add version suffix
    base, ext = os.path.splitext(safe_name)
    versioned_name = f"{base}_v{next_ver}{ext}"
    file_path = os.path.join(UPLOAD_DIR, versioned_name)
    file_bytes = uploaded_file.getvalue()
    with open(file_path, "wb") as f:
        f.write(file_bytes)
    file_size = len(file_bytes)

    # 5. Insert version record
    _create_version_record(paper_id, next_ver, versioned_name,
                           file_path, file_size, uploaded_by, change_notes)

    # 6. Update papers table — new file + status back to pending
    _run("""
        UPDATE papers
        SET file_name=%s, file_path=%s, file_size=%s,
            status='pending', updated_at=NOW()
        WHERE paper_id=%s
    """, (versioned_name, file_path, file_size, paper_id))

    # 7. Record status change
    _record_status_change(
        paper_id, "changes_requested", "pending",
        uploaded_by, f"Version {next_ver} uploaded: {change_notes}")

    # 8. Notify admin (all admins)
    try:
        admins = _run(
            "SELECT user_id FROM users WHERE role='admin' AND is_active=1",
            fetch="all") or []
        for admin in admins:
            _send_notification(
                admin["user_id"],
                f"Faculty re-uploaded paper '{paper['title'][:50]}' "
                f"(v{next_ver}) — now pending review.")
    except Exception:
        pass

    updated_paper = get_paper_by_id(paper_id)
    return (True,
            f"Version {next_ver} uploaded successfully. "
            f"Paper is now pending review.",
            updated_paper)


def get_all_versions_summary() -> list:
    """Admin view: all papers with version counts."""
    return _run("""
        SELECT p.paper_id, p.paper_code, p.title, p.status,
               d.dept_name, u.full_name AS uploader_name,
               COUNT(pv.version_id) AS version_count,
               MAX(pv.uploaded_at) AS last_uploaded
        FROM papers p
        LEFT JOIN departments  d  ON p.dept_id    = d.dept_id
        LEFT JOIN users        u  ON p.uploaded_by = u.user_id
        LEFT JOIN paper_versions pv ON p.paper_id  = pv.paper_id
        GROUP BY p.paper_id
        ORDER BY p.created_at DESC
    """, fetch="all") or []


def delete_paper(paper_id: int, user_id: int, user_role: str) -> tuple[bool, str]:
    """
    Permanently deletes a paper, its versions, associated records, and physical files.
    Permissions:
      - Admin can delete any paper.
      - Faculty or Student can ONLY delete their own paper if it was rejected or changes requested.
    """
    paper = get_paper_by_id(paper_id)
    if not paper:
        return False, "Paper not found."

    is_admin = (user_role == "admin")
    is_author = (paper.get("uploaded_by") == user_id)
    is_rejected = (paper.get("status") in ("rejected", "changes_requested"))

    if not is_admin and not (is_author and is_rejected):
        return False, "You do not have permission to delete this paper. Only Admin or author of a rejected paper can delete it."

    try:
        from services.ui_theme_service import resolve_pdf_path
        from services.auth_service import log_activity

        files_to_remove = []
        if paper.get("file_path"):
            files_to_remove.append(paper["file_path"])

        versions = get_paper_versions(paper_id)
        for v in versions:
            if v.get("file_path"):
                files_to_remove.append(v["file_path"])

        try:
            from services.qr_service import get_qr_path
            qr_file = get_qr_path(paper["paper_code"])
            if qr_file and os.path.exists(qr_file):
                files_to_remove.append(qr_file)
        except Exception:
            pass

        _run("DELETE FROM bookmarks WHERE paper_id = %s", (paper_id,))
        _run("DELETE FROM downloads WHERE paper_id = %s", (paper_id,))
        _run("DELETE FROM paper_versions WHERE paper_id = %s", (paper_id,))
        _run("DELETE FROM paper_status_history WHERE paper_id = %s", (paper_id,))
        _run("DELETE FROM papers WHERE paper_id = %s", (paper_id,))

        for fpath in set(files_to_remove):
            res_path = resolve_pdf_path(fpath) or fpath
            if os.path.exists(res_path) and os.path.isfile(res_path):
                try:
                    os.remove(res_path)
                except Exception:
                    pass

        log_activity(user_id, "delete_paper", "paper", paper_id)
        return True, f"Paper '{paper['paper_code']}' has been permanently deleted."
    except Exception as e:
        return False, f"Failed to delete paper: {e}"
