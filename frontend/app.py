"""
app.py — RPRMS Entry Point — Styled Modern UI Dashboard
Run: streamlit run app.py
"""
import streamlit as st
import os
import base64
from html import escape as html_escape
from services.auth_service import init_session, get_unread_count
from auth.login import show as login_show
from auth.logout import logout
import services.ui_theme_service
from services.ui_theme_service import (
    apply_custom_theme, render_top_header, init_theme_state, get_user_avatar_html, render_sidebar_toggle, get_brand_logo_html
)

st.set_page_config(
    page_title="RPRMS — Research Paper Repository",
    page_icon=os.path.join(os.path.dirname(__file__), "assets", "logo_transparent.png") if os.path.exists(os.path.join(os.path.dirname(__file__), "assets", "logo_transparent.png")) else ":material/description:",
    layout="wide",
    initial_sidebar_state="expanded"
)

init_session()
init_theme_state()
apply_custom_theme()

_forced_nav = st.session_state.pop("_nav", None)

if not st.session_state["is_logged_in"]:
    login_show()
    st.stop()

# Persistent global navigation toggle
render_sidebar_toggle()

role    = st.session_state["user_role"]
user_id = st.session_state["user_id"]
name    = st.session_state["user_name"]
brand   = st.session_state.get("brand_logo", "RPRMS")

