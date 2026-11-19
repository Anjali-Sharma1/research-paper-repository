"""
pages/admin/user_management.py
Module 3: Admin — full user management UI.
Create / view / edit / deactivate / role-change / reset password.
"""
import streamlit as st
from services.auth_service import require_role
from services.user_service import (
    get_all_users, get_user, create_user,
    update_user, toggle_active, admin_reset_password, log_action
)
from services.department_service import get_all_departments_simple

ROLES = ["admin", "faculty", "student"]
STATUS_ICON = {1: ":material/check_circle:", 0: ":material/cancel:"}


def _dept_map():
    depts = get_all_departments_simple()
    return {"— None —": None} | {d["dept_name"]: d["dept_id"] for d in depts}


def show():
    require_role("admin")
    admin_id = st.session_state["user_id"]
    st.title(":material/group: User Management")

    tab_all, tab_create = st.tabs(["All Users", "Create New User"])

    # ── TAB 1: ALL USERS ──────────────────────────────────────────────────────
    with tab_all:
        users = get_all_users()

        c1, c2 = st.columns([3, 1])
        search = c1.text_input("Search", placeholder="Name or email...",
                               label_visibility="collapsed")
        role_f = c2.selectbox("Role filter",
                              ["All", "admin", "faculty", "student"],
                              label_visibility="collapsed")

        if search.strip():
            s = search.strip().lower()
            users = [u for u in users
                     if s in u["full_name"].lower()
                     or s in u["email"].lower()]
        if role_f != "All":
            users = [u for u in users if u["role"] == role_f]

        st.caption(f"Showing {len(users)} user(s)")

        if not users:
            st.info("No users found.")

        for u in users:
            icon  = ":material/check_circle:" if u["is_active"] else ":material/cancel:"
            label = f"{icon} {u['full_name']}  —  {u['email']}  [{u['role'].title()}]"

            with st.expander(label):
                c1, c2, c3 = st.columns(3)
                c1.write(f"**Dept:** {u['dept_name'] or '—'}")
                c2.write(f"**Joined:** {str(u['created_at'])[:10]}")
                c3.write(f"**Last login:** {str(u['last_login'])[:10] if u['last_login'] else 'Never'}")

                dm = _dept_map()
                cur_dept = u["dept_name"] if u["dept_name"] in dm else "— None —"

                with st.form(f"edit_user_{u['user_id']}"):
                    st.markdown("**Edit User Details**")
                    new_name  = st.text_input("Full Name",  value=u["full_name"])
                    new_role  = st.selectbox("Role", ROLES, index=ROLES.index(u["role"]))
                    new_dept  = st.selectbox("Department", list(dm.keys()),
                                            index=list(dm.keys()).index(cur_dept))
                    new_phone = st.text_input("Phone", value=u.get("phone") or "")
                    new_pw    = st.text_input("Reset Password (blank = no change)",
                                             type="password")

                    ca, cb, cc = st.columns(3)
                    save   = ca.form_submit_button(":material/save: Save",  type="primary")
                    toggle = cb.form_submit_button(
                        ":material/cancel: Deactivate" if u["is_active"] else ":material/check_circle: Activate")
                    reset  = cc.form_submit_button(":material/vpn_key: Reset PW")

                if save:
                    ok, msg = update_user(u["user_id"], new_name, new_role,
                                         dm[new_dept], new_phone)
                    if ok:
                        log_action(admin_id, "edit_user", "user", u["user_id"])
                        st.success(msg); st.rerun()
                    else:
                        st.error(msg)

                if toggle:
                    ok, msg = toggle_active(u["user_id"])
                    if ok:
                        action = "deactivate_user" if u["is_active"] else "activate_user"
                        log_action(admin_id, action, "user", u["user_id"])
                        st.success(msg); st.rerun()
                    else:
                        st.error(msg)

                if reset:
                    if not new_pw.strip():
                        st.error("Enter a new password first.")
                    else:
                        ok, msg = admin_reset_password(u["user_id"], new_pw)
                        if ok:
                            log_action(admin_id, "reset_password", "user", u["user_id"])
                            st.success(msg)
                        else:
                            st.error(msg)

    # ── TAB 2: CREATE USER ────────────────────────────────────────────────────
    with tab_create:
        st.subheader("Create New User")
        dm = _dept_map()

        with st.form("create_user_form"):
            full_name = st.text_input("Full Name *")
            email     = st.text_input("Email Address *")
            password  = st.text_input("Password * (min 6 chars)", type="password")
            role      = st.selectbox("Role *", ROLES)
            dept      = st.selectbox("Department", list(dm.keys()))
            phone     = st.text_input("Phone (optional)")

            if st.form_submit_button("Create User", type="primary",
                                     use_container_width=True):
                ok, msg = create_user(full_name, email, password, role,
                                      dm[dept], phone, admin_id)
                if ok:
                    log_action(admin_id, "create_user", "user")
                    st.success(msg)
                else:
                    st.error(msg)
