# Public home page shown before login - explains what the system does, shows total published papers and gives Login / Register / Browse buttons.
"""
landing.py - the public home page of the Research Paper Repository.

app.py registers this module as the default screen for a guest, so it is the
first thing a visitor sees. It introduces every module of the system, shows
live counts read from repo_store.py, lets anyone search the published papers
without signing in, and points to Register / Login / Browse.

No st.set_page_config() here - app.py owns the page shell and the sidebar.
"""

import os
import sys

import altair as alt
import pandas as pd
import streamlit as st

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import auth_utils as au
import repo_store as store

# Script pages can be opened with st.switch_page(); the catalogue screens in
# app.py are function pages, so they are reached by their url_path instead.
REGISTER_PAGE = "views/register.py"
LOGIN_PAGE = "views/pages/login.py"
PROFILE_PAGE = "views/pages/profile.py"
BROWSE_URL = "/browse_search"

ACCENT = "#3538CD"
PUBLISHED = "Approved"
PREVIEW_ROWS = 5

PAGE_STYLE = """
<style>
.home-hero {
    border:1px solid #E4E7EC; border-radius:16px; padding:30px 34px; margin-bottom:18px;
    background: linear-gradient(135deg, #F5F6FF 0%, #FFFFFF 55%, #F7F9FC 100%);
}
.home-eyebrow { color:#3538CD; font-size:0.78rem; font-weight:700; letter-spacing:0.08em; }
.home-title { font-size:2.1rem; font-weight:700; margin:6px 0 4px; color:#101828; }
.home-tagline { color:#475467; font-size:1.02rem; max-width:760px; margin-bottom:0; }
.home-card {
    border:1px solid #E4E7EC; border-radius:12px; padding:16px 18px; height:200px;
    background: linear-gradient(180deg, #FFFFFF 0%, #F7F9FC 100%); margin-bottom:12px;
}
.home-card-icon { font-size:1.5rem; }
.home-card-title { font-weight:650; color:#101828; margin:6px 0 4px; }
.home-card-text { color:#475467; font-size:0.86rem; margin:0 0 10px; }
.home-step { border-left:3px solid #3538CD; padding:2px 0 12px 14px; margin:0 0 6px 4px; }
.home-step-title { font-weight:650; color:#101828; }
.home-step-text { color:#475467; font-size:0.86rem; }
.badge {
    display:inline-block; padding:2px 9px; border-radius:999px;
    background:#EEF2FF; color:#3538CD; font-size:0.72rem; font-weight:600;
}
.home-foot { color:#98A2B3; font-size:0.78rem; text-align:center; padding-top:6px; }
</style>
"""

# Every screen the system offers, in the order a new user meets them.
MODULES = [
    ("&#128269;", "Browse & Search", "Full-text search over titles, authors and keywords, with filters "
     "for department, year, publication type and indexing.", "Open to all"),
    ("&#128196;", "Paper Details", "One full record: abstract, PDF download, DOI, a QR code for the "
     "paper and its live citation count.", "Open to all"),
    ("&#128228;", "Submit Paper", "Upload the PDF and fill in the publication metadata; possible "
     "duplicates are flagged before a reviewer sees it.", "Researcher"),
    ("&#128193;", "My Papers", "Your own submissions with their status, edit access and soft delete.",
     "Researcher"),
    ("&#128202;", "My Dashboard", "Your paper counts, what is still awaiting approval and your recent "
     "activity.", "Researcher"),
    ("&#9989;", "Review Queue", "Guides approve or reject the papers assigned to them and leave a "
     "remark for the author.", "Guide"),
    ("&#128200;", "Reports", "NAAC / NBA publication reports for any period, downloadable as PDF or "
     "Excel.", "Guide &middot; Admin"),
    ("&#128101;", "User Management", "Accounts, roles and department access - activate, deactivate or "
     "reset an account.", "Admin"),
    ("&#128276;", "Notifications", "Announcements to everyone, to one department or to a single user.",
     "Admin"),
    ("&#128465;", "Recycle Bin", "Deleted papers are kept, so anything removed by mistake can be "
     "restored.", "Admin"),
    ("&#128336;", "Activity Timeline", "The audit trail - who added, edited, approved or deleted what, "
     "and when.", "Admin"),
    ("&#128736;", "Admin Console", "All nine admin modules in one place, with charts covering the whole "
     "repository.", "Admin"),
]

