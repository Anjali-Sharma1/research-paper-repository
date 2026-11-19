"""
auth/logout.py
Logout — clears session and logs the action.
Module 2 — Member 1.
"""
import streamlit as st
from services.auth_service import clear_session, log_activity


def logout():
    """Log the logout action then wipe all session keys."""
    user_id = st.session_state.get("user_id")
    if user_id:
        log_activity(user_id, "logout")
    clear_session()
    st.rerun()
