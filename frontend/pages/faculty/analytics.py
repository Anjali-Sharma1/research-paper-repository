"""
pages/faculty/analytics.py
Module 10: Faculty — personal analytics for their own papers.
Shows own upload stats, downloads, bookmarks per paper.
"""
import streamlit as st
import pandas as pd
from services.auth_service import require_role
from services.analytics_service import (
    get_faculty_personal_stats, get_faculty_paper_performance
)


def show():
    require_role("faculty", "admin")
    user_id = st.session_state["user_id"]
    name    = st.session_state["user_name"]

    c_t, c_b = st.columns([4, 1.3], vertical_alignment="center")
    with c_t:
        st.title(":material/bar_chart: My Analytics")
        st.caption(f"Personal performance report for **{name}**")
    with c_b:
        if st.button("Reset Graphs", icon=":material/restart_alt:", key="btn_reset_fac_analytics", use_container_width=True):
            st.toast("Analytics graphs reset and refreshed!", icon=":material/refresh:")
            st.rerun()
    st.divider()

    stats = get_faculty_personal_stats(user_id)

    # ── KPIs ──────────────────────────────────────────────────────────────────
    c1,c2,c3,c4,c5,c6 = st.columns(6)
    c1.metric("My Papers",        stats["total_papers"])
    c2.metric(":material/check_circle: Approved",       stats["approved"])
    c3.metric(":material/hourglass_top: Pending",        stats["pending"])
    c4.metric(":material/cancel: Action Needed",  stats["action_needed"])
    c5.metric(":material/download: Total Downloads",stats["total_downloads"])
    c6.metric("★ Total Bookmarks", stats["total_bookmarks"])
    st.divider()

    # ── Per-paper performance ─────────────────────────────────────────────────
    st.subheader(":material/description: Per-Paper Performance")
    data = get_faculty_paper_performance(user_id)
    if not data:
        st.info("Upload papers to see your analytics.")
        return

    df = pd.DataFrame(data)
    df["status"] = df["status"].str.replace("_"," ").str.title()
    df.columns   = ["Code","Title","Status","Year","Downloads","Bookmarks"]
    df["Title"]  = df["Title"].str[:50]
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.divider()

    # ── Charts ────────────────────────────────────────────────────────────────
    col_l, col_r = st.columns(2)

    with col_l:
        st.subheader("Downloads per Paper")
        if df["Downloads"].sum() > 0:
            chart_df = df[["Code","Downloads"]].set_index("Code")
            st.bar_chart(chart_df)
        else:
            st.info("No downloads recorded yet.")

    with col_r:
        st.subheader("Bookmarks per Paper")
        if df["Bookmarks"].sum() > 0:
            chart_df = df[["Code","Bookmarks"]].set_index("Code")
            st.bar_chart(chart_df)
        else:
            st.info("No bookmarks recorded yet.")