WORKFLOW = [
    ("1 - Register", "Sign up with your institutional email, employee or roll ID and department. Your "
     "designation decides whether you start as a Researcher or a Guide."),
    ("2 - Submit", "Upload the paper with its journal, year, DOI and indexing details. It is saved as "
     "Pending and shows up in your My Papers list straight away."),
    ("3 - Review", "A guide opens the review queue, reads the record and approves or rejects it with a "
     "remark. Every decision is written to the audit trail."),
    ("4 - Publish", "Approved papers become searchable to everyone, each with a QR code, a citation "
     "count and a downloadable PDF."),
    ("5 - Report", "The department pulls NAAC / NBA ready reports for any year range - no manual "
     "spreadsheet work."),
]

ROLE_MATRIX = [
    ("Search and read published papers", "Yes", "Yes", "Yes"),
    ("Submit and edit own papers", "Yes", "-", "Yes"),
    ("Approve or reject papers", "-", "Yes", "Yes"),
    ("NAAC / NBA reports", "-", "Yes", "Yes"),
    ("Manage users and roles", "-", "-", "Yes"),
    ("Recycle bin and audit log", "-", "-", "Yes"),
]


# --------------------------------------------------------------------------
# HELPERS
# --------------------------------------------------------------------------
def total(series):
    """Sum a numeric column and hand back a plain int."""
    return int(pd.Series(series).to_numpy().sum())


def published_papers(papers) -> pd.DataFrame:
    return pd.DataFrame(papers.loc[papers["status"] == PUBLISHED]).reset_index(drop=True)


def module_card(icon, title, text, tag):
    return (
        f"<div class='home-card'><div class='home-card-icon'>{icon}</div>"
        f"<div class='home-card-title'>{title}</div>"
        f"<p class='home-card-text'>{text}</p>"
        f"<span class='badge'>{tag}</span></div>"
    )


