# Registration screen - collects name, email, password and department.
"""
register.py  —  STEP 1 of the flow (register.py -> pages/login.py -> pages/profile.py)
Reached from app.py (the entry point):  streamlit run app.py

app.py registers this screen and resolves every st.switch_page() path
relative to itself, which is why the paths below start with views/.

Fields: Full Name, Institutional Email ID, Employee ID / Roll Number,
Department, Designation, Password, Confirm Password.
"""

import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime

import streamlit as st

# Keep auth_utils.py importable no matter which working directory Streamlit was
# launched from (pages/login.py and pages/profile.py do the same thing).
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import auth_utils as au

# --------------------------------------------------------------------------
# CONSTANTS
# --------------------------------------------------------------------------
PAGE_TITLE = "Research Repository — Register"
PAGE_ICON = "📝"
LOGIN_PAGE = "views/pages/login.py"

# Short pause after "account created", so the message is readable before we move on.
REDIRECT_DELAY_SECONDS = 1

# au.password_strength() scores a password from 0 to 4 - one icon per score.
MAX_STRENGTH_SCORE = 4
STRENGTH_ICONS = {0: "🔴", 1: "🟠", 2: "🟡", 3: "🟢", 4: "✅"}

POLICY_LABEL = "I agree to the Institution's Data Privacy & Acceptable Use Policy *"

PAGE_STYLE = """
<style>
.stApp { background-color: #FFFFFF; }
.auth-header { text-align:center; margin-bottom: 4px; }
.auth-sub { text-align:center; color:#667085; margin-bottom: 22px; }
.strength-label { font-size:0.82rem; font-weight:600; }
.field-hint { color:#98A2B3; font-size:0.78rem; margin-top:-8px; }
</style>
"""


@dataclass
class RegistrationForm:
    """Exactly what the user typed - raw and untrimmed. Cleaning happens later,
    in build_user_row(), so validation always sees the original input."""

    full_name: str
    email: str
    employee_id: str
    department: str
    designation: str
    password: str
    confirm_password: str
    accepted_policy: bool


# --------------------------------------------------------------------------
# SESSION STATE + NOTIFICATIONS
# --------------------------------------------------------------------------
def init_session_state():
    if "notifications_outbox" not in st.session_state:
        st.session_state.notifications_outbox = []


def send_simulated_email(to, subject, body):
    """Stand-in for a real SMTP/email-API call. Replace with smtplib or a
    provider (SendGrid, SES, etc.) for production account-verification mail."""
    st.session_state.notifications_outbox.insert(0, {
        "timestamp": datetime.now(), "to": to, "subject": subject, "body": body,
    })


# --------------------------------------------------------------------------
# PAGE RENDERING
# --------------------------------------------------------------------------
def render_header():
    st.markdown("<h2 class='auth-header'>📝 Create your account</h2>", unsafe_allow_html=True)
    st.markdown(
        "<p class='auth-sub'>Step 1 of 3 — Register with your institutional details.</p>",
        unsafe_allow_html=True,
    )


def render_form():
    """Draw every input and return what the user typed.

    These fields deliberately sit outside st.form(): a form only reruns the
    script on submit, so the live password-strength meter and the live e-mail /
    confirm-password hints below would never update while typing.
    """
    full_name = st.text_input("Full Name *", placeholder="e.g. Dr. Ravi Kumar", key="reg_full_name")

    email = st.text_input(
        "Institutional Email ID *", placeholder="e.g. ravi.kumar@college.edu.in", key="reg_email",
    )
    render_email_hint(email)

    left, right = st.columns(2)
    with left:
        employee_id = st.text_input(
            "Employee ID / Roll Number *", placeholder="e.g. EMP-2026-014", key="reg_employee_id",
        )
        department = st.selectbox("Department *", au.DEPARTMENTS, key="reg_department")
    with right:
        designation = st.selectbox("Designation *", au.DESIGNATIONS, key="reg_designation")
        st.markdown(
            "<div class='field-hint'>Choose Student if registering as a research scholar/UG/PG student.</div>",
            unsafe_allow_html=True,
        )

    password = st.text_input(
        "Password *", type="password", key="reg_password",
        help="At least 8 characters, with an uppercase letter, a number and a special character.",
    )
    render_password_strength(password)

    confirm_password = st.text_input("Confirm Password *", type="password", key="reg_confirm_password")
    render_password_match_hint(password, confirm_password)

    accepted_policy = st.checkbox(POLICY_LABEL, key="reg_agree")

    return RegistrationForm(
        full_name=full_name,
        email=email,
        employee_id=employee_id,
        department=department,
        designation=designation,
        password=password,
        confirm_password=confirm_password,
        accepted_policy=accepted_policy,
    )


