# Login screen - takes email and password and stores the returned token.
"""
pages/login.py  —  STEP 2 of the flow (register.py -> login.py -> profile.py)

Registered by app.py, which is the entry point of the whole frontend.
A successful sign-in only stores the user and reruns - app.py then rebuilds
the menu for that role and lands on the right home screen.

Fields: Full Name, Email, Password.
"""

import os
import sys
import time
from datetime import datetime, timedelta

import streamlit as st

# Make sure auth_utils.py (in the project root, one level up from pages/)
# is importable regardless of the working directory Streamlit was launched from.
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
import auth_utils as au

st.set_page_config(page_title="Research Repository — Login", page_icon="🔐", layout="centered")

st.markdown(
    """
    <style>
    .stApp { background-color: #FFFFFF; }
    .auth-header { text-align:center; margin-bottom: 4px; }
    .auth-sub { text-align:center; color:#667085; margin-bottom: 22px; }
    </style>
    """,
    unsafe_allow_html=True,
)

MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_MINUTES = 3

if "login_attempts" not in st.session_state:
    st.session_state.login_attempts = {}          # email -> {"count": int, "locked_until": datetime|None}
if "logged_in_user" not in st.session_state:
    st.session_state.logged_in_user = None
if "remember_me" not in st.session_state:
    st.session_state.remember_me = False
if "notifications_outbox" not in st.session_state:
    st.session_state.notifications_outbox = []


def send_simulated_email(to, subject, body):
    st.session_state.notifications_outbox.insert(0, {
        "timestamp": datetime.now(), "to": to, "subject": subject, "body": body,
    })


def is_locked_out(email):
    entry = st.session_state.login_attempts.get(email)
    if not entry or not entry.get("locked_until"):
        return False, None
    if datetime.now() < entry["locked_until"]:
        return True, entry["locked_until"] - datetime.now()
    st.session_state.login_attempts[email] = {"count": 0, "locked_until": None}
    return False, None


def register_failed_attempt(email):
    entry = st.session_state.login_attempts.setdefault(email, {"count": 0, "locked_until": None})
    entry["count"] += 1
    if entry["count"] >= MAX_LOGIN_ATTEMPTS:
        entry["locked_until"] = datetime.now() + timedelta(minutes=LOCKOUT_MINUTES)


def reset_attempts(email):
    st.session_state.login_attempts[email] = {"count": 0, "locked_until": None}


# --------------------------------------------------------------------------
# If already logged in, skip straight to profile
# --------------------------------------------------------------------------
if st.session_state.logged_in_user:
    st.success(f"Already signed in as {st.session_state.logged_in_user['full_name']}.")
    st.stop()

st.markdown("<h2 class='auth-header'>🔐 Sign in</h2>", unsafe_allow_html=True)
st.markdown("<p class='auth-sub'>Step 2 of 3 — Access the centralized research paper repository.</p>",
            unsafe_allow_html=True)

if st.session_state.get("just_registered_email"):
    st.success(f"Account created for **{st.session_state['just_registered_email']}** — please sign in below.")
    st.session_state["just_registered_email"] = None

with st.form("login_form"):
    full_name = st.text_input("Full Name", placeholder="e.g. Dr. Ravi Kumar")
    email = st.text_input("Email", placeholder="e.g. ravi.kumar@college.edu.in")
    password = st.text_input("Password", type="password")
    remember = st.checkbox("Remember me on this device")
    submitted = st.form_submit_button("Login", use_container_width=True)

with st.expander("Forgot password?"):
    reset_email = st.text_input("Enter your registered email", key="reset_email")
    if st.button("Send reset instructions"):
        if reset_email and au.find_user_by_email(reset_email):
            send_simulated_email(
                reset_email, "Password reset requested",
                "We received a request to reset your password. In production this email would "
                "contain a secure, time-limited reset link.",
            )
        st.success("If an account exists for that email, reset instructions have been sent.")

if submitted:
    if not full_name.strip() or not email.strip() or not password:
        st.error("Please fill in Full Name, Email, and Password.")
    else:
        email_clean = email.strip().lower()
        locked, remaining = is_locked_out(email_clean)
        if locked and remaining:
            mins = int(remaining.total_seconds() // 60) + 1
            st.error(f"🔒 Too many failed attempts. Please try again in about {mins} minute(s).")
        else:
            user = au.find_user_by_email(email_clean)
            if not user:
                register_failed_attempt(email_clean)
                st.error("No account found for that email. Please register first.")
            elif user.get("is_active", "1") != "1":
                st.error("This account has been deactivated. Please contact the administrator.")
            elif user["full_name"].strip().lower() != full_name.strip().lower():
                register_failed_attempt(email_clean)
                st.error("The name entered does not match our records for this email.")
            elif not au.verify_password(password, user["salt"], user["password_hash"]):
                register_failed_attempt(email_clean)
                remaining_attempts = MAX_LOGIN_ATTEMPTS - st.session_state.login_attempts[email_clean]["count"]
                if remaining_attempts > 0:
                    st.error(f"Incorrect password. {remaining_attempts} attempt(s) remaining before lockout.")
                else:
                    st.error(f"🔒 Account temporarily locked for {LOCKOUT_MINUTES} minutes.")
            else:
                reset_attempts(email_clean)
                st.session_state.logged_in_user = user
                st.session_state.remember_me = remember
                st.success(f"Welcome back, {user['full_name']}!")
                time.sleep(0.6)
                st.rerun()

st.divider()
st.caption("Don't have an account yet?")
if st.button("← Back to Register", use_container_width=True):
    st.switch_page("views/register.py")