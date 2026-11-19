"""
pages/faculty/upload_paper.py
Module 5: Faculty paper upload form.
Handles metadata entry, PDF upload, validation, and submission.
uploaded_by always comes from session_state — never from user input.
"""
import streamlit as st
from services.auth_service import require_role, log_activity
from services.paper_service import create_paper, get_paper_types
from services.department_service import get_all_departments_simple
import datetime


def show():
    require_role("faculty", "student", "admin")
    user_id = st.session_state["user_id"]

    st.title(":material/upload_file: Upload Research Paper")
    st.caption("All fields marked * are required.")
    st.divider()

    # ── Load dropdowns ────────────────────────────────────────────────────────
    depts      = get_all_departments_simple()
    dept_map   = {d["dept_name"]: d["dept_id"] for d in depts}
    paper_types= get_paper_types()
    cur_year   = datetime.date.today().year

    if not depts:
        st.error("No departments found. Ask Admin to create departments first.")
        return

    # ── Upload form ───────────────────────────────────────────────────────────
    with st.form("upload_paper_form", clear_on_submit=False):
        st.subheader(":material/description: Paper Metadata")

        title  = st.text_input("Paper Title *",
                               placeholder="Enter the full title of your research paper")
        abstract = st.text_area("Abstract *", height=140,
                                placeholder="Provide a summary of your research (min 20 characters)")

        col1, col2 = st.columns(2)
        with col1:
            keywords     = st.text_input("Keywords",
                                         placeholder="e.g. machine learning, CNN, image processing")
            research_area= st.text_input("Research Area",
                                         placeholder="e.g. Artificial Intelligence")
            guide_name   = st.text_input("Guide / Supervisor Name",
                                         placeholder="e.g. Dr. Priya Mehta / Prof. R. K. Verma")
        with col2:
            dept_name    = st.selectbox("Department *", list(dept_map.keys()))
            pub_year     = st.number_input("Publication Year *",
                                           min_value=1990,
                                           max_value=cur_year,
                                           value=cur_year,
                                           step=1)
            paper_type   = st.selectbox("Paper Type *",
                                        [t.replace("_", " ").title() for t in paper_types])

        st.divider()
        st.subheader(":material/description: Upload PDF")
        pdf_file = st.file_uploader(
            "Select PDF file * (max 20 MB)",
            type=["pdf"],
            help="Only PDF files are accepted. Maximum file size is 20 MB."
        )

        if pdf_file:
            size_mb = pdf_file.size / (1024 * 1024)
            st.caption(f"Selected: **{pdf_file.name}**  |  Size: {size_mb:.2f} MB")

        st.divider()
        submitted = st.form_submit_button(
            ":material/send: Submit Paper", type="primary", use_container_width=True)

    # ── Handle submission ─────────────────────────────────────────────────────
    if submitted:
        # map display type back to DB value
        type_display_to_db = {
            t.replace("_", " ").title(): t for t in paper_types}
        paper_type_db = type_display_to_db.get(paper_type, "other")

        ok, message, paper = create_paper(
            title         = title,
            abstract      = abstract,
            keywords      = keywords,
            research_area = research_area,
            guide_name    = guide_name,
            dept_id       = dept_map[dept_name],
            pub_year      = int(pub_year),
            paper_type    = paper_type_db,
            uploaded_by   = user_id,      # ← from session, never user input
            uploaded_file = pdf_file
        )

        if ok:
            log_activity(user_id, "upload_paper", "paper", paper["paper_id"])
            # Notify all admins of new submission
            from services.notification_service import notify_role
            notify_role("admin",
                        f"New paper submitted: '{paper['title'][:60]}' "
                        f"by {st.session_state['user_name']}. "
                        f"Paper ID: {paper['paper_code']}")
            st.success(message)

            # ── Show paper summary ────────────────────────────────────────────
            st.divider()
            st.subheader(":material/check_circle: Paper Submitted Successfully")
            st.info("Your paper has been submitted with status **Pending**. "
                    "Admin will review and notify you.")

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Paper ID",   paper["paper_code"])
            c2.metric("Status",     paper["status"].title())
            c3.metric("Department", paper["dept_name"] or "—")
            c4.metric("Year",       paper["pub_year"]  or "—")

            with st.expander("View submitted details"):
                st.write(f"**Title:** {paper['title']}")
                st.write(f"**Abstract:** {paper['abstract']}")
                st.write(f"**Keywords:** {paper['keywords'] or '—'}")
                st.write(f"**Research Area:** {paper['research_area'] or '—'}")
                st.write(f"**Guide:** {paper['guide_name'] or '—'}")
                st.write(f"**Paper Type:** {paper['paper_type'].replace('_',' ').title()}")
                sz = paper["file_size"] or 0
                st.write(f"**File:** {paper['file_name']}  "
                         f"({sz / 1024 / 1024:.2f} MB)")

        else:
            st.error(message)
