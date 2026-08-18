import base64
import hashlib
import re
import unicodedata
from io import BytesIO
from html import escape
import requests
import os
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle,
)
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
)
# FASTAPI URL — set FASTAPI_URL in Streamlit Cloud secrets to point to your Render backend
FASTAPI_URL = os.getenv(
    "FASTAPI_URL",
    "https://ai-interview-studio-7.onrender.com",
).rstrip("/")
# PAGE CONFIG
st.set_page_config(
    page_title="AI Interview Studio",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)
# FRONTEND THEME — DARK AI STUDIO
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    :root {
        --bg: #080b12;
        --bg-2: #0d111b;
        --surface: #111722;
        --surface-2: #151c29;
        --surface-3: #1a2332;
        --border: #263143;
        --border-hover: #3b4a63;
        --text: #f5f7fb;
        --text-2: #c7d0df;
        --muted: #8e9aae;
        --blue: #5b8cff;
        --blue-2: #7aa2ff;
        --cyan: #36c5f0;
        --green: #22c55e;
        --orange: #f59e0b;
        --red: #ef4444;
        --shadow: 0 16px 42px rgba(0, 0, 0, .28);
        --shadow-soft: 0 8px 24px rgba(0, 0, 0, .18);
    }

    /* ===============================
       GLOBAL DARK BACKGROUND
       =============================== */
    html, body {
        background: var(--bg) !important;
    }
    body,
    [data-testid="stAppViewContainer"],
    [data-testid="stSidebar"] {
        font-family: 'Inter', sans-serif !important;
    }
    /* Remove only Streamlit's top chrome, not the application containers. */
    header[data-testid="stHeader"] {
        display: none !important;
    }
    div[data-testid="stToolbar"] {
        display: none !important;
    }
    #MainMenu {
        visibility: hidden !important;
        display: none !important;
    }
    footer {
        visibility: hidden !important;
        display: none !important;
    }
    .block-container {
        font-family: 'Inter', sans-serif !important;
    }
    /* Keep Streamlit's icon ligature fonts intact. */
    .material-icons,
    .material-symbols-rounded,
    .material-symbols-outlined,
    [data-testid="stIcon"],
    [data-testid="stIcon"] *,
    span[class*="material-symbols"],
    i[class*="material-icons"] {
        font-family: "Material Symbols Rounded", "Material Symbols Outlined",
                     "Material Icons", sans-serif !important;
    }
    [data-testid="stAppViewContainer"],
    [data-testid="stAppViewContainer"] > .main,
    [data-testid="stMain"],
    section[data-testid="stMain"] {
        background:
            radial-gradient(circle at 78% 5%, rgba(91,140,255,.08), transparent 24%),
            radial-gradient(circle at 8% 85%, rgba(54,197,240,.05), transparent 26%),
            linear-gradient(180deg, #080b12 0%, #0b0f17 100%) !important;
        color: var(--text) !important;
    }
    [data-testid="stHeader"] {
        background: rgba(8,11,18,.78) !important;
    }
    .block-container {
        max-width: 1440px !important;
        padding-top: 2.1rem !important;
        padding-right: 2rem !important;
        padding-bottom: 5rem !important;
        position: relative;
        z-index: 1;
    }
    /* Consistent vertical rhythm between every Streamlit element. */
    [data-testid="stVerticalBlock"] > div {
        margin-bottom: 0.35rem;
    }
    [data-testid="stHorizontalBlock"] {
        gap: 1.25rem !important;
    }
    [data-testid="stColumn"] {
        min-width: 0 !important;
    }
    /* Prevent custom HTML cards from sitting against the next widget. */
    .card-v3,
    .question-v3,
    .report-highlight,
    .live-v3,
    .question-panel-v3,
    .soft-v3 {
        margin-bottom: 18px !important;
    }
    /* Keep headings separated from the controls that follow them. */
    [data-testid="stMain"] h1,
    [data-testid="stMain"] h2,
    [data-testid="stMain"] h3,
    [data-testid="stMain"] h4 {
        margin-top: 0.35rem !important;
        margin-bottom: 0.75rem !important;
    }
    [data-testid="stMain"] hr {
        margin: 1.25rem 0 !important;
        border-color: #263143 !important;
    }
    /* Extra room around columns containing upload/input controls. */
    [data-testid="stHorizontalBlock"] [data-testid="stVerticalBlock"] {
        padding-bottom: 0.55rem;
    }
    [data-testid="stAppViewContainer"] {
        min-height: 100vh;
    }
    /* ===============================
       SIDEBAR
       =============================== */
    section[data-testid="stSidebar"] {
        background:
            linear-gradient(180deg, #0a0e16 0%, #0e1420 100%) !important;
        border-right: 1px solid #1f2937 !important;
    }
    section[data-testid="stSidebar"] * {
        color: #e6ebf3 !important;
    }
    section[data-testid="stSidebar"] [data-testid="stRadio"] label {
        padding: 8px 10px !important;
        border-radius: 10px !important;
        transition: .18s ease;
    }
    section[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
        background: rgba(255,255,255,.05) !important;
        transform: translateX(2px);
    }
    /* ===============================
       TEXT
       =============================== */
    section[data-testid="stMain"] h1,
    section[data-testid="stMain"] h2,
    section[data-testid="stMain"] h3,
    section[data-testid="stMain"] h4,
    section[data-testid="stMain"] h5 {
        color: var(--text) !important;
        -webkit-text-fill-color: var(--text) !important;
    }
    section[data-testid="stMain"] p,
    section[data-testid="stMain"] label,
    section[data-testid="stMain"] small {
        color: var(--muted) !important;
        font-family: 'Inter', sans-serif !important;
    }
    /* ===============================
       HERO
       =============================== */
    .hero-v3 {
        position: relative;
        overflow: hidden;
        background:
            radial-gradient(circle at 87% 18%, rgba(91,140,255,.25), transparent 27%),
            radial-gradient(circle at 12% 90%, rgba(54,197,240,.10), transparent 24%),
            linear-gradient(135deg, #101827 0%, #17243a 58%, #14294a 100%);
        border: 1px solid rgba(122,162,255,.18);
        border-radius: 24px;
        padding: 32px 34px;
        margin-bottom: 18px;
        box-shadow: 0 22px 55px rgba(0,0,0,.32);
    }
    .hero-v3::before {
        content: "";
        position: absolute;
        width: 340px;
        height: 340px;
        right: -140px;
        top: -160px;
        border-radius: 50%;
        border: 1px solid rgba(122,162,255,.11);
        box-shadow: 0 0 90px rgba(91,140,255,.08);
    }
    .hero-v3::after {
        content: "";
        position: absolute;
        width: 7px;
        height: 7px;
        right: 78px;
        top: 72px;
        border-radius: 50%;
        background: #6ea8ff;
        box-shadow:
            0 0 0 5px rgba(91,140,255,.10),
            0 0 22px rgba(91,140,255,.65);
        animation: pulse-dot 2.4s infinite;
    }
    .hero-v3 .kicker {
        color: #8fa9cf !important;
        font-size: 11px;
        font-weight: 800;
        letter-spacing: .16em;
        text-transform: uppercase;
        margin-bottom: 8px;
    }
    .hero-v3 .title {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        font-size: 32px;
        font-weight: 800;
        line-height: 1.14;
        letter-spacing: -.04em;
        margin-bottom: 8px;
    }
    .hero-v3 .subtitle {
        color: #aebbd0 !important;
        -webkit-text-fill-color: #aebbd0 !important;
        max-width: 870px;
        line-height: 1.6;
        font-size: 14px;
    }
    /* ===============================
       INTERACTION / GESTURES
       =============================== */
    .card-v3,
    .question-v3,
    .question-panel-v3,
    [data-testid="stMetric"],
    [data-testid="stExpander"] {
        transition:
            transform .20s ease,
            border-color .20s ease,
            box-shadow .20s ease,
            background .20s ease;
    }
    .card-v3:hover,
    .question-v3:hover,
    .question-panel-v3:hover,
    [data-testid="stMetric"]:hover {
        transform: translateY(-3px);
        border-color: var(--border-hover) !important;
        box-shadow: var(--shadow);
    }
    .flow-item-v3 {
        transition: .18s ease;
    }
    .flow-item-v3:hover {
        transform: translateY(-2px);
        border-color: #3d5277 !important;
        background: #172031 !important;
    }
    .stButton > button {
        transition:
            transform .16s ease,
            box-shadow .16s ease,
            border-color .16s ease,
            background .16s ease !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 10px 22px rgba(0,0,0,.22) !important;
    }
    .stButton > button:active {
        transform: translateY(0) scale(.985) !important;
    }
    @keyframes pulse-dot {
        0%, 100% {
            opacity: .6;
            transform: scale(1);
        }
        50% {
            opacity: 1;
            transform: scale(1.15);
        }
    }
    @keyframes soft-glow {
        0%, 100% {
            box-shadow: 0 0 0 rgba(91,140,255,0);
        }
        50% {
            box-shadow: 0 0 30px rgba(91,140,255,.12);
        }
    }
    /* ===============================
       WORKFLOW
       =============================== */
    .flow-v3 {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
        margin-bottom: 18px;
    }
    .flow-item-v3 {
        display: inline-flex;
        align-items: center;
        gap: 7px;
        padding: 7px 11px;
        border-radius: 999px;
        background: #111722;
        color: #9eabc0 !important;
        border: 1px solid #253043;
        font-size: 12px;
        font-weight: 700;
        box-shadow: var(--shadow-soft);
    }
    .flow-item-v3.active {
        color: #9fc0ff !important;
        background: rgba(91,140,255,.10);
        border-color: rgba(91,140,255,.34);
    }
    .flow-dot-v3 {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background: #65738a;
    }
    .flow-item-v3.active .flow-dot-v3 {
        background: var(--blue);
        box-shadow: 0 0 12px rgba(91,140,255,.7);
    }
    /* ===============================
       CARDS
       =============================== */
    .card-v3 {
        background: linear-gradient(180deg, #111722 0%, #0f151f 100%);
        border: 1px solid #263143;
        border-radius: 18px;
        padding: 20px;
        box-shadow: var(--shadow-soft);
    }
    .card-title-v3 {
        color: #f2f4f7 !important;
        -webkit-text-fill-color: #f2f4f7 !important;
        font-size: 16px;
        font-weight: 800;
        margin-bottom: 4px;
    }
    .card-subtitle-v3 {
        color: #8e9aae !important;
        -webkit-text-fill-color: #8e9aae !important;
        font-size: 13px;
        line-height: 1.55;
    }
    /* ===============================
       INPUTS
       =============================== */
    input,
    textarea,
    select,
    [data-baseweb="input"],
    [data-baseweb="textarea"],
    [data-baseweb="select"] {
        background: #0f151f !important;
        color: #f3f5f8 !important;
        -webkit-text-fill-color: #f3f5f8 !important;
        caret-color: #ffffff !important;
    }
    input::placeholder,
    textarea::placeholder {
        color: #6f7c90 !important;
        -webkit-text-fill-color: #6f7c90 !important;
        opacity: 1 !important;
    }
    [data-testid="stTextInput"] input,
    [data-testid="stTextArea"] textarea {
        background: #0f151f !important;
        color: #f3f5f8 !important;
        -webkit-text-fill-color: #f3f5f8 !important;
        border: 1px solid #2b374a !important;
        border-radius: 11px !important;
        box-shadow: inset 0 1px 0 rgba(255,255,255,.015) !important;
    }
    [data-testid="stTextInput"] input:focus,
    [data-testid="stTextArea"] textarea:focus {
        border-color: #557cc4 !important;
        box-shadow: 0 0 0 3px rgba(91,140,255,.10) !important;
    }
    [data-testid="stTextArea"] textarea {
        min-height: 235px !important;
    }
    [data-testid="stTextInput"] label,
    [data-testid="stTextArea"] label,
    [data-testid="stSelectbox"] label,
    [data-testid="stSlider"] label,
    [data-testid="stFileUploader"] label {
        color: #c5cfde !important;
        margin-bottom: 6px !important;
        -webkit-text-fill-color: #c5cfde !important;
        font-weight: 700 !important;
    }
    [data-testid="stSelectbox"] [data-baseweb="select"] {
        background: #0f151f !important;
        border: 1px solid #2b374a !important;
        border-radius: 11px !important;
    }
    [data-testid="stSelectbox"] [data-baseweb="select"] * {
        background: #0f151f !important;
        color: #f3f5f8 !important;
        -webkit-text-fill-color: #f3f5f8 !important;
    }
    /* ===============================
       UPLOAD
       =============================== */
    [data-testid="stFileUploader"] {
        background: transparent !important;
        border: 0 !important;
    }
    [data-testid="stFileUploaderDropzone"] {
        background: #0f151f !important;
        border: 1px dashed #344158 !important;
        border-radius: 14px !important;
        min-height: 116px !important;
        padding: 14px !important;
        margin-top: 6px !important;
    }
    [data-testid="stFileUploaderDropzone"] * {
        color: #aab6c8 !important;
        -webkit-text-fill-color: #aab6c8 !important;
    }
    [data-testid="stFileUploaderDropzone"] button {
        background: #162136 !important;
        color: #a9c7ff !important;
        border: 1px solid #344b71 !important;
        border-radius: 9px !important;
    }
    [data-testid="stFileUploaderDropzoneInstructions"] {
        color: #8e9aae !important;
    }
    [data-testid="stFileUploaderDropzoneInstructions"] span {
        color: #8e9aae !important;
        font-family: 'Inter', sans-serif !important;
    }
    [data-testid="stFileUploaderDropzone"] small {
        color: #6f7c90 !important;
        font-family: 'Inter', sans-serif !important;
    }
    /* Keep the native Streamlit upload icon font intact.
       The previous global span rule turned the icon ligature
       "upload" into visible text, producing "uploadpload". */
    [data-testid="stFileUploaderDropzone"] button {
        position: relative !important;
        z-index: 2 !important;
        flex-shrink: 0 !important;
        white-space: nowrap !important;
        overflow: visible !important;
        margin: 0 12px 0 0 !important;
        padding: 8px 14px !important;
        min-width: 96px !important;
    }
    [data-testid="stFileUploaderDropzoneInstructions"] {
        flex: 1 1 auto !important;
        min-width: 0 !important;
        text-align: left !important;
        padding-left: 0 !important;
        white-space: normal !important;
    }
    [data-testid="stFileUploaderDropzone"] {
        display: flex !important;
        align-items: center !important;
        justify-content: flex-start !important;
        gap: 6px !important;
    }
    /* ===============================
       BUTTONS
       =============================== */
    .stButton > button {
        min-height: 44px !important;
        border-radius: 11px !important;
        border: 1px solid #2f3c50 !important;
        background: #141c28 !important;
        color: #d9e1ed !important;
        -webkit-text-fill-color: #d9e1ed !important;
        font-weight: 750 !important;
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #4f7fff, #315ed8) !important;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        border-color: #4f7fff !important;
        box-shadow: 0 10px 24px rgba(49,94,216,.28) !important;
        animation: soft-glow 3s infinite;
    }
    /* ===============================
       METRICS
       =============================== */
    [data-testid="stMetric"] {
        background: #111722 !important;
        border: 1px solid #263143 !important;
        border-radius: 16px !important;
        padding: 15px 17px !important;
        box-shadow: var(--shadow-soft) !important;
    }
    [data-testid="stMetricLabel"] {
        color: #8f9caf !important;
        -webkit-text-fill-color: #8f9caf !important;
    }
    [data-testid="stMetricValue"] {
        color: #f5f7fb !important;
        -webkit-text-fill-color: #f5f7fb !important;
        font-weight: 800 !important;
    }
    /* ===============================
       EXPANDERS
       =============================== */
    [data-testid="stExpander"] {
        background: #111722 !important;
        border: 1px solid #263143 !important;
        border-radius: 14px !important;
        overflow: hidden !important;
        box-shadow: var(--shadow-soft) !important;
    }
    [data-testid="stExpander"] summary,
    [data-testid="stExpander"] summary span {
        color: #d8e0eb !important;
        -webkit-text-fill-color: #d8e0eb !important;
    }
    /* ===============================
       QUESTION CARDS
       =============================== */
    .question-v3 {
        background: linear-gradient(180deg, #111722, #0f151f);
        border: 1px solid #263143;
        border-radius: 16px;
        padding: 19px 20px;
        margin: 11px 0;
        box-shadow: var(--shadow-soft);
    }
    .question-id-v3 {
        color: #7aa2ff !important;
        font-size: 11px;
        font-weight: 800;
        letter-spacing: .12em;
        text-transform: uppercase;
        margin-bottom: 7px;
    }
    .question-text-v3 {
        color: #f5f7fb !important;
        -webkit-text-fill-color: #f5f7fb !important;
        font-size: 16px;
        line-height: 1.62;
        font-weight: 650;
        margin-bottom: 8px;
    }
    .meta-v3 {
        color: #8e9aae !important;
        -webkit-text-fill-color: #8e9aae !important;
        font-size: 12px;
    }
    /* ===============================
       CHIPS
       =============================== */
    .chip-v3 {
        display: inline-block;
        padding: 5px 10px;
        border-radius: 999px;
        margin: 3px 4px 3px 0;
        font-size: 11px;
        font-weight: 800;
    }
    .chip-match {
        color: #7ee2a8 !important;
        background: rgba(34,197,94,.09);
        border: 1px solid rgba(34,197,94,.25);
    }
    .chip-missing {
        color: #ff9d99 !important;
        background: rgba(239,68,68,.09);
        border: 1px solid rgba(239,68,68,.23);
    }
    .chip-partial {
        color: #ffc56b !important;
        background: rgba(245,158,11,.09);
        border: 1px solid rgba(245,158,11,.23);
    }
    /* ===============================
       REPORT
       =============================== */
    .report-highlight {
        background:
            linear-gradient(135deg, rgba(91,140,255,.10), rgba(255,255,255,0)),
            #111722;
        border: 1px solid rgba(91,140,255,.25);
        border-radius: 17px;
        padding: 17px 18px;
        box-shadow: var(--shadow-soft);
    }
    /* ===============================
       LIVE INTERVIEW
       =============================== */
    .live-v3 {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 16px;
        background:
            radial-gradient(circle at 80% 0%, rgba(91,140,255,.17), transparent 27%),
            linear-gradient(135deg, #111722, #14263f);
        border: 1px solid rgba(91,140,255,.18);
        border-radius: 18px;
        padding: 18px 20px;
        box-shadow: var(--shadow);
    }
    .live-v3 * {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
    }
    .live-dot-v3 {
        width: 9px;
        height: 9px;
        background: #22c55e;
        display: inline-block;
        border-radius: 50%;
        margin-right: 7px;
        box-shadow: 0 0 0 4px rgba(34,197,94,.12), 0 0 15px rgba(34,197,94,.45);
        animation: pulse-dot 1.8s infinite;
    }
    .question-panel-v3 {
        background:
            radial-gradient(circle at 92% 10%, rgba(91,140,255,.08), transparent 22%),
            #111722;
        border: 1px solid #2b374a;
        border-radius: 20px;
        padding: 26px;
        min-height: 250px;
        box-shadow: var(--shadow);
        animation: soft-glow 4s infinite;
    }
    .question-label-v3 {
        color: #7aa2ff !important;
        -webkit-text-fill-color: #7aa2ff !important;
        font-size: 11px;
        font-weight: 800;
        letter-spacing: .13em;
        text-transform: uppercase;
        margin-bottom: 13px;
    }
    .question-body-v3 {
        color: #f6f8fb !important;
        -webkit-text-fill-color: #f6f8fb !important;
        font-size: 21px;
        line-height: 1.55;
        font-weight: 750;
    }
    .soft-v3 {
        background: #0f151f;
        border: 1px solid #263143;
        color: #8e9aae !important;
        border-radius: 13px;
        padding: 13px 15px;
        line-height: 1.55;
        font-size: 13px;
    }
    [data-testid="stAudio"] {
        background: #0f151f !important;
        border: 1px solid #263143 !important;
        border-radius: 11px !important;
        margin-top: 12px !important;
        margin-bottom: 18px !important;
    }
    [data-testid="stProgress"] {
        margin: 10px 0 22px !important;
    }
    [data-testid="stAudioInput"] {
        margin-top: 8px !important;
        margin-bottom: 18px !important;
    }
    /* Progress bar */
    [data-testid="stProgress"] > div {
        background: #182131 !important;
    }
    [data-testid="stProgress"] > div > div > div {
        background: linear-gradient(90deg, #4f7fff, #5bc0ff) !important;
    }
    /* Prevent long content from escaping rounded cards. */
    .card-v3,
    .question-v3,
    .report-highlight,
    .live-v3,
    .question-panel-v3 {
        overflow: hidden;
        overflow-wrap: anywhere;
        word-break: normal;
    }
    /* Keep Streamlit widgets inside their columns. */
    [data-testid="stColumn"] > div {
        width: 100% !important;
        max-width: 100% !important;
    }
    /* Avoid negative/overlapping visual rhythm caused by markdown blocks. */
    [data-testid="stMarkdownContainer"] {
        overflow-wrap: anywhere;
    }
    /* ===============================
       RESPONSIVE
       =============================== */
    @media (max-width: 900px) {
        .hero-v3 {
            padding: 24px;
            border-radius: 18px;
        }
        .hero-v3 .title {
            font-size: 25px;
        }
        .question-body-v3 {
            font-size: 18px;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)
def ui_hero(kicker: str, title: str, subtitle: str):
    st.markdown(
        f"""
        <div class="hero-v3">
            <div class="kicker">{kicker}</div>
            <div class="title">{title}</div>
            <div class="subtitle">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
def ui_section(title: str, subtitle: str = ""):
    st.markdown(
        f"""
        <div class="card-v3">
            <div class="card-title-v3">{title}</div>
            <div class="card-subtitle-v3">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
def ui_workflow_steps(steps, active_index=0):
    html = '<div class="flow-v3">'
    for i, label in enumerate(steps):
        active = " active" if i == active_index else ""
        html += (
            f'<div class="flow-item-v3{active}">'
            f'<span class="flow-dot-v3"></span>{label}</div>'
        )
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

# SESSION STATE

def initialize_session_state():

    defaults = {
        # NAVIGATION
        "page": "Question Generator",
        # QUESTION GENERATOR
        "gap_result": None,
        "question_result": None,
        # AI INTERVIEW
        "interview_started": False,
        "interview_role": "AI Engineer",
        "interview_difficulty": "Medium",
        "ai_interview_id": None,
        "ai_current_question": "",
        "ai_question_number": 0,
        "ai_total_questions": 5,
        "ai_audio": None,
        "ai_transcript": "",
        "ai_evaluation": "",
        "ai_score": 0,
        "ai_processed_audio_hash": None,
        # FINAL REPORT
        "ai_final_report": "",
        "ai_final_score": 0,
        "ai_completed_questions": 0,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# FASTAPI HEALTH

def check_fastapi():
    try:
        response = requests.get(
            f"{FASTAPI_URL}/health",
            timeout=5,
        )
        return response.ok
    except requests.RequestException:
        return False

# DOCUMENT ID

def create_document_id(
    text: str,
    prefix: str,
) -> str:
    digest = hashlib.sha256(
        text.encode("utf-8")
    ).hexdigest()[:16]
    return f"{prefix}_{digest}"

# RESUME TEXT EXTRACTION

def extract_resume_text(
    uploaded_file,
):
    if uploaded_file is None:
        return ""
    filename = (
        uploaded_file.name.lower()
    )
    # TXT / MD
    if filename.endswith(
        (
            ".txt",
            ".md",
        )
    ):
        return (
            uploaded_file
            .read()
            .decode(
                "utf-8",
                errors="ignore",
            )
        )
    # PDF
    if filename.endswith(".pdf"):
        try:
            import pypdf
            reader = pypdf.PdfReader(
                uploaded_file
            )
            pages = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    pages.append(
                        text
                    )
            return "\n".join(
                pages
            )
        except Exception as e:
            st.error(
                f"Resume PDF extraction failed: {e}"
            )
            return ""
    return ""

# QUESTION GENERATOR API

def generate_questions_with_api(
    resume_text: str,
    job_description: str,
    job_title: str,
    difficulty: str,
    num_questions: int,
):
    response = requests.post(
        f"{FASTAPI_URL}/api/interview/generate",
        json={
            "resume_text": resume_text,
            "job_description": job_description,
            "job_title": job_title,
            "difficulty": difficulty,
            "num_questions": num_questions,
        },
        timeout=300,
    )
    response.raise_for_status()
    return response.json()

# AI INTERVIEW API

def start_ai_interview(
    role: str,
    difficulty: str,
):
    response = requests.post(
        f"{FASTAPI_URL}/api/ai-interview/start",
        data={
            "role": role,
            "difficulty": difficulty,
        },
        timeout=180,
    )
    response.raise_for_status()
    return response.json()

def submit_ai_answer(
    interview_id: str,
    audio_file,
):
    audio_bytes = (
        audio_file.getvalue()
    )
    response = requests.post(
        f"{FASTAPI_URL}/api/ai-interview/answer",
        data={
            "interview_id": interview_id,
        },
        files={
            "audio": (
                "answer.wav",
                audio_bytes,
                "audio/wav",
            )
        },
        timeout=300,
    )
    response.raise_for_status()
    return response.json()

def quit_ai_interview(
    interview_id: str,
):
    response = requests.post(
        f"{FASTAPI_URL}/api/ai-interview/quit",
        params={
            "interview_id": interview_id,
        },
        timeout=120,
    )
    response.raise_for_status()
    return response.json()

# SIDEBAR

def render_sidebar():
    st.sidebar.markdown(
        """
        <div style="padding:8px 4px 18px 4px;">
            <div style="font-size:1.55rem;font-weight:800;">🎙️ AI Interview</div>
            <div style="font-size:.78rem;opacity:.68;margin-top:5px;">
                Interview preparation workspace
            </div>
            <div style="display:inline-flex;align-items:center;gap:6px;margin-top:10px;
                        padding:4px 9px;border:1px solid rgba(122,162,255,.20);
                        border-radius:999px;background:rgba(91,140,255,.07);
                        color:#9fb8e4;font-size:.67rem;font-weight:700;letter-spacing:.03em;">
                <span style="width:6px;height:6px;border-radius:50%;background:#4ade80;"></span>
                AI Workspace
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.sidebar.markdown(
        "<div style='font-size:.72rem;font-weight:800;letter-spacing:.12em;opacity:.55;text-transform:uppercase;'>Workspace</div>",
        unsafe_allow_html=True,
    )
    selected_page = st.sidebar.radio(
        "Select Section",
        [
            "📝 Question Generator",
            "🎙️ Interview with AI",
        ],
        label_visibility="collapsed",
    )
    if selected_page.startswith("📝"):
        st.session_state.page = (
            "Question Generator"
        )
    else:
        st.session_state.page = (
            "Interview with AI"
        )
    st.sidebar.divider()
    st.sidebar.subheader(
        "Backend Status"
    )
    if check_fastapi():
        st.sidebar.success(
            "FastAPI: Connected"
        )
    else:
        st.sidebar.error(
            "FastAPI: Offline"
        )
        st.sidebar.caption(
            f"Backend URL: {FASTAPI_URL}\n"
            "Ensure the Render backend is deployed and FASTAPI_URL secret is set."
        )

# QUESTION GENERATOR

def render_question_generator():
    ui_hero(
        "Question Intelligence",
        "📝 Interview Question Generator",
        "Match a candidate resume with a job description, identify skill gaps, and generate targeted interview questions.",
    )
    ui_workflow_steps(
        ["1. Resume & JD", "2. AI Analysis", "3. Interview Questions"],
        active_index=0,
    )
    st.markdown('<div style="height:10px"></div>', unsafe_allow_html=True)
    # INPUT
    ui_section(
        "Candidate & Job Information",
        "Upload the candidate resume and paste the target job description.",
    )
    col1, col2 = st.columns(2)
    # RESUME
    with col1:
        st.markdown(
            """
            <div class="section-card-title" style="font-size:1.03rem;">📄 Candidate Resume</div>
            <div class="section-card-subtitle">Upload PDF, TXT or Markdown resume.</div>
            """,
            unsafe_allow_html=True,
        )
        resume_file = st.file_uploader(
            "Select Resume File",
            type=[
                "pdf",
                "txt",
                "md",
            ],
            key="generator_resume",
        )
    # JOB DESCRIPTION
    with col2:
        st.markdown(
            """
            <div class="section-card-title" style="font-size:1.03rem;">💼 Job Description</div>
            <div class="section-card-subtitle">Paste the complete job description for the target role.</div>
            """,
            unsafe_allow_html=True,
        )
        job_description = st.text_area(
            "Job Description",
            height=240,
            placeholder=(
                "Job Title: AI Engineer\n\n"
                "Required Skills:\n"
                "Python, Machine Learning, NLP, LLMs...\n\n"
                "Responsibilities:\n"
                "Build AI-powered applications..."
            ),
            key="generator_jd",
        )
    # SETTINGS
    ui_section(
        "Interview Settings",
        "Configure the role, difficulty, and number of generated questions.",
    )
    c1, c2, c3 = st.columns(3)
    with c1:
        job_title = st.text_input(
            "Job Title",
            placeholder="AI Engineer",
            key="generator_job_title",
        )
    with c2:
        difficulty = st.selectbox(
            "Difficulty",
            [
                "Easy",
                "Medium",
                "Hard",
            ],
            key="generator_difficulty",
        )
    with c3:
        num_questions = st.slider(
            "Number of Questions",
            min_value=6,
            max_value=30,
            value=20,
            step=1,
            key="generator_question_count",
        )
    st.divider()
    # GENERATE
    if st.button(
        "🚀 Generate Personalized Questions",
        type="primary",
        use_container_width=True,
        key="generate_questions",
    ):
        # VALIDATION
        if resume_file is None:
            st.warning(
                "Please upload a candidate resume."
            )
            st.stop()
        if not job_description.strip():
            st.warning(
                "Please paste the job description."
            )
            st.stop()
        if not job_title.strip():
            st.warning(
                "Please enter the job title."
            )
            st.stop()
        # EXTRACT RESUME
        with st.spinner(
            "Extracting resume..."
        ):
            resume_text = (
                extract_resume_text(
                    resume_file
                )
            )
        if not resume_text.strip():
            st.error(
                "No readable text was found in the resume."
            )
            st.stop()
        # JOB DESCRIPTION
        jd_text = (
            job_description.strip()
        )
        # DOCUMENT IDS
        candidate_id = (
            create_document_id(
                resume_text,
                "candidate",
            )
        )
        job_id = (
            create_document_id(
                jd_text,
                "job",
            )
        )
        # These IDs are retained for compatibility
        # with your existing workflow.
        _ = candidate_id
        _ = job_id

        # FASTAPI

        with st.spinner(
            "Analyzing resume and generating questions..."
        ):
            try:
                result = (
                    generate_questions_with_api(
                        resume_text=resume_text,
                        job_description=jd_text,
                        job_title=job_title,
                        difficulty=difficulty,
                        num_questions=num_questions,
                    )
                )
            except requests.ConnectionError:
                st.error(
                    f"Could not connect to backend: {FASTAPI_URL}\n\n"
                    "Ensure the Render backend is running and "
                    "FASTAPI_URL is set correctly in Streamlit Cloud secrets."
                )
                st.stop()
            except requests.Timeout:
                st.error(
                    "FastAPI request timed out."
                )
                st.stop()
            except requests.HTTPError as e:
                st.error(
                    "FastAPI returned an error."
                )
                try:
                    st.json(
                        e.response.json()
                    )
                except Exception:
                    st.code(
                        str(e)
                    )
                st.stop()
            except Exception as e:
                st.error(
                    f"Interview generation failed: {e}"
                )
                st.stop()
        # SAVE
        st.session_state.gap_result = (
            result.get(
                "gap_analysis"
            )
        )
        st.session_state.question_result = (
            result.get(
                "interview_questions"
            )
        )
        st.success(
            "Interview questions generated successfully."
        )
    # GAP ANALYSIS
    if st.session_state.gap_result:
        gap_result = (
            st.session_state.gap_result
        )
        st.divider()
        st.subheader(
            "📊 Resume vs Job Analysis"
        )
        # FIT
        overall_fit = (
            gap_result.get(
                "overall_fit",
                {},
            )
        )
        st.info(
            f"**Overall Fit:** "
            f"{overall_fit.get('status', 'Unknown')}\n\n"
            f"{overall_fit.get('reason', '')}"
        )
        # COMPARISON
        comparison = (
            gap_result.get(
                "comparison",
                {},
            )
        )
        skill_gaps = (
            gap_result.get(
                "skill_gap_analysis",
                {},
            )
        )
        matched_required = (
            comparison.get(
                "matched_required_skills",
                [],
            )
        )
        missing_required = (
            comparison.get(
                "missing_required_skills",
                [],
            )
        )
        partial_required = (
            comparison.get(
                "partially_matched_required_skills",
                [],
            )
        )
        critical_gaps = (
            skill_gaps.get(
                "critical_gaps",
                [],
            )
        )
        # METRICS
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric(
                "Matched Required",
                len(matched_required),
            )
        with m2:
            st.metric(
                "Missing Required",
                len(missing_required),
            )
        with m3:
            st.metric(
                "Partial Skills",
                len(partial_required),
            )
        with m4:
            st.metric(
                "Critical Gaps",
                len(critical_gaps),
            )
        # INFORMATION
        with st.expander(
            "👤 Candidate Information"
        ):
            st.json(
                gap_result.get(
                    "candidate",
                    {},
                )
            )
        with st.expander(
            "💼 Job Information"
        ):
            st.json(
                gap_result.get(
                    "job",
                    {},
                )
            )
        # MATCHED
        with st.expander(
            "✅ Matched Required Skills"
        ):
            if matched_required:
                for skill in matched_required:
                    st.success(
                        skill
                    )
            else:
                st.info(
                    "No matched required skills."
                )
        # MISSING
        with st.expander(
            "⚠️ Missing Required Skills"
        ):
            if missing_required:
                for skill in missing_required:
                    st.warning(
                        skill
                    )
            else:
                st.success(
                    "No missing required skills."
                )
        # PARTIAL
        with st.expander(
            "🔶 Partially Matched Skills"
        ):
            if partial_required:
                for skill in partial_required:
                    st.info(
                        skill
                    )
            else:
                st.info(
                    "No partially matched skills."
                )
        # TECHNOLOGIES
        with st.expander(
            "🛠️ Technology Gaps"
        ):
            missing_technologies = (
                comparison.get(
                    "missing_technologies",
                    [],
                )
            )
            if missing_technologies:
                for technology in missing_technologies:
                    st.warning(
                        technology
                    )
            else:
                st.success(
                    "No major technology gaps."
                )
        # EXPERIENCE
        with st.expander(
            "📈 Experience Gap"
        ):
            st.json(
                gap_result.get(
                    "experience_gap",
                    {},
                )
            )
    # GENERATED QUESTIONS
    if st.session_state.question_result:
        result = (
            st.session_state.question_result
        )
        st.divider()
        st.subheader(
            "🎤 Personalized Interview Questions"
        )
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric(
                "Job",
                result.get(
                    "job_title",
                    "Unknown",
                ),
            )
        with c2:
            st.metric(
                "Difficulty",
                difficulty,
            )
        with c3:
            st.metric(
                "Questions",
                result.get(
                    "total_questions",
                    0,
                ),
            )
        # DISTRIBUTION
        st.markdown(
            "### Question Distribution"
        )
        distribution = (
            result.get(
                "category_distribution",
                {},
            )
        )
        def _get_dist(k1, k2):
            return distribution.get(k1, distribution.get(k2, 0)) if isinstance(distribution, dict) else 0

        d1, d2, d3 = st.columns(3)
        with d1:
            st.write(
                f"**Basic:** "
                f"{_get_dist('Basic', 'Basic')}"
            )
            st.write(
                f"**Technical:** "
                f"{_get_dist('Technical', 'Technical')}"
            )
        with d2:
            st.write(
                f"**Resume-Based:** "
                f"{_get_dist('Resume-Based', 'Resume_Based')}"
            )
            st.write(
                f"**Project-Based:** "
                f"{_get_dist('Project-Based', 'Project_Based')}"
            )
        with d3:
            st.write(
                f"**Scenario-Based:** "
                f"{_get_dist('Scenario-Based', 'Scenario_Based')}"
            )
            st.write(
                f"**Skill Gap:** "
                f"{_get_dist('Skill Gap', 'Skill_Gap')}"
            )
        # PDF DOWNLOAD
        pdf_bytes = build_interview_questions_pdf(
            result
        )
        st.markdown(
            '<div style="height:6px"></div>',
            unsafe_allow_html=True,
        )
        download_col, info_col = st.columns(
            [1, 3],
            gap="medium",
        )
        with download_col:
            st.download_button(
                label="Download Questions PDF",
                data=pdf_bytes,
                file_name=(
                    f"{_pdf_safe_text(job_title) or 'AI_Interview'}_"
                    "Interview_Questions.pdf"
                ).replace(
                    " ",
                    "_",
                ),
                mime="application/pdf",
                use_container_width=True,
                key="download_interview_questions_pdf",
            )
        with info_col:
            st.caption(
                "Download all generated questions with expected answers "
                "and interviewer key points in one PDF."
            )
        # QUESTIONS
        for question in result.get(
            "questions",
            [],
        ):
            st.markdown(
                f"### "
                f"{question.get('question_id')}. "
                f"{question.get('question')}"
            )
            st.caption(
                f"Category: **"
                f"{question.get('category')}"
                f"** | Difficulty: **"
                f"{question.get('difficulty')}"
                f"**"
            )
            with st.expander(
                "💡 Expected Answer"
            ):
                st.write(
                    question.get(
                        "expected_answer",
                        "",
                    )
                )
            with st.expander(
                "🔑 Key Points"
            ):
                for point in question.get(
                    "key_points",
                    [],
                ):
                    st.write(
                        f"- {point}"
                    )
# PDF EXPORT - QUESTION / ANSWER / KEY POINTS
def _pdf_safe_text(value) -> str:
    """
    Convert arbitrary model text to ASCII-safe text for ReportLab's
    built-in Helvetica family.
    This avoids broken glyphs from emojis and Unicode punctuation
    while preserving the actual question/answer content.
    """
    if value is None:
        return ""
    text = str(value)
    replacements = {
        "\u2013": "-",
        "\u2014": "-",
        "\u2212": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2022": "-",
        "\u2192": "->",
        "\u00a0": " ",
        "\u2026": "...",
    }
    for source_char, target_char in replacements.items():
        text = text.replace(
            source_char,
            target_char,
        )
    # Drop unsupported symbols such as emojis while keeping normal
    # letters/numbers/punctuation.
    text = unicodedata.normalize(
        "NFKD",
        text,
    )
    text = text.encode(
        "ascii",
        "ignore",
    ).decode(
        "ascii"
    )
    text = re.sub(
        r"[ \t]+",
        " ",
        text,
    )
    return text.strip()

def build_interview_questions_pdf(
    interview_result: dict,
) -> bytes:
    """
    Create a downloadable PDF containing every generated question,
    expected answer, and key points.
    The PDF is generated completely in memory, so no temporary file
    is required on the server.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=16 * mm,
        leftMargin=16 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title="AI Interview Question Report",
        author="AI Interview Studio",
        subject="Interview Questions, Expected Answers and Key Points",
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "PDFTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        alignment=TA_CENTER,
        spaceAfter=8,
        textColor=colors.HexColor(
            "#172033"
        ),
    )
    subtitle_style = ParagraphStyle(
        "PDFSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=13,
        alignment=TA_CENTER,
        textColor=colors.HexColor(
            "#667085"
        ),
        spaceAfter=16,
    )
    meta_label_style = ParagraphStyle(
        "PDFMetaLabel",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor(
            "#344054"
        ),
    )
    meta_value_style = ParagraphStyle(
        "PDFMetaValue",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor(
            "#101828"
        ),
    )
    question_style = ParagraphStyle(
        "PDFQuestion",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12.5,
        leading=17,
        textColor=colors.HexColor(
            "#1D4ED8"
        ),
        spaceBefore=4,
        spaceAfter=8,
    )
    body_style = ParagraphStyle(
        "PDFBody",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor(
            "#253047"
        ),
        spaceAfter=8,
    )
    answer_label_style = ParagraphStyle(
        "PDFAnswerLabel",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor(
            "#0F766E"
        ),
        spaceBefore=3,
        spaceAfter=5,
    )
    key_label_style = ParagraphStyle(
        "PDFKeyLabel",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor(
            "#7C3AED"
        ),
        spaceBefore=3,
        spaceAfter=5,
    )
    point_style = ParagraphStyle(
        "PDFPoint",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        leftIndent=12,
        firstLineIndent=-8,
        textColor=colors.HexColor(
            "#344054"
        ),
        spaceAfter=3,
    )
    category_style = ParagraphStyle(
        "PDFCategory",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor(
            "#475467"
        ),
        spaceAfter=10,
    )
    story = []
    job_title = _pdf_safe_text(
        interview_result.get(
            "job_title",
            "Interview",
        )
    )
    difficulty = _pdf_safe_text(
        interview_result.get(
            "difficulty",
            "Not specified",
        )
    )
    total_questions = interview_result.get(
        "total_questions",
        0,
    )
    story.append(
        Paragraph(
            "AI Interview Question Report",
            title_style,
        )
    )
    story.append(
        Paragraph(
            "Questions, expected answers and interviewer key points",
            subtitle_style,
        )
    )
    metadata = [
        [
            Paragraph(
                "Job Title",
                meta_label_style,
            ),
            Paragraph(
                escape(job_title),
                meta_value_style,
            ),
        ],
        [
            Paragraph(
                "Difficulty",
                meta_label_style,
            ),
            Paragraph(
                escape(difficulty),
                meta_value_style,
            ),
        ],
        [
            Paragraph(
                "Total Questions",
                meta_label_style,
            ),
            Paragraph(
                escape(str(total_questions)),
                meta_value_style,
            ),
        ],
    ]
    metadata_table = Table(
        metadata,
        colWidths=[
            42 * mm,
            125 * mm,
        ],
        hAlign="LEFT",
    )
    metadata_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    colors.HexColor(
                        "#F8FAFC"
                    ),
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.6,
                    colors.HexColor(
                        "#D0D5DD"
                    ),
                ),
                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.3,
                    colors.HexColor(
                        "#E4E7EC"
                    ),
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
            ]
        )
    )
    story.append(
        metadata_table
    )
    story.append(
        Spacer(
            1,
            12,
        )
    )
    questions = interview_result.get(
        "questions",
        [],
    )
    for index, question in enumerate(
        questions,
        start=1,
    ):
        question_id = _pdf_safe_text(
            question.get(
                "question_id",
                index,
            )
        )
        question_text = _pdf_safe_text(
            question.get(
                "question",
                "",
            )
        )
        category = _pdf_safe_text(
            question.get(
                "category",
                "General",
            )
        )
        question_difficulty = _pdf_safe_text(
            question.get(
                "difficulty",
                difficulty,
            )
        )
        expected_answer = _pdf_safe_text(
            question.get(
                "expected_answer",
                "",
            )
        )
        key_points = question.get(
            "key_points",
            [],
        )
        if not isinstance(
            key_points,
            list,
        ):
            key_points = [
                key_points
            ]
        section = []
        section.append(
            Paragraph(
                f"Question {escape(str(question_id))}: "
                f"{escape(question_text)}",
                question_style,
            )
        )
        section.append(
            Paragraph(
                f"Category: <b>{escape(category)}</b> "
                f"&nbsp;&nbsp;|&nbsp;&nbsp; "
                f"Difficulty: <b>{escape(question_difficulty)}</b>",
                category_style,
            )
        )
        section.append(
            Paragraph(
                "Expected Answer",
                answer_label_style,
            )
        )
        section.append(
            Paragraph(
                escape(
                    expected_answer
                    or "No expected answer provided."
                ),
                body_style,
            )
        )
        section.append(
            Paragraph(
                "Key Points",
                key_label_style,
            )
        )
        if key_points:
            for point in key_points:
                safe_point = _pdf_safe_text(
                    point
                )
                section.append(
                    Paragraph(
                        f"- {escape(safe_point)}",
                        point_style,
                    )
                )
        else:
            section.append(
                Paragraph(
                    "- No key points provided.",
                    point_style,
                )
            )
        card = Table(
            [[section]],
            colWidths=[
                168 * mm
            ],
        )
        card.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, -1),
                        colors.white,
                    ),
                    (
                        "BOX",
                        (0, 0),
                        (-1, -1),
                        0.7,
                        colors.HexColor(
                            "#D0D5DD"
                        ),
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        12,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        12,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        10,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        10,
                    ),
                ]
            )
        )
        story.append(
            KeepTogether(card)
        )
        if index != len(questions):
            story.append(
                Spacer(
                    1,
                    10,
                )
            )
    if not questions:
        story.append(
            Paragraph(
                "No interview questions were generated.",
                body_style,
            )
        )
    doc.build(
        story
    )
    return buffer.getvalue()

# FINAL INTERVIEW REPORT

def render_final_interview_report():
    if not st.session_state.ai_final_report:
        return
    st.divider()
    st.markdown("## 📊 Final Interview Evaluation")
    st.markdown(
        """
        <div class="report-highlight">
            <b>Interview session summary</b><br>
            <span style="color:#64748b;">
                The evaluation is based only on the questions you actually answered.
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    c1, c2 = st.columns(2)
    with c1:
        st.metric(
            "Questions Completed",
            st.session_state.ai_completed_questions,
        )
    with c2:
        st.metric(
            "Average Score",
            f"{st.session_state.ai_final_score}/10",
        )
    st.info(
        "The evaluation is based only on the questions "
        "you actually answered."
    )
    with st.expander(
        "View Final Report",
        expanded=True,
    ):
        st.markdown(
            st.session_state.ai_final_report
        )
    if st.button(
        "🔄 Start New AI Interview",
        use_container_width=True,
    ):
        st.session_state.ai_final_report = ""
        st.session_state.ai_final_score = 0
        st.session_state.ai_completed_questions = 0
        st.rerun()

# INTERVIEW WITH AI

def render_ai_interview():
    ui_hero(
        "Live Practice",
        "🎙️ Interview with AI",
        "Practice a realistic technical interview with voice input, AI evaluation, and automatic follow-up questions.",
    )
    # INTERVIEW SETUP
    st.markdown("## Interview Setup")
    # SHOW FINAL REPORT ONLY AFTER QUIT / COMPLETION
    if st.session_state.ai_final_report:
        st.success(
            "Interview session completed."
        )
        c1, c2 = st.columns(2)
        with c1:
            st.metric(
                "Questions Completed",
                st.session_state.ai_completed_questions,
            )
        with c2:
            st.metric(
                "Average Score",
                f"{st.session_state.ai_final_score}/10",
            )
        st.subheader(
            "📊 Final Interview Evaluation"
        )
        st.info(
            "This report is based only on the questions "
            "you actually answered."
        )
        st.markdown(
            st.session_state.ai_final_report
        )
        st.divider()
        if st.button(
            "🔄 Start New Interview",
            use_container_width=True,
            key="new_ai_interview",
        ):
            st.session_state.ai_final_report = ""
            st.session_state.ai_final_score = 0
            st.session_state.ai_completed_questions = 0
            st.session_state.ai_interview_id = None
            st.session_state.ai_current_question = ""
            st.session_state.ai_question_number = 0
            st.session_state.ai_audio = None
            st.session_state.ai_transcript = ""
            st.session_state.ai_evaluation = ""
            st.session_state.ai_score = 0
            st.session_state.ai_processed_audio_hash = None
            st.rerun()
        # Don't show the setup/live interview under
        # the final report until user starts a new session.
        return
    # SETUP FORM
    if not st.session_state.interview_started:
        st.write(
            "Select the role and interview level."
        )
        c1, c2 = st.columns(2)
        with c1:
            role = st.selectbox(
                "Select Role",
                [
                    "AI Engineer",
                    "Machine Learning Engineer",
                    "Python Developer",
                    "Data Scientist",
                    "Data Analyst",
                    "Backend Developer",
                    "Software Engineer",
                    "Generative AI Engineer",
                    "NLP Engineer",
                ],
                key="ai_role",
            )
        with c2:
            interview_difficulty = st.selectbox(
                "Interview Level",
                [
                    "Easy",
                    "Medium",
                    "Hard",
                ],
                index=1,
                key="ai_difficulty",
            )
        st.info(
            """
            **Interview Flow**
            AI asks a question → you record your answer →
            STT converts your speech to text → LangGraph evaluates
            your answer → AI generates the next question → TTS
            speaks the next question.
            **Maximum questions: 5**
            """
        )
        if st.button(
            "🚀 Start AI Interview",
            type="primary",
            use_container_width=True,
            key="start_ai_interview",
        ):
            try:
                with st.spinner(
                    "Starting AI interviewer..."
                ):
                    result = start_ai_interview(
                        role=role,
                        difficulty=interview_difficulty,
                    )
                # START SESSION
                st.session_state.interview_started = True
                st.session_state.interview_role = (
                    result["role"]
                )
                st.session_state.interview_difficulty = (
                    result["difficulty"]
                )
                st.session_state.ai_interview_id = (
                    result["interview_id"]
                )
                st.session_state.ai_current_question = (
                    result["question"]
                )
                st.session_state.ai_question_number = (
                    result["question_number"]
                )
                st.session_state.ai_total_questions = (
                    result.get(
                        "total_questions",
                        5,
                    )
                )
                st.session_state.ai_audio = (
                    base64.b64decode(
                        result["audio_base64"]
                    )
                )
                st.session_state.ai_transcript = ""
                st.session_state.ai_evaluation = ""
                st.session_state.ai_score = 0
                st.session_state.ai_processed_audio_hash = (
                    None
                )
                st.session_state.ai_final_report = ""
                st.session_state.ai_final_score = 0
                st.session_state.ai_completed_questions = 0
                st.rerun()
            except requests.ConnectionError:
                st.error(
                    f"Could not connect to backend: {FASTAPI_URL}\n\n"
                    "Ensure the Render backend is running and "
                    "FASTAPI_URL is set in Streamlit Cloud secrets."
                )
            except requests.Timeout:
                st.error(
                    "FastAPI request timed out."
                )
            except requests.HTTPError as e:
                st.error(
                    "FastAPI returned an error."
                )
                try:
                    st.json(
                        e.response.json()
                    )
                except Exception:
                    st.code(
                        str(e)
                    )
            except Exception as e:
                st.error(
                    f"Could not start AI interview: {e}"
                )
        return
    # LIVE INTERVIEW
    st.markdown('<div style="height:14px"></div>', unsafe_allow_html=True)
    role = (
        st.session_state.interview_role
    )
    difficulty = (
        st.session_state.interview_difficulty
    )
    question = (
        st.session_state.ai_current_question
    )
    question_number = (
        st.session_state.ai_question_number
    )
    total_questions = (
        st.session_state.ai_total_questions
    )
    # LIVE HEADER
    st.markdown(
        f"""
        <div class="live-v3">
            <div>
                <div style="font-size:.74rem;font-weight:800;letter-spacing:.1em;opacity:.68;text-transform:uppercase;">
                    Live Interview
                </div>
                <div style="font-size:1.2rem;font-weight:800;margin-top:3px;">
                    {role}
                </div>
            </div>
            <div style="font-weight:800;">
                <span class="live-dot-v3"></span>LIVE
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.progress(
        min(
            question_number / total_questions,
            1.0,
        ),
        text=(
            f"Question "
            f"{question_number} "
            f"of "
            f"{total_questions}"
        ),
    )
    st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)
    # AI QUESTION
    left, right = st.columns(
        [1, 2],
        gap="large",
    )
    with left:
        st.markdown(
            "## 🤖"
        )
        st.subheader(
            "AI Interviewer"
        )
        st.caption(
            "Listen to the question and answer naturally."
        )
        st.write(
            f"Difficulty: **{difficulty}**"
        )
    with right:
        st.markdown(
            f"""
            <div class="question-panel-v3">
                <div class="question-label-v3">
                    Question {question_number} / {total_questions}
                </div>
                <div class="question-body-v3">
                    {question}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        # TTS
        if st.session_state.ai_audio:
            st.audio(
                st.session_state.ai_audio,
                format="audio/mpeg",
                autoplay=True,
            )
    st.markdown('<div style="height:18px"></div>', unsafe_allow_html=True)
    # STT
    st.markdown("## 🎤 Your Answer")
    st.markdown(
        """
        <div class="answer-panel">
            <div class="section-card-title">Record your response</div>
            <div class="section-card-subtitle">
                When recording finishes, your answer is automatically sent to STT and the AI evaluator.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    audio_value = st.audio_input(
        "Record your answer",
        sample_rate=16000,
        key=(
            f"ai_audio_input_"
            f"{question_number}"
        ),
    )
    # AUTOMATIC PROCESSING
    if audio_value is not None:
        current_audio = (
            audio_value.getvalue()
        )
        audio_hash = hashlib.sha256(
            current_audio
        ).hexdigest()
        already_processed = (
            st.session_state.ai_processed_audio_hash
            == audio_hash
        )
        if not already_processed:
            st.session_state.ai_processed_audio_hash = (
                audio_hash
            )
            try:
                with st.spinner(
                    "🎧 Transcribing and evaluating your answer..."
                ):
                    result = submit_ai_answer(
                        interview_id=(
                            st.session_state
                            .ai_interview_id
                        ),
                        audio_file=audio_value,
                    )
                # SAVE CURRENT ANSWER
                st.session_state.ai_transcript = (
                    result.get(
                        "transcript",
                        "",
                    )
                )
                st.session_state.ai_evaluation = (
                    result.get(
                        "evaluation",
                        "",
                    )
                )
                st.session_state.ai_score = (
                    result.get(
                        "score",
                        0,
                    )
                )
                completed = result.get(
                    "completed_questions",
                    question_number,
                )
                st.session_state.ai_completed_questions = (
                    completed
                )
                # FIVE QUESTIONS COMPLETED
                if result.get(
                    "interview_completed",
                    False,
                ):
                    with st.spinner(
                        "Generating final evaluation..."
                    ):
                        final_result = (
                            quit_ai_interview(
                                st.session_state
                                .ai_interview_id
                            )
                        )
                    st.session_state.ai_final_report = (
                        final_result.get(
                            "final_report",
                            "",
                        )
                    )
                    st.session_state.ai_final_score = (
                        final_result.get(
                            "average_score",
                            0,
                        )
                    )
                    st.session_state.ai_completed_questions = (
                        final_result.get(
                            "completed_questions",
                            completed,
                        )
                    )
                    # STOP LIVE INTERVIEW
                    st.session_state.interview_started = False
                    st.session_state.ai_interview_id = None
                    st.session_state.ai_current_question = ""
                    st.session_state.ai_question_number = 0
                    st.session_state.ai_audio = None
                    st.session_state.ai_transcript = ""
                    st.session_state.ai_evaluation = ""
                    st.session_state.ai_score = 0
                    st.session_state.ai_processed_audio_hash = (
                        None
                    )
                    st.rerun()
                else:
                    # NEXT QUESTION
                    st.session_state.ai_current_question = (
                        result["next_question"]
                    )
                    st.session_state.ai_question_number = (
                        result["question_number"]
                    )
                    # NEXT TTS
                    audio_base64 = result.get(
                        "audio_base64",
                        "",
                    )
                    if audio_base64:
                        st.session_state.ai_audio = (
                            base64.b64decode(
                                audio_base64
                            )
                        )
                    st.session_state.ai_processed_audio_hash = (
                        None
                    )
                    st.rerun()
            except requests.ConnectionError:
                st.error(
                    "FastAPI connection failed."
                )
            except requests.Timeout:
                st.error(
                    "Interview request timed out."
                )
            except requests.HTTPError as e:
                st.error(
                    "FastAPI returned an error."
                )
                try:
                    st.json(
                        e.response.json()
                    )
                except Exception:
                    st.code(
                        str(e)
                    )
            except Exception as e:
                st.error(
                    f"Could not process answer: {e}"
                )
    # LAST ANSWER
    if st.session_state.ai_transcript:
        st.markdown('<div style="height:16px"></div>', unsafe_allow_html=True)
        st.subheader(
            "📝 Your Last Answer"
        )
        st.write(
            st.session_state.ai_transcript
        )
    # CURRENT EVALUATION
    if st.session_state.ai_evaluation:
        st.markdown('<div style="height:10px"></div>', unsafe_allow_html=True)
        with st.expander(
            f"🧠 Current Answer Evaluation "
            f"— {st.session_state.ai_score}/10"
        ):
            st.write(
                st.session_state.ai_evaluation
            )
    # QUIT
    st.divider()
    if st.button(
        "⏹️ Quit Interview",
        use_container_width=True,
        key="quit_ai_interview",
    ):
        try:
            if st.session_state.ai_interview_id:
                with st.spinner(
                    "Generating final evaluation..."
                ):
                    final_result = (
                        quit_ai_interview(
                            st.session_state.ai_interview_id
                        )
                    )
                # SAVE FINAL REPORT
                st.session_state.ai_final_report = (
                    final_result.get(
                        "final_report",
                        "",
                    )
                )
                st.session_state.ai_final_score = (
                    final_result.get(
                        "average_score",
                        0,
                    )
                )
                st.session_state.ai_completed_questions = (
                    final_result.get(
                        "completed_questions",
                        0,
                    )
                )
        except requests.ConnectionError:
            st.error(
                "Could not connect to FastAPI."
            )
            return
        except requests.HTTPError as e:
            st.error(
                "Could not generate final evaluation."
            )
            try:
                st.json(
                    e.response.json()
                )
            except Exception:
                st.code(
                    str(e)
                )
            return
        except Exception as e:
            st.error(
                f"Could not finish interview: {e}"
            )
            return
        # STOP INTERVIEW
        st.session_state.interview_started = False
        st.session_state.ai_interview_id = None
        st.session_state.ai_current_question = ""
        st.session_state.ai_question_number = 0
        st.session_state.ai_audio = None
        st.session_state.ai_transcript = ""
        st.session_state.ai_evaluation = ""
        st.session_state.ai_score = 0
        st.session_state.ai_processed_audio_hash = (
            None
        )
        st.rerun()
# =========================================================
# MAIN
# =========================================================

def main():
    initialize_session_state()
    render_sidebar()
    # =====================================================
    # PAGE ROUTING
    # =====================================================
    if (
        st.session_state.page
        == "Question Generator"
    ):
        render_question_generator()
    else:
        render_ai_interview()
# =========================================================
# ENTRY POINT
# =========================================================
if __name__ == "__main__":
    main()