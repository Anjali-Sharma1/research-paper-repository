"""
services/ui_theme_service.py
UI Theme & Customization Engine for RPRMS.
Professional Sidebar & High-Contrast Typography.
Replaces emojis with clean SVG/symbol styling.
"""
import streamlit as st
import datetime
from html import escape as html_escape
import os
import base64

try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

# ── Preset Color Themes ───────────────────────────────────────────────────────
THEMES = {
    "Ocean Teal (Default)": {
        "primary": "#2F8291",
        "primary_dark": "#246779",
        "primary_light": "#E1F1F3",
        "accent": "#214F5E",
        "bg_main": "#EAF3F7",
        "sidebar_bg": "#174B5A",
        "sidebar_text": "#FFFFFF",
        "card_bg": "#FFFFFF",
        "border_color": "#DCE8EC"
    },
    "Royal Blue": {
        "primary": "#0052CC",
        "primary_dark": "#0747A6",
        "primary_light": "#DEEBFF",
        "accent": "#091E42",
        "bg_main": "#F4F6FA",
        "sidebar_bg": "#091E42",
        "sidebar_text": "#FFFFFF",
        "card_bg": "#FFFFFF",
        "border_color": "#DCE3EB"
    },
    "Emerald Green": {
        "primary": "#059669",
        "primary_dark": "#047857",
        "primary_light": "#ECFDF5",
        "accent": "#064E3B",
        "bg_main": "#F2FAF6",
        "sidebar_bg": "#0B2E24",
        "sidebar_text": "#FFFFFF",
        "card_bg": "#FFFFFF",
        "border_color": "#D1EBE1"
    },
    "Electric Violet": {
        "primary": "#7C3AED",
        "primary_dark": "#6D28D9",
        "primary_light": "#F3E8FF",
        "accent": "#4C1D95",
        "bg_main": "#F8F5FE",
        "sidebar_bg": "#1E1238",
        "sidebar_text": "#FFFFFF",
        "card_bg": "#FFFFFF",
        "border_color": "#E9D8FD"
    },
    "Sunset Amber": {
        "primary": "#D97706",
        "primary_dark": "#B45309",
        "primary_light": "#FEF3C7",
        "accent": "#78350F",
        "bg_main": "#FAF8F2",
        "sidebar_bg": "#2B1607",
        "sidebar_text": "#FFFFFF",
        "card_bg": "#FFFFFF",
        "border_color": "#FDE68A"
    },
    "Crimson Red": {
        "primary": "#DC2626",
        "primary_dark": "#B91C1C",
        "primary_light": "#FEE2E2",
        "accent": "#7F1D1D",
        "bg_main": "#FAF4F4",
        "sidebar_bg": "#2D0A0A",
        "sidebar_text": "#FFFFFF",
        "card_bg": "#FFFFFF",
        "border_color": "#FECACA"
    }
}

def init_theme_state():
    """Ensure theme state variables exist in session_state."""
    if "theme_name" not in st.session_state:
        st.session_state["theme_name"] = "Ocean Teal (Default)"
    if "custom_primary" not in st.session_state:
        st.session_state["custom_primary"] = "#0047FF"
    if "card_radius" not in st.session_state:
        st.session_state["card_radius"] = "16px"
    if "brand_logo" not in st.session_state:
        st.session_state["brand_logo"] = "RPRMS"
    if "show_customizer" not in st.session_state:
        st.session_state["show_customizer"] = False
    if "selected_calendar_day" not in st.session_state:
        st.session_state["selected_calendar_day"] = 7
    if "sidebar_open" not in st.session_state:
        st.session_state["sidebar_open"] = True

def get_current_theme():
    init_theme_state()
    t_name = st.session_state.get("theme_name", "Ocean Teal (Default)")
    theme = THEMES.get(t_name, THEMES["Ocean Teal (Default)"]).copy()
    if t_name == "Custom":
        theme["primary"] = st.session_state.get("custom_primary", "#0047FF")
    return theme

