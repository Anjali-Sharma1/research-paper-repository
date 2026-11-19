"""
services/search_service.py
Module 8: Search & Paper Discovery.
All search queries use parameterised SQL — no injection risk.
Only approved papers are returned to students/faculty.
Admin can optionally see all statuses.
"""
from database.connection import get_connection

PAPER_TYPES  = ["journal", "conference", "thesis", "book_chapter", "other"]
SORT_OPTIONS = {
    "Newest First":       "p.created_at DESC",
    "Oldest First":       "p.created_at ASC",
    "Title A-Z":          "p.title ASC",
    "Year (Newest)":      "p.pub_year DESC",
    "Year (Oldest)":      "p.pub_year ASC",
}


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


def search_papers(keyword: str = "",
                  dept_id: int = None,
                  pub_year: int = None,
                  paper_type: str = None,
                  research_area: str = None,
                  sort_by: str = "Newest First",
                  admin_view: bool = False) -> list:
    """
    Full-text search across title, abstract, keywords, research_area, guide_name.
    All filters are optional — omitting all returns all approved papers.
    admin_view=True allows seeing all statuses (for Admin All Papers page).
    Uses parameterised LIKE queries — safe from SQL injection.
    """
    sql = """
        SELECT p.paper_id, p.paper_code, p.title, p.abstract,
               p.keywords, p.research_area, p.guide_name,
               p.pub_year, p.paper_type, p.status,
               p.file_name, p.file_size, p.created_at,
               d.dept_name, d.dept_id,
               u.full_name AS uploader_name
        FROM papers p
        LEFT JOIN departments d ON p.dept_id    = d.dept_id
        LEFT JOIN users       u ON p.uploaded_by = u.user_id
        WHERE 1=1
    """
    params = []

    # Status filter — students/faculty only see approved
    if not admin_view:
        sql += " AND p.status = 'approved'"

    # Comprehensive multi-field tokenized search
    if keyword.strip():
        tokens = keyword.strip().split()
        for tok in tokens:
            term = f"%{tok}%"
            sql += """ AND (
                p.paper_code    LIKE %s OR
                p.title         LIKE %s OR
                p.abstract      LIKE %s OR
                p.keywords      LIKE %s OR
                p.research_area LIKE %s OR
                p.guide_name    LIKE %s OR
                u.full_name     LIKE %s OR
                d.dept_name     LIKE %s OR
                d.dept_code     LIKE %s OR
                p.paper_type    LIKE %s OR
                CAST(p.pub_year AS CHAR) LIKE %s
            )"""
            params += [term] * 11

    # Department filter
    if dept_id:
        sql += " AND p.dept_id = %s"
        params.append(dept_id)

    # Year filter
    if pub_year:
        sql += " AND p.pub_year = %s"
        params.append(pub_year)

    # Paper type filter
    if paper_type and paper_type != "All":
        sql += " AND p.paper_type = %s"
        params.append(paper_type)

    # Research area filter
    if research_area and research_area.strip():
        sql += " AND p.research_area LIKE %s"
        params.append(f"%{research_area.strip()}%")

    # Sorting
    order = SORT_OPTIONS.get(sort_by, "p.created_at DESC")
    sql += f" ORDER BY {order}"

    return _run(sql, params, fetch="all") or []


def get_paper_detail(paper_id: int,
                     approved_only: bool = True) -> dict | None:
    """
    Full paper detail for detail/preview view.
    approved_only=False allows admin to view any paper.
    """
    sql = """
        SELECT p.*, d.dept_name, u.full_name AS uploader_name
        FROM papers p
        LEFT JOIN departments d ON p.dept_id    = d.dept_id
        LEFT JOIN users       u ON p.uploaded_by = u.user_id
        WHERE p.paper_id = %s
    """
    params = [paper_id]
    if approved_only:
        sql += " AND p.status = 'approved'"
    return _run(sql, params, fetch="one")


def get_recently_added(limit: int = 6) -> list:
    """Most recently approved papers."""
    return _run("""
        SELECT p.paper_id, p.paper_code, p.title,
               p.pub_year, p.paper_type, p.research_area,
               p.created_at, d.dept_name, u.full_name AS uploader_name
        FROM papers p
        LEFT JOIN departments d ON p.dept_id    = d.dept_id
        LEFT JOIN users       u ON p.uploaded_by = u.user_id
        WHERE p.status = 'approved'
        ORDER BY p.created_at DESC
        LIMIT %s
    """, (limit,), fetch="all") or []


def get_available_years() -> list:
    """Distinct publication years for year filter dropdown."""
    rows = _run("""
        SELECT DISTINCT pub_year
        FROM papers
        WHERE status = 'approved' AND pub_year IS NOT NULL
        ORDER BY pub_year DESC
    """, fetch="all") or []
    return [r["pub_year"] for r in rows]


def get_search_stats() -> dict:
    """Quick counts for the search page header."""
    total = _run(
        "SELECT COUNT(*) AS n FROM papers WHERE status='approved'",
        fetch="one")
    depts = _run(
        """SELECT COUNT(DISTINCT dept_id) AS n
           FROM papers WHERE status='approved'""",
        fetch="one")
    years = _run(
        """SELECT COUNT(DISTINCT pub_year) AS n
           FROM papers WHERE status='approved' AND pub_year IS NOT NULL""",
        fetch="one")
    return {
        "total_papers": total["n"] if total else 0,
        "total_depts":  depts["n"] if depts else 0,
        "total_years":  years["n"] if years else 0,
    }
