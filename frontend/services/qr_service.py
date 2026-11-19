"""
services/qr_service.py
Module 12 (Enhanced): QR Code generation for research papers.

QR encodes a full URL:  <RPRMS_BASE_URL>/?paper_id=<paper_id>
- Configurable base URL via RPRMS_BASE_URL in .env
- Default: http://localhost:8501
- For mobile scanning on LAN: set to http://192.168.x.x:8501
- For production: set to https://your-domain.com

QR images stored in uploads/qr/ and path saved in papers.qr_code_path.
Generated once, reused on subsequent views.
Regenerated automatically if file is missing.
"""
import os
import qrcode
from dotenv import load_dotenv
from database.connection import get_connection

load_dotenv()

QR_DIR = "uploads/qr"
os.makedirs(QR_DIR, exist_ok=True)


def get_base_url() -> str:
    """
    Read RPRMS_BASE_URL from .env.
    Falls back to http://localhost:8501 if not set.
    Change this to your LAN IP or production domain for mobile scanning.
    """
    return os.getenv("RPRMS_BASE_URL", "http://localhost:8501").rstrip("/")


def paper_url(paper_id: int) -> str:
    """Build the full URL that a QR scan will open."""
    return f"{get_base_url()}/?paper_id={paper_id}"


def _run(query, params=(), fetch=None):
    conn = get_connection()
    cur  = conn.cursor(dictionary=True)
    cur.execute(query, params)
    if fetch == "one":   result = cur.fetchone()
    elif fetch == "all": result = cur.fetchall()
    else:                conn.commit(); result = cur.lastrowid
    cur.close(); conn.close()
    return result


def _qr_path(paper_code: str) -> str:
    """Return the expected file path for a paper's QR code."""
    safe = paper_code.replace("/", "_").replace(" ", "_")
    return os.path.join(QR_DIR, f"{safe}_qr.png")


def _generate_qr_image(paper_id: int, paper_code: str, file_path: str):
    """
    Create a QR PNG that encodes the paper's full access URL.
    Format: <RPRMS_BASE_URL>/?paper_id=<paper_id>
    """
    url = paper_url(paper_id) if paper_id else paper_code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=3,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(file_path)


def get_or_create_qr(paper_id: int, paper_code: str) -> str | None:
    """
    Return the QR code file path for a paper.
    Creates the QR image if not already generated.
    Updates papers.qr_code_path in DB if newly created.
    Returns None on failure.
    """
    row = _run("SELECT qr_code_path FROM papers WHERE paper_id=%s",
               (paper_id,), fetch="one")
    if not row:
        return None

    stored_path = row.get("qr_code_path")
    expected_path = _qr_path(paper_code)

    # Use stored path if file exists on disk
    if stored_path and os.path.exists(stored_path):
        return stored_path

    # Generate QR image
    try:
        _generate_qr_image(paper_id, paper_code, expected_path)
        _run("UPDATE papers SET qr_code_path=%s WHERE paper_id=%s",
             (expected_path, paper_id))
        return expected_path
    except Exception:
        return None


def regenerate_qr(paper_id: int, paper_code: str) -> str | None:
    """Force-regenerate QR (useful when RPRMS_BASE_URL changes)."""
    path = _qr_path(paper_code)
    if os.path.exists(path):
        os.remove(path)
    _run("UPDATE papers SET qr_code_path=NULL WHERE paper_id=%s", (paper_id,))
    return get_or_create_qr(paper_id, paper_code)


def generate_qr_for_all_approved() -> tuple[int, int]:
    """
    Batch: generate QR codes for all approved papers that don't have one.
    Returns (generated_count, skipped_count).
    """
    papers = _run("""
        SELECT paper_id, paper_code
        FROM papers
        WHERE status = 'approved'
        ORDER BY paper_id ASC
    """, fetch="all") or []

    generated = 0
    skipped   = 0

    for p in papers:
        path = get_or_create_qr(p["paper_id"], p["paper_code"])
        if path:
            generated += 1
        else:
            skipped += 1

    return generated, skipped


def get_papers_with_qr_status() -> list:
    """
    Return all approved papers with their QR status and generated URL.
    Used by Admin QR management page.
    """
    papers = _run("""
        SELECT p.paper_id, p.paper_code, p.title,
               p.qr_code_path, d.dept_name
        FROM papers p
        LEFT JOIN departments d ON p.dept_id = d.dept_id
        WHERE p.status = 'approved'
        ORDER BY p.paper_id ASC
    """, fetch="all") or []

    result = []
    for p in papers:
        path   = p.get("qr_code_path")
        exists = bool(path and os.path.exists(path))
        result.append({
            **p,
            "qr_exists": exists,
            "paper_url": paper_url(p["paper_id"])
        })
    return result


def delete_qr(paper_id: int, paper_code: str):
    """Delete the QR image file and clear DB path (admin utility)."""
    path = _qr_path(paper_code)
    if os.path.exists(path):
        os.remove(path)
    _run("UPDATE papers SET qr_code_path=NULL WHERE paper_id=%s",
         (paper_id,))
