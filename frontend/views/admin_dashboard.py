# Admin home - total papers, department-wise stats and pending approvals count.
"""
admin_dashboard.py - Admin console for the Research Paper Repository.

Modules: Overview, Paper Management, Approval Queue, User Management, Reports,
Recycle Bin, Activity Log, Notifications and Settings.

Users come from auth_utils.py; papers, approvals, audit entries and
notifications come from repo_store.py.
"""

import os
import sys
from datetime import date, datetime

import altair as alt
import pandas as pd
import streamlit as st

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import auth_utils as au
import repo_store as store

PAGE_TITLE = "Research Repository — Admin"
PAGE_ICON = "🛠️"
LOGIN_PAGE = "views/pages/login.py"
PROFILE_PAGE = "views/pages/profile.py"

ADMIN_ROLE = "Admin"
CURRENT_YEAR = date.today().year
PAPER_COLUMNS = ["paper_id", "title", "authors", "department", "publication_type", "year", "status", "citations"]
STATUS_COLORS = {"Approved": "#12B76A", "Pending": "#F79009", "Rejected": "#F04438"}
ACCENT = "#3538CD"

PAGE_STYLE = """
<style>
:root { --ink:#1D2939; --ink-strong:#101828; --ink-muted:#667085; }
.stApp { background-color:#FFFFFF; color:var(--ink); }
.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6 { color:var(--ink-strong); }
.stApp p, .stApp li, .stApp label, .stApp th, .stApp td, .stApp code { color:var(--ink); }
.stApp [data-testid="stMetricValue"] { color:var(--ink-strong); }
.stApp [data-testid="stMetricLabel"], .stApp [data-testid="stCaptionContainer"] { color:var(--ink-muted); }
.stApp .page-title { margin-bottom:0; color:var(--ink-strong); }
.stApp .page-sub { color:var(--ink-muted); margin-top:2px; }
.stApp .side-card {
    border:1px solid #E4E7EC; border-radius:10px; padding:12px 14px;
    background: linear-gradient(180deg, #FFFFFF 0%, #F7F9FC 100%); margin-bottom:10px;
    color:var(--ink);
}
.stApp .badge {
    display:inline-block; padding:2px 9px; border-radius:999px;
    background:#EEF2FF; color:#3538CD; font-size:0.72rem; font-weight:600;
}
.stApp .timeline-item {
    border-left:2px solid #E4E7EC; padding:2px 0 10px 12px; margin-left:4px; color:var(--ink);
}
.stApp .timeline-time { color:var(--ink-muted); font-size:0.75rem; }
</style>
"""


# --------------------------------------------------------------------------
# SHARED HELPERS
# --------------------------------------------------------------------------
def require_admin():
    """Only a signed-in Admin may see this console."""
    user = st.session_state.get("logged_in_user")
    if not user:
        st.warning("Please sign in to open the admin console.")
        if st.button("Go to login →"):
            st.switch_page(LOGIN_PAGE)
        st.stop()

    if role_of(user) != ADMIN_ROLE:
        st.error("🔒 Admin access only. Your account does not have administrator rights.")
        if st.button("← Back to profile"):
            st.switch_page(PROFILE_PAGE)
        st.stop()
    return user


def role_of(user):
    return user.get("role") or au.default_role(user.get("designation", ""))


def header(title, subtitle):
    st.markdown(f"#### {title}")
    st.caption(subtitle)


def format_timestamp(value):
    try:
        return datetime.fromisoformat(str(value)).strftime("%d %b %Y, %I:%M %p")
    except ValueError:
        return str(value) or "—"


def option_index(options, value):
    return options.index(value) if value in options else 0


def to_csv(frame):
    return frame.to_csv(index=False).encode("utf-8")


def total(series):
    """Sum a numeric column and hand back a plain int."""
    return int(pd.Series(series).to_numpy().sum())


def year_bounds(papers):
    years = pd.Series(papers["year"]).to_numpy()
    return int(years.min()), int(years.max())


