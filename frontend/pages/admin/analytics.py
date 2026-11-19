"""
pages/admin/analytics.py
Module 10: Admin Analytics Dashboard.
Shows system-wide stats using native Streamlit charts.
"""
import streamlit as st
import pandas as pd
from services.auth_service import require_role
from services.analytics_service import (
    get_system_kpis, get_papers_by_status, get_papers_by_department,
    get_papers_by_year, get_papers_by_type, get_downloads_by_month,
    get_top_downloaded_papers, get_top_bookmarked_papers,
    get_faculty_upload_stats, get_dept_download_stats
)


def show():
    require_role("admin")
    c_t, c_b = st.columns([4, 1.3], vertical_alignment="center")
    with c_t:
        st.title(":material/bar_chart: Analytics & Reports")
    with c_b:
        if st.button("Reset Graphs", icon=":material/restart_alt:", key="btn_reset_admin_analytics", use_container_width=True):
            st.toast("Analytics graphs reset and refreshed!", icon=":material/refresh:")
            st.rerun()
    st.divider()

    kpis = get_system_kpis()

    # ── ROW 1: System KPIs ────────────────────────────────────────────────────
    st.subheader(":material/dashboard: System Overview")
    c1,c2,c3,c4,c5,c6 = st.columns(6)
    c1.metric("Total Users",     kpis["total_users"])
    c2.metric("Active Users",    kpis["active_users"])
    c3.metric("Faculty",         kpis["total_faculty"])
    c4.metric("Students",        kpis["total_students"])
    c5.metric("Departments",     kpis["total_depts"])
    c6.metric("Total Papers",    kpis["total_papers"])

    c1,c2,c3,c4,c5,c6 = st.columns(6)
    c1.metric(":material/check_circle: Approved",     kpis["approved_papers"])
    c2.metric(":material/hourglass_top: Pending",      kpis["pending_papers"])
    c3.metric(":material/cancel: Rejected",     kpis["rejected_papers"])
    c4.metric(":material/download: Downloads",    kpis["total_downloads"])
    c5.metric(":material/bookmark: Bookmarks",     kpis["total_bookmarks"])
    c6.metric("Unique DL Users", kpis["unique_downloaders"])
    st.divider()

    # ── ROW 2: Paper charts ───────────────────────────────────────────────────
    col_l, col_r = st.columns(2)

    with col_l:
        st.subheader("Papers by Status")
        data = get_papers_by_status()
        if data:
            df = pd.DataFrame(data).rename(
                columns={"status": "Status", "count": "Count"})
            st.bar_chart(df.set_index("Status")["Count"])
        else:
            st.info("No papers yet.")

    with col_r:
        st.subheader("Papers by Department")
        data = get_papers_by_department()
        if data:
            df = pd.DataFrame(data).rename(
                columns={"dept_name": "Department", "count": "Count"})
            st.bar_chart(df.set_index("Department")["Count"])
        else:
            st.info("No data yet.")

    col_l2, col_r2 = st.columns(2)

    with col_l2:
        st.subheader("Papers by Publication Year")
        data = get_papers_by_year()
        if data:
            df = pd.DataFrame(data).rename(
                columns={"year": "Year", "count": "Count"})
            df["Year"] = df["Year"].astype(str)
            st.bar_chart(df.set_index("Year")["Count"])
        else:
            st.info("No data yet.")

    with col_r2:
        st.subheader("Papers by Type")
        data = get_papers_by_type()
        if data:
            df = pd.DataFrame(data).rename(
                columns={"paper_type": "Type", "count": "Count"})
            df["Type"] = df["Type"].str.replace("_"," ").str.title()
            st.bar_chart(df.set_index("Type")["Count"])
        else:
            st.info("No data yet.")

    st.divider()

    # ── Downloads by month ────────────────────────────────────────────────────
    st.subheader(":material/download: Downloads by Month (Last 12)")
    data = get_downloads_by_month()
    if data:
        df = pd.DataFrame(data[::-1]).rename(
            columns={"month": "Month", "count": "Downloads"})
        st.line_chart(df.set_index("Month")["Downloads"])
    else:
        st.info("No downloads recorded yet.")

    col_l3, col_r3 = st.columns(2)

    with col_l3:
        st.subheader(":material/trending_up: Top Downloaded Papers")
        data = get_top_downloaded_papers(10)
        if data:
            df = pd.DataFrame(data)[
                ["paper_code","title","dept_name","download_count"]]
            df.columns = ["Code","Title","Department","Downloads"]
            df["Title"] = df["Title"].str[:40]
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No downloads yet.")

    with col_r3:
        st.subheader("★ Top Bookmarked Papers")
        data = get_top_bookmarked_papers(10)
        if data:
            df = pd.DataFrame(data)[
                ["paper_code","title","dept_name","bookmark_count"]]
            df.columns = ["Code","Title","Department","Bookmarks"]
            df["Title"] = df["Title"].str[:40]
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No bookmarks yet.")

    st.divider()

    # ── Faculty upload stats ──────────────────────────────────────────────────
    st.subheader(":material/person:‍:material/school: Faculty Upload Report")
    data = get_faculty_upload_stats()
    if data:
        df = pd.DataFrame(data)
        df.columns = ["Faculty","Department",
                      "Total","Approved","Pending","Action Needed"]
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No faculty data yet.")

    st.divider()

    # ── Dept download stats ───────────────────────────────────────────────────
    st.subheader(":material/account_balance: Downloads by Department")
    data = get_dept_download_stats()
    if data:
        df = pd.DataFrame(data).rename(
            columns={"dept_name":"Department","download_count":"Downloads"})
        st.bar_chart(df.set_index("Department")["Downloads"])
    else:
        st.info("No download data yet.")