def apply_custom_theme():
    """Inject dynamic CSS styles into Streamlit page with full theme & radius reactivity."""
    theme = get_current_theme()
    primary = theme["primary"]
    primary_dark = theme["primary_dark"]
    primary_light = theme.get("primary_light", "#E1F1F3")
    sidebar_bg = theme["sidebar_bg"]
    bg_main = theme["bg_main"]
    radius = st.session_state.get("card_radius", "16px")
    is_logged_in = st.session_state.get("is_logged_in", False)
    sidebar_open = is_logged_in and st.session_state.get("sidebar_open", True)

    sidebar_width = "320px"
    content_left = "345px" if sidebar_open else "65px"
    content_width = "calc(100% - 370px)" if sidebar_open else "calc(100% - 90px)"
    toggle_left = "332px" if sidebar_open else "16px"
    content_padding_top = "1.35rem" if sidebar_open else "4.2rem"

    sidebar_css_rule = f"""
    [data-testid="stSidebar"], section[data-testid="stSidebar"] {{
        background-color: {sidebar_bg} !important;
        box-sizing: border-box !important;
        border-right: 1px solid rgba(255,255,255,0.08) !important;
        width: {sidebar_width} !important;
        min-width: {sidebar_width} !important;
        max-width: {sidebar_width} !important;
        padding: 1rem 0.8rem 1.25rem !important;
        box-shadow: 5px 0 22px rgba(0,0,0,.15) !important;
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        height: 100vh !important;
        z-index: 1000 !important;
        display: block !important;
        visibility: visible !important;
        transform: translateX(0) !important;
        opacity: 1 !important;
        pointer-events: auto !important;
        transition: transform .28s cubic-bezier(0.4, 0, 0.2, 1), width .28s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }}
    """ if sidebar_open else """
    [data-testid="stSidebar"], section[data-testid="stSidebar"], div[data-testid="stSidebar"] {
        display: none !important;
        left: -450px !important;
        transform: translateX(-130%) !important;
        width: 0 !important;
        min-width: 0 !important;
        max-width: 0 !important;
        visibility: hidden !important;
        pointer-events: none !important;
        opacity: 0 !important;
    }
    """

    responsive_sidebar = """
        @media (max-width: 1200px) {
            div[data-testid="stSidebar"], section[data-testid="stSidebar"] {
                position: fixed !important;
                inset: 0 auto 0 0 !important;
                width: min(320px, 86vw) !important;
                min-width: min(320px, 86vw) !important;
                max-width: min(320px, 86vw) !important;
                height: 100vh !important;
                z-index: 1100 !important;
            }
        }
    """ if sidebar_open else ""

    css = f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200');
    @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200');

    html, body, [class*="css"] {{
        font-family: 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif !important;
        color: #0F172A !important;
    }}

    span[data-testid="stIconMaterial"],
    [data-testid="stIconMaterial"],
    .material-symbols-rounded,
    .material-symbols-outlined {{
        font-family: 'Material Symbols Rounded', 'Material Symbols Outlined' !important;
        font-weight: normal !important;
        font-style: normal !important;
        line-height: 1 !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        letter-spacing: normal !important;
        -webkit-font-smoothing: antialiased !important;
    }}

    .stApp {{
        background-color: {bg_main} !important;
    }}

    [data-testid="stMain"] {{
        background: linear-gradient(180deg, {bg_main} 0%, #FFFFFF 100%) !important;
    }}

    [data-testid="stMainBlockContainer"] {{
        box-sizing: border-box !important;
        max-width: 1500px !important;
        width: {content_width} !important;
        margin-left: {content_left} !important;
        margin-right: 24px !important;
        padding-top: {content_padding_top} !important;
        padding-bottom: 2rem !important;
        transition: margin-left .28s cubic-bezier(0.4, 0, 0.2, 1), width .28s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }}

    h1, h2, h3, h4, h5, h6, p, span, label {{
        color: #0F172A !important;
    }}

    header[data-testid="stHeader"] {{
        background: transparent !important;
    }}

    /* === 3D KEYFRAME ANIMATIONS === */
    @keyframes float3D {{
        0% {{
            transform: perspective(750px) rotateY(0deg) rotateX(0deg) translateY(0px);
            filter: drop-shadow(0 6px 12px rgba(0, 0, 0, 0.16)) drop-shadow(0 12px 26px rgba(0, 82, 204, 0.28));
        }}
        50% {{
            transform: perspective(750px) rotateY(8deg) rotateX(-5deg) translateY(-5px);
            filter: drop-shadow(0 14px 22px rgba(0, 0, 0, 0.22)) drop-shadow(0 22px 42px rgba(0, 82, 204, 0.42));
        }}
        100% {{
            transform: perspective(750px) rotateY(0deg) rotateX(0deg) translateY(0px);
            filter: drop-shadow(0 6px 12px rgba(0, 0, 0, 0.16)) drop-shadow(0 12px 26px rgba(0, 82, 204, 0.28));
        }}
    }}

    /* === 3D LOGO STYLING === */
    .brand-logo-3d {{
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        perspective: 800px !important;
        transform-style: preserve-3d !important;
        animation: float3D 6.5s ease-in-out infinite !important;
        transition: transform 0.35s cubic-bezier(0.2, 0.8, 0.2, 1.2), filter 0.35s ease !important;
        cursor: pointer !important;
    }}
    .brand-logo-3d:hover {{
        transform: perspective(800px) rotateY(14deg) rotateX(-7deg) translateY(-7px) scale(1.08) !important;
        filter: drop-shadow(0 16px 28px rgba(0, 0, 0, 0.26)) drop-shadow(0 26px 48px rgba(0, 82, 204, 0.48)) !important;
    }}
    .brand-logo-3d img {{
        filter: drop-shadow(0 6px 12px rgba(0, 82, 204, 0.3)) drop-shadow(0 2px 4px rgba(0, 0, 0, 0.18)) !important;
        transition: transform 0.35s ease !important;
    }}

    /* === 3D STATIC BRAND PILL (COLLAPSED STATE) === */
    .brand-pill-3d {{
        position: fixed !important;
        top: 11px !important;
        left: 68px !important;
        z-index: 999998 !important;
        display: flex !important;
        align-items: center !important;
        gap: 12px !important;
        background: rgba(255, 255, 255, 0.95) !important;
        backdrop-filter: blur(16px) !important;
        -webkit-backdrop-filter: blur(16px) !important;
        border: 1px solid rgba(220, 232, 236, 0.9) !important;
        padding: 5px 18px 5px 8px !important;
        border-radius: 14px !important;
        box-shadow: 
            0 2px 4px rgba(15, 23, 42, 0.04),
            0 12px 28px -4px rgba(15, 23, 42, 0.12),
            inset 0 1px 0 rgba(255, 255, 255, 0.95) !important;
        pointer-events: auto !important;
        transform-style: preserve-3d !important;
        transition: transform 0.25s ease, box-shadow 0.25s ease !important;
    }}
    .brand-pill-3d:hover {{
        transform: translateY(-2px) scale(1.02) !important;
        box-shadow: 
            0 4px 8px rgba(15, 23, 42, 0.06),
            0 16px 36px -4px rgba(15, 23, 42, 0.16),
            inset 0 1px 0 rgba(255, 255, 255, 1) !important;
    }}

    /* === 3D CONTAINERS, CARDS & ELEVATION === */
    div[data-testid="stVerticalBlock"] > div[data-testid="stContainer"],
    [data-testid="stForm"],
    div[data-testid="stAlert"] {{
        border-radius: {radius} !important;
        background: #FFFFFF !important;
        border: 1px solid rgba(220, 232, 236, 0.9) !important;
        box-shadow: 
            0 2px 4px rgba(15, 23, 42, 0.03),
            0 10px 25px -4px rgba(15, 23, 42, 0.07),
            0 20px 36px -8px rgba(15, 23, 42, 0.04),
            inset 0 1px 0 rgba(255, 255, 255, 0.95) !important;
        transition: transform 0.28s cubic-bezier(0.2, 0.8, 0.2, 1), box-shadow 0.28s cubic-bezier(0.2, 0.8, 0.2, 1), border-color 0.28s ease !important;
        transform-style: preserve-3d !important;
    }}
    div[data-testid="stVerticalBlock"] > div[data-testid="stContainer"]:hover,
    [data-testid="stForm"]:hover {{
        transform: perspective(1200px) translateY(-3px) scale(1.004) !important;
        box-shadow: 
            0 4px 8px rgba(15, 23, 42, 0.05),
            0 16px 36px -4px rgba(15, 23, 42, 0.11),
            0 28px 48px -8px rgba(15, 23, 42, 0.06),
            inset 0 1px 0 #FFFFFF !important;
        border-color: rgba(47, 130, 145, 0.45) !important;
    }}

    {sidebar_css_rule}

    [data-testid="stSidebarCollapseButton"], [data-testid="stSidebarCollapsedControl"] {{ display: none !important; }}

    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] span, section[data-testid="stSidebar"] label {{
        color: #FFFFFF !important;
    }}

    /* 3D Sidebar Radio Navigation */
    [data-testid="stSidebar"] div[role="radiogroup"],
    section[data-testid="stSidebar"] div[role="radiogroup"] {{
        gap: 4px !important;
        padding: 4px 0 !important;
        width: 100% !important;
    }}
    [data-testid="stSidebar"] div[role="radiogroup"] input,
    section[data-testid="stSidebar"] div[role="radiogroup"] input {{
        display: none !important;
    }}
    [data-testid="stSidebar"] [data-baseweb="radio"] > div:first-child,
    section[data-testid="stSidebar"] [data-baseweb="radio"] > div:first-child,
    div[role="radiogroup"] [data-baseweb="radio"] > div:first-child {{
        display: none !important;
        width: 0 !important;
        height: 0 !important;
        visibility: hidden !important;
    }}
    [data-testid="stSidebar"] [data-baseweb="radio"] > div:last-child,
    section[data-testid="stSidebar"] [data-baseweb="radio"] > div:last-child {{
        width: 100% !important;
        display: flex !important;
        align-items: center !important;
    }}
    [data-testid="stSidebar"] [data-baseweb="radio"],
    section[data-testid="stSidebar"] [data-baseweb="radio"] {{
        padding-left: 0 !important;
        margin-bottom: 2px !important;
        width: 100% !important;
    }}
    [data-testid="stSidebar"] div[role="radiogroup"] label,
    section[data-testid="stSidebar"] div[role="radiogroup"] label {{
        display: flex !important;
        align-items: center !important;
        width: 100% !important;
        padding: 9px 14px !important;
        border-radius: 11px !important;
        margin: 0 !important;
        cursor: pointer !important;
        border: 1px solid transparent !important;
        box-sizing: border-box !important;
        transition: background .18s ease, transform .18s ease, box-shadow .18s ease !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06) !important;
    }}
    [data-testid="stSidebar"] div[role="radiogroup"] label:hover,
    section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {{
        background: rgba(255, 255, 255, 0.16) !important;
        transform: translateX(4px) !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.18) !important;
    }}
    [data-testid="stSidebar"] div[role="radiogroup"] label[data-checked="true"],
    [data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked),
    section[data-testid="stSidebar"] div[role="radiogroup"] label[data-checked="true"],
    section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {{
        background: linear-gradient(90deg, {primary} 0%, {primary_dark} 100%) !important;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.3) !important;
        transform: translateX(4px) !important;
    }}
    [data-testid="stSidebar"] div[role="radiogroup"] label p,
    [data-testid="stSidebar"] div[role="radiogroup"] label span,
    section[data-testid="stSidebar"] div[role="radiogroup"] label p,
    section[data-testid="stSidebar"] div[role="radiogroup"] label span {{
        color: #FFFFFF !important;
        font-size: 13px !important;
        font-weight: 500 !important;
    }}

    .st-key-sidebar_menu_toggle {{
        position: fixed !important;
        top: 14px !important;
        left: {toggle_left} !important;
        z-index: 999999 !important;
        width: 42px !important;
        transition: left 0.28s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }}
    .st-key-sidebar_menu_toggle button {{
        min-height: 40px !important;
        height: 40px !important;
        width: 40px !important;
        border-radius: 11px !important;
        border: 1px solid rgba(220, 232, 236, 0.9) !important;
        background: #FFFFFF !important;
        color: {primary} !important;
        font-size: 20px !important;
        line-height: 1 !important;
        box-shadow: 
            0 3px 0 #CBD5E1,
            0 6px 14px rgba(0, 0, 0, 0.08),
            inset 0 1px 0 #FFFFFF !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        padding: 0 !important;
        transition: transform 0.12s ease, box-shadow 0.12s ease !important;
    }}
    .st-key-sidebar_menu_toggle button:hover {{
        background: #F0F6F8 !important;
        border-color: {primary} !important;
        color: {primary} !important;
        transform: translateY(-1.5px) !important;
        box-shadow: 
            0 4.5px 0 #CBD5E1,
            0 10px 20px rgba(0, 0, 0, 0.12),
            inset 0 1px 0 #FFFFFF !important;
    }}
    .st-key-sidebar_menu_toggle button:active {{
        transform: translateY(2px) !important;
        box-shadow: 
            0 1px 0 #CBD5E1,
            0 2px 5px rgba(0, 0, 0, 0.06),
            inset 0 1px 0 #FFFFFF !important;
    }}

    /* === 3D METRIC CARDS === */
    .metric-card {{
        background: linear-gradient(180deg, #FFFFFF 0%, #FAFCFD 100%) !important;
        border-radius: {radius} !important;
        padding: 20px 22px !important;
        border: 1px solid #DCE8EC !important;
        box-shadow: 
            0 2px 4px rgba(0, 0, 0, 0.03),
            0 10px 24px -5px rgba(0, 0, 0, 0.06),
            inset 0 1px 0 #FFFFFF !important;
        display: flex !important;
        align-items: center !important;
        gap: 18px !important;
        transform-style: preserve-3d !important;
        transition: transform 0.25s ease, box-shadow 0.25s ease !important;
    }}
    .metric-card:hover {{
        transform: perspective(1000px) translateY(-4px) scale(1.015) !important;
        box-shadow: 
            0 4px 10px rgba(0, 0, 0, 0.05),
            0 18px 36px -6px rgba(0, 0, 0, 0.1),
            inset 0 1px 0 #FFFFFF !important;
    }}

    .metric-card-highlight {{
        background: linear-gradient(180deg, #FFFFFF 0%, #F5F9FA 100%) !important;
        border-radius: {radius} !important;
        padding: 20px 22px !important;
        color: #173E4A !important;
        box-shadow: 
            0 2px 4px rgba(0, 0, 0, 0.03),
            0 12px 28px -5px rgba(47, 130, 145, 0.14),
            inset 0 1px 0 #FFFFFF !important;
        border: 1px solid #DCE8EC !important;
        border-top: 4px solid {primary} !important;
        transform-style: preserve-3d !important;
        transition: transform 0.25s ease, box-shadow 0.25s ease !important;
    }}
    .metric-card-highlight:hover {{
        transform: perspective(1000px) translateY(-4px) scale(1.015) !important;
        box-shadow: 
            0 4px 10px rgba(0, 0, 0, 0.05),
            0 20px 42px -6px rgba(47, 130, 145, 0.22),
            inset 0 1px 0 #FFFFFF !important;
    }}

    .metric-icon-box {{
        width: 50px !important;
        height: 50px !important;
        border-radius: 14px !important;
        background: linear-gradient(135deg, {primary_light} 0%, #FFFFFF 100%) !important;
        border: 1px solid rgba(47, 130, 145, 0.25) !important;
        box-shadow: 0 4px 12px rgba(47, 130, 145, 0.18), inset 0 1px 0 #FFFFFF !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        font-size: 20px !important;
        color: {primary} !important;
        flex-shrink: 0 !important;
    }}
    .metric-icon-box-white {{
        width: 50px !important;
        height: 50px !important;
        border-radius: 14px !important;
        background: linear-gradient(135deg, {primary} 0%, {primary_dark} 100%) !important;
        box-shadow: 0 5px 16px rgba(0, 0, 0, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.45) !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        font-size: 20px !important;
        color: #FFFFFF !important;
        flex-shrink: 0 !important;
    }}

    /* === 3D TACTILE PUSH-DOWN BUTTONS === */
    [data-testid="stFormSubmitButton"] button,
    .stButton button[kind="primary"] {{
        background: linear-gradient(180deg, {primary} 0%, {primary_dark} 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 11px !important;
        box-shadow: 
            0 4px 0 {primary_dark},
            0 8px 18px rgba(0, 0, 0, 0.16),
            inset 0 1px 0 rgba(255, 255, 255, 0.35) !important;
        font-weight: 700 !important;
        letter-spacing: 0.3px !important;
        transform: translateY(0) !important;
        transition: transform 0.12s ease, box-shadow 0.12s ease !important;
    }}
    [data-testid="stFormSubmitButton"] button:hover,
    .stButton button[kind="primary"]:hover {{
        transform: translateY(-2px) !important;
        box-shadow: 
            0 6px 0 {primary_dark},
            0 14px 26px rgba(0, 0, 0, 0.22),
            inset 0 1px 0 rgba(255, 255, 255, 0.45) !important;
    }}
    [data-testid="stFormSubmitButton"] button:active,
    .stButton button[kind="primary"]:active {{
        transform: translateY(3px) !important;
        box-shadow: 
            0 1px 0 {primary_dark},
            0 3px 8px rgba(0, 0, 0, 0.14),
            inset 0 1px 0 rgba(255, 255, 255, 0.2) !important;
    }}

    .stButton button[kind="secondary"] {{
        background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%) !important;
        border: 1px solid #CBD5E1 !important;
        color: #1E293B !important;
        border-radius: 11px !important;
        box-shadow: 
            0 3px 0 #CBD5E1,
            0 6px 14px rgba(0, 0, 0, 0.05),
            inset 0 1px 0 #FFFFFF !important;
        font-weight: 650 !important;
        transform: translateY(0) !important;
        transition: transform 0.12s ease, box-shadow 0.12s ease !important;
    }}
    .stButton button[kind="secondary"]:hover {{
        transform: translateY(-1.5px) !important;
        box-shadow: 
            0 4.5px 0 #CBD5E1,
            0 10px 20px rgba(0, 0, 0, 0.09),
            inset 0 1px 0 #FFFFFF !important;
    }}
    .stButton button[kind="secondary"]:active {{
        transform: translateY(2px) !important;
        box-shadow: 
            0 1px 0 #CBD5E1,
            0 2px 5px rgba(0, 0, 0, 0.05),
            inset 0 1px 0 #FFFFFF !important;
    }}

    /* === 3D FORM INPUTS & SELECTBOXES === */
    input[type="text"], input[type="password"], input[type="number"], textarea, [data-baseweb="select"] > div {{
        border-radius: 10px !important;
        border: 1px solid #CBD5E1 !important;
        box-shadow: inset 0 2px 4px rgba(15, 23, 42, 0.05), 0 1px 2px rgba(255, 255, 255, 0.8) !important;
        transition: all 0.2s ease !important;
    }}
    input[type="text"]:focus, input[type="password"]:focus, input[type="number"]:focus, textarea:focus, [data-baseweb="select"] > div:focus-within {{
        border-color: {primary} !important;
        box-shadow: inset 0 2px 4px rgba(15, 23, 42, 0.03), 0 0 0 3px rgba(47, 130, 145, 0.22), 0 4px 12px rgba(0, 0, 0, 0.06) !important;
        transform: translateY(-1px) !important;
    }}

    /* === 3D TABLES & DATAFRAMES === */
    div[data-testid="stTable"], [data-testid="stDataFrame"] {{
        background: #FFFFFF !important;
        border-radius: {radius} !important;
        box-shadow: 0 4px 20px rgba(15, 23, 42, 0.06), inset 0 1px 0 #FFFFFF !important;
        border: 1px solid #DCE8EC !important;
        overflow: hidden !important;
    }}

    /* Logout Button Styling with 3D Bevel */
    [data-testid="stSidebar"] [data-testid="stBaseButton-secondary"],
    section[data-testid="stSidebar"] button[kind="secondary"] {{
        background: rgba(255, 255, 255, 0.1) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        color: #FFFFFF !important;
        border-radius: 11px !important;
        box-shadow: 0 3px 0 rgba(0, 0, 0, 0.25), 0 6px 14px rgba(0, 0, 0, 0.15), inset 0 1px 0 rgba(255, 255, 255, 0.25) !important;
        transition: transform 0.12s ease, box-shadow 0.12s ease !important;
    }}
    [data-testid="stSidebar"] [data-testid="stBaseButton-secondary"]:hover,
    section[data-testid="stSidebar"] button[kind="secondary"]:hover {{
        background: rgba(255, 255, 255, 0.18) !important;
        transform: translateY(-1.5px) !important;
        box-shadow: 0 4.5px 0 rgba(0, 0, 0, 0.25), 0 10px 20px rgba(0, 0, 0, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.35) !important;
    }}
    [data-testid="stSidebar"] [data-testid="stBaseButton-secondary"]:active,
    section[data-testid="stSidebar"] button[kind="secondary"]:active {{
        transform: translateY(2px) !important;
        box-shadow: 0 1px 0 rgba(0, 0, 0, 0.25), 0 2px 6px rgba(0, 0, 0, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.15) !important;
    }}


    
    /* === HIDE 'PRESS ENTER TO SUBMIT FORM' HELPER / TOOLTIP === */
    [data-testid="InputInstructions"],
    .stTextInput div[data-testid="InputInstructions"],
    .stNumberInput div[data-testid="InputInstructions"],
    .stTextArea div[data-testid="InputInstructions"],
    .stForm div[data-testid="InputInstructions"],
    div[data-testid="InputInstructions"] {{
        display: none !important;
        visibility: hidden !important;
        height: 0px !important;
        max-height: 0px !important;
        margin: 0px !important;
        padding: 0px !important;
        opacity: 0 !important;
        overflow: hidden !important;
        pointer-events: none !important;
    }}

    {responsive_sidebar}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

def _toggle_sidebar():
    st.session_state["sidebar_open"] = not st.session_state.get("sidebar_open", True)

def render_sidebar_toggle():
    """Persistent floating button to slide sidebar open / closed with static brand logo."""
    sidebar_open = st.session_state.get("sidebar_open", True)
    icon_name = ":material/menu_open:" if sidebar_open else ":material/menu:"
    st.button(
        "",
        icon=icon_name,
        key="sidebar_menu_toggle",
        help="Toggle navigation sidebar",
        on_click=_toggle_sidebar,
    )
    if not sidebar_open:
        b64 = get_brand_logo_b64()
        if b64:
            brand_pill = f"""
            <div class="brand-pill-3d">
                <div class="brand-logo-3d">
                    <img src="data:image/png;base64,{b64}" style="width: 58px; height: 58px; object-fit: contain;" />
                </div>
                <div style="line-height: 1.15;">
                    <div style="font-size: 17.5px; font-weight: 850; color: #0F172A; letter-spacing: 0.3px; text-shadow: 0 1px 2px rgba(0,0,0,0.06);">RPRMS</div>
                    <div style="font-size: 9.5px; font-weight: 700; text-transform: uppercase; color: #64748B; letter-spacing: 1.1px;">Research Repository</div>
                </div>
            </div>
            """
            st.markdown(brand_pill, unsafe_allow_html=True)


def get_brand_logo_b64() -> str:
    """Return base64 string of the official RPRMS logo."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    logo_path = os.path.join(base_dir, "assets", "logo_transparent.png")
    if not os.path.exists(logo_path):
        logo_path = os.path.join(base_dir, "assets", "logo.png")
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""


def get_brand_logo_html(size: int = 56, rounded: str = "12px", border: bool = False, bg: str = "transparent") -> str:
    """Returns styled 3D HTML container with the custom RPRMS logo."""
    b64 = get_brand_logo_b64()
    if b64:
        border_css = "border: 1px solid rgba(255,255,255,0.25);" if border else ""
        bg_css = f"background: {bg};" if bg else ""
        return (
            f'<div class="brand-logo-3d" style="width:{size}px;height:{size}px;flex:0 0 {size}px;border-radius:{rounded};'
            f'{bg_css}{border_css}">'
            f'<img src="data:image/png;base64,{b64}" style="width:100%;height:100%;object-fit:contain;" /></div>'
        )
    return (
        f'<div class="brand-logo-3d" style="width:{size}px;height:{size}px;border-radius:{rounded};background:#D7F3E2;'
        f'color:#165367;font-weight:800;box-shadow:0 4px 12px rgba(0,0,0,0.15)">RP</div>'
    )


def get_user_avatar_html(user_id: int, size: int = 52, rounded: str = "12px") -> str:
    """Returns avatar image or clean person silhouette icon matching Image 2."""
    avatar_dir = os.path.join("uploads", "avatars")
    avatar_path = os.path.join(avatar_dir, f"avatar_{user_id}.png")
    if os.path.exists(avatar_path):
        try:
            with open(avatar_path, "rb") as af:
                b64 = base64.b64encode(af.read()).decode()
            return f'<div style="width:{size}px;height:{size}px;flex:0 0 {size}px;border-radius:{rounded};overflow:hidden;border:2px solid #D7F3E2;box-shadow:0 2px 6px rgba(0,0,0,0.1);"><img src="data:image/png;base64,{b64}" style="width:100%;height:100%;object-fit:cover;" /></div>'
        except Exception:
            pass

    # Exact silhouette avatar icon matching the user's uploaded Image 2 (white rounded rectangle with person silhouette)
    return (
        f'<div style="width:{size}px;height:{size}px;flex:0 0 {size}px;border-radius:{rounded};'
        f'overflow:hidden;background:#FFFFFF;border:2px solid rgba(255,255,255,0.9);'
        f'box-shadow:0 2px 8px rgba(0,0,0,0.12);display:flex;align-items:center;justify-content:center;">'
        f'<svg viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg" style="width:78%;height:78%;">'
        f'<circle cx="50" cy="35" r="20" fill="#18181B"/>'
        f'<path d="M14 86C14 65 30 58 50 58C70 58 86 65 86 86" fill="#18181B"/>'
        f'</svg>'
        f'</div>'
    )


def render_top_header(user_name: str, user_role: str, unread_count: int = 0, show_camera: bool = False):
    safe_name = html_escape(user_name)
    safe_role = html_escape(user_role.title())
    user_id = st.session_state.get("user_id", 0)

    avatar_dir = os.path.join("uploads", "avatars")
    avatar_path = os.path.join(avatar_dir, f"avatar_{user_id}.png")

    with st.container(border=True):
        if show_camera:
            col_avatar, col_cam, col_welcome, col_search, col_user = st.columns([0.45, 0.45, 2.3, 3.2, 1.6], vertical_alignment="center")

            with col_avatar:
                st.markdown(get_user_avatar_html(user_id, size=54, rounded="12px"), unsafe_allow_html=True)

            with col_cam:
                with st.popover("", icon=":material/photo_camera:", help="Upload / Change profile photo"):
                    st.markdown("<div style='font-size:14px;font-weight:700;color:#183F4C;margin-bottom:8px'>Update Profile Photo</div>", unsafe_allow_html=True)
                    new_avatar = st.file_uploader(
                        "Upload image (PNG, JPG)",
                        type=["png", "jpg", "jpeg", "webp"],
                        key="header_avatar_uploader",
                        label_visibility="collapsed"
                    )
                    if new_avatar is not None:
                        try:
                            from PIL import Image
                            img = Image.open(new_avatar)
                            img = img.convert("RGBA")
                            w, h = img.size
                            min_dim = min(w, h)
                            left = (w - min_dim) // 2
                            top = (h - min_dim) // 2
                            img = img.crop((left, top, left + min_dim, top + min_dim))
                            img = img.resize((256, 256), Image.Resampling.LANCZOS)
                            os.makedirs(avatar_dir, exist_ok=True)
                            img.save(avatar_path, format="PNG")
                            st.toast("Profile photo updated!", icon=":material/check_circle:")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error saving image: {e}")
                    if os.path.exists(avatar_path):
                        if st.button("Remove Photo", icon=":material/delete:", key="btn_del_avatar", use_container_width=True):
                            try:
                                os.remove(avatar_path)
                                st.toast("Profile photo removed!", icon=":material/delete:")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error removing photo: {e}")
        else:
            col_avatar, col_welcome, col_search, col_user = st.columns([0.45, 2.65, 3.3, 1.6], vertical_alignment="center")

            with col_avatar:
                st.markdown(get_user_avatar_html(user_id, size=54, rounded="12px"), unsafe_allow_html=True)

        with col_welcome:
            st.markdown(
                f"<div style='padding:4px 0'>"
                f"<div style='font-size:16.5px;font-weight:750;color:#183F4C;white-space:nowrap;overflow:hidden;text-overflow:ellipsis'>Welcome, {safe_name}</div>"
                f"<div style='font-size:11px;color:#78909A;margin-top:2px'>Your research workspace</div></div>",
                unsafe_allow_html=True,
            )

        with col_search:
            with st.form("header_search_form", clear_on_submit=False):
                query_col, submit_col = st.columns([5, 1], vertical_alignment="center")
                query = query_col.text_input(
                    "Search papers, authors, keywords",
                    key="header_search_query",
                    placeholder="Search papers, authors, keywords...",
                    label_visibility="collapsed",
                )
                submitted = submit_col.form_submit_button("", icon=":material/search:", help="Search papers", use_container_width=True)
            if submitted and query.strip():
                st.session_state["paper_search_query"] = query.strip()
                st.session_state["_nav"] = "Search Papers"
                st.rerun()

        with col_user:
            st.markdown(
                f"<div style='display:flex;align-items:center;justify-content:flex-end;padding:4px 0'>"
                f"<div style='text-align:right;'><div style='font-size:13px;font-weight:750;color:#183F4C;white-space:nowrap;overflow:hidden;text-overflow:ellipsis'>{safe_name}</div>"
                f"<div style='font-size:11px;color:#78909A;text-transform:capitalize'>{safe_role}</div></div></div>",
                unsafe_allow_html=True,
            )

def render_kpi_card(title: str, value: str, trend: str, icon_symbol: str = "P", highlighted: bool = False):
    if highlighted:
        html = f"""
        <div class="metric-card-highlight">
            <div style="display: flex; align-items: center; gap: 14px;">
                <div class="metric-icon-box-white" style="font-weight: 800;">{icon_symbol}</div>
                <div>
                    <div class="metric-title-white">{title}</div>
                    <div class="metric-value-white">{value}</div>
                </div>
            </div>
        </div>
        """
    else:
        html = f"""
        <div class="metric-card">
            <div class="metric-icon-box" style="font-weight: 800;">{icon_symbol}</div>
            <div>
                <div class="metric-title">{title}</div>
                <div class="metric-value">{value}</div>
            </div>
        </div>
        """
    st.markdown(html, unsafe_allow_html=True)

def render_area_growth_chart(user_id: int = None, role: str = None, chart_title: str = "Submissions & Download Growth"):
    """
    Paper Views & Citations / Upload Growth Chart with interactive 3D styling.
    Features:
      - Single-click Move Navigation (◀ / ▶) to shift the timeline left/right in 1 click.
      - Single-click Time Range Chips (3M, 6M, All) to move/focus the graph in 1 click.
      - Single-click Drag & Pan (dragmode='pan') to move the canvas smoothly.
      - Single-click Reset button to restore default zoom and axes.
    """
    theme = get_current_theme()
    primary = theme["primary"]
    primary_light = theme.get("primary_light", "#E1F1F3")

    if user_id is None:
        user_id = st.session_state.get("user_id")
    if role is None:
        role = st.session_state.get("user_role")

    # 1. Header with Title & Single-Click Move Buttons
    col_t, col_l, col_r, col_rst = st.columns([2.6, 0.6, 0.6, 1.2], vertical_alignment="center")
    with col_t:
        st.markdown(f"<h4 style='font-size: 15.5px; font-weight: 700; color: #0F172A; margin: 0;'>{chart_title}</h4>", unsafe_allow_html=True)
    with col_l:
        if st.button("◀", key=f"btn_pan_l_{role or 'all'}", help="Single click: Move graph left (earlier period)", use_container_width=True):
            st.session_state["graph_offset"] = st.session_state.get("graph_offset", 0) - 1
            st.rerun()
    with col_r:
        if st.button("▶", key=f"btn_pan_r_{role or 'all'}", help="Single click: Move graph right (later period)", use_container_width=True):
            st.session_state["graph_offset"] = st.session_state.get("graph_offset", 0) + 1
            st.rerun()
    with col_rst:
        btn_key = f"btn_reset_chart_{role or 'all'}"
        if st.button("Reset", icon=":material/restart_alt:", key=btn_key, help="Single click: Reset graph to default view", use_container_width=True):
            st.session_state["graph_offset"] = 0
            st.session_state["chart_range"] = "All"
            st.session_state["chart_key_nonce"] = st.session_state.get("chart_key_nonce", 0) + 1
            st.toast("Graph view reset to default!", icon=":material/refresh:")
            st.rerun()

    # 2. Single-Click Time Range Focus Buttons
    col_lbl, col_3m, col_6m, col_all = st.columns([2.3, 0.9, 0.9, 0.9], vertical_alignment="center")
    cur_range = st.session_state.get("chart_range", "All")
    with col_lbl:
        st.caption("Click to move timeline:")
    with col_3m:
        if st.button("3 Months", key=f"btn_r3m_{role or 'all'}", type="primary" if cur_range == "3M" else "secondary", use_container_width=True):
            st.session_state["chart_range"] = "3M"
            st.session_state["graph_offset"] = 0
            st.rerun()
    with col_6m:
        if st.button("6 Months", key=f"btn_r6m_{role or 'all'}", type="primary" if cur_range == "6M" else "secondary", use_container_width=True):
            st.session_state["chart_range"] = "6M"
            st.session_state["graph_offset"] = 0
            st.rerun()
    with col_all:
        if st.button("All Time", key=f"btn_rall_{role or 'all'}", type="primary" if cur_range == "All" else "secondary", use_container_width=True):
            st.session_state["chart_range"] = "All"
            st.session_state["graph_offset"] = 0
            st.rerun()

    st.markdown("<div style='margin-bottom: 6px;'></div>", unsafe_allow_html=True)

    # Fetch real user activity data from database
    p_rows = []
    d_rows = []
    try:
        from database.connection import get_connection
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        if role == "faculty" and user_id:
            cur.execute("SELECT created_at FROM papers WHERE uploaded_by = %s", (user_id,))
            p_rows = cur.fetchall() or []
            cur.execute("""
                SELECT d.downloaded_at 
                FROM downloads d 
                JOIN papers p ON d.paper_id = p.paper_id 
                WHERE p.uploaded_by = %s
            """, (user_id,))
            d_rows = cur.fetchall() or []
        elif role == "student" and user_id:
            # Query student uploaded papers first, fallback to bookmarks
            cur.execute("SELECT created_at FROM papers WHERE uploaded_by = %s", (user_id,))
            p_rows = cur.fetchall() or []
            if not p_rows:
                cur.execute("SELECT created_at FROM bookmarks WHERE user_id = %s", (user_id,))
                p_rows = cur.fetchall() or []
            cur.execute("SELECT downloaded_at FROM downloads WHERE user_id = %s", (user_id,))
            d_rows = cur.fetchall() or []
        else:
            cur.execute("SELECT created_at FROM papers")
            p_rows = cur.fetchall() or []
            cur.execute("SELECT downloaded_at FROM downloads")
            d_rows = cur.fetchall() or []
    except Exception:
        pass

    has_data = len(p_rows) > 0 or len(d_rows) > 0

    if not has_data:
        # Elegant, professional empty state when user has no uploads/views yet
        empty_html = f"""
        <div style="background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%); border: 1.5px dashed #CBD5E1; border-radius: 14px; padding: 26px 20px; text-align: center; margin: 4px 0;">
            <div style="width: 52px; height: 52px; border-radius: 50%; background: {primary_light}; color: {primary}; display: inline-flex; align-items: center; justify-content: center; margin-bottom: 12px;">
                <span class="material-symbols-rounded" style="font-size: 28px;">insights</span>
            </div>
            <div style="font-size: 16px; font-weight: 750; color: #0F172A; margin-bottom: 6px;">No View & Citation Trends Recorded Yet</div>
            <div style="font-size: 13px; color: #64748B; max-width: 480px; margin: 0 auto 18px; line-height: 1.5;">
                Trends will automatically populate once your research papers receive views, downloads, and citations across institutional networks.
            </div>
            <div style="display: flex; justify-content: center; gap: 14px; flex-wrap: wrap;">
                <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 10px 16px; text-align: left; min-width: 130px; box-shadow: 0 2px 6px rgba(0,0,0,0.03);">
                    <div style="font-size: 10.5px; font-weight: 750; color: #94A3B8; text-transform: uppercase;">Step 1</div>
                    <div style="font-size: 13px; font-weight: 700; color: #1E293B; margin-top: 2px;">Upload Paper</div>
                </div>
                <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 10px 16px; text-align: left; min-width: 130px; box-shadow: 0 2px 6px rgba(0,0,0,0.03);">
                    <div style="font-size: 10.5px; font-weight: 750; color: #94A3B8; text-transform: uppercase;">Step 2</div>
                    <div style="font-size: 13px; font-weight: 700; color: #1E293B; margin-top: 2px;">Peer Approval</div>
                </div>
                <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 10px 16px; text-align: left; min-width: 130px; box-shadow: 0 2px 6px rgba(0,0,0,0.03);">
                    <div style="font-size: 10.5px; font-weight: 750; color: #94A3B8; text-transform: uppercase;">Step 3</div>
                    <div style="font-size: 13px; font-weight: 700; color: #1E293B; margin-top: 2px;">Track Trends</div>
                </div>
            </div>
        </div>
        """
        st.markdown(empty_html, unsafe_allow_html=True)
        if role == "faculty":
            col_b1, col_b2, col_b3 = st.columns([1, 2, 1])
            with col_b2:
                if st.button("Submit Your First Research Paper", icon=":material/upload_file:", key="btn_empty_upload", type="primary", use_container_width=True):
                    st.session_state["_nav"] = "Upload Paper"
                    st.rerun()
        return

    # Real data aggregation by month
    from collections import defaultdict
    from datetime import datetime
    months_map = defaultdict(lambda: {"uploads": 0, "downloads": 0})

    for r in p_rows:
        dt = r.get("created_at")
        if isinstance(dt, str):
            try:
                dt = datetime.fromisoformat(dt[:19])
            except Exception:
                dt = None
        if dt:
            months_map[dt.strftime("%b %Y")]["uploads"] += 1

    for r in d_rows:
        dt = r.get("downloaded_at")
        if isinstance(dt, str):
            try:
                dt = datetime.fromisoformat(dt[:19])
            except Exception:
                dt = None
        if dt:
            months_map[dt.strftime("%b %Y")]["downloads"] += 1

    sorted_keys = sorted(months_map.keys())
    all_months = sorted_keys if len(sorted_keys) >= 3 else ["May 2026", "Jun 2026", "Jul 2026", "Aug 2026", "Sep 2026"] + sorted_keys
    raw_uploads = [months_map[m]["uploads"] for m in all_months]
    raw_downloads = [months_map[m]["downloads"] for m in all_months]

    # Single-click range & offset movement calculation
    active_range = st.session_state.get("chart_range", "All")
    offset = st.session_state.get("graph_offset", 0)

    if active_range == "3M" and len(all_months) > 3:
        w_size = 3
    elif active_range == "6M" and len(all_months) > 6:
        w_size = 6
    else:
        w_size = len(all_months)

    max_start = max(0, len(all_months) - w_size)
    start_idx = max(0, min(max_start, max_start + offset))
    end_idx = min(len(all_months), start_idx + w_size)

    x_months = all_months[start_idx:end_idx]
    y_uploads = raw_uploads[start_idx:end_idx]
    y_downloads = raw_downloads[start_idx:end_idx]

    if HAS_PLOTLY:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=x_months,
            y=y_uploads,
            mode='lines+markers',
            name='Paper Publications',
            line=dict(color=primary, width=3.5, shape='spline'),
            fill='tozeroy',
            fillcolor='rgba(47, 130, 145, 0.15)',
            marker=dict(size=7, color=primary, line=dict(width=2, color='#FFFFFF')),
            hovertemplate='<b>%{x}</b><br>Publications: <b>%{y}</b><extra></extra>'
        ))
        if any(y_downloads):
            fig.add_trace(go.Scatter(
                x=x_months,
                y=y_downloads,
                mode='lines+markers',
                name='Views & Downloads',
                line=dict(color='#0284C7', width=2.5, shape='spline', dash='dot'),
                marker=dict(size=6, color='#0284C7', line=dict(width=1.5, color='#FFFFFF')),
                hovertemplate='<b>%{x}</b><br>Downloads: <b>%{y}</b><extra></extra>'
            ))
        fig.update_layout(
            autosize=True,
            height=235,
            margin=dict(l=30, r=20, t=20, b=25),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            dragmode='pan',  # Enables single click & drag to move/pan the graph canvas immediately!
            hovermode='x unified',
            hoverlabel=dict(bgcolor='#0F172A', font_size=12, font_family='Plus Jakarta Sans, sans-serif', font_color='#FFFFFF'),
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1, font=dict(size=11, color='#475569')),
            xaxis=dict(showgrid=False, linecolor='#E2E8F0', tickfont=dict(size=11, color='#64748B'), fixedrange=False),
            yaxis=dict(showgrid=True, gridcolor='#F1F5F9', zeroline=False, tickfont=dict(size=11, color='#64748B'), fixedrange=False),
        )
        nonce = st.session_state.get("chart_key_nonce", 0)
        st.plotly_chart(
            fig,
            key=f"growth_chart_{role or 'all'}_{nonce}",
            use_container_width=True,
            config={
                'displayModeBar': 'hover',
                'displaylogo': False,
                'scrollZoom': True, 'modeBarButtonsToRemove': ['lasso2d', 'select2d'],
                'toImageButtonOptions': {'format': 'png', 'filename': 'research_growth_chart'}
            }
        )
    else:
        st.info("Interactive charts available with Plotly.")

def render_donut_chart(title="Top Paper Categories", center_text="Total Papers", user_id=None, role=None):
    """
    Renders an interactive Plotly donut chart of paper categories from real DB data.
    Provides cursor hover tooltips with exact counts and percentages.
    """
    theme = get_current_theme()
    primary = theme["primary"]

    if user_id is None:
        user_id = st.session_state.get("user_id")
    if role is None:
        role = st.session_state.get("user_role")

    labels = []
    values = []
    try:
        from database.connection import get_connection
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        if role == "faculty" and user_id:
            cur.execute("""
                SELECT paper_type, COUNT(*) as cnt 
                FROM papers 
                WHERE uploaded_by = %s 
                GROUP BY paper_type 
                ORDER BY cnt DESC
            """, (user_id,))
            rows = cur.fetchall() or []
            if not rows:
                cur.execute("""
                    SELECT paper_type, COUNT(*) as cnt 
                    FROM papers 
                    GROUP BY paper_type 
                    ORDER BY cnt DESC
                """)
                rows = cur.fetchall() or []
        elif role == "student" and user_id:
            cur.execute("""
                SELECT paper_type, COUNT(*) as cnt 
                FROM papers 
                WHERE uploaded_by = %s 
                GROUP BY paper_type 
                ORDER BY cnt DESC
            """, (user_id,))
            rows = cur.fetchall() or []
            if not rows:
                cur.execute("""
                    SELECT paper_type, COUNT(*) as cnt 
                    FROM papers 
                    GROUP BY paper_type 
                    ORDER BY cnt DESC
                """)
                rows = cur.fetchall() or []
        else:
            cur.execute("""
                SELECT paper_type, COUNT(*) as cnt 
                FROM papers 
                GROUP BY paper_type 
                ORDER BY cnt DESC
            """)
            rows = cur.fetchall() or []

        for r in rows:
            pt = (r.get("paper_type") or "Other").replace("_", " ").title()
            labels.append(pt)
            values.append(r.get("cnt", 0))
    except Exception:
        pass

    if not values or sum(values) == 0:
        empty_html = f"""
        <div style="background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%); border: 1.5px dashed #CBD5E1; border-radius: 12px; padding: 22px 16px; text-align: center; margin: 4px 0;">
            <div style="font-size: 14px; font-weight: 700; color: #0F172A;">No Paper Categories Yet</div>
            <div style="font-size: 12px; color: #64748B; margin-top: 4px;">Distribution appears once papers are categorized in the repository.</div>
        </div>
        """
        st.markdown(empty_html, unsafe_allow_html=True)
        return

    total_val = sum(values)
    colors = [primary, "#165367", "#0284C7", "#7C3AED", "#D97706", "#64748B"]

    if HAS_PLOTLY:
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.62,
            marker=dict(colors=colors[:len(labels)], line=dict(color='#FFFFFF', width=2.5)),
            textinfo='percent',
            textposition='inside',
            hoverinfo='label+value+percent',
            hovertemplate='<b>%{label}</b><br>Papers: <b>%{value}</b> (%{percent})<extra></extra>'
        )])
        fig.update_layout(
            autosize=True,
            height=205,
            margin=dict(l=10, r=10, t=10, b=10),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            showlegend=True,
            legend=dict(
                orientation='v',
                yanchor='middle',
                y=0.5,
                xanchor='left',
                x=1.02,
                font=dict(size=11, color='#334155', family='Plus Jakarta Sans, sans-serif')
            ),
            annotations=[dict(
                text=f"<span style='font-size:10px;color:#64748B;font-weight:600;'>TOTAL</span><br><b style='font-size:16px;color:#0F172A;'>{total_val:,}</b>",
                x=0.5, y=0.5,
                font_size=13,
                showarrow=False
            )]
        )
        nonce = st.session_state.get("chart_key_nonce", 0)
        st.plotly_chart(
            fig,
            key=f"donut_chart_{role or 'all'}_{nonce}",
            use_container_width=True,
            config={'displayModeBar': 'hover', 'displaylogo': False}
        )
    else:
        for lbl, val in zip(labels, values):
            pct = (val / total_val) * 100
            st.markdown(f"**{lbl}**: {val} ({pct:.1f}%)")

def render_traffic_progress(user_id=None, role=None):
    """
    Renders real department-wise research paper counts and percentage share from DB.
    """
    theme = get_current_theme()
    primary = theme["primary"]
    palette = [primary, "#165367", "#0284C7", "#7C3AED", "#D97706", "#94A3B8"]

    sources = []
    try:
        from database.connection import get_connection
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("""
            SELECT d.dept_name, COUNT(p.paper_id) as cnt
            FROM departments d
            LEFT JOIN papers p ON d.dept_id = p.dept_id
            GROUP BY d.dept_id, d.dept_name
            ORDER BY cnt DESC
        """)
        rows = cur.fetchall() or []
        total_p = sum(r["cnt"] for r in rows)
        for i, r in enumerate(rows):
            cnt = r["cnt"]
            pct = int((cnt / total_p * 100)) if total_p > 0 else 0
            color = palette[i % len(palette)]
            sources.append((r["dept_name"], f"{cnt} papers ({pct}%)", pct, color))
    except Exception:
        pass

    if not sources:
        st.caption("No department data recorded yet.")
        return

    for name, pct_str, pct_val, color in sources:
        html = f"""
        <div style="margin-bottom: 12px;">
            <div style="display: flex; justify-content: space-between; font-size: 13px; font-weight: 600; color: #334155;">
                <span style="white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:260px;" title="{html_escape(name)}">{html_escape(name)}</span>
                <span style="color:#0F172A;font-weight:700;">{pct_str}</span>
            </div>
            <div style="background: #F1F5F9; border-radius: 8px; height: 9px; width: 100%; overflow: hidden; margin-top: 5px; box-shadow: inset 0 1px 2px rgba(0,0,0,0.06);">
                <div style="height: 100%; width: {max(pct_val, 2)}%; background: {color}; border-radius: 8px; transition: width 0.4s ease;"></div>
            </div>
        </div>
        """
        st.markdown(html, unsafe_allow_html=True)

def render_calendar_widget():
    """
    Upcoming Research Deadlines & Academic Milestones.
    Professional layout with clear fonts, date badges, and countdown indicators.
    """
    theme = get_current_theme()
    primary = theme["primary"]

    header_html = f"""
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px;">
        <div style="display: flex; align-items: center; gap: 10px;">
            <div style="width: 38px; height: 38px; border-radius: 10px; background: rgba(47, 130, 145, 0.12); display: flex; align-items: center; justify-content: center; color: {primary};">
                <span class="material-symbols-rounded" style="font-size: 22px;">event_upcoming</span>
            </div>
            <div>
                <div style="font-size: 17px; font-weight: 800; color: #0F172A; letter-spacing: -0.01em;">Upcoming Research Deadlines</div>
                <div style="font-size: 12.5px; color: #64748B; margin-top: 1px;">Conference submissions, journal revisions & camera-ready milestones</div>
            </div>
        </div>
        <div style="font-size: 12px; font-weight: 750; color: #334155; background: #F1F5F9; border: 1px solid #E2E8F0; padding: 4px 12px; border-radius: 8px;">Q1 2025</div>
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)

    deadlines = [
        {
            "month": "JAN",
            "day": "15",
            "title": "IEEE Conference on Machine Learning (ICML 2025)",
            "milestone": "Full Research Paper Submission Deadline",
            "track": "Track: Deep Learning & Neural Architectures · Vienna, Austria",
            "badge": "5 Days Left",
            "badge_bg": "#FEF2F2",
            "badge_color": "#DC2626",
            "border_color": "#F87171",
            "date_bg": "#FEF2F2",
            "date_border": "#FCA5A5",
            "date_text": "#DC2626",
            "dot_color": "#DC2626"
        },
        {
            "month": "JAN",
            "day": "22",
            "title": "Springer Journal of Cloud Computing & Big Data",
            "milestone": "Revised Manuscript & Review Responses Due",
            "track": "Indexed in SCI Q1 · Fast-Track Peer Review Cycle",
            "badge": "12 Days Left",
            "badge_bg": "#FFFBEB",
            "badge_color": "#D97706",
            "border_color": "#FBBF24",
            "date_bg": "#FFFBEB",
            "date_border": "#FDE68A",
            "date_text": "#D97706",
            "dot_color": "#D97706"
        },
        {
            "month": "FEB",
            "day": "05",
            "title": "ACM Transactions on Autonomous & Intelligent Systems",
            "milestone": "Camera-Ready Final Submission & Author Copyright",
            "track": "ACM Digital Library & IEEE Xplore Joint Archival",
            "badge": "26 Days Left",
            "badge_bg": "#F0FDF4",
            "badge_color": "#16A34A",
            "border_color": "#4ADE80",
            "date_bg": "#F0FDF4",
            "date_border": "#BBF7D0",
            "date_text": "#16A34A",
            "dot_color": "#16A34A"
        }
    ]

    for d in deadlines:
        card_html = f"""
        <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-left: 4.5px solid {d['border_color']}; border-radius: 13px; padding: 13px 16px; margin-bottom: 11px; display: flex; align-items: center; justify-content: space-between; gap: 14px; box-shadow: 0 2px 8px rgba(0,0,0,0.03); transition: transform 0.15s ease, box-shadow 0.15s ease;">
            <div style="display: flex; align-items: center; gap: 14px; min-width: 0;">
                <div style="background: {d['date_bg']}; border: 1.5px solid {d['date_border']}; border-radius: 11px; width: 56px; height: 56px; display: flex; flex-direction: column; align-items: center; justify-content: center; flex-shrink: 0;">
                    <span style="font-size: 11px; font-weight: 800; text-transform: uppercase; color: {d['date_text']}; letter-spacing: 0.5px; line-height: 1;">{d['month']}</span>
                    <span style="font-size: 21px; font-weight: 850; color: #0F172A; line-height: 1.15; margin-top: 2px;">{d['day']}</span>
                </div>
                <div style="min-width: 0;">
                    <div style="font-size: 15.5px; font-weight: 750; color: #0F172A; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; letter-spacing: -0.01em;">{d['title']}</div>
                    <div style="font-size: 13px; font-weight: 600; color: #334155; margin-top: 3px;">
                        <span style="color: {primary}; font-weight: 700;">●</span> {d['milestone']}
                    </div>
                    <div style="font-size: 12px; color: #64748B; margin-top: 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{d['track']}</div>
                </div>
            </div>
            <div style="white-space: nowrap; flex-shrink: 0;">
                <span style="font-size: 12.5px; font-weight: 750; background: {d['badge_bg']}; color: {d['badge_color']}; padding: 6px 14px; border-radius: 20px; border: 1px solid {d['border_color']}; display: inline-flex; align-items: center; gap: 6px;">
                    <span style="width: 7px; height: 7px; border-radius: 50%; background: {d['dot_color']}; display: inline-block;"></span>
                    {d['badge']}
                </span>
            </div>
        </div>
        """
        st.markdown(card_html, unsafe_allow_html=True)

def render_customizer_panel():
    st.markdown("### Customize UI & Theme")
    st.caption("Personalize colors, card styling, and sidebar preferences to match your brand.")

    col1, col2 = st.columns(2)
    with col1:
        selected_theme = st.selectbox(
            "Select Accent Theme",
            options=list(THEMES.keys()),
            index=list(THEMES.keys()).index(st.session_state.get("theme_name", "Ocean Teal (Default)"))
        )
        if selected_theme != st.session_state.get("theme_name"):
            st.session_state["theme_name"] = selected_theme
            st.rerun()

    with col2:
        radius = st.selectbox(
            "Card Corner Style",
            options=["16px", "24px (Extra Pill)", "8px (Compact Sharp)"],
            index=0 if st.session_state.get("card_radius") == "16px" else (1 if "24px" in st.session_state.get("card_radius", "") else 2)
        )
        if radius.split()[0] != st.session_state.get("card_radius"):
            st.session_state["card_radius"] = radius.split()[0]
            st.rerun()

    st.markdown("---")
    brand = st.text_input("Brand Logo Text", value=st.session_state.get("brand_logo", "RPRMS"))
    if brand != st.session_state.get("brand_logo"):
        st.session_state["brand_logo"] = brand
        st.rerun()

    st.success("Theme settings saved & applied live!")


def resolve_pdf_path(raw_path: str) -> str | None:
    """Bulletproof resolution of paper PDF file on disk."""
    if not raw_path:
        return None
    base_app = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    candidates = [
        raw_path,
        os.path.join(base_app, raw_path),
        os.path.join("rprms_app", raw_path),
        os.path.join(base_app, "uploads", "papers", os.path.basename(raw_path)),
        os.path.join("uploads", "papers", os.path.basename(raw_path)),
        os.path.abspath(raw_path),
    ]
    for c in candidates:
        if os.path.exists(c) and os.path.isfile(c):
            return os.path.abspath(c)
    return None


def render_inline_pdf_viewer(
    file_path: str,
    file_name: str = "manuscript.pdf",
    file_size: int = 0,
    key: str = "pdf_view",
    height: str = "680px",
    allow_download: bool = True
) -> bool:
    """
    Renders an embedded, interactive PDF research paper viewer inside Streamlit.
    Features:
      - Embedded base64 iframe with browser PDF controls (zoom, page flip, search).
      - Quick download button.
      - File size badge and clean layout.
    """
    resolved_path = resolve_pdf_path(file_path)
    if not resolved_path:
        st.warning("⚠️ Manuscript PDF file could not be read from server storage.")
        return False

    try:
        with open(resolved_path, "rb") as f:
            pdf_bytes = f.read()
    except Exception as e:
        st.warning(f"⚠️ Unable to open PDF file: {e}")
        return False

    sz_mb = (file_size or os.path.getsize(resolved_path)) / (1024 * 1024)
    display_name = file_name or os.path.basename(resolved_path)

    col_info, col_dl = st.columns([3, 1.5], vertical_alignment="center")
    with col_info:
        st.markdown(
            f"<div style='font-size: 14px; font-weight: 700; color: #0F172A;'>"
            f"<span class='material-symbols-rounded' style='font-size: 20px; vertical-align: middle; color: #2F8291; margin-right: 6px;'>description</span>"
            f"{display_name} <span style='font-size: 12px; font-weight: 600; color: #64748B;'>({sz_mb:.2f} MB)</span></div>",
            unsafe_allow_html=True
        )
    with col_dl:
        if allow_download:
            st.download_button(
                label=":material/download: Download Full PDF",
                data=pdf_bytes,
                file_name=display_name,
                mime="application/pdf",
                key=f"dl_inline_{key}",
                type="secondary",
                use_container_width=True
            )

    b64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")
    pdf_iframe = f"""
    <div style="margin-top: 10px; border-radius: 12px; overflow: hidden; border: 1.5px solid #CBD5E1; box-shadow: 0 4px 18px rgba(15,23,42,0.08);">
        <iframe src="data:application/pdf;base64,{b64_pdf}#toolbar=1&navpanes=1" width="100%" height="{height}" type="application/pdf" style="border: none; display: block;"></iframe>
    </div>
    """
    st.markdown(pdf_iframe, unsafe_allow_html=True)
    st.caption(":material/info: Use the reader controls above to scroll, zoom, search text, and read all pages of this research paper.")
    return True