def load_user_frame() -> pd.DataFrame:
    users = pd.DataFrame(au.load_users())
    if users.empty:
        return pd.DataFrame(columns=au.FIELDNAMES)
    users["is_active"] = pd.Series(pd.to_numeric(users["is_active"], errors="coerce")).fillna(1).astype(int)
    users["role"] = users["role"].fillna("").replace("", "Researcher")
    return users


def count_by(frame, column) -> pd.DataFrame:
    counts = pd.Series(frame[column]).astype(str).replace("", "Unspecified").value_counts().reset_index()
    counts.columns = [column, "count"]
    return counts.sort_values(column)


def bar_chart(frame, column, title, color=ACCENT):
    return (
        alt.Chart(frame, title=title)
        .mark_bar(color=color, cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X(f"{column}:N", title="", sort=None),
            y=alt.Y("count:Q", title="Papers"),
            tooltip=[column, "count"],
        )
        .properties(height=270)
    )


def status_donut(papers):
    counts = count_by(papers, "status")
    return (
        alt.Chart(counts, title="Approval status")
        .mark_arc(innerRadius=62)
        .encode(
            theta=alt.Theta("count:Q"),
            color=alt.Color(
                "status:N",
                title="",
                scale=alt.Scale(domain=list(STATUS_COLORS), range=list(STATUS_COLORS.values())),
            ),
            tooltip=["status", "count"],
        )
        .properties(height=270)
    )


def render_timeline(entries):
    if entries.empty:
        st.caption("Nothing recorded yet.")
        return
    for entry in entries.to_dict("records"):
        target = f" · <code>{entry['target']}</code>" if entry["target"] else ""
        details = f"<br>{entry['details']}" if entry["details"] else ""
        st.markdown(
            f"<div class='timeline-item'><b>{entry['action']}</b>{target}"
            f"<div class='timeline-time'>{format_timestamp(entry['timestamp'])} · {entry['actor']}</div>"
            f"{details}</div>",
            unsafe_allow_html=True,
        )


# --------------------------------------------------------------------------
# MODULE 1 - OVERVIEW
# --------------------------------------------------------------------------
def render_overview(admin):
    header("Overview", "A live snapshot of everything in the repository.")

    papers = store.load_papers()
    users = load_user_frame()
    counts = papers["status"].value_counts().to_dict()

    cells = st.columns(5)
    cells[0].metric("Total papers", len(papers))
    cells[1].metric("Approved", int(counts.get("Approved", 0)))
    cells[2].metric("Pending approval", int(counts.get("Pending", 0)))
    cells[3].metric("Registered users", len(users))
    cells[4].metric("Total citations", total(papers["citations"]))

    if papers.empty:
        st.info("No papers yet. Add one from the Paper Management module.")
        return

    left, right = st.columns(2)
    left.altair_chart(bar_chart(count_by(papers, "year"), "year", "Publications per year"))
    right.altair_chart(bar_chart(count_by(papers, "department"), "department", "Papers by department"))

    left, right = st.columns(2)
    left.altair_chart(status_donut(papers))
    right.altair_chart(
        bar_chart(count_by(papers, "publication_type"), "publication_type", "Publication type", "#7A5AF8")
    )

    left, right = st.columns([3, 2])
    with left:
        st.markdown("**Latest submissions**")
        latest = papers.sort_values(by="submitted_on", ascending=False).head(6)
        st.dataframe(latest[["paper_id", "title", "department", "status"]], hide_index=True)
    with right:
        st.markdown("**Recent activity**")
        render_timeline(store.load_audit_log().head(5))


