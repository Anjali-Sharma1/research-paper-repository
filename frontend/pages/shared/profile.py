"""
pages/shared/profile.py
Module 3: All roles — view own profile, manage avatar/photo, edit name/phone,
change password, customize settings & theme, and view departments list.
"""
import os
import streamlit as st
from services.auth_service import require_role
from services.user_service import (
    get_user, update_own_profile, change_own_password, log_action
)
from services.department_service import get_all_departments
from services.ui_theme_service import get_user_avatar_html, THEMES


def show():
    if not st.session_state.get("is_logged_in"):
        st.error("Please log in.")
        return

    user_id = st.session_state["user_id"]
    role    = st.session_state["user_role"]
    user    = get_user(user_id)
    if not user:
        st.error("User not found.")
        return

    st.title(":material/person: My Profile")

    avatar_dir = os.path.join("uploads", "avatars")
    avatar_path = os.path.join(avatar_dir, f"avatar_{user_id}.png")

    # ── PROFILE PHOTO MANAGEMENT CARD ─────────────────────────────────────────
    with st.container(border=True):
        col_img, col_info, col_actions = st.columns([0.8, 3.5, 2.5], vertical_alignment="center")

        with col_img:
            st.markdown(get_user_avatar_html(user_id, size=72, rounded="16px"), unsafe_allow_html=True)

        with col_info:
            st.markdown(
                f"<div style='font-size:17px;font-weight:750;color:#0F172A'>{user['full_name']}</div>"
                f"<div style='font-size:12px;color:#64748B;margin-top:2px'>{user['email']} · <strong style='color:#0284C7;text-transform:capitalize'>{role}</strong></div>"
                f"<div style='font-size:11px;color:#94A3B8;margin-top:4px'>PNG, JPG or WEBP formats supported (Auto-cropped to square)</div>",
                unsafe_allow_html=True
            )

        with col_actions:
            with st.popover("Upload / Change Photo", icon=":material/photo_camera:", use_container_width=True):
                st.markdown("<div style='font-size:13.5px;font-weight:700;color:#183F4C;margin-bottom:8px'>Select New Photo</div>", unsafe_allow_html=True)
                new_photo = st.file_uploader(
                    "Upload Image",
                    type=["png", "jpg", "jpeg", "webp"],
                    key="profile_page_avatar_uploader",
                    label_visibility="collapsed"
                )
                if new_photo is not None:
                    try:
                        from PIL import Image
                        img = Image.open(new_photo)
                        img = img.convert("RGBA")
                        w, h = img.size
                        min_dim = min(w, h)
                        left = (w - min_dim) // 2
                        top = (h - min_dim) // 2
                        img = img.crop((left, top, left + min_dim, top + min_dim))
                        img = img.resize((256, 256), Image.Resampling.LANCZOS)
                        os.makedirs(avatar_dir, exist_ok=True)
                        img.save(avatar_path, format="PNG")
                        st.toast("Profile photo updated successfully!", icon=":material/check_circle:")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error saving image: {e}")

                if os.path.exists(avatar_path):
                    if st.button("Remove Photo", icon=":material/delete:", key="btn_profile_del_avatar", use_container_width=True):
                        try:
                            os.remove(avatar_path)
                            st.toast("Profile photo reset to default avatar!", icon=":material/delete:")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error removing photo: {e}")

    st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)

    # ── TABS: PROFILE INFO | CHANGE PASSWORD | SETTINGS | DEPARTMENTS ─────────
    tab_labels = ["Profile Info", "Change Password", "Settings & Appearance", "Departments"]
    tab_info, tab_pw, tab_settings, tab_dept = st.tabs(tab_labels)

    # ── PROFILE INFO ──────────────────────────────────────────────────────────
    with tab_info:
        c1, c2, c3 = st.columns(3)
        c1.metric("Role", role.title())
        c2.metric("Department", user["dept_name"] or "—")
        c3.metric("Member Since", str(user["created_at"])[:10])
        st.caption(f"Email: **{user['email']}**  (cannot be changed)")
        st.divider()

        with st.form("profile_form"):
            name  = st.text_input("Full Name *", value=user["full_name"])
            phone = st.text_input("Phone", value=user.get("phone") or "")
            st.caption("Role and department can only be changed by an Admin.")

            if st.form_submit_button("Save Changes", type="primary", use_container_width=True):
                ok, msg = update_own_profile(user_id, name, phone)
                if ok:
                    st.session_state["user_name"] = name.strip()
                    log_action(user_id, "update_profile", "user", user_id)
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

    # ── CHANGE PASSWORD ───────────────────────────────────────────────────────
    with tab_pw:
        with st.form("pw_form"):
            old_pw  = st.text_input("Current Password",     type="password")
            new_pw  = st.text_input("New Password",         type="password")
            conf_pw = st.text_input("Confirm New Password", type="password")

            if st.form_submit_button("Change Password", type="primary", use_container_width=True):
                ok, msg = change_own_password(user_id, old_pw, new_pw, conf_pw)
                if ok:
                    log_action(user_id, "change_password", "user", user_id)
                    st.success(msg)
                else:
                    st.error(msg)

    # ── SETTINGS & APPEARANCE ─────────────────────────────────────────────────
    with tab_settings:
        st.subheader(":material/palette: Appearance & Workspace Settings")
        st.caption("Customize accent colors, card corner styling, and notification preferences.")

        col_theme, col_corners = st.columns(2)
        with col_theme:
            theme_options = list(THEMES.keys())
            current_theme = st.session_state.get("theme_name", "Ocean Teal (Default)")
            if current_theme not in theme_options:
                current_theme = theme_options[0]

            def _on_theme_change():
                st.session_state["theme_name"] = st.session_state["tab_theme_select"]
                st.toast(f"Theme updated to {st.session_state['tab_theme_select']}!", icon=":material/check_circle:")

            st.selectbox(
                "Accent Color Theme",
                options=theme_options,
                index=theme_options.index(current_theme),
                key="tab_theme_select",
                on_change=_on_theme_change
            )

        with col_corners:
            radius_options = ["16px (Rounded Balanced)", "24px (Pill Soft)", "8px (Compact Modern)"]
            curr_radius = st.session_state.get("card_radius", "16px")
            r_idx = 0
            if "24px" in curr_radius:
                r_idx = 1
            elif "8px" in curr_radius:
                r_idx = 2

            def _on_radius_change():
                clean_r = st.session_state["tab_radius_select"].split()[0]
                st.session_state["card_radius"] = clean_r
                st.toast(f"Card corner style set to {clean_r}!", icon=":material/check_circle:")

            st.selectbox(
                "Card Corner Style",
                options=radius_options,
                index=r_idx,
                key="tab_radius_select",
                on_change=_on_radius_change
            )

        st.divider()
        st.subheader(":material/notifications_active: Notification Preferences")
        c_notif1, c_notif2 = st.columns(2)
        with c_notif1:
            def _on_notif_status_change():
                st.toast("Paper status notification preference saved!", icon=":material/check_circle:")
            st.toggle(
                "Email on Paper Status Changes",
                value=st.session_state.get("notif_paper_status", True),
                key="notif_paper_status",
                on_change=_on_notif_status_change,
                help="Receive email alerts when papers are submitted, reviewed, approved or rejected."
            )
        with c_notif2:
            def _on_notif_deadline_change():
                st.toast("Milestone deadline notification preference saved!", icon=":material/check_circle:")
            st.toggle(
                "Email on Milestone & Deadlines",
                value=st.session_state.get("notif_deadlines", True),
                key="notif_deadlines",
                on_change=_on_notif_deadline_change,
                help="Receive alerts for upcoming research submission deadlines."
            )

    # ── DEPARTMENTS (read-only for all roles) ─────────────────────────────────
    with tab_dept:
        st.subheader(":material/account_tree: College Departments")
        depts = get_all_departments()
        if not depts:
            st.info("No departments found.")
        for d in depts:
            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                c1.write(f"**{d['dept_name']}**  `{d['dept_code']}`")
                c1.caption(f"HoD: {d['hod_name'] or '—'}")
                c2.metric("Users", d["user_count"])

    # ── FLOATING SETTINGS WIDGET (ONLY ON MY PROFILE) ─────────────────────────
    st.markdown(
        """
        <style>
        .st-key-float_quick_settings {
            position: fixed !important;
            bottom: 24px !important;
            right: 24px !important;
            z-index: 99999 !important;
        }
        .st-key-float_quick_settings button {
            width: 48px !important;
            height: 48px !important;
            min-height: 48px !important;
            border-radius: 50% !important;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.22) !important;
            background: #174B5A !important;
            color: #FFFFFF !important;
            border: 2px solid #FFFFFF !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            padding: 0 !important;
        }
        .st-key-float_quick_settings button:hover {
            background: #246779 !important;
            transform: scale(1.08);
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3) !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    with st.popover("", icon=":material/settings:", help="Float Settings & Quick Theme", key="float_quick_settings"):
        st.markdown("<div style='font-size:14.5px;font-weight:750;color:#0F172A;margin-bottom:6px'>Quick Theme Settings</div>", unsafe_allow_html=True)
        st.caption("Change active theme or styling instantly.")
        
        float_theme_options = list(THEMES.keys())
        curr_t = st.session_state.get("theme_name", "Ocean Teal (Default)")
        if curr_t not in float_theme_options:
            curr_t = float_theme_options[0]

        def _on_float_theme():
            st.session_state["theme_name"] = st.session_state["floating_theme_select"]
            st.rerun()

        st.selectbox(
            "Accent Theme",
            options=float_theme_options,
            index=float_theme_options.index(curr_t),
            key="floating_theme_select",
            on_change=_on_float_theme
        )

        float_rad_options = ["16px", "24px", "8px"]
        curr_r = st.session_state.get("card_radius", "16px")
        r_f_idx = 0
        if "24px" in curr_r:
            r_f_idx = 1
        elif "8px" in curr_r:
            r_f_idx = 2

        def _on_float_radius():
            st.session_state["card_radius"] = st.session_state["floating_radius_select"]
            st.rerun()

        st.selectbox(
            "Corner Radius",
            options=float_rad_options,
            index=r_f_idx,
            key="floating_radius_select",
            on_change=_on_float_radius
        )

