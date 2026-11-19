import base64
import os
"""
pages/admin/papers.py
Module 5 + 6 update: Admin views ALL papers (all statuses) with full details.
Links to approval queue for pending papers.
"""
import streamlit as st
from services.auth_service import require_role
from services.ui_theme_service import render_inline_pdf_viewer
from services.paper_service import (
    get_all_papers_admin, get_paper_by_id,
    get_paper_status_history
)

STATUS_ICON = {
    "pending":           ":material/hourglass_top:",
    "approved":          ":material/check_circle:",
    "rejected":          ":material/cancel:",
    "changes_requested": ":material/info:",
}


def _resolve_pdf_path(raw_path: str) -> str | None:
    if not raw_path:
        return None
    candidates = [
        raw_path,
        os.path.join("rprms_app", raw_path),
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), raw_path),
        os.path.join("rprms_app", "uploads", "papers", os.path.basename(raw_path)),
        os.path.join("uploads", "papers", os.path.basename(raw_path)),
        os.path.abspath(raw_path),
    ]
    for c in candidates:
        if os.path.exists(c):
            return os.path.abspath(c)
    return None


def show():
    require_role("admin")
    st.title(":material/description: All Papers")
    st.divider()

    papers = get_all_papers_admin()

    if not papers:
        st.info("No papers have been submitted yet.")
        return

    # ── Summary row ───────────────────────────────────────────────────────────
    total    = len(papers)
    pending  = sum(1 for p in papers if p["status"] == "pending")
    approved = sum(1 for p in papers if p["status"] == "approved")
    rejected = sum(1 for p in papers if p["status"] == "rejected")
    changes  = sum(1 for p in papers if p["status"] == "changes_requested")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total",           total)
    c2.metric(":material/hourglass_top: Pending",      pending)
    c3.metric(":material/check_circle: Approved",     approved)
    c4.metric(":material/cancel: Rejected",     rejected)
    c5.metric(":material/info: Changes Req.", changes)

    if pending > 0:
        st.warning(f"⚠ {pending} paper(s) awaiting review. "
                   f"Go to **Pending Approvals** to review them.")
    st.divider()

    # ── Filters ───────────────────────────────────────────────────────────────
    col_s, col_f = st.columns([3, 1])
    search   = col_s.text_input("Search", placeholder="Title, uploader or dept...",
                                label_visibility="collapsed")
    status_f = col_f.selectbox("Status", ["All", "pending", "approved",
                                           "rejected", "changes_requested"],
                               label_visibility="collapsed")

    filtered = papers
    if search.strip():
        s = search.strip().lower()
        filtered = [p for p in filtered
                    if s in p["title"].lower()
                    or s in (p["uploader_name"] or "").lower()
                    or s in (p["dept_name"] or "").lower()
                    or s in (p["paper_code"] or "").lower()]
    if status_f != "All":
        filtered = [p for p in filtered if p["status"] == status_f]

    st.caption(f"Showing {len(filtered)} paper(s)")

    # ── Paper list ────────────────────────────────────────────────────────────
    for p in filtered:
        icon  = STATUS_ICON.get(p["status"], "⚪")
        label = (f"{icon} {p['paper_code']}  —  {p['title'][:50]}  "
                 f"| {p['uploader_name']} | {p['dept_name'] or '—'}")

        with st.expander(label):
            c1, c2, c3, c4 = st.columns(4)
            c1.write(f"**Status:** {p['status'].replace('_',' ').title()}")
            c2.write(f"**Year:** {p['pub_year'] or '—'}")
            c3.write(f"**Type:** "
                     f"{p['paper_type'].replace('_',' ').title() if p['paper_type'] else '—'}")
            c4.write(f"**Submitted:** {str(p['created_at'])[:10]}")

            full = get_paper_by_id(p["paper_id"])
            if full:
                with st.container(border=True):
                    st.markdown("**Abstract**")
                    st.write(full["abstract"] or "—")
                    col_l, col_r = st.columns(2)
                    col_l.write(f"**Keywords:** {full['keywords'] or '—'}")
                    col_l.write(f"**Research Area:** {full['research_area'] or '—'}")
                    col_r.write(f"**Guide:** {full['guide_name'] or '—'}")
                    sz = (full["file_size"] or 0) / 1024 / 1024
                    res_path = _resolve_pdf_path(full.get("file_path"))
                    pdf_b = None
                    if res_path and os.path.exists(res_path):
                        try:
                            with open(res_path, "rb") as pf:
                                pdf_b = pf.read()
                        except Exception:
                            pdf_b = None

                    with st.expander(":material/menu_book: View Full Research Paper (PDF Preview)"):
                        render_inline_pdf_viewer(
                            full.get("file_path"),
                            full.get("file_name"),
                            full.get("file_size"),
                            key=f"all_{p['paper_id']}"
                        )

            # Delete Paper option for Admin
            with st.expander(":material/delete_forever: Delete Paper (Admin)"):
                st.caption("Permanently delete this paper and its files from the repository.")
                col_d1, col_d2 = st.columns([3, 1], vertical_alignment="center")
                confirm = col_d1.checkbox("Confirm permanent deletion", key=f"chk_adm_all_{p['paper_id']}")
                if col_d2.button(":material/delete: Delete Paper", key=f"btn_del_all_{p['paper_id']}", disabled=not confirm, type="primary"):
                    from services.paper_service import delete_paper
                    ok, msg = delete_paper(p["paper_id"], st.session_state["user_id"], "admin")
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

            # show review history
            history = get_paper_status_history(p["paper_id"])
            if history:
                with st.expander(":material/history_edu: Review History"):
                    for h in history:
                        arrow = (f"{h['old_status']} → {h['new_status']}"
                                 if h["old_status"] else h["new_status"])
                        st.caption(
                            f"{str(h['changed_at'])[:16]}  |  **{arrow}**  |  "
                            f"by {h['reviewer_name']}  |  {h['comments'] or ''}")