# --------------------------------------------------------------------------
# MODULE 2 - PAPER MANAGEMENT
# --------------------------------------------------------------------------
def paper_inputs(key_prefix, paper=None):
    paper = paper or {}
    left, right = st.columns(2)
    title = left.text_input("Title *", value=paper.get("title", ""), key=f"{key_prefix}_title") or ""
    authors = right.text_input(
        "Author(s) *", value=paper.get("authors", ""), placeholder="Separate names with ;",
        key=f"{key_prefix}_authors",
    ) or ""

    left, middle, right = st.columns(3)
    department = left.selectbox(
        "Department", au.DEPARTMENTS, index=option_index(au.DEPARTMENTS, paper.get("department")),
        key=f"{key_prefix}_department",
    )
    publication_type = middle.selectbox(
        "Publication type", store.PUBLICATION_TYPES,
        index=option_index(store.PUBLICATION_TYPES, paper.get("publication_type")),
        key=f"{key_prefix}_type",
    )
    year = right.number_input(
        "Year", min_value=1990, max_value=CURRENT_YEAR + 1,
        value=int(paper.get("year") or CURRENT_YEAR), step=1, key=f"{key_prefix}_year",
    )

    left, right = st.columns(2)
    journal = left.text_input(
        "Journal / Conference", value=paper.get("journal", ""), key=f"{key_prefix}_journal",
    ) or ""
    doi = right.text_input("DOI", value=paper.get("doi", ""), key=f"{key_prefix}_doi") or ""

    left, middle, right = st.columns(3)
    indexing = left.selectbox(
        "Indexing", store.INDEXING_TYPES, index=option_index(store.INDEXING_TYPES, paper.get("indexing")),
        key=f"{key_prefix}_indexing",
    )
    status = middle.selectbox(
        "Status", store.STATUSES, index=option_index(store.STATUSES, paper.get("status")),
        key=f"{key_prefix}_status",
    )
    citations = right.number_input(
        "Citations", min_value=0, value=int(paper.get("citations") or 0), step=1, key=f"{key_prefix}_citations",
    )

    keywords = st.text_input("Keywords", value=paper.get("keywords", ""), key=f"{key_prefix}_keywords") or ""
    abstract = st.text_area(
        "Abstract", value=paper.get("abstract", ""), height=110, key=f"{key_prefix}_abstract",
    ) or ""

    return {
        "title": title.strip(),
        "authors": authors.strip(),
        "department": department,
        "publication_type": publication_type,
        "journal": journal.strip(),
        "year": int(year),
        "doi": doi.strip(),
        "indexing": indexing,
        "status": status,
        "citations": int(citations),
        "keywords": keywords.strip(),
        "abstract": abstract.strip(),
    }


def paper_errors(values):
    errors = []
    if len(values["title"]) < 5:
        errors.append("Title must be at least 5 characters.")
    if not values["authors"]:
        errors.append("At least one author is required.")
    return errors


def render_add_paper(admin):
    with st.form("add_paper", clear_on_submit=True):
        values = paper_inputs("new")
        upload = st.file_uploader("Paper file (PDF)", type=["pdf"], key="new_file")
        submitted = st.form_submit_button("Add paper", type="primary")

    if not submitted:
        return
    errors = paper_errors(values)
    if errors:
        for error in errors:
            st.error(error)
        return

    if upload:
        values["file_name"] = store.save_upload(upload)
    values["submitted_by"] = admin["email"]
    paper_id = store.add_paper(values, admin["email"])
    st.success(f"✅ Added {paper_id}.")
    st.rerun()


def filter_papers(papers, query, department, status, publication_type, years):
    result = papers
    if query:
        haystack = pd.Series(
            result["title"] + " " + result["authors"] + " " + result["journal"]
            + " " + result["doi"] + " " + result["keywords"]
        ).str.lower()
        result = result.loc[haystack.str.contains(query.strip().lower(), regex=False)]
    if department != "All":
        result = result.loc[result["department"] == department]
    if status != "All":
        result = result.loc[result["status"] == status]
    if publication_type != "All":
        result = result.loc[result["publication_type"] == publication_type]
    if years:
        result = result.loc[result["year"].between(*years)]
    return result.reset_index(drop=True)


