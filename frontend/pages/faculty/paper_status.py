"""
pages/faculty/paper_status.py
Module 6: Faculty views status history and reviewer comments for their papers.
Read-only — approval actions are admin-only.
"""
import streamlit as st
from services.auth_service import require_role
from services.ui_theme_service import render_inline_pdf_viewer
from services.paper_service import (
    get_papers_by_uploader, get_paper_by_id,
    get_paper_status_history
)

STATUS_ICON = {
    "pending":           ":material/hourglass_top: Pending",
    "approved":          ":material/check_circle: Approved",
    "rejected":          ":material/cancel: Rejected",
    "changes_requested": ":material/info: Changes Requested",
}
STATUS_COLOR = {
    "pending":           "orange",
    "approved":          "green",
    "rejected":          "red",
    "changes_requested": "blue",
}


def show():
    require_role("faculty", "student", "admin")
    user_id = st.session_state["user_id"]

    st.title(":material/bar_chart: My Paper Status")
    st.caption("View the approval status and reviewer comments for all your submitted papers.")
    st.divider()

    papers = get_papers_by_uploader(user_id)

    if not papers:
        st.info("You have not uploaded any papers yet.")
        if st.button(":material/upload_file: Upload Your First Paper", type="primary"):
            st.session_state["_nav"] = "Upload Paper"
            st.rerun()
        return

    # ── Quick summary badges ───────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total",              len(papers))
    c2.metric(":material/hourglass_top: Pending",        sum(1 for p in papers if p["status"] == "pending"))
    c3.metric(":material/check_circle: Approved",       sum(1 for p in papers if p["status"] == "approved"))
    c4.metric(":material/cancel:/:material/info: Action Req.", sum(1 for p in papers
                                        if p["status"] in ("rejected","changes_requested")))
    st.divider()

    # ── Per-paper status + history ─────────────────────────────────────────────
    for p in papers:
        status_label = STATUS_ICON.get(p["status"], p["status"])
        label = f"{status_label}  |  {p['paper_code']}  —  {p['title'][:55]}"

        with st.expander(label):
            # Paper details
            c1, c2, c3 = st.columns(3)
            c1.write(f"**Department:** {p['dept_name'] or '—'}")
            c2.write(f"**Year:** {p['pub_year'] or '—'}")
            c3.write(f"**Submitted:** {str(p['created_at'])[:10]}")

            # Status-specific guidance
            if p["status"] == "pending":
                st.info("⏳ Your paper is in the admin review queue. "
                        "You will be notified when a decision is made.")
            elif p["status"] == "approved":
                st.success(":material/check_circle: Your paper has been approved and is now "
                           "visible in the repository.")
            elif p["status"] == "rejected":
                st.error(":material/cancel: Your paper was rejected. "
                         "Please read the reviewer comment below.")
                with st.expander(":material/delete: Delete Rejected Paper"):
                    st.caption("You can delete this rejected submission to clean up your status list.")
                    col_s1, col_s2 = st.columns([3, 1], vertical_alignment="center")
                    confirm_st = col_s1.checkbox("Confirm deletion", key=f"chk_rej_st_{p['paper_id']}")
                    if col_s2.button(":material/delete: Delete", key=f"btn_rej_st_{p['paper_id']}", disabled=not confirm_st, type="primary"):
                        from services.paper_service import delete_paper
                        ok, msg = delete_paper(p["paper_id"], user_id, st.session_state.get("user_role", "student"))
                        if ok:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
            elif p["status"] == "changes_requested":
                st.warning(":material/info: Admin has requested changes. Read the comment "
                           "below. Re-upload will be available in Module 7.")

            full = get_paper_by_id(p["paper_id"]) or p
            with st.expander(":material/menu_book: View Submitted Research Paper (PDF Preview)"):
                render_inline_pdf_viewer(
                    full.get("file_path"),
                    full.get("file_name"),
                    full.get("file_size"),
                    key=f"status_view_{p['paper_id']}"
                )

            # Review history
            history = get_paper_status_history(p["paper_id"])
            if history:
                st.markdown("**Review History**")
                for h in history:
                    arrow = (f"{h['old_status']} → {h['new_status']}"
                             if h["old_status"] else f"Submitted → {h['new_status']}")
                    with st.container(border=True):
                        col_l, col_r = st.columns([3, 1])
                        col_l.write(f"**{arrow}**")
                        col_r.caption(str(h["changed_at"])[:16])
                        if h["comments"]:
                            st.write(f":material/comment: *{h['comments']}*")
                        st.caption(f"Reviewed by: {h['reviewer_name']} "
                                   f"[{h['role'].title()}]")
            else:
                st.caption("No review history yet.")
