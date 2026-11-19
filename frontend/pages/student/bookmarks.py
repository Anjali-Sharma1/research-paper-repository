"""
pages/student/bookmarks.py
Module 9: Student bookmarks and download history — tabbed view.
"""
import streamlit as st
from services.auth_service import require_role, log_activity
from services.ui_theme_service import render_inline_pdf_viewer
from services.bookmark_download_service import (
    get_my_bookmarks, remove_bookmark,
    get_my_downloads, record_download,
    get_my_bookmark_count, get_my_download_count
)


def show():
    require_role("student", "faculty", "admin")
    user_id = st.session_state["user_id"]

    st.title("★ My Bookmarks & Downloads")
    st.divider()

    c1, c2 = st.columns(2)
    c1.metric("★ Total Bookmarks",  get_my_bookmark_count(user_id))
    c2.metric(":material/download: Total Downloads", get_my_download_count(user_id))
    st.divider()

    tab_bm, tab_dl = st.tabs(["★ My Bookmarks", ":material/download: Download History"])

    # ── BOOKMARKS ─────────────────────────────────────────────────────────────
    with tab_bm:
        bookmarks = get_my_bookmarks(user_id)
        if not bookmarks:
            st.info("You haven't bookmarked any papers yet. "
                    "Use the ☆ Save button on any paper in Search.")
        else:
            st.caption(f"{len(bookmarks)} bookmarked paper(s)")
            for bm in bookmarks:
                with st.container(border=True):
                    col_l, col_r = st.columns([5, 1])
                    with col_l:
                        st.write(f"**{bm['title']}**")
                        st.caption(
                            f":material/push_pin: {bm['paper_code']}  |  "
                            f":material/account_balance: {bm['dept_name'] or '—'}  |  "
                            f":material/calendar_today: {bm['pub_year'] or '—'}  |  "
                            f":material/person: {bm['uploader_name']}")
                        st.caption(f"Bookmarked: {str(bm['bookmarked_at'])[:16]}")
                    with col_r:
                        if bm.get("file_path"):
                            try:
                                with open(bm["file_path"], "rb") as f:
                                    pdf_bytes = f.read()
                                if st.download_button(
                                        ":material/download: Download",
                                        data=pdf_bytes,
                                        file_name=bm["file_name"],
                                        mime="application/pdf",
                                        key=f"bm_dl_{bm['bookmark_id']}",
                                        use_container_width=True):
                                    record_download(bm["paper_id"], user_id)
                                    log_activity(user_id, "download_paper",
                                                 "paper", bm["paper_id"])
                                    st.toast("Download recorded!")
                            except FileNotFoundError:
                                st.caption("File missing")
                    if dl.get("file_path"):
                        with st.expander(":material/menu_book: View Paper (PDF Preview)"):
                            render_inline_pdf_viewer(
                                dl.get("file_path"),
                                dl.get("file_name"),
                                key=f"dl_pdf_{dl['download_id']}"
                            )

                        if st.button(":material/delete: Remove",
                                     key=f"rm_{bm['bookmark_id']}",
                                     use_container_width=True):
                            ok, msg = remove_bookmark(bm["paper_id"], user_id)
                            if ok:
                                st.success(msg); st.rerun()
                            else:
                                st.error(msg)
                    if bm.get("file_path"):
                        with st.expander(":material/menu_book: View Paper (PDF Preview)"):
                            render_inline_pdf_viewer(
                                bm.get("file_path"),
                                bm.get("file_name"),
                                key=f"bm_pdf_{bm['bookmark_id']}"
                            )

    # ── DOWNLOAD HISTORY ──────────────────────────────────────────────────────
    with tab_dl:
        downloads = get_my_downloads(user_id)
        if not downloads:
            st.info("You haven't downloaded any papers yet. "
                    "Go to Search Papers to find papers.")
        else:
            st.caption(f"{len(downloads)} download event(s)")
            for dl in downloads:
                with st.container(border=True):
                    col_l, col_r = st.columns([5, 1])
                    with col_l:
                        st.write(f"**{dl['title']}**")
                        st.caption(
                            f":material/push_pin: {dl['paper_code']}  |  "
                            f":material/account_balance: {dl['dept_name'] or '—'}  |  "
                            f":material/calendar_today: {dl['pub_year'] or '—'}")
                        st.caption(
                            f"Downloaded: {str(dl['downloaded_at'])[:16]}")
                    with col_r:
                        if dl.get("file_path"):
                            try:
                                with open(dl["file_path"], "rb") as f:
                                    pdf_bytes = f.read()
                                if st.download_button(
                                        ":material/download: Re-download",
                                        data=pdf_bytes,
                                        file_name=dl["file_name"],
                                        mime="application/pdf",
                                        key=f"re_dl_{dl['download_id']}",
                                        use_container_width=True):
                                    record_download(dl["paper_id"], user_id)
                                    log_activity(user_id, "download_paper",
                                                 "paper", dl["paper_id"])
                            except FileNotFoundError:
                                st.caption("File missing")