def paper_filter_controls(papers, key_prefix):
    top = st.columns([3, 1, 1, 1])
    query = top[0].text_input("Search title, author, journal or DOI", key=f"{key_prefix}_query")
    department = top[1].selectbox("Department", ["All"] + au.DEPARTMENTS, key=f"{key_prefix}_dept")
    status = top[2].selectbox("Status", ["All"] + store.STATUSES, key=f"{key_prefix}_status")
    publication_type = top[3].selectbox("Type", ["All"] + store.PUBLICATION_TYPES, key=f"{key_prefix}_type")

    low, high = year_bounds(papers)
    years = None
    if low < high:
        years = st.slider("Year range", low, high, (low, high), key=f"{key_prefix}_years")
    return filter_papers(papers, query, department, status, publication_type, years)


def paper_labels(papers):
    return {f"{row['paper_id']} — {row['title']}": row["paper_id"] for row in papers.to_dict("records")}


def render_paper_editor(papers, admin):
    labels = paper_labels(papers)
    selected = st.selectbox("Select a paper to edit", list(labels), key="edit_choice")
    paper = store.get_paper(labels[selected])
    if not paper:
        return

    with st.form("edit_paper"):
        values = paper_inputs(f"edit_{paper['paper_id']}", paper)
        replacement = st.file_uploader("Replace file (PDF)", type=["pdf"], key=f"edit_file_{paper['paper_id']}")
        saved = st.form_submit_button("Save changes", type="primary")

    if saved:
        errors = paper_errors(values)
        if errors:
            for error in errors:
                st.error(error)
        else:
            if replacement:
                values["file_name"] = store.save_upload(replacement)
            store.update_paper(paper["paper_id"], values, admin["email"])
            st.success("Changes saved.")
            st.rerun()

    if paper["file_name"]:
        st.caption(f"📎 Attached file: {paper['file_name']}")
    if st.button("🗑️ Move to recycle bin", key=f"delete_{paper['paper_id']}"):
        store.set_paper_deleted(paper["paper_id"], True, admin["email"])
        st.warning(f"{paper['paper_id']} moved to the recycle bin.")
        st.rerun()


def render_papers(admin):
    header("Paper management", "Add, search, edit and remove submissions.")

    with st.expander("➕ Add a new paper"):
        render_add_paper(admin)

    papers = store.load_papers()
    if papers.empty:
        st.info("The repository is empty.")
        return

    filtered = paper_filter_controls(papers, "papers")
    st.caption(f"Showing {len(filtered)} of {len(papers)} papers")
    st.dataframe(filtered[PAPER_COLUMNS], hide_index=True)
    st.download_button("⬇️ Download list (CSV)", to_csv(filtered), "papers.csv", "text/csv")

    if filtered.empty:
        return
    st.divider()
    render_paper_editor(filtered, admin)


# --------------------------------------------------------------------------
# MODULE 3 - APPROVAL QUEUE
# --------------------------------------------------------------------------
def render_approval_card(paper, admin):
    paper_id = paper["paper_id"]
    with st.expander(f"{paper_id} — {paper['title']}"):
        left, right = st.columns(2)
        left.markdown(
            f"**Authors:** {paper['authors']}  \n**Department:** {paper['department']}"
            f"  \n**Year:** {paper['year']}"
        )
        right.markdown(
            f"**Type:** {paper['publication_type']}  \n**Journal:** {paper['journal'] or '—'}"
            f"  \n**DOI:** {paper['doi'] or '—'}"
        )
        if paper["abstract"]:
            st.caption(paper["abstract"])

        remark = st.text_area("Reviewer remark", key=f"remark_{paper_id}", height=80) or ""
        approve, reject = st.columns(2)
        if approve.button("✅ Approve", key=f"approve_{paper_id}", type="primary", width="stretch"):
            store.decide_paper(paper_id, "Approved", remark.strip(), admin["email"])
            st.rerun()
        if reject.button("❌ Reject", key=f"reject_{paper_id}", width="stretch"):
            if not remark.strip():
                st.error("A remark is required when rejecting a paper.")
            else:
                store.decide_paper(paper_id, "Rejected", remark.strip(), admin["email"])
                st.rerun()


