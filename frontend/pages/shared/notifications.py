"""
pages/shared/notifications.py
Module 11: Notification inbox for all roles.
Mark read/all-read, delete, clear read.
"""
import streamlit as st
from services.notification_service import (
    get_notifications, get_unread_count,
    mark_read, mark_all_read,
    delete_notification, delete_all_read
)


def show():
    if not st.session_state.get("is_logged_in"):
        st.error("Please log in."); return

    user_id = st.session_state["user_id"]
    st.title(":material/notifications: Notifications")
    st.divider()

    notifs = get_notifications(user_id)
    unread = [n for n in notifs if not n["is_read"]]
    read   = [n for n in notifs if n["is_read"]]

    # ── Summary + action buttons ──────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total",   len(notifs))
    c2.metric(":material/info: Unread", len(unread))
    c3.metric(":material/check_circle: Read",   len(read))

    with c4:
        if unread:
            if st.button("Mark all as read", use_container_width=True):
                mark_all_read(user_id); st.rerun()
        if read:
            if st.button("Clear read", use_container_width=True):
                delete_all_read(user_id); st.rerun()

    st.divider()

    if not notifs:
        st.info("No notifications yet. "
                "You will be notified when papers are approved, "
                "rejected or changes are requested.")
        return

    # ── Notification list ─────────────────────────────────────────────────────
    for n in notifs:
        icon = ":material/info:" if not n["is_read"] else "⚪"
        bg   = "border" if not n["is_read"] else None

        with st.container(border=not n["is_read"]):
            col_msg, col_time, col_act = st.columns([5, 1, 1])

            col_msg.write(f"{icon}  {n['message']}")
            col_time.caption(str(n["created_at"])[:16])

            with col_act:
                if not n["is_read"]:
                    if st.button(":material/check: Read",
                                 key=f"rd_{n['notif_id']}",
                                 use_container_width=True):
                        mark_read(n["notif_id"], user_id)
                        st.rerun()
                if st.button(":material/delete:",
                             key=f"del_{n['notif_id']}",
                             use_container_width=True):
                    delete_notification(n["notif_id"], user_id)
                    st.rerun()
