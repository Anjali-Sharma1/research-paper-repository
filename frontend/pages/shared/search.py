"""
pages/shared/search.py
Module 9 update: Bookmark toggle + proper download tracking + robust search & pagination.
"""
import streamlit as st
from services.search_service import (
    search_papers, get_search_stats,
    get_available_years, PAPER_TYPES, SORT_OPTIONS, get_paper_detail
)
from services.department_service import get_all_departments_simple
from services.bookmark_download_service import (
    is_bookmarked, toggle_bookmark,
    record_download, get_download_count
)
from services.auth_service import log_activity
from services.ui_theme_service import render_inline_pdf_viewer


def _paper_card(p, user_id, role, idx):
    with st.container(border=True):
        col_l, col_r = st.columns([5, 1], vertical_alignment="center")
        with col_l:
            st.markdown(f"<div style='font-size: 16px; font-weight: 750; color: #0F172A;'>{p['title']}</div>", unsafe_allow_html=True)
            st.caption(
                f":material/push_pin: **{p['paper_code']}**  |  "
                f":material/account_balance: {p['dept_name'] or '—'}  |  "
                f":material/calendar_today: {p['pub_year'] or '—'}  |  "
                f":material/description: {(p['paper_type'] or '').replace('_',' ').title()}  |  "
                f":material/person: {p['uploader_name']}  |  "
                f":material/download: {get_download_count(p['paper_id'])} downloads")
            if p.get("keywords"):
                st.caption(f":material/vpn_key: **Keywords:** {p['keywords']}")
            if p.get("research_area"):
                st.caption(f":material/science: **Area:** {p['research_area']}")
        with col_r:
            if role in ("student", "faculty") and user_id:
                bm = is_bookmarked(p["paper_id"], user_id)
                if st.button("★ Saved" if bm else "☆ Save",
                             key=f"bm_{p['paper_id']}_{idx}",
                             use_container_width=True):
                    ok, msg, _ = toggle_bookmark(p["paper_id"], user_id)
                    if ok:
                        st.toast(msg); st.rerun()
                    else:
                        st.error(msg)
            if st.button("View →",
                         key=f"view_{p['paper_id']}_{idx}",
                         type="primary",
                         use_container_width=True):
                st.session_state["view_paper_id"] = p["paper_id"]
                st.rerun()