def render_approvals(admin):
    header("Approval queue", "Approve or reject submissions waiting for review.")

    papers = store.load_papers()
    pending = papers.loc[papers["status"] == "Pending"]

    cells = st.columns(3)
    cells[0].metric("Awaiting review", len(pending))
    cells[1].metric("Approved so far", total(papers["status"] == "Approved"))
    cells[2].metric("Rejected so far", total(papers["status"] == "Rejected"))

    if pending.empty:
        st.success("🎉 The queue is clear — nothing is waiting for review.")
    for paper in pending.to_dict("records"):
        render_approval_card(paper, admin)

    st.divider()
    st.markdown("**Recent decisions**")
    decisions = store.load_approvals().head(10)
    if decisions.empty:
        st.caption("No decisions recorded yet.")
    else:
        st.dataframe(decisions, hide_index=True)


# --------------------------------------------------------------------------
# MODULE 4 - USER MANAGEMENT
# --------------------------------------------------------------------------
def render_user_editor(users, admin):
    labels = {f"{row['full_name']} ({row['email']})": row["email"] for row in users.to_dict("records")}
    selected = st.selectbox("Select an account", list(labels), key="user_choice")
    email = labels[selected]
    user = au.find_user_by_email(email)
    if not user:
        return

    is_self = email.lower() == admin["email"].lower()
    if is_self:
        st.caption("ℹ️ This is your own account — role and status changes are disabled.")

    # Widget keys carry the email so switching accounts reloads that account's values.
    with st.form("edit_user"):
        left, middle, right = st.columns(3)
        role = left.selectbox(
            "Role", au.ROLES, index=option_index(au.ROLES, role_of(user)), disabled=is_self,
            key=f"user_role_{email}",
        )
        department = middle.selectbox(
            "Department", au.DEPARTMENTS, index=option_index(au.DEPARTMENTS, user["department"]),
            key=f"user_dept_{email}",
        )
        designation = right.selectbox(
            "Designation", au.DESIGNATIONS, index=option_index(au.DESIGNATIONS, user["designation"]),
            key=f"user_designation_{email}",
        )
        active = st.checkbox(
            "Account active", value=user["is_active"] == "1", disabled=is_self, key=f"user_active_{email}",
        )
        saved = st.form_submit_button("Save account", type="primary")

    if saved:
        au.update_user(email, {
            "role": role_of(user) if is_self else role,
            "department": department,
            "designation": designation,
            "is_active": user["is_active"] if is_self else str(int(active)),
        })
        store.log_action(admin["email"], "Updated user", email, f"role={role}, active={active}")
        st.success("Account updated.")
        st.rerun()

    left, right = st.columns(2)
    with left:
        temporary = st.text_input("Temporary password", type="password", key=f"user_password_{email}")
        if st.button("🔑 Reset password", key=f"user_reset_{email}", width="stretch"):
            policy_error = au.validate_password_policy(temporary)
            if policy_error:
                st.error(policy_error)
            else:
                au.set_user_password(email, temporary)
                store.log_action(admin["email"], "Reset password", email)
                st.success("Password reset. Share it with the user over a secure channel.")
    with right:
        confirm = st.checkbox("I understand this cannot be undone", key=f"user_delete_confirm_{email}")
        if st.button("🗑️ Delete account", key=f"user_delete_{email}", disabled=is_self or not confirm, width="stretch"):
            au.delete_user(email)
            store.log_action(admin["email"], "Deleted user", email)
            st.warning(f"Deleted {email}.")
            st.rerun()


