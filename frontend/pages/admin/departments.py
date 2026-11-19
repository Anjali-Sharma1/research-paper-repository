"""
pages/admin/departments.py
Module 3: Admin — department management UI.
Create / view / edit / safe-delete departments.
"""
import streamlit as st
from services.auth_service import require_role
from services.department_service import (
    get_all_departments, create_department,
    update_department, delete_department, can_delete_department
)
from services.user_service import log_action


def show():
    require_role("admin")
    admin_id = st.session_state["user_id"]
    st.title(":material/account_balance: Department Management")

    tab_list, tab_create = st.tabs(["All Departments", "Add Department"])

    # ── TAB 1: ALL DEPARTMENTS ────────────────────────────────────────────────
    with tab_list:
        depts = get_all_departments()
        if not depts:
            st.info("No departments yet. Add one using the tab above.")
        else:
            st.caption(f"{len(depts)} department(s)")

        for d in depts:
            can_del, reason = can_delete_department(d["dept_id"])
            del_icon = ":material/delete:" if can_del else ":material/lock:"
            label = (f"**{d['dept_code']}** — {d['dept_name']}  "
                     f"| :material/group: {d['user_count']} users  {del_icon}")

            with st.expander(label):
                st.caption(f"HoD: {d['hod_name'] or '—'}")
                if not can_del:
                    st.caption(f":material/lock: {reason}")

                with st.form(f"edit_dept_{d['dept_id']}"):
                    name = st.text_input("Department Name *",
                                        value=d["dept_name"])
                    code = st.text_input("Short Code *",
                                        value=d["dept_code"])
                    hod  = st.text_input("Head of Department",
                                        value=d["hod_name"] or "")

                    ca, cb = st.columns(2)
                    save_btn = ca.form_submit_button(":material/save: Update", type="primary")
                    del_btn  = cb.form_submit_button(":material/delete: Delete",
                                                     disabled=not can_del)

                if save_btn:
                    ok, msg = update_department(d["dept_id"], name, code, hod)
                    if ok:
                        log_action(admin_id, "edit_department",
                                   "department", d["dept_id"])
                        st.success(msg); st.rerun()
                    else:
                        st.error(msg)

                if del_btn:
                    ok, msg = delete_department(d["dept_id"])
                    if ok:
                        log_action(admin_id, "delete_department",
                                   "department", d["dept_id"])
                        st.success(msg); st.rerun()
                    else:
                        st.error(msg)

    # ── TAB 2: CREATE DEPARTMENT ──────────────────────────────────────────────
    with tab_create:
        st.subheader("Add New Department")

        with st.form("new_dept_form"):
            name = st.text_input(
                "Department Name *",
                placeholder="e.g. Master of Computer Applications")
            code = st.text_input(
                "Short Code *",
                placeholder="e.g. MCA")
            hod  = st.text_input("Head of Department (optional)")

            if st.form_submit_button("Create Department", type="primary",
                                     use_container_width=True):
                ok, msg = create_department(name, code, hod)
                if ok:
                    log_action(admin_id, "create_department", "department")
                    st.success(msg)
                else:
                    st.error(msg)
