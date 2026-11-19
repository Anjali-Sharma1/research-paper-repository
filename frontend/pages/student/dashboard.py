"""
pages/student/dashboard.py
Student Dashboard — Styled matching the UI reference design.
Uses real database statistics.
"""
import streamlit as st
from services.auth_service import require_role
from services.user_service import get_user
from services.dashboard_service import get_student_stats, get_recently_added_papers
from services.bookmark_download_service import (
    get_my_bookmark_count, get_my_download_count, get_most_downloaded
)
from services.ui_theme_service import (
    render_kpi_card, render_area_growth_chart,
    render_donut_chart, render_traffic_progress, render_calendar_widget
)

def show():
    require_role("student")
    user_id = st.session_state["user_id"]
    name    = st.session_state["user_name"]
    user    = get_user(user_id)
    stats   = get_student_stats(user_id)
    bm_cnt  = get_my_bookmark_count(user_id)
    dl_cnt  = get_my_download_count(user_id)

    # ── Real Database Statistics ─────────────────────────────────────────────
    avail_papers = stats.get("available_papers", 0) or 0
    bookmarks_val = bm_cnt or 0
    downloads_val = dl_cnt or 0

    # Fetch student's own submissions
    my_papers_cnt = 0
    try:
        from database.connection import get_connection
        _c = get_connection()
        _cur = _c.cursor(dictionary=True)
        _cur.execute("SELECT COUNT(*) as cnt FROM papers WHERE uploaded_by = %s", (user_id,))
        _r = _cur.fetchone()
        if _r:
            my_papers_cnt = _r.get("cnt", 0)
    except Exception:
        pass

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        render_kpi_card("My Uploaded Papers", f"{my_papers_cnt:,}", "My Submissions", icon_symbol="U", highlighted=True)

    with c2:
        render_kpi_card("Repository Papers", f"{avail_papers:,}", "6.40%", icon_symbol="P", highlighted=False)

    with c3:
        render_kpi_card("Saved Bookmarks", f"{bookmarks_val:,}", "8.10%", icon_symbol="B", highlighted=False)

    with c4:
        render_kpi_card("Total Downloads", f"{downloads_val:,}", "14.2%", icon_symbol="D", highlighted=False)

    st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

    # ── Main 2-Column Dashboard Layout ──────────────────────────────────────────
    left_col, right_col = st.columns([7, 5])

    with left_col:
        with st.container(border=True):
            render_area_growth_chart(chart_title="Repository Activity & Paper Trends")

        st.markdown("<div style='margin-bottom: 16px;'></div>", unsafe_allow_html=True)

        with st.container(border=True):
            render_calendar_widget()

    with right_col:
        with st.container(border=True):
            st.markdown("<h4 style='font-size: 16px; font-weight: 700; color: #0F172A; margin-bottom: 8px;'>Repository Categories</h4>", unsafe_allow_html=True)
            render_donut_chart(center_text=f"Total Papers\n{avail_papers:,}")

        st.markdown("<div style='margin-bottom: 16px;'></div>", unsafe_allow_html=True)

        with st.container(border=True):
            st.markdown("<h4 style='font-size: 16px; font-weight: 700; color: #0F172A; margin-bottom: 12px;'>Department Publications</h4>", unsafe_allow_html=True)
            render_traffic_progress()

    st.markdown("<div style='margin-bottom: 24px;'></div>", unsafe_allow_html=True)

    # ── Search & Discovery ──────────────────────────────────────────────────
    st.markdown("<h3 style='font-size: 20px; font-weight: 800; color: #0F172A;'>Research Discovery</h3>", unsafe_allow_html=True)
    q1, q2 = st.columns(2)

    with q1:
        with st.container(border=True):
            st.markdown("<h4 style='font-size: 16px; font-weight: 700; color: #0F172A;'>Researcher Quick Actions</h4>", unsafe_allow_html=True)
            if st.button("Submit Research Paper", icon=":material/upload_file:", type="primary", use_container_width=True):
                st.session_state["_nav"] = "Upload Paper"
                st.rerun()
            col_qa1, col_qa2 = st.columns(2)
            with col_qa1:
                if st.button("My Papers", icon=":material/folder:", use_container_width=True):
                    st.session_state["_nav"] = "My Papers"
                    st.rerun()
            with col_qa2:
                if st.button("Track Status", icon=":material/fact_check:", use_container_width=True):
                    st.session_state["_nav"] = "Paper Status"
                    st.rerun()
            if st.button("Search & Browse Catalog", icon=":material/search:", use_container_width=True):
                st.session_state["_nav"] = "Search Papers"
                st.rerun()

    with q2:
        with st.container(border=True):
            st.markdown("<h4 style='font-size: 16px; font-weight: 700; color: #0F172A;'>Most Downloaded Papers</h4>", unsafe_allow_html=True)
            top = get_most_downloaded(4)
            if not top:
                st.info("No downloads recorded yet.")
            else:
                for i, p in enumerate(top, 1):
                    st.markdown(f"""
                    <div style="display: flex; align-items: center; justify-content: space-between; background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 10px; margin-bottom: 8px;">
                        <span style="font-weight: 700; font-size: 13px; color: #0F172A;">#{i} {p['title'][:32]}...</span>
                        <span style="font-size: 11px; font-weight: 700; color: #0047FF;">{p['download_count']} DLs</span>
                    </div>
                    """, unsafe_allow_html=True)
                if st.button("View My Saved Bookmarks", use_container_width=True):
                    st.session_state["_nav"] = "My Bookmarks"
                    st.rerun()
