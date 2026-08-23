# Lets the logged-in user update their own details and change password.
"""
pages/profile.py  —  STEP 3 of the flow (register.py -> login.py -> profile.py)

Shows the signed-in user's profile. Guards itself: if nobody is logged in
(e.g. someone jumps here directly via the sidebar), it bounces back to login.
"""

import os
import sys

import streamlit as st

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
import auth_utils as au  # noqa: F401  (kept for future use, e.g. profile edits)

st.set_page_config(page_title="Research Repository — Profile", page_icon="✅", layout="centered")

st.markdown(
    """
    <style>
    .stApp { background-color: #FFFFFF; }
    .auth-header { text-align:center; margin-bottom: 4px; }
    .profile-card {
        border:1px solid #E4E7EC; border-radius:12px; padding:22px 26px;
        background: linear-gradient(180deg, #FFFFFF 0%, #F7F9FC 100%);
    }
    .badge {
        display:inline-block; padding:3px 10px; border-radius:999px;
        background:#EEF2FF; color:#3538CD; font-size:0.78rem; font-weight:600;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --------------------------------------------------------------------------
# GUARD: must be logged in to view this page
# --------------------------------------------------------------------------
if "logged_in_user" not in st.session_state or not st.session_state.logged_in_user:
    st.warning("Please log in to view your profile.")
    st.switch_page("views/pages/login.py")

user = st.session_state.logged_in_user

st.markdown("<h2 class='auth-header'>✅ You're signed in</h2>", unsafe_allow_html=True)
st.caption("Step 3 of 3 — Profile")

st.markdown(
    f"""
    <div class="profile-card">
        <h3 style="margin-bottom:4px;">{user['full_name']}</h3>
        <span class="badge">{user['designation']}</span>
        <span class="badge">{user['department']}</span>
        <p style="margin-top:14px;color:#475467;">
            📧 {user['email']}<br>
            🆔 {user['employee_id']}<br>
            🗓️ Registered on {user['created_on'][:10]}
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

if st.session_state.get("remember_me"):
    st.caption("🔁 This device will be remembered for future visits (demo only — session-based).")

st.write("")

role = user.get("role") or au.default_role(user.get("designation", ""))
if role == "Admin":
    if st.button("🛠️ Open Admin Console", type="primary", use_container_width=True):
        st.switch_page("views/pages/admin_console.py")
else:
    st.info(
        "Your researcher workspace (Submit Paper, My Papers, Search) loads from here. "
        "Administrator accounts also see the Admin Console."
    )

if st.button("🚪 Logout", use_container_width=True):
    st.session_state.logged_in_user = None
    st.rerun()

with st.expander("📧 Simulated email outbox (for this demo)"):
    outbox = st.session_state.get("notifications_outbox", [])
    if not outbox:
        st.caption("No emails sent yet.")
    for n in outbox[:20]:
        st.markdown(f"**To:** {n['to']}  ·  **Subject:** {n['subject']}")
        st.caption(n["timestamp"].strftime("%d %b %Y, %I:%M %p"))
        st.write(n["body"])
        st.divider()