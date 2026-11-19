"""
pages/admin/paper_versions.py
Module 7: Admin views version history across all papers.
Shows which papers have multiple versions (re-uploads after changes).
"""
import streamlit as st
from services.auth_service import require_role
from services.ui_theme_service import render_inline_pdf_viewer
from services.paper_service import (
    get_all_versions_summary, get_paper_versions, get_paper_by_id
)

STATUS_ICON = {
    "pending":           ":material/hourglass_top:",
    "approved":          ":material/check_circle:",
    "rejected":          ":material/cancel:",
    "changes_requested": ":material/info:",
}


def show():
    require_role("admin")
    st.title(":material/folder_copy: Paper Version History")
    st.caption("View all papers and their uploaded versions.")
    st.divider()

    papers = get_all_versions_summary()

    if not papers:
        st.info("No papers have been uploaded yet.")
        return

    # ── Summary ───────────────────────────────────────────────────────────────
    multi_version = sum(1 for p in papers if (p["version_count"] or 0) > 1)
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Papers",         len(papers))
    c2.metric("Multi-Version Papers", multi_version)
    c3.metric("Single-Version Papers",len(papers) - multi_version)
    st.divider()

    # ── Filters ───────────────────────────────────────────────────────────────
    col_s, col_f = st.columns([3, 1])
    search   = col_s.text_input("Search", placeholder="Title, paper code or uploader...",
                                label_visibility="collapsed")
    ver_f    = col_f.selectbox("Versions", ["All", "Multi-version only"],
                               label_visibility="collapsed")

    filtered = papers
    if search.strip():
        s = search.strip().lower()
        filtered = [p for p in filtered
                    if s in p["title"].lower()
                    or s in (p["paper_code"] or "").lower()
                    or s in (p["uploader_name"] or "").lower()]
    if ver_f == "Multi-version only":
        filtered = [p for p in filtered if (p["version_count"] or 0) > 1]

    st.caption(f"Showing {len(filtered)} paper(s)")

    # ── Paper list ────────────────────────────────────────────────────────────
    for p in filtered:
        icon      = STATUS_ICON.get(p["status"], "⚪")
        ver_badge = f"  |  :material/description: v{p['version_count']}" if p["version_count"] else ""
        label     = (f"{icon} {p['paper_code']}  —  {p['title'][:50]}"
                     f"{ver_badge}  |  {p['uploader_name']}")

        with st.expander(label):
            c1, c2, c3 = st.columns(3)
            c1.write(f"**Status:** {p['status'].replace('_',' ').title()}")
            c2.write(f"**Dept:** {p['dept_name'] or '—'}")
            c3.write(f"**Total Versions:** {p['version_count'] or 0}")

            if p["last_uploaded"]:
                st.caption(f"Last uploaded: {str(p['last_uploaded'])[:16]}")

            # Version rows
            versions = get_paper_versions(p["paper_id"])
            if versions:
                st.markdown("**Version History**")
                for v in versions:
                    sz = (v["file_size"] or 0) / 1024 / 1024
                    is_latest = v["version_no"] == versions[0]["version_no"]
                    badge = " ← **Latest**" if is_latest else ""
                    with st.container(border=True):
                        col_l, col_r = st.columns([3, 1])
                        col_l.write(
                            f"**Version {v['version_no']}**{badge}")
                        col_l.write(
                            f":material/edit_note: {v['change_notes'] or 'No notes'}")
                        col_r.caption(f"{sz:.2f} MB")
                        col_r.caption(str(v["uploaded_at"])[:16])
                        st.caption(
                            f"File: {v['file_name']}  |  "
                            f"By: {v['uploader_name']}")
                        with st.expander(f":material/menu_book: Preview Version {v['version_no']} PDF"):
                            render_inline_pdf_viewer(
                                v.get("file_path"),
                                v.get("file_name"),
                                v.get("file_size"),
                                key=f"ver_adm_{v['version_id']}_{v['version_no']}"
                            )
            else:
                st.caption("No version records found for this paper.")
