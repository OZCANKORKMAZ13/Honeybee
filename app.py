import streamlit as st
import tempfile
import os
import time
import base64
from dotenv import load_dotenv
from app.main import run_pipeline

# ================== ENV ==================
load_dotenv()
APP_USERNAME = os.getenv("APP_USERNAME")
APP_PASSWORD = os.getenv("APP_PASSWORD")

# ================== PAGE CONFIG ==================
st.set_page_config(
    page_title="🐝 Honeybee Attendance Engine",
    layout="wide"
)

# ================== GLOBAL CSS ==================
st.markdown("""
<style>
/* 🚨 ASIL OLAY BURASI 🚨 */
/* Streamlit root container'ı DARALTIYORUZ */
.block-container {
    max-width: 900px;
    padding-left: 2rem;
    padding-right: 2rem;
    margin: auto;
}

/* Genel font */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Kart */
.card {
    background: white;
    padding: 26px;
    border-radius: 18px;
    box-shadow: 0 12px 35px rgba(0,0,0,0.10);
}

/* File uploader */
section[data-testid="stFileUploader"] {
    border: 2px dashed #f4b400;
    padding: 16px;
    border-radius: 12px;
    background-color: #fffdf5;
}

/* Primary button */
button[kind="primary"] {
    background: linear-gradient(90deg, #fbbc04, #f4b400);
    color: black;
    border-radius: 14px;
    height: 3em;
    font-weight: 600;
    font-size: 15px;
}

/* Progress bar */
div[data-testid="stProgress"] > div {
    background-color: #fbbc04;
}

/* Alerts */
div[data-testid="stAlert"] {
    border-radius: 12px;
}
</style>
""", unsafe_allow_html=True)

# ================== SESSION STATE ==================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "is_processing" not in st.session_state:
    st.session_state.is_processing = False

# ================== HELPERS ==================
def show_logo():
    logo_path = os.path.join("assets", "logo.png")
    if not os.path.exists(logo_path):
        return

    with open(logo_path, "rb") as f:
        logo_b64 = base64.b64encode(f.read()).decode()

    st.markdown(
        f"""
        <div style="display:flex; justify-content:center; margin-bottom:14px;">
            <img src="data:image/png;base64,{logo_b64}" width="150"/>
        </div>
        """,
        unsafe_allow_html=True
    )

# ================== LOGIN ==================
def login():
    show_logo()
    st.markdown("<div class='card'>", unsafe_allow_html=True)

    st.subheader("🔐 Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("Login", use_container_width=True):
        if username == APP_USERNAME and password == APP_PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Invalid username or password")

    st.markdown("</div>", unsafe_allow_html=True)

# ================== AUTH GATE ==================
if not st.session_state.authenticated:
    login()
    st.stop()

# ================== LOGOUT ==================
_, col = st.columns([5, 1])
with col:
    if st.button("Logout"):
        st.session_state.authenticated = False
        st.rerun()

# ================== PROGRESS ==================
def animated_progress():
    bar = st.progress(0)
    status = st.empty()

    steps = [
        ("🐝 Gathering files", 20),
        ("⚙️ Processing data", 45),
        ("🧮 Reconciling attendance", 70),
        ("📊 Generating report", 90),
        ("✅ Finalizing", 100),
    ]

    current = 0
    for text, target in steps:
        status.markdown(f"**{text}...**")
        while current < target:
            current += 1
            bar.progress(current)
            time.sleep(0.02)

# ================== MAIN APP ==================
show_logo()
st.markdown("<div class='card'>", unsafe_allow_html=True)

st.markdown(
    "<h1 style='text-align:center;'>🐝 Honeybee Attendance Engine</h1>",
    unsafe_allow_html=True
)
st.markdown(
    "<p style='text-align:center; color:gray;'>Automated attendance reconciliation</p>",
    unsafe_allow_html=True
)

st.markdown("<hr>", unsafe_allow_html=True)

procare_file = st.file_uploader("Upload Procare Excel", type=["xls", "xlsx"])
if procare_file:
    st.success("✅ Procare file uploaded successfully")

dhs_file = st.file_uploader("Upload DHS Excel", type=["xls", "xlsx"])
if dhs_file:
    st.success("✅ DHS file uploaded successfully")

st.markdown("<br>", unsafe_allow_html=True)

if st.button(
    "🚀 Generate Attendance Report",
    type="primary",
    use_container_width=True,
    disabled=st.session_state.is_processing
):
    if not procare_file or not dhs_file:
        st.error("Please upload both files.")
        st.stop()

    st.session_state.is_processing = True

    with tempfile.TemporaryDirectory() as tmpdir:
        animated_progress()

        procare_path = os.path.join(tmpdir, "procare.xlsx")
        dhs_path = os.path.join(tmpdir, "dhs.xlsx")
        output_path = os.path.join(tmpdir, "final_attendance.xlsx")

        with open(procare_path, "wb") as f:
            f.write(procare_file.read())
        with open(dhs_path, "wb") as f:
            f.write(dhs_file.read())

        try:
            run_pipeline(procare_path, dhs_path, output_path)
            with open(output_path, "rb") as f:
                st.success("Report generated!")
                st.download_button(
                    "⬇️ Download Report",
                    data=f,
                    file_name="final_attendance.xlsx"
                )
        except Exception as e:
            st.error(str(e))

    st.session_state.is_processing = False

st.markdown("</div>", unsafe_allow_html=True)
