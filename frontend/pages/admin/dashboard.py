"""
pages/admin/dashboard.py
Admin Dashboard — Styled matching the UI reference design.
Uses real database statistics.
"""
import streamlit as st
from services.auth_service import require_role
from services.dashboard_service import (
    get_admin_stats, get_recent_activity, get_pending_papers_summary
)
from services.ui_theme_service import (
    render_kpi_card, render_area_growth_chart,
    render_donut_chart, render_traffic_progress, render_calendar_widget
)

def show():
    require_role("admin")
    name  = st.session_state["user_name"]
    stats = get_admin_stats()

    # ── Real Database Statistics ─────────────────────────────────────────────
    total_papers = stats.get("total_papers", 0) or 0
    pending_papers = stats.get("pending_papers", 0) or 0
    total_users = stats.get("total_users", 0) or 0

    c1, c2, c3 = st.columns(3)

    with c1:
        render_kpi_card("Total Papers", f"{total_papers:,}", "5.25%", icon_symbol="P", highlighted=False)

    with c2:
        render_kpi_card("Pending Reviews", f"{pending_papers:,}", "3.12%", icon_symbol="R", highlighted=False)

    with c3:
        render_kpi_card("Active Users", f"{total_users:,}", "8.55%", icon_symbol="U", highlighted=True)

    st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

    # ── Main 2-Column Dashboard Layout ──────────────────────────────────────────
    left_col, right_col = st.columns([7, 5])

    with left_col:
        with st.container(border=True):
            render_area_growth_chart(chart_title="Submissions & Download Growth")

        st.markdown("<div style='margin-bottom: 16px;'></div>", unsafe_allow_html=True)

        with st.container(border=True):
            render_calendar_widget()

    with right_col:
        with st.container(border=True):
            st.markdown("<h4 style='font-size: 16px; font-weight: 700; color: #0F172A; margin-bottom: 8px;'>Top Paper Types</h4>", unsafe_allow_html=True)
            render_donut_chart(center_text=f"Total Papers\n{total_papers:,}")

        st.markdown("<div style='margin-bottom: 16px;'></div>", unsafe_allow_html=True)

        with st.container(border=True):
            st.markdown("<h4 style='font-size: 16px; font-weight: 700; color: #0F172A; margin-bottom: 12px;'>Department Share</h4>", unsafe_allow_html=True)
            render_traffic_progress()

    st.markdown("<div style='margin-bottom: 24px;'></div>", unsafe_allow_html=True)

    # ── Queue & Activity ──────────────────────────────────────────────────────
    st.markdown("<h3 style='font-size: 20px; font-weight: 800; color: #0F172A;'>System Administration & Queue</h3>", unsafe_allow_html=True)
    q1, q2 = st.columns(2)

    with q1:
        with st.container(border=True):
            st.markdown("<h4 style='font-size: 16px; font-weight: 700; color: #0F172A;'>Pending Review Papers</h4>", unsafe_allow_html=True)
            pending_list = get_pending_papers_summary(5)
            if not pending_list:
                st.info("No papers currently awaiting approval.")
            else:
                for p in pending_list:
                    st.markdown(f"""
                    <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 12px; margin-bottom: 8px;">
                        <div style="font-weight: 700; color: #0F172A; font-size: 14px;">{p['paper_code']} — {p['title'][:40]}...</div>
                        <div style="font-size: 12px; color: #64748B; margin-top: 4px;">By: {p['uploader_name']}  •  {str(p['created_at'])[:10]}</div>
                    </div>
                    """, unsafe_allow_html=True)
                if st.button("Review Pending Queue", type="primary", use_container_width=True):
                    st.session_state["_nav"] = "Pending Approvals"
                    st.rerun()

    with q2:
        with st.container(border=True):
            st.markdown("<h4 style='font-size: 16px; font-weight: 700; color: #0F172A;'>Recent Audit Logs</h4>", unsafe_allow_html=True)
            logs = get_recent_activity(5)
            if not logs:
                st.caption("No recent system activity recorded.")
            else:
                for l in logs:
                    action = (l["action"] or "").replace("_", " ").title()
                    user   = l["full_name"] or "System"
                    when   = str(l["created_at"])[:16]
                    st.markdown(f"""
                    <div style="display: flex; align-items: center; justify-content: space-between; border-bottom: 1px dashed #E2E8F0; padding: 8px 0;">
                        <span style="font-weight: 600; font-size: 13px; color: #1E293B;">{action}</span>
                        <span style="font-size: 12px; color: #64748B;">{user} ({when})</span>
                    </div>
                    """, unsafe_allow_html=True)
                if st.button("View Full Audit Log", use_container_width=True):
                    st.session_state["_nav"] = "Activity Logs"
                    st.rerun()