def render_users(admin):
    header("User management", "Roles, departments and account access.")

    users = load_user_frame()
    if users.empty:
        st.info("No accounts registered yet.")
        return

    cells = st.columns(4)
    cells[0].metric("Accounts", len(users))
    cells[1].metric("Admins", total(users["role"] == "Admin"))
    cells[2].metric("Guides", total(users["role"] == "Guide"))
    cells[3].metric("Deactivated", total(users["is_active"] == 0))

    top = st.columns([3, 1, 1])
    query = top[0].text_input("Search name, email or employee ID", key="user_query")
    role = top[1].selectbox("Role", ["All"] + au.ROLES, key="user_role_filter")
    department = top[2].selectbox("Department", ["All"] + au.DEPARTMENTS, key="user_dept_filter")

    filtered = users
    if query:
        haystack = pd.Series(
            filtered["full_name"] + " " + filtered["email"] + " " + filtered["employee_id"]
        ).str.lower()
        filtered = filtered.loc[haystack.str.contains(query.strip().lower(), regex=False)]
    if role != "All":
        filtered = filtered.loc[filtered["role"] == role]
    if department != "All":
        filtered = filtered.loc[filtered["department"] == department]
    filtered = filtered.reset_index(drop=True)

    visible = ["full_name", "email", "employee_id", "department", "designation", "role", "is_active", "created_on"]
    st.caption(f"Showing {len(filtered)} of {len(users)} accounts")
    st.dataframe(filtered[visible], hide_index=True)
    st.download_button("⬇️ Download users (CSV)", to_csv(filtered[visible]), "users.csv", "text/csv")

    if filtered.empty:
        return
    st.divider()
    render_user_editor(filtered, admin)


# --------------------------------------------------------------------------
# MODULE 5 - REPORTS
# --------------------------------------------------------------------------
def render_reports(admin):
    header("Reports", "NAAC / NBA style publication summaries.")

    papers = store.load_papers()
    if papers.empty:
        st.info("No data available to report on.")
        return

    low, high = year_bounds(papers)
    years = st.slider("Assessment period", low, high, (low, high), key="report_years") if low < high else (low, high)

    left, middle, right = st.columns(3)
    departments = left.multiselect("Departments", au.DEPARTMENTS, key="report_depts")
    statuses = middle.multiselect("Status", store.STATUSES, default=["Approved"], key="report_status")
    types = right.multiselect("Publication type", store.PUBLICATION_TYPES, key="report_types")

    report = papers.loc[papers["year"].between(*years)]
    if departments:
        report = report.loc[report["department"].isin(departments)]
    if statuses:
        report = report.loc[report["status"].isin(statuses)]
    if types:
        report = report.loc[report["publication_type"].isin(types)]

    if report.empty:
        st.warning("No papers match the selected filters.")
        return

    cells = st.columns(4)
    cells[0].metric("Publications", len(report))
    citations = total(report["citations"])
    cells[1].metric("Departments covered", int(report["department"].nunique()))
    cells[2].metric("Total citations", citations)
    cells[3].metric("Avg citations / paper", round(citations / len(report), 1))

    st.markdown("**Department-wise publications per year**")
    matrix = pd.pivot_table(
        pd.DataFrame(report), index="department", columns="year", values="paper_id", aggfunc="count",
        fill_value=0, margins=True, margins_name="Total",
    )
    matrix.columns = [str(column) for column in matrix.columns]
    st.dataframe(matrix)

    left, right = st.columns(2)
    with left:
        st.markdown("**By publication type**")
        st.dataframe(count_by(report, "publication_type"), hide_index=True)
    with right:
        st.markdown("**By indexing**")
        st.dataframe(count_by(report, "indexing"), hide_index=True)

    st.markdown("**Detailed publication list**")
    detailed = report[PAPER_COLUMNS + ["journal", "doi", "indexing"]]
    st.dataframe(detailed, hide_index=True)

    period = f"{years[0]}-{years[1]}"
    left, right = st.columns(2)
    left.download_button(
        "⬇️ Detailed report (CSV)", to_csv(detailed), f"publications_{period}.csv", "text/csv", width="stretch",
    )
    right.download_button(
        "⬇️ Summary matrix (CSV)", matrix.to_csv().encode("utf-8"), f"summary_{period}.csv", "text/csv",
        width="stretch",
    )


# --------------------------------------------------------------------------
# MODULE 6 - RECYCLE BIN
# --------------------------------------------------------------------------
def render_recycle_bin(admin):
    header("Recycle bin", "Restore removed papers or delete them permanently.")

    everything = store.load_papers(include_deleted=True)
    deleted = everything.loc[everything["is_deleted"] == 1].reset_index(drop=True)
    if deleted.empty:
        st.success("The recycle bin is empty.")
        return

    st.dataframe(deleted[PAPER_COLUMNS], hide_index=True)

    labels = paper_labels(deleted)
    selected = st.selectbox("Select a paper", list(labels), key="bin_choice")
    paper_id = labels[selected]

    left, right = st.columns(2)
    if left.button("♻️ Restore", key=f"bin_restore_{paper_id}", type="primary", width="stretch"):
        store.set_paper_deleted(paper_id, False, admin["email"])
        st.success(f"{paper_id} restored.")
        st.rerun()
    confirm = right.checkbox("Confirm permanent delete", key=f"bin_confirm_{paper_id}")
    if right.button("🔥 Delete forever", key=f"bin_purge_{paper_id}", disabled=not confirm, width="stretch"):
        store.purge_paper(paper_id, admin["email"])
        st.warning(f"{paper_id} permanently deleted.")
        st.rerun()


# --------------------------------------------------------------------------
# MODULE 7 - ACTIVITY LOG
# --------------------------------------------------------------------------
def render_activity_log(admin):
    header("Activity log", "Every action recorded against the repository.")

    log = store.load_audit_log()
    if log.empty:
        st.info("No activity recorded yet.")
        return

    left, middle, right = st.columns([1, 2, 1])
    actor = left.selectbox("Actor", ["All"] + sorted(log["actor"].unique()), key="log_actor")
    query = middle.text_input("Search action or target", key="log_query")
    limit = right.number_input("Entries to show", min_value=10, max_value=500, value=50, step=10, key="log_limit")

    filtered = log
    if actor != "All":
        filtered = filtered.loc[filtered["actor"] == actor]
    if query:
        haystack = pd.Series(
            filtered["action"] + " " + filtered["target"] + " " + filtered["details"]
        ).str.lower()
        filtered = filtered.loc[haystack.str.contains(query.strip().lower(), regex=False)]

    st.caption(f"{len(filtered)} matching entries")
    render_timeline(filtered.head(int(limit)))
    st.download_button("⬇️ Download log (CSV)", to_csv(filtered), "activity_log.csv", "text/csv")


# --------------------------------------------------------------------------
# MODULE 8 - NOTIFICATIONS
# --------------------------------------------------------------------------
def render_notifications(admin):
    header("Notifications", "Send announcements to researchers and guides.")

    users = load_user_frame()
    audience = st.radio("Audience", store.AUDIENCES, horizontal=True, key="notify_audience")

    target = ""
    if audience == "Department":
        target = st.selectbox("Department", au.DEPARTMENTS, key="notify_dept")
    elif audience == "Single user":
        emails = users["email"].tolist()
        target = st.selectbox("User", emails, key="notify_user") if emails else ""

    with st.form("send_notification", clear_on_submit=True):
        title = st.text_input("Title")
        message = st.text_area("Message", height=120)
        sent = st.form_submit_button("📨 Send notification", type="primary")

    if sent:
        if not title.strip() or not message.strip():
            st.error("Both a title and a message are required.")
        else:
            store.add_notification(audience, target, title.strip(), message.strip(), admin["email"])
            st.success("Notification sent.")
            st.rerun()

    st.divider()
    st.markdown("**Sent notifications**")
    notifications = store.load_notifications()
    if notifications.empty:
        st.caption("Nothing sent yet.")
        return
    for item in notifications.head(15).to_dict("records"):
        recipient = item["target"] or item["audience"]
        with st.expander(f"{item['title']} → {recipient}"):
            st.caption(f"{format_timestamp(item['created_on'])} · sent by {item['sent_by']}")
            st.write(item["message"])


# --------------------------------------------------------------------------
# MODULE 9 - SETTINGS
# --------------------------------------------------------------------------
def render_settings(admin):
    header("Settings", "Master lists, data exports and maintenance.")

    papers = store.load_papers(include_deleted=True)
    users = load_user_frame()

    cells = st.columns(3)
    cells[0].metric("Paper records", len(papers))
    cells[1].metric("User accounts", len(users))
    cells[2].metric("Log entries", len(store.load_audit_log()))

    st.markdown("**Master lists**")
    lists = {
        "Departments": au.DEPARTMENTS,
        "Designations": au.DESIGNATIONS,
        "Roles": au.ROLES,
        "Paper status": store.STATUSES,
        "Publication types": store.PUBLICATION_TYPES,
        "Indexing": store.INDEXING_TYPES,
    }
    for name, values in lists.items():
        st.markdown(
            f"{name}: " + " ".join(f"<span class='badge'>{value}</span>" for value in values),
            unsafe_allow_html=True,
        )

    st.divider()
    st.markdown("**Data export**")
    exports = {
        "papers.csv": store.load_papers(include_deleted=True),
        "approvals.csv": store.load_approvals(),
        "activity_log.csv": store.load_audit_log(),
        "notifications.csv": store.load_notifications(),
    }
    columns = st.columns(len(exports))
    for column, (name, frame) in zip(columns, exports.items()):
        column.download_button(f"⬇️ {name}", to_csv(frame), name, "text/csv", key=f"export_{name}", width="stretch")

    st.caption(f"Storage folder: `{store.DATA_DIR}`")

    st.divider()
    st.markdown("**Danger zone**")
    confirm = st.checkbox("I want to wipe all papers and reload the sample data", key="reset_confirm")
    if st.button("♻️ Reset repository data", disabled=not confirm, key="reset_button"):
        store.reset_repository(admin["email"])
        st.success("Repository reset to sample data.")
        st.rerun()


# --------------------------------------------------------------------------
# SHELL
# --------------------------------------------------------------------------
MODULES = {
    "📊 Overview": render_overview,
    "📄 Paper Management": render_papers,
    "✅ Approval Queue": render_approvals,
    "👥 User Management": render_users,
    "📈 Reports": render_reports,
    "🗑️ Recycle Bin": render_recycle_bin,
    "🕒 Activity Log": render_activity_log,
    "🔔 Notifications": render_notifications,
    "⚙️ Settings": render_settings,
}


def render_sidebar(admin):
    with st.sidebar:
        st.markdown(
            f"<div class='side-card'><b>{admin['full_name']}</b><br>"
            f"<span class='badge'>{role_of(admin)}</span> "
            f"<span class='badge'>{admin['department']}</span><br>"
            f"<span class='timeline-time'>{admin['email']}</span></div>",
            unsafe_allow_html=True,
        )
        module = st.radio("Module", list(MODULES), label_visibility="collapsed", key="admin_module")

        st.divider()
        papers = store.load_papers()
        st.metric("Pending approvals", total(papers["status"] == "Pending"))
    return module


def main():
    st.set_page_config(page_title=PAGE_TITLE, page_icon=PAGE_ICON, layout="wide")
    st.markdown(PAGE_STYLE, unsafe_allow_html=True)

    admin = require_admin()
    store.seed_demo_data()
    module = render_sidebar(admin)

    st.markdown(f"<h2 class='page-title'>{PAGE_ICON} Admin Console</h2>", unsafe_allow_html=True)
    st.markdown(
        "<p class='page-sub'>Research Paper Repository Management System</p>", unsafe_allow_html=True
    )
    st.divider()
    MODULES[module](admin)


render = main

if __name__ == "__main__":
    main()
