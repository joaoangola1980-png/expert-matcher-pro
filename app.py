import streamlit as st
import pandas as pd
import re
import PyPDF2
from docx import Document
from openai import OpenAI

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.set_page_config(page_title="Expert Matcher PRO", layout="wide")

st.title("🧠 Expert Matcher PRO")

# =========================
# 📂 UPLOAD
# =========================

data_file = st.file_uploader("Upload Experts Database", type=["csv", "xlsx"])
tor_file = st.file_uploader("Upload ToR", type=["pdf", "docx", "txt"])

# =========================
# 📄 READ FILES
# =========================

def read_pdf(file):
    reader = PyPDF2.PdfReader(file)
    return " ".join([p.extract_text() or "" for p in reader.pages])

def read_docx(file):
    doc = Document(file)
    return "\n".join([p.text for p in doc.paragraphs])

def read_txt(file):
    return file.read().decode("utf-8")

# =========================
# 🧠 READ TOR
# =========================

tor_text = ""

if tor_file:
    if tor_file.type == "application/pdf":
        tor_text = read_pdf(tor_file)
    elif "word" in tor_file.type:
        tor_text = read_docx(tor_file)
    else:
        tor_text = read_txt(tor_file)

    st.success("ToR loaded ✅")

# =========================
# 🧠 AI ANALYSIS
# =========================

def analyze_tor(tor_text):
    prompt = f"""
    Analyze this Terms of Reference and return:

    1. Project explanation (max 4 lines, simple)
    2. Is it a TEAM or INDIVIDUAL assignment
    3. List exact expert profiles required (job titles)
    4. Duration in days (or N/A)
    5. Clear deliverables list

    Format cleanly.

    ToR:
    {tor_text}
    """

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content

# =========================
# 🧩 HELPERS
# =========================

def get_name(row):
    return f"{row.get('First Name','')} {row.get('Last Name','')}"

def get_profile(row):
    return str(row.get("Brief Professional Profile", ""))[:250]

def parse_experience(val):
    val = str(val)
    nums = re.findall(r"\d+", val)
    return int(nums[0]) if nums else 0

# =========================
# 🧮 SCORING (REAL)
# =========================

def score_candidate(row, tor_text):

    text = (
        str(row.get("Primary Area of Expertise", "")) + " " +
        str(row.get("Brief Professional Profile", ""))
    ).lower()

    tor_text = tor_text.lower()

    keywords = ["data", "system", "mis", "governance", "social"]

    matches = sum(1 for k in keywords if k in text)

    exp = parse_experience(row.get("Total years of relevant professional experience", ""))

    score = (matches / len(keywords)) * 3 + (exp / 20) * 2

    return round(min(score, 5), 1)

# =========================
# 🚀 MAIN
# =========================

if data_file and tor_text:

    # LOAD DATA
    if data_file.name.endswith(".csv"):
        df = pd.read_csv(data_file, engine="python", on_bad_lines="skip")
    else:
        df = pd.read_excel(data_file)

    df = df.drop_duplicates(subset="Email Address")

    # =========================
    # 🧠 TOR OUTPUT (AI)
    # =========================

    st.header("📄 ToR Analysis")

    analysis = analyze_tor(tor_text)

    st.write(analysis)

    # =========================
    # 🧮 SCORE
    # =========================

    df["score"] = df.apply(lambda x: score_candidate(x, tor_text), axis=1)

    df = df.sort_values("score", ascending=False)

    # =========================
    # 👥 MOSAIC EXPERTS
    # =========================

    st.header("👥 Recommended Experts")

    top = df.head(6)

    cols = st.columns(3)

    for i, (_, row) in enumerate(top.iterrows()):
        with cols[i % 3]:
            st.markdown(f"""
            ### {get_name(row)}
            📧 {row.get('Email Address','N/A')}

            ⭐ **Match Score:** {row['score']} / 5

            **Expertise:**  
            {row.get('Primary Area of Expertise','')}

            **Profile:**  
            {get_profile(row)}
            """)