with st.sidebar:
    import base64
    brand_logo_html = get_brand_logo_html(size=68, rounded="12px", border=False, bg="transparent")
    initials = "".join(part[0] for part in name.split()[:2]).upper() or "U"
    safe_brand = html_escape(brand)
    safe_name = html_escape(name)
    safe_role = html_escape(role)
    safe_initials = html_escape(initials)

    st.markdown(f"""
    <div style="padding:12px 10px 18px;border-bottom:1px solid rgba(255,255,255,.13);margin-bottom:18px">
      <div style="display:flex;align-items:center;gap:13px;margin-bottom:18px">
        {brand_logo_html}
        <div><div style="font-size:20.5px;font-weight:850;letter-spacing:.4px;color:#fff;line-height:1.2">{safe_brand}</div>
        <div style="font-size:10.5px;letter-spacing:1.2px;text-transform:uppercase;color:#C5DDE3;font-weight:700">Research Repository</div></div>
      </div>
      <div style="display:flex;align-items:center;gap:11px;background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.1);border-radius:12px;padding:10px 13px">
        <div style="width:34px;height:34px;border-radius:9px;background:rgba(255,255,255,.15);display:flex;align-items:center;justify-content:center;color:#FFFFFF;font-weight:750;font-size:13px;flex-shrink:0">{safe_initials}</div>
        <div style="min-width:0"><div style="font-size:12.5px;font-weight:700;color:#fff;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{safe_name}</div>
        <div style="font-size:10.5px;color:#C5DDE3;text-transform:capitalize">{safe_role}</div></div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    unread = get_unread_count(user_id)
    notif_label = f"Notifications ({unread})" if unread else "Notifications"

    if role == "admin":
        menu_items = [
            "Dashboard", "Pending Approvals", "All Papers",
            "Version History", "Search Papers", "Analytics", "QR Codes",
            "User Management", "Departments", "Activity Logs", notif_label, "My Profile"
        ]
    elif role == "faculty":
        menu_items = [
            "Dashboard", "Upload Paper", "My Papers", "Upload Revision",
            "Paper Status", "Search Papers", "Analytics", notif_label, "My Profile"
        ]
    else:
        menu_items = [
            "Dashboard", "Upload Paper", "My Papers", "Upload Revision",
            "Paper Status", "Search Papers", "My Bookmarks", "Analytics", notif_label, "My Profile"
        ]

    if _forced_nav:
        for item in menu_items:
            if _forced_nav in item:
                st.session_state["active_page"] = item
                break
    if st.session_state.get("active_page") not in menu_items:
        st.session_state["active_page"] = menu_items[0]

    nav_icons = {
        "Dashboard": "dashboard", "Pending Approvals": "approval", "All Papers": "description",
        "Version History": "history", "Search Papers": "search", "Analytics": "bar_chart",
        "QR Codes": "qr_code_2", "User Management": "group", "Departments": "account_tree",
        "Activity Logs": "list_alt", "Notifications": "notifications", "Upload Paper": "upload_file",
        "My Papers": "library_books", "Upload Revision": "edit_document", "Paper Status": "fact_check",
        "My Bookmarks": "bookmarks", "My Profile": "person",
    }
    nav_icons[notif_label] = "notifications"
    page = st.radio(
        "Navigation", menu_items, key="active_page", label_visibility="collapsed",
        format_func=lambda item: f":material/{nav_icons.get(item, 'circle')}:  {item}",
    )
    st.divider()
    if st.button("Log Out", icon=":material/logout:", key="logout_button", use_container_width=True):
        logout()

# ── QR scan / Direct link: detect ?paper_id= query parameter ──────────────────
_qr_paper_id = None
try:
    params = st.query_params
    if "paper_id" in params:
        raw = params["paper_id"]
        _qr_paper_id = int(raw) if str(raw).isdigit() else None
except Exception:
    pass

if _qr_paper_id:
    # Direct paper view mode (from QR scan)
    from pages.shared.search import _show_detail
    from services.search_service import get_paper_detail

    paper = get_paper_detail(_qr_paper_id, approved_only=(role == "student"))
    if paper:
        st.info(":material/qr_code_scanner: Scanned / Direct Link Access")
        _show_detail(_qr_paper_id, user_id=user_id,
                     role=role, admin_view=(role == "admin"))
    else:
        st.error(f"Paper #{_qr_paper_id} not found or not yet approved for public viewing.")
    st.stop()

if "Notifications" in page:
    page = "Notifications"

clean = page.strip()

# Introduction header shown ONLY on Dashboard
if clean == "Dashboard":
    render_top_header(name, role, unread, show_camera=False)

if clean == "Dashboard":
    st.title(":material/dashboard: Research Repository Overview")
    st.caption("Publications, submissions, and activity at a glance.")

if role == "admin":
    if   clean == "Dashboard":
        from pages.admin.dashboard        import show; show()
    elif clean == "Pending Approvals":
        from pages.admin.approvals        import show; show()
    elif clean == "All Papers":
        from pages.admin.papers           import show; show()
    elif clean == "Version History":
        from pages.admin.paper_versions   import show; show()
    elif clean == "Search Papers":
        from pages.shared.search          import show; show(admin_view=True)
    elif clean == "Analytics":
        from pages.admin.analytics        import show; show()
    elif clean == "QR Codes":
        from pages.admin.qr_codes         import show; show()
    elif clean == "User Management":
        from pages.admin.user_management  import show; show()
    elif clean == "Departments":
        from pages.admin.departments      import show; show()
    elif clean == "Activity Logs":
        from pages.admin.activity_logs    import show; show()
    elif clean == "Notifications":
        from pages.shared.notifications   import show; show()
    elif clean == "My Profile":
        from pages.shared.profile         import show; show()

elif role == "faculty":
    if   clean == "Dashboard":
        from pages.faculty.dashboard          import show; show()
    elif clean == "Upload Paper":
        from pages.faculty.upload_paper       import show; show()
    elif clean == "My Papers":
        from pages.faculty.my_papers          import show; show()
    elif clean == "Upload Revision":
        from pages.faculty.upload_new_version import show; show()
    elif clean == "Paper Status":
        from pages.faculty.paper_status       import show; show()
    elif clean == "Search Papers":
        from pages.shared.search              import show; show(admin_view=False)
    elif clean == "Analytics":
        from pages.faculty.analytics          import show; show()
    elif clean == "Notifications":
        from pages.shared.notifications       import show; show()
    elif clean == "My Profile":
        from pages.shared.profile             import show; show()

else:
    if   clean == "Dashboard":
        from pages.student.dashboard          import show; show()
    elif clean == "Upload Paper":
        from pages.faculty.upload_paper       import show; show()
    elif clean == "My Papers":
        from pages.faculty.my_papers          import show; show()
    elif clean == "Upload Revision":
        from pages.faculty.upload_new_version import show; show()
    elif clean == "Paper Status":
        from pages.faculty.paper_status       import show; show()
    elif clean == "Search Papers":
        from pages.shared.search              import show; show(admin_view=False)
    elif clean == "My Bookmarks":
        from pages.student.bookmarks          import show; show()
    elif clean == "Analytics":
        from pages.student.analytics          import show; show()
    elif clean == "Notifications":
        from pages.shared.notifications       import show; show()
    elif clean == "My Profile":
        from pages.shared.profile             import show; show()
