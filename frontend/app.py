# Frontend entry point - sets page config, shows the landing page to guests and routes logged-in users to their view.
"""
app.py - the single entry point of the Research Paper Repository frontend.

Run:  streamlit run app.py

Every screen under views/ is registered here, so this file is the one place
that decides what a guest, a researcher, a guide or an admin can open.
Screens that are already written run their own script; the rest show a short
"planned" panel until they grow a render() function - then they light up here
on their own, with no change to this file.
"""

import importlib
import os
import sys

import streamlit as st

FRONTEND_DIR = os.path.dirname(os.path.abspath(__file__))
VIEWS_DIR = os.path.join(FRONTEND_DIR, "views")
sys.path.insert(0, VIEWS_DIR)

import auth_utils as au

PAGE_TITLE = "Research Paper Repository"
PAGE_ICON = "📚"
STYLESHEET = os.path.join(FRONTEND_DIR, "assets", "styles.css")

# Screens that are already written run as their own script, addressed by a path
# relative to this file - which is also what st.switch_page() expects.
REGISTER_PAGE = "views/register.py"
LOGIN_PAGE = "views/pages/login.py"
PROFILE_PAGE = "views/pages/profile.py"
ADMIN_PAGE = "views/pages/admin_console.py"

# Everything else in views/, as: module -> (title, icon, what it is for).
CATALOGUE = {
    "landing": ("Home", "🏠", "Public home page - what the repository holds and how to join."),
    "browse_search": ("Browse & Search", "🔍", "Search the published papers with filters and paging."),
    "paper_detail": ("Paper Details", "📄", "Full record of one paper: PDF, QR code and citations."),
    "researcher_dashboard": ("My Dashboard", "📊", "Your paper counts, pending reviews and recent activity."),
    "submit_paper": ("Submit Paper", "📤", "Upload a PDF and fill in the publication metadata."),
    "my_papers": ("My Papers", "📁", "Your own submissions with their status and edit options."),
    "guide_review": ("Review Queue", "✅", "Approve or reject the papers assigned to you."),
    "reports": ("Reports", "📈", "NAAC / NBA publication reports as PDF or Excel."),
    "user_management": ("User Management", "👥", "Accounts, roles and access - also inside the Admin Console."),
    "recycle_bin": ("Recycle Bin", "🗑️", "Restore or purge deleted papers - also inside the Admin Console."),
    "activity_timeline": ("Activity Timeline", "🕒", "The audit log as a readable timeline."),
}

SIDEBAR_STYLE = """
<style>
.shell-card {
    border:1px solid #E4E7EC; border-radius:10px; padding:12px 14px;
    background: linear-gradient(180deg, #FFFFFF 0%, #F7F9FC 100%); margin-bottom:10px;
}
.shell-badge {
    display:inline-block; padding:2px 9px; border-radius:999px;
    background:#EEF2FF; color:#3538CD; font-size:0.72rem; font-weight:600;
}
.shell-mail { color:#98A2B3; font-size:0.75rem; }
</style>
"""


def load_styles():
    st.markdown(SIDEBAR_STYLE, unsafe_allow_html=True)
    if os.path.exists(STYLESHEET):
        with open(STYLESHEET, encoding="utf-8") as handle:
            st.markdown(f"<style>{handle.read()}</style>", unsafe_allow_html=True)


def init_session_state():
    st.session_state.setdefault("logged_in_user", None)
    st.session_state.setdefault("login_attempts", {})
    st.session_state.setdefault("notifications_outbox", [])
    st.session_state.setdefault("remember_me", False)


def role_of(user):
    return user.get("role") or au.default_role(user.get("designation", ""))


# --------------------------------------------------------------------------
# PAGES
# --------------------------------------------------------------------------
def render_placeholder(module_name):
    title, _, purpose = CATALOGUE[module_name]
    st.markdown(f"#### {title}")
    st.caption(purpose)
    st.info(
        f"This screen is not built yet. Add a `render()` function to "
        f"`views/{module_name}.py` and it will appear here automatically."
    )


def module_page(module_name):
    """Wrap views/<module_name>.py so the router can call it like any other page."""

    def page():
        module = importlib.import_module(module_name)
        renderer = getattr(module, "render", None)
        if renderer:
            renderer()
        else:
            render_placeholder(module_name)

    page.__name__ = module_name
    return page


def catalogue_page(module_name, default=False):
    title, icon, _ = CATALOGUE[module_name]
    return st.Page(module_page(module_name), title=title, icon=icon, url_path=module_name, default=default)


def script_page(path, title, icon, url_path, default=False):
    return st.Page(path, title=title, icon=icon, url_path=url_path, default=default)


def guest_navigation():
    return {
        "Welcome": [catalogue_page("landing", default=True), catalogue_page("browse_search")],
        "Account": [
            script_page(REGISTER_PAGE, "Register", "📝", "register"),
            script_page(LOGIN_PAGE, "Login", "🔐", "login"),
        ],
    }


def navigation_for(user):
    """Menu for the signed-in user, chosen by role."""
    role = role_of(user)
    library = [catalogue_page("browse_search"), catalogue_page("paper_detail")]
    account = [script_page(PROFILE_PAGE, "My Profile", "👤", "profile")]

    if role == "Admin":
        return {
            "Console": [script_page(ADMIN_PAGE, "Admin Console", "🛠️", "admin", default=True)],
            "Library": library,
            "Standalone screens": [
                catalogue_page("user_management"),
                catalogue_page("reports"),
                catalogue_page("recycle_bin"),
                catalogue_page("activity_timeline"),
            ],
            "Account": account,
        }

    if role == "Guide":
        return {
            "Review": [catalogue_page("guide_review", default=True), catalogue_page("reports")],
            "Library": library,
            "Account": account,
        }

    return {
        "Research": [
            catalogue_page("researcher_dashboard", default=True),
            catalogue_page("submit_paper"),
            catalogue_page("my_papers"),
        ],
        "Library": library,
        "Account": account,
    }


# --------------------------------------------------------------------------
# SHELL
# --------------------------------------------------------------------------
def render_sidebar(user):
    with st.sidebar:
        if not user:
            st.caption("👋 Browsing as a guest — register or sign in to submit papers.")
            return
        st.markdown(
            f"<div class='shell-card'><b>{user['full_name']}</b><br>"
            f"<span class='shell-badge'>{role_of(user)}</span> "
            f"<span class='shell-badge'>{user['department']}</span><br>"
            f"<span class='shell-mail'>{user['email']}</span></div>",
            unsafe_allow_html=True,
        )
        if st.button("🚪 Logout", width="stretch"):
            st.session_state.logged_in_user = None
            st.rerun()


def main():
    st.set_page_config(page_title=PAGE_TITLE, page_icon=PAGE_ICON, layout="wide")
    load_styles()
    init_session_state()

    user = st.session_state.logged_in_user
    navigation = st.navigation(navigation_for(user) if user else guest_navigation())
    render_sidebar(user)
    navigation.run()


main()
 