"""
pages/admin/activity_logs.py
Module 11: Admin — searchable activity log viewer with summary stats.
"""
import streamlit as st
from services.auth_service import require_role
from services.notification_service import get_logs, get_log_summary

ACTION_ICONS = {
    "login":            ":material/vpn_key:",
    "logout":           ":material/logout:",
    "upload_paper":     ":material/upload_file:",
    "approve_paper":    ":material/check_circle:",
    "reject_paper":     ":material/cancel:",
    "request_changes":  ":material/info:",
    "upload_new_version":":material/sync:",
    "download_paper":   ":material/download:",
    "create_user":      ":material/person:",
    "edit_user":        "✏",
    "deactivate_user":  ":material/cancel:",
    "activate_user":    ":material/check_circle:",
    "reset_password":   ":material/vpn_key:",
    "create_department":":material/account_balance:",
    "edit_department":  "✏",
    "update_profile":   ":material/person:",
    "change_password":  ":material/vpn_key:",
}


def show():
    require_role("admin")
    st.title(":material/history_edu: Activity Logs")
    st.divider()

    # ── Summary KPIs ──────────────────────────────────────────────────────────
    summary = get_log_summary()
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Actions",    summary["total_actions"])
    c2.metric(":material/vpn_key: Logins",        summary["total_logins"])
    c3.metric(":material/upload_file: Uploads",       summary["total_uploads"])
    c4.metric(":material/check_circle: Approvals",     summary["total_approvals"])
    c5.metric(":material/download: Downloads",     summary["total_downloads"])
    st.divider()

    # ── Filters ───────────────────────────────────────────────────────────────
    col_s, col_l = st.columns([3, 1])
    action_filter = col_s.text_input(
        "Filter by action or user",
        placeholder="e.g. upload_paper, login, approve...",
        label_visibility="collapsed")
    limit = col_l.selectbox("Show", [50, 100, 200, 500],
                             label_visibility="collapsed")

    logs = get_logs(limit=limit, action_filter=action_filter)

    st.caption(f"Showing {len(logs)} entries")
    st.divider()

    if not logs:
        st.info("No activity recorded yet.")
        return

    for l in logs:
        icon   = ACTION_ICONS.get(l["action"], ":material/chevron_right:")
        action = (l["action"] or "").replace("_", " ").title()
        user   = l["user_name"] or "System"
        role   = l["role"]   or "—"
        when   = str(l["created_at"])[:16]

        entity_info = ""
        if l["entity"] and l["entity_id"]:
            entity_info = f"  |  {l['entity']} #{l['entity_id']}"
        elif l["entity"]:
            entity_info = f"  |  {l['entity']}"

        st.caption(
            f"`{when}`  {icon}  **{action}**  "
            f"|  {user} [{role}]{entity_info}"
        )
