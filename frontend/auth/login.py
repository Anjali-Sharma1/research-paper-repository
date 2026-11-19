from services.ui_theme_service import get_brand_logo_html
"""
auth/login.py
Login page UI styled matching the reference dashboard theme.
Delegates ALL auth logic to services/auth_service.py.
Also switches to the student registration form (auth/register.py).
"""
import streamlit as st
from services.auth_service import (
    authenticate_user, create_session,
    update_last_login, log_activity
)
from auth.register import render as render_register


def show():
    """Render the login page (or the student registration form)."""

    brand = st.session_state.get("brand_logo", "RPRMS")
    view = st.session_state.get("auth_view", "login")

    _, col, _ = st.columns([1, 1.8, 1])

    with col:
        st.markdown(f"""
        <div style="text-align: center; margin-bottom: 24px;">
            <div class="brand-logo-3d" style="display: inline-flex; align-items: center; justify-content: center; width: 104px; height: 104px; margin-bottom: 14px; filter: drop-shadow(0 14px 32px rgba(0, 82, 204, 0.36)) drop-shadow(0 4px 8px rgba(0, 0, 0, 0.16)); perspective: 800px;">
                {get_brand_logo_html(size=96, rounded='20px', border=False, bg='transparent')}
            </div>
            <h1 style="font-size: 32px; font-weight: 850; color: #0F172A; margin: 0; letter-spacing: -0.5px; text-shadow: 0 2px 4px rgba(0,0,0,0.06);">{brand}</h1>
            <p style="font-size: 14px; color: #64748B; margin-top: 4px; font-weight: 500;">Research Paper Repository Management System</p>
        </div>
        """, unsafe_allow_html=True)

        # ── Registration view ────────────────────────────────────────────────
        if view == "register":
            render_register()
            return

        # ── Login view ───────────────────────────────────────────────────────
        reg_msg = st.session_state.pop("reg_success", None)
        if reg_msg:
            st.success(reg_msg)

        with st.form("login_form"):
            st.markdown("<h4 style='font-size: 18px; font-weight: 700; color: #0F172A; margin-bottom: 16px;'>Sign In</h4>", unsafe_allow_html=True)
            email    = st.text_input("Email Address", placeholder="Enter your email address")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submitted = st.form_submit_button(
                "Sign In to Account", type="primary", use_container_width=True)

        if submitted:
            ok, error_msg, user = authenticate_user(email, password)

            if not ok:
                st.error(error_msg)
                return

            create_session(user)
            update_last_login(user["user_id"])
            log_activity(user["user_id"], "login")

            st.success(f"Welcome back, {user['full_name']}!")
            st.rerun()

        st.markdown(
            "<p style='text-align:center;font-size:13px;color:#64748B;margin:14px 0 6px;'>"
            "New student?</p>", unsafe_allow_html=True)
        if st.button("Create a Student Account", use_container_width=True,
                     key="go_register"):
            st.session_state["auth_view"] = "register"
            st.rerun()
