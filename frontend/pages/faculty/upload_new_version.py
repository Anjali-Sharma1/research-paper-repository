"""
pages/faculty/upload_new_version.py
Module 7: Faculty re-uploads a revised paper after 'changes_requested'.
Only shown/accessible when a paper has status = 'changes_requested'.
"""
import streamlit as st
from services.auth_service import require_role, log_activity
from services.paper_service import (
    get_papers_by_uploader, get_paper_by_id,
    get_paper_versions, get_paper_status_history,
    upload_new_version
)


def show():
    require_role("faculty", "student", "admin")
    user_id = st.session_state["user_id"]

    st.title(":material/sync: Upload Revised Version")
    st.caption("Re-upload your paper after admin has requested changes.")
    st.divider()

    # ── Get papers that need changes ──────────────────────────────────────────
    all_papers = get_papers_by_uploader(user_id)
    needs_changes = [p for p in all_papers
                     if p["status"] == "changes_requested"]

    if not needs_changes:
        st.info("You have no papers requiring a revised upload right now.")
        if st.button("← Back to My Papers"):
            st.session_state["_nav"] = "My Papers"
            st.rerun()
        return

    # ── Paper selector ────────────────────────────────────────────────────────
    paper_options = {
        f"{p['paper_code']} — {p['title'][:55]}": p["paper_id"]
        for p in needs_changes
    }
    selected_label = st.selectbox(
        "Select paper to revise *",
        list(paper_options.keys()),
        help="Only papers with 'Changes Requested' status appear here."
    )
    paper_id   = paper_options[selected_label]
    paper_full = get_paper_by_id(paper_id)

    if not paper_full:
        st.error("Paper not found."); return

    st.divider()

    # ── Show current paper info ───────────────────────────────────────────────
    with st.container(border=True):
        st.markdown(f"**{paper_full['paper_code']}** — {paper_full['title']}")
        c1, c2, c3 = st.columns(3)
        c1.write(f"**Status:** :material/info: Changes Requested")
        c2.write(f"**Dept:** {paper_full['dept_name'] or '—'}")
        c3.write(f"**Year:** {paper_full['pub_year'] or '—'}")

    # ── Show reviewer comments ────────────────────────────────────────────────
    history = get_paper_status_history(paper_id)
    changes_comments = [h for h in history
                        if h["new_status"] == "changes_requested"]
    if changes_comments:
        st.subheader(":material/comment: Admin's Review Comment")
        for h in changes_comments:
            with st.container(border=True):
                st.write(f"**Comment:** {h['comments'] or 'No comment provided.'}")
                st.caption(
                    f"By: {h['reviewer_name']}  |  {str(h['changed_at'])[:16]}")

    # ── Version history ───────────────────────────────────────────────────────
    versions = get_paper_versions(paper_id)
    if versions:
        with st.expander(f":material/description: Version History ({len(versions)} version(s))"):
            for v in versions:
                sz = (v["file_size"] or 0) / 1024 / 1024
                st.write(f"**v{v['version_no']}** — "
                         f"{v['change_notes'] or 'No notes'}")
                st.caption(
                    f"File: {v['file_name']}  |  {sz:.2f} MB  |  "
                    f"Uploaded by {v['uploader_name']}  |  "
                    f"{str(v['uploaded_at'])[:16]}")

    st.divider()

    # ── Re-upload form ────────────────────────────────────────────────────────
    st.subheader(":material/description: Upload Revised PDF")
    with st.form("reupload_form"):
        change_notes = st.text_area(
            "What did you change? *",
            placeholder="Describe the changes made in this revision "
                        "(e.g. Updated references, revised methodology section).",
            height=100)

        pdf_file = st.file_uploader(
            "Select revised PDF * (max 20 MB)",
            type=["pdf"])

        if pdf_file:
            sz = pdf_file.size / 1024 / 1024
            st.caption(f"Selected: **{pdf_file.name}**  |  {sz:.2f} MB")

        submitted = st.form_submit_button(
            ":material/send: Submit Revised Version",
            type="primary",
            use_container_width=True)

    if submitted:
        ok, msg, updated = upload_new_version(
            paper_id    = paper_id,
            uploaded_file = pdf_file,
            uploaded_by   = user_id,
            change_notes  = change_notes
        )
        if ok:
            log_activity(user_id, "upload_new_version",
                         "paper", paper_id)
            st.success(msg)
            st.balloons()
            st.info("Your revised paper is now **Pending** review again. "
                    "Admin will be notified.")

            if updated:
                c1, c2 = st.columns(2)
                c1.metric("Paper Code", updated["paper_code"])
                c2.metric("New Status", "Pending Review")
        else:
            st.error(msg)
