"""
pages/admin/qr_codes.py
Module 12: Admin QR Code management page.
Generate, view, and manage QR codes for approved papers.
"""
import streamlit as st
from PIL import Image
from services.auth_service import require_role
from services.qr_service import (
    get_papers_with_qr_status, get_or_create_qr,
    generate_qr_for_all_approved, delete_qr, get_base_url
)


def show():
    require_role("admin")
    st.title(":material/qr_code_2: QR Code Management")
    st.caption("Generate and manage QR codes for approved research papers.")
    st.divider()

    # ── Paper overview ───

    papers = get_papers_with_qr_status()
    total   = len(papers)
    has_qr  = sum(1 for p in papers if p["qr_exists"])
    no_qr   = total - has_qr

    c1, c2, c3 = st.columns(3)
    c1.metric("Approved Papers", total)
    c2.metric(":material/check_circle: QR Generated", has_qr)
    c3.metric("⏳ QR Missing",   no_qr)

    # ── Batch generate ────────────────────────────────────────────────────────
    if no_qr > 0:
        st.warning(f"{no_qr} approved paper(s) don't have QR codes yet.")
        if st.button(":material/sync: Generate All Missing QR Codes", type="primary"):
            with st.spinner("Generating QR codes..."):
                gen, skip = generate_qr_for_all_approved()
            st.success(f"Done! Generated: {gen}  |  Skipped/Failed: {skip}")
            st.rerun()
    else:
        if total > 0:
            st.success("All approved papers have QR codes. :material/check_circle:")

    if not papers:
        st.info("No approved papers found. Approve papers first.")
        return

    st.divider()

    # ── Filter ────────────────────────────────────────────────────────────────
    filter_opt = st.radio("Show", ["All", ":material/check_circle: Has QR", "⏳ Missing QR"],
                          horizontal=True)

    if filter_opt == ":material/check_circle: Has QR":
        papers = [p for p in papers if p["qr_exists"]]
    elif filter_opt == "⏳ Missing QR":
        papers = [p for p in papers if not p["qr_exists"]]

    st.caption(f"Showing {len(papers)} paper(s)")
    st.divider()

    # ── Paper list ────────────────────────────────────────────────────────────
    for p in papers:
        qr_badge = ":material/check_circle: QR Ready" if p["qr_exists"] else "⏳ No QR"
        label = f"{qr_badge}  |  {p['paper_code']}  —  {p['title'][:55]}"

        with st.expander(label):
            col_info, col_qr = st.columns([2, 1])

            with col_info:
                st.write(f"**Paper Code:** `{p['paper_code']}`")
                st.write(f"**Department:** {p['dept_name'] or '—'}")
                st.write(f"**QR Path:** `{p['qr_code_path'] or 'Not generated'}`")

                # Action buttons
                if not p["qr_exists"]:
                    if st.button("⚡ Generate QR",
                                 key=f"gen_{p['paper_id']}",
                                 type="primary"):
                        path = get_or_create_qr(p["paper_id"], p["paper_code"])
                        if path:
                            st.success("QR code generated!"); st.rerun()
                        else:
                            st.error("QR generation failed.")
                else:
                    if st.button(":material/sync: Regenerate QR",
                                 key=f"regen_{p['paper_id']}"):
                        delete_qr(p["paper_id"], p["paper_code"])
                        path = get_or_create_qr(p["paper_id"], p["paper_code"])
                        if path:
                            st.success("QR regenerated!"); st.rerun()
                        else:
                            st.error("Regeneration failed.")

            with col_qr:
                if p["qr_exists"]:
                    try:
                        img = Image.open(p["qr_code_path"])
                        st.image(img, caption=f"Scan for {p['paper_code']}", width=230)
                        # Download QR as PNG
                        with open(p["qr_code_path"], "rb") as f:
                            st.download_button(
                                ":material/download: Download QR",
                                data=f.read(),
                                file_name=f"{p['paper_code']}_qr.png",
                                mime="image/png",
                                key=f"dl_qr_{p['paper_id']}")
                    except Exception:
                        st.warning("QR file unreadable.")
                else:
                    st.info("No QR yet.")
