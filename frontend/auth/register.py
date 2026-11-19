"""
auth/register.py
Student registration form. Drawn inside the login page (see auth/login.py).
Only creates accounts with the "student" role.
"""
import streamlit as st
from services.registration_service import register_student
from services.department_service import get_all_departments_simple
from services.auth_service import log_activity


def render():
    """Draw the registration form. Call inside a Streamlit column."""
    depts = get_all_departments_simple()
    dept_map = {"— Select department —": None}
    dept_map.update({d["dept_name"]: d["dept_id"] for d in depts})

    with st.form("register_form"):
        st.markdown(
            "<h4 style='font-size:18px;font-weight:700;color:#0F172A;"
            "margin-bottom:4px;'>Student Registration</h4>"
            "<p style='font-size:13px;color:#64748B;margin-bottom:12px;'>"
            "Create a student account to search and bookmark papers.</p>",
            unsafe_allow_html=True,
        )
        full_name = st.text_input("Full Name *", placeholder="Enter your full name")
        email = st.text_input("Email Address *", placeholder="Enter your email address")
        dept_label = st.selectbox("Department", list(dept_map.keys()))
        phone = st.text_input("Phone (optional)", placeholder="Enter your phone number")
        password = st.text_input("Password * (min 6 characters)", type="password",
                                 placeholder="Create a password")
        confirm = st.text_input("Confirm Password *", type="password",
                                placeholder="Re-enter your password")
        submitted = st.form_submit_button(
            "Create Student Account", type="primary", use_container_width=True)

    if submitted:
        ok, msg, new_id = register_student(
            full_name, email, password, confirm,
            dept_id=dept_map[dept_label], phone=phone,
        )
        if not ok:
            st.error(msg)
        else:
            log_activity(new_id, "student_registered", "user", new_id)
            st.session_state["auth_view"] = "login"
            st.session_state["reg_success"] = msg
            st.rerun()

    if st.button("← Back to Sign In", use_container_width=True, key="back_to_login"):
        st.session_state["auth_view"] = "login"
        st.rerun()