def render_email_hint(email):
    """Nudge - not a blocker - when the address is valid but looks personal."""
    if not email:
        return
    message, format_ok = au.validate_email(email)
    if message and format_ok:
        st.caption("ℹ️ " + message)


def render_password_strength(password):
    if not password:
        return
    score, label, unmet = au.password_strength(password)
    st.progress(score / MAX_STRENGTH_SCORE)
    st.markdown(
        f"<span class='strength-label'>{STRENGTH_ICONS[score]} Strength: {label}</span>",
        unsafe_allow_html=True,
    )
    if unmet:
        st.caption("Still needed: " + "; ".join(unmet))


def render_password_match_hint(password, confirm_password):
    if confirm_password and password != confirm_password:
        st.caption("⚠️ Passwords do not match yet.")


def render_footer():
    st.divider()
    st.caption("Already have an account?")
    if st.button("Go to Login →", use_container_width=True):
        st.switch_page(LOGIN_PAGE)


# --------------------------------------------------------------------------
# VALIDATION
# --------------------------------------------------------------------------
def collect_errors(form):
    """Check every field and return all problems at once, so the user can fix
    them in one pass instead of meeting a new error on each submit."""
    errors = []

    name_error = au.validate_full_name(form.full_name)
    if name_error:
        errors.append(name_error)

    # A valid-but-personal address only earns a hint, so it is reported here
    # only when the format itself is wrong.
    email_error, email_format_ok = au.validate_email(form.email)
    if email_error and not email_format_ok:
        errors.append(email_error)

    employee_id_error = au.validate_employee_id(form.employee_id)
    if employee_id_error:
        errors.append(employee_id_error)

    errors.extend(password_errors(form.password, form.confirm_password))

    if not form.accepted_policy:
        errors.append("You must accept the Data Privacy & Acceptable Use Policy to register.")

    # Uniqueness is checked last, and only for values that parsed correctly -
    # looking up a malformed email or ID in the store would be pointless.
    if email_format_ok and au.find_user_by_email(form.email):
        errors.append("An account with this email already exists. Please log in instead.")
    if not employee_id_error and au.find_user_by_employee_id(form.employee_id):
        errors.append("This Employee ID / Roll Number is already registered.")

    return errors


def password_errors(password, confirm_password):
    """Present -> matching -> strong enough. Each check assumes the previous one
    passed, so only the first real problem is reported."""
    if not password or not confirm_password:
        return ["Password and Confirm Password are required."]
    if password != confirm_password:
        return ["Password and Confirm Password do not match."]

    policy_error = au.validate_password_policy(password)
    return [policy_error] if policy_error else []


# --------------------------------------------------------------------------
# ACCOUNT CREATION
# --------------------------------------------------------------------------
def build_user_row(form):
    """Turn the form into the CSV row shape auth_utils.save_user() expects.
    Email is lower-cased here because every lookup compares it that way."""
    salt, password_hash = au.hash_password(form.password)
    return {
        "full_name": form.full_name.strip(),
        "email": form.email.strip().lower(),
        "employee_id": form.employee_id.strip(),
        "department": form.department,
        "designation": form.designation,
        "salt": salt,
        "password_hash": password_hash,
        "created_on": datetime.now().isoformat(timespec="seconds"),
        "is_active": "1",
    }


def create_account(form):
    """Persist the new user and queue their welcome mail. Returns the saved row."""
    user = build_user_row(form)
    au.save_user(user)
    send_simulated_email(
        user["email"],
        "Welcome — verify your account",
        f"Hi {user['full_name']}, your account has been created for {user['department']} "
        f"({user['designation']}). You can now sign in with your registered email.",
    )
    return user


def handle_submit(form):
    errors = collect_errors(form)
    if errors:
        for error in errors:
            st.error(error)
        return

    user = create_account(form)
    st.success("✅ Account created successfully!")
    st.balloons()

    # pages/login.py reads this to greet the new user on arrival.
    st.session_state["just_registered_email"] = user["email"]
    time.sleep(REDIRECT_DELAY_SECONDS)
    st.switch_page(LOGIN_PAGE)


# --------------------------------------------------------------------------
# ENTRY POINT
# --------------------------------------------------------------------------
def main():
    # set_page_config() must run before any other Streamlit call.
    st.set_page_config(page_title=PAGE_TITLE, page_icon=PAGE_ICON, layout="centered")
    st.markdown(PAGE_STYLE, unsafe_allow_html=True)
    init_session_state()

    render_header()
    form = render_form()

    if st.button("Create Account", type="primary", use_container_width=True):
        handle_submit(form)

    render_footer()


main()
