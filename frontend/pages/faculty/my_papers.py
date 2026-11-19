"""
pages/faculty/my_papers.py
Module 7 update: Shows version history per paper + link to re-upload.
"""
import streamlit as st
from services.auth_service import require_role
from services.ui_theme_service import render_inline_pdf_viewer
from services.paper_service import (
    get_papers_by_uploader, get_paper_by_id,
    get_paper_versions
)

STATUS_ICON = {
    "pending":           ":material/hourglass_top: Pending",
    "approved":          ":material/check_circle: Approved",
    "rejected":          ":material/cancel: Rejected",
    "changes_requested": ":material/info: Changes Requested",
}


def show():
    require_role("faculty", "student", "admin")
    user_id = st.session_state["user_id"]

    st.title(":material/folder: My Papers")
    st.divider()

    papers = get_papers_by_uploader(user_id)

    if not papers:
        st.info("You have not uploaded any papers yet.")
        if st.button(":material/upload_file: Upload Your First Paper", type="primary"):
            st.session_state["_nav"] = "Upload Paper"
            st.rerun()
        return

    # ── Summary ───────────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total",    len(papers))
    c2.metric(":material/hourglass_top: Pending",  sum(1 for p in papers if p["status"]=="pending"))
    c3.metric(":material/check_circle: Approved", sum(1 for p in papers if p["status"]=="approved"))
    c4.metric(":material/info: Changes",  sum(1 for p in papers
                                  if p["status"]=="changes_requested"))
    st.divider()

    for p in papers:
        status_label = STATUS_ICON.get(p["status"], p["status"])
        versions     = get_paper_versions(p["paper_id"])
        ver_count    = len(versions)
        label = (f"{status_label}  |  {p['paper_code']}  —  "
                 f"{p['title'][:50]}  |  v{ver_count}")

        with st.expander(label):
            c1, c2, c3 = st.columns(3)
            c1.write(f"**Department:** {p['dept_name'] or '—'}")
            c2.write(f"**Year:** {p['pub_year'] or '—'}")
            c3.write(f"**Type:** "
                     f"{p['paper_type'].replace('_',' ').title() if p['paper_type'] else '—'}")
            st.caption(f"Submitted: {str(p['created_at'])[:16]}")

            # Status guidance
            if p["status"] == "pending":
                st.info("⏳ Awaiting admin review.")
            elif p["status"] == "approved":
                st.success(":material/check_circle: Approved — visible in the repository.")
            elif p["status"] == "rejected":
                st.error(":material/cancel: Rejected. See Paper Status for admin comments.")
                with st.expander(":material/delete: Delete Rejected Submission"):
                    st.caption("Since this paper was rejected by admin, you can permanently remove it from your paper list.")
                    col_r1, col_r2 = st.columns([3, 1], vertical_alignment="center")
                    confirm_rej = col_r1.checkbox("Confirm remove rejected paper", key=f"chk_rej_my_{p['paper_id']}")
                    if col_r2.button(":material/delete: Delete", key=f"btn_rej_my_{p['paper_id']}", disabled=not confirm_rej, type="primary"):
                        from services.paper_service import delete_paper
                        ok, msg = delete_paper(p["paper_id"], user_id, st.session_state.get("user_role", "student"))
                        if ok:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
            elif p["status"] == "changes_requested":
                st.warning(":material/info: Admin requested changes.")
                if st.button(":material/sync: Upload Revised Version",
                             key=f"rev_{p['paper_id']}", type="primary"):
                    st.session_state["_nav"] = "Upload Revision"
                    st.rerun()

            full = get_paper_by_id(p["paper_id"]) or p
            if full.get("abstract"):
                with st.expander(":material/subject: Abstract & Research Info"):
                    st.write(full.get("abstract") or "—")
                    if full.get("keywords"):
                        st.caption(f"**Keywords:** {full.get('keywords')}")
                    if full.get("guide_name"):
                        st.caption(f"**Guide:** {full.get('guide_name')}")

            with st.expander(":material/menu_book: View Research Paper (PDF Preview)"):
                render_inline_pdf_viewer(
                    full.get("file_path"),
                    full.get("file_name"),
                    full.get("file_size"),
                    key=f"my_pdf_{p['paper_id']}"
                )

            # Version history
            if versions:
                st.markdown(f"**Version History ({ver_count} version(s))**")
                for v in versions:
                    sz = (v["file_size"] or 0) / 1024 / 1024
                    is_latest = v["version_no"] == versions[0]["version_no"]
                    latest_badge = " ← Latest" if is_latest else ""
                    with st.container(border=True):
                        col_l, col_r = st.columns([4, 1])
                        col_l.write(
                            f"**v{v['version_no']}**{latest_badge}  |  "
                            f"{v['change_notes'] or 'Initial upload'}")
                        col_r.caption(f"{sz:.2f} MB")
                        st.caption(
                            f"Uploaded: {str(v['uploaded_at'])[:16]}  |  "
                            f"File: {v['file_name']}")
                        with st.expander(f":material/description: View v{v['version_no']} Manuscript"):
                            render_inline_pdf_viewer(
                                v.get("file_path"),
                                v.get("file_name"),
                                v.get("file_size"),
                                key=f"my_ver_{v['version_id']}_{v['version_no']}"
                            )
            else:
                st.caption("No version records yet.")
