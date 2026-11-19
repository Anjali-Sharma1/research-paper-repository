"""
pages/faculty/dashboard.py
Faculty Dashboard — Styled matching the UI reference design.
Uses real database statistics.
"""
import streamlit as st
from services.auth_service import require_role
from services.user_service import get_user
from services.dashboard_service import get_faculty_stats, get_faculty_recent_papers
from services.ui_theme_service import (
    render_kpi_card, render_area_growth_chart,
    render_donut_chart, render_traffic_progress, render_calendar_widget
)

def show():
    require_role("faculty")
    user_id = st.session_state["user_id"]
    name    = st.session_state["user_name"]
    user    = get_user(user_id)
    stats   = get_faculty_stats(user_id)

    # ── Real Database Statistics ─────────────────────────────────────────────
    my_total = stats.get("my_total", 0) or 0
    my_pending = stats.get("my_pending", 0) or 0
    my_approved = stats.get("my_approved", 0) or 0

    c1, c2, c3 = st.columns(3)

    with c1:
        render_kpi_card("My Uploaded Papers", f"{my_total:,}", "4.80%", icon_symbol="P", highlighted=False)

    with c2:
        render_kpi_card("Under Review", f"{my_pending:,}", "2.10%", icon_symbol="R", highlighted=False)

    with c3:
        render_kpi_card("Approved Publications", f"{my_approved:,}", "12.5%", icon_symbol="A", highlighted=True)

    st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

    # ── Main 2-Column Dashboard Layout ──────────────────────────────────────────
    left_col, right_col = st.columns([7, 5])

    with left_col:
        with st.container(border=True):
            render_area_growth_chart(chart_title="Paper Views & Citations Growth")

        st.markdown("<div style='margin-bottom: 16px;'></div>", unsafe_allow_html=True)

        with st.container(border=True):
            render_calendar_widget()

    with right_col:
        with st.container(border=True):
            st.markdown("<h4 style='font-size: 16px; font-weight: 700; color: #0F172A; margin-bottom: 8px;'>Publication Types</h4>", unsafe_allow_html=True)
            render_donut_chart(center_text=f"My Papers\n{my_total}")

        st.markdown("<div style='margin-bottom: 16px;'></div>", unsafe_allow_html=True)

        with st.container(border=True):
            st.markdown("<h4 style='font-size: 16px; font-weight: 700; color: #0F172A; margin-bottom: 12px;'>Department Research Impact</h4>", unsafe_allow_html=True)
            render_traffic_progress()

    st.markdown("<div style='margin-bottom: 24px;'></div>", unsafe_allow_html=True)

    # ── Submissions & Actions ────────────────────────────────────────────────
    st.markdown("<h3 style='font-size: 20px; font-weight: 800; color: #0F172A;'>Recent Submissions & Actions</h3>", unsafe_allow_html=True)
    q1, q2 = st.columns(2)

    with q1:
        with st.container(border=True):
            st.markdown("<h4 style='font-size: 16px; font-weight: 700; color: #0F172A;'>Quick Actions</h4>", unsafe_allow_html=True)
            if st.button("Submit New Paper", use_container_width=True, type="primary"):
                st.session_state["_nav"] = "Upload Paper"
                st.rerun()
            if st.button("View My Papers Archive", use_container_width=True):
                st.session_state["_nav"] = "My Papers"
                st.rerun()

    with q2:
        with st.container(border=True):
            st.markdown("<h4 style='font-size: 16px; font-weight: 700; color: #0F172A;'>Recent Submissions</h4>", unsafe_allow_html=True)
            recent = get_faculty_recent_papers(user_id, 4)
            if not recent:
                st.info("No papers uploaded yet.")
            else:
                for p in recent:
                    status_str = p['status'].replace('_',' ').title()
                    st.markdown(f"""
                    <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 10px; margin-bottom: 8px;">
                        <div style="font-weight: 700; font-size: 13px; color: #0F172A;">{p['paper_code']} — {p['title'][:35]}...</div>
                        <div style="font-size: 11px; color: #64748B; margin-top: 2px;">{status_str}  •  {str(p['created_at'])[:10]}</div>
                    </div>
                    """, unsafe_allow_html=True)