def bar_chart(frame, column, title, color=ACCENT):
    return (
        alt.Chart(frame, title=title)
        .mark_bar(color=color, cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
        .encode(
            x=alt.X(f"{column}:N", title="", sort=None),
            y=alt.Y("count:Q", title="Papers"),
            tooltip=[column, "count"],
        )
        .properties(height=230)
    )


def count_by(frame, column) -> pd.DataFrame:
    counts = pd.Series(frame[column]).astype(str).replace("", "Unspecified").value_counts().reset_index()
    counts.columns = [column, "count"]
    return counts.sort_values(column)


def matches(papers, query) -> pd.DataFrame:
    """Case-insensitive search across the fields a visitor would type into."""
    if papers.empty:
        return papers
    columns = ["title", "authors", "keywords", "journal", "department"]
    haystack = papers[columns].astype(str).agg(" ".join, axis=1).str.lower()
    return pd.DataFrame(papers.loc[haystack.str.contains(query.strip().lower(), regex=False)])


# --------------------------------------------------------------------------
# SECTIONS
# --------------------------------------------------------------------------
def render_hero(user):
    st.markdown(
        "<div class='home-hero'>"
        "<div class='home-eyebrow'>RESEARCH PAPER REPOSITORY MANAGEMENT SYSTEM</div>"
        "<div class='home-title'>&#128218; One home for every paper the institute publishes</div>"
        "<p class='home-tagline'>Submit once, get it reviewed by a guide, and let it stay searchable "
        "for good - with PDFs, DOIs, QR codes, citation counts and NAAC / NBA reports built in. "
        "Anyone may search the published work; an account is needed only to submit or review.</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    if user:
        st.success(f"You are signed in as **{user['full_name']}** — your workspace is in the sidebar.")
        if st.button("👤 Go to my profile", type="primary"):
            st.switch_page(PROFILE_PAGE)
        return

    left, middle, right = st.columns(3)
    if left.button("📝 Create an account", type="primary", width="stretch"):
        st.switch_page(REGISTER_PAGE)
    if middle.button("🔐 Sign in", width="stretch"):
        st.switch_page(LOGIN_PAGE)
    right.link_button("🔍 Browse the repository", BROWSE_URL, width="stretch")


def render_stats(papers, live):
    st.markdown("#### The repository right now")
    st.caption("These counts change the moment a paper is submitted or approved.")

    cells = st.columns(5)
    cells[0].metric("Published papers", len(live))
    cells[1].metric("Total submissions", len(papers))
    cells[2].metric("Awaiting review", total(papers["status"] == "Pending"))
    cells[3].metric("Departments", int(pd.Series(live["department"]).nunique()) if len(live) else 0)
    cells[4].metric("Citations recorded", total(live["citations"]))


def render_quick_search(live):
    st.markdown("#### Try the search without signing in")
    if live.empty:
        st.caption("The search lights up as soon as the first paper is published.")
        return

    query = st.text_input(
        "Search published papers",
        placeholder="e.g. federated learning, solar, R. Kumar, CSE",
        key="landing_search",
    )
    if not query.strip():
        st.caption("Type a title, an author, a keyword or a department to see how the search behaves.")
        return

    found = matches(live, query)
    if found.empty:
        st.warning(f"No published paper matches '{query}'. Try a broader word.")
        return

    st.success(f"{len(found)} published paper(s) match '{query}' — showing the first {PREVIEW_ROWS}.")
    st.dataframe(
        found.sort_values(by="year", ascending=False)
        .head(PREVIEW_ROWS)[["paper_id", "title", "authors", "department", "year", "citations"]],
        hide_index=True,
        width="stretch",
    )
    st.caption("Open **Browse & Search** for filters, paging and the full record of each paper.")


def render_modules():
    st.markdown("#### What the system does")
    st.caption("Every screen below is part of the system - which ones you can open depends on your role.")

    for start in range(0, len(MODULES), 3):
        for column, module in zip(st.columns(3), MODULES[start:start + 3]):
            column.markdown(module_card(*module), unsafe_allow_html=True)


def render_workflow():
    st.markdown("#### How a paper travels through the system")
    for title, text in WORKFLOW:
        st.markdown(
            f"<div class='home-step'><div class='home-step-title'>{title}</div>"
            f"<div class='home-step-text'>{text}</div></div>",
            unsafe_allow_html=True,
        )


def render_roles():
    st.markdown("#### Who can do what")
    st.caption("Your role comes from your designation at registration; an admin can change it later.")

    matrix = pd.DataFrame(ROLE_MATRIX, columns=["Capability", "Researcher", "Guide", "Admin"])
    st.dataframe(matrix, hide_index=True, width="stretch")


def render_charts(live):
    if live.empty:
        return
    st.markdown("#### Published work at a glance")
    left, right = st.columns(2)
    left.altair_chart(bar_chart(count_by(live, "year"), "year", "Publications per year"))
    right.altair_chart(
        bar_chart(count_by(live, "department"), "department", "Papers by department", "#7A5AF8")
    )


def render_latest(live):
    if live.empty:
        st.info("No papers have been published yet. Register and submit the first one.")
        return
    st.markdown("#### Recently published")
    latest = live.sort_values(by="submitted_on", ascending=False).head(PREVIEW_ROWS)
    st.dataframe(
        latest[["paper_id", "title", "authors", "journal", "year", "citations"]],
        hide_index=True,
        width="stretch",
    )


def render_footer(user):
    st.divider()
    if not user:
        left, right = st.columns(2)
        if left.button("📝 Register and submit your first paper", type="primary", width="stretch"):
            st.switch_page(REGISTER_PAGE)
        if right.button("🔐 I already have an account", width="stretch"):
            st.switch_page(LOGIN_PAGE)
    st.markdown(
        f"<p class='home-foot'>Research Paper Repository Management System &middot; "
        f"{len(au.load_users())} registered member(s) &middot; demo data lives in CSV files under "
        f"views/data/</p>",
        unsafe_allow_html=True,
    )


# --------------------------------------------------------------------------
# ENTRY POINT (called by app.py)
# --------------------------------------------------------------------------
def render():
    st.markdown(PAGE_STYLE, unsafe_allow_html=True)
    store.seed_demo_data()

    user = st.session_state.get("logged_in_user")
    papers = store.load_papers()
    live = published_papers(papers)

    render_hero(user)
    st.divider()
    render_stats(papers, live)
    st.divider()
    render_quick_search(live)
    st.divider()
    render_modules()
    st.divider()
    render_workflow()
    st.divider()
    render_roles()
    st.divider()
    render_charts(live)
    render_latest(live)
    render_footer(user)


if __name__ == "__main__":
    render()