def show(admin_view: bool = False):
    user_id = st.session_state.get("user_id")
    role    = st.session_state.get("user_role", "")

    # Fast route: if user clicked on paper detail
    if "view_paper_id" in st.session_state:
        _show_detail(st.session_state["view_paper_id"],
                     user_id=user_id, role=role, admin_view=admin_view)
        return

    st.title(":material/search: Search Research Papers")

    stats = get_search_stats()
    if stats["total_papers"] == 0:
        st.info("No approved papers in the repository yet.")
        return

    c1, c2, c3 = st.columns(3)
    c1.metric("Papers Available", stats["total_papers"])
    c2.metric("Departments",      stats["total_depts"])
    c3.metric("Publication Years",stats["total_years"])
    st.divider()

    col_q, col_clear = st.columns([5, 1], vertical_alignment="center")
    with col_q:
        keyword = st.text_input("Search",
            placeholder="Search by Title, ID (RPRMS...), Department, Author, Keyword, Year...",
            label_visibility="collapsed",
            key="paper_search_query")
    with col_clear:
        if st.button("Clear", icon=":material/backspace:", key="btn_clear_search", use_container_width=True):
            st.session_state["paper_search_query"] = ""
            st.rerun()

    with st.expander(":material/tune: Filters & Sort", expanded=False):
        depts    = get_all_departments_simple()
        dept_map = {"All Departments": None} | {
            d["dept_name"]: d["dept_id"] for d in depts}
        years    = get_available_years()
        year_opts= ["All Years"] + [str(y) for y in years]
        type_opts= ["All"] + [t.replace("_"," ").title() for t in PAPER_TYPES]

        c1, c2, c3, c4 = st.columns(4)
        dept_sel = c1.selectbox("Department", list(dept_map.keys()))
        year_sel = c2.selectbox("Year",        year_opts)
        type_sel = c3.selectbox("Paper Type",  type_opts)
        sort_sel = c4.selectbox("Sort By",     list(SORT_OPTIONS.keys()))
        area_sel = st.text_input("Research Area",
                                 placeholder="e.g. Machine Learning")

    dept_id   = dept_map.get(dept_sel)
    pub_year  = int(year_sel) if year_sel != "All Years" else None
    paper_type= None if type_sel == "All"                 else type_sel.lower().replace(" ", "_")

    results = search_papers(
        keyword=keyword, dept_id=dept_id, pub_year=pub_year,
        paper_type=paper_type, research_area=area_sel,
        sort_by=sort_sel, admin_view=admin_view)

    total_results = len(results)
    if keyword.strip() or dept_id or pub_year or paper_type or area_sel:
        st.caption(f"Found **{total_results}** result(s) matching your criteria")
        if not results:
            st.warning("No papers found. Try different keywords or clear filters.")
            return
    else:
        st.caption(f"Showing repository papers ({total_results} available)")

    # ── Pagination ────────────────────────────────────────────────────────────
    PAGE_SIZE = 10
    total_pages = max(1, (total_results + PAGE_SIZE - 1) // PAGE_SIZE)
    if "search_page" not in st.session_state:
        st.session_state["search_page"] = 1
    if st.session_state["search_page"] > total_pages:
        st.session_state["search_page"] = 1

    cur_page = st.session_state["search_page"]
    start_idx = (cur_page - 1) * PAGE_SIZE
    end_idx = min(start_idx + PAGE_SIZE, total_results)
    page_items = results[start_idx:end_idx]

    for i, p in enumerate(page_items, start=start_idx):
        _paper_card(p, user_id=user_id, role=role, idx=i)

    if total_pages > 1:
        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
        col_p1, col_p2, col_p3 = st.columns([1, 2, 1], vertical_alignment="center")
        with col_p1:
            if st.button("◀ Previous", disabled=(cur_page <= 1), use_container_width=True, key="search_prev_btn"):
                st.session_state["search_page"] = cur_page - 1
                st.rerun()
        with col_p2:
            st.markdown(f"<div style='text-align:center; font-weight:600; color:#64748B;'>Page {cur_page} of {total_pages} ({total_results} total papers)</div>", unsafe_allow_html=True)
        with col_p3:
            if st.button("Next ▶", disabled=(cur_page >= total_pages), use_container_width=True, key="search_next_btn"):
                st.session_state["search_page"] = cur_page + 1
                st.rerun()


def _show_detail(paper_id, user_id, role, admin_view=False):
    if st.button("← Back to Search Results", type="secondary"):
        del st.session_state["view_paper_id"]
        st.rerun()

    st.divider()
    paper = get_paper_detail(paper_id, approved_only=not admin_view)
    if not paper:
        st.error("Paper not found or not yet approved."); return

    col_title, col_bm = st.columns([5, 1], vertical_alignment="center")
    with col_title:
        st.title(paper["title"])

    with col_bm:
        if role in ("student", "faculty") and user_id:
            bm = is_bookmarked(paper_id, user_id)
            if st.button("★ Saved" if bm else "☆ Bookmark",
                         key=f"det_bm_{paper_id}",
                         type="primary" if bm else "secondary",
                         use_container_width=True):
                ok, msg, _ = toggle_bookmark(paper_id, user_id)
                if ok:
                    st.toast(msg); st.rerun()

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Paper ID",   paper["paper_code"])
    c2.metric("Department", paper["dept_name"] or "—")
    c3.metric("Year",       paper["pub_year"]  or "—")
    c4.metric("Type",
              paper["paper_type"].replace("_"," ").title()
              if paper["paper_type"] else "—")
    c5.metric("Downloads",  get_download_count(paper_id))

    st.caption(f"Uploaded by: **{paper['uploader_name']}**  |  Submitted: {str(paper['created_at'])[:10]}")
    st.divider()

    col_l, col_r = st.columns([3, 1])
    with col_l:
        st.subheader("Abstract & Research Scope")
        st.write(paper["abstract"] or "—")
        st.write(f"**Keywords:** {paper['keywords'] or '—'}")
        st.write(f"**Research Area:** {paper['research_area'] or '—'}")
        st.write(f"**Guide:** {paper['guide_name'] or '—'}")
    with col_r:
        sz = (paper["file_size"] or 0) / 1024 / 1024
        st.metric("File Size", f"{sz:.2f} MB")

        # QR Code — Module 12 with larger 220px image
        try:
            from services.qr_service import get_or_create_qr, paper_url
            qr_path = get_or_create_qr(paper_id, paper["paper_code"])
            if qr_path:
                from PIL import Image
                st.image(Image.open(qr_path),
                         caption="Scan for mobile preview",
                         width=220)
                st.caption(f":material/link: `{paper_url(paper_id)}`")
                with open(qr_path, "rb") as f:
                    st.download_button(
                        ":material/download: Download QR",
                        data=f.read(),
                        file_name=f"{paper['paper_code']}_qr.png",
                        mime="image/png",
                        key=f"dl_qr_detail_{paper_id}"
                    )
        except Exception:
            pass

    st.divider()
    st.subheader(":material/menu_book: Manuscript PDF & Document Reader")
    if paper.get("file_path"):
        opened = render_inline_pdf_viewer(
            paper.get("file_path"),
            paper.get("file_name"),
            paper.get("file_size"),
            key=f"search_detail_{paper_id}"
        )
        if opened and user_id:
            record_download(paper_id, user_id)
            log_activity(user_id, "view_paper", "paper", paper_id)
    else:
        st.info("No PDF attached to this paper.")
