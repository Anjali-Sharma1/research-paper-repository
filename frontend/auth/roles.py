"""
auth/roles.py
Thin wrapper — kept for backward compatibility with any existing imports.
Core role logic now lives in services/auth_service.py.
Module 2.
"""
import streamlit as st
from services.auth_service import require_role   # re-export


def is_logged_in() -> bool:
    return st.session_state.get("is_logged_in", False)


def current_role() -> str:
    return st.session_state.get("user_role", "")


def current_user_id() -> int | None:
    return st.session_state.get("user_id")
