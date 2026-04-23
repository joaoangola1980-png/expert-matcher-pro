import streamlit as st
import pandas as pd
import re
import PyPDF2
from docx import Document

st.set_page_config(page_title="Expert Matcher PRO", layout="wide")

st.title("🧠 Expert Matcher PRO")

# =========================
# 📂 UPLOAD
# =========================

data_file = st.file_uploader("Upload Experts Database (Excel or CSV)", type=["csv", "xlsx"])
tor_file = st.file_uploader("Upload ToR (PDF, Word, TXT)", type=["pdf", "docx", "txt"])

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
# 🧠 EXTRACT TOR TEXT
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
# 🧠 TOR ANALYSIS
# =========================

def extract_tor_info(text):
    text_lower = text.lower()

    # resumo simples
    summary = text[:500]

    # dias
    days = re.findall(r"\d+\s*days", text_lower)
    days = days[0] if days else "N/A"

    # deliverables
    deliverables = re.findall(r"deliverables?.{0,100}", text_lower)

    # perfis
    roles = re.findall(r"expert|specialist|consultant", text_lower)
    roles = list(set(roles))

    return summary, days, deliverables[:5], roles[:5]

# =========================
# 🧩 HELPERS
# =========================

def parse_experience(val):
    val = str(val)
    if "20+" in val:
        return 20
    nums = re.findall(r"\d+", val)
    return int(nums[0]) if nums else 0

def get_name(row):
    return f"{row.get('First Name','')} {row.get('Last Name','')}"

def get_profile(row):
    return str(row.get("Brief Professional Profile", ""))[:200]

# =========================
# 🧮 SCORE (0-5)
# =========================

def score_candidate(row, tor_text):

    text = (
        str(row.get("Primary Area of Expertise", "")) + " " +
        str(row.get("Brief Professional Profile", ""))
    ).lower()

    tor_text = tor_text.lower()

    score = 0

    keywords = [
        "data", "system", "mis", "digital",
        "governance", "social", "analysis"
    ]

    matches = sum(1 for k in keywords if k in text and k in tor_text)

    score += matches

    exp = parse_experience(row.get("Total years of relevant professional experience", ""))
    score += exp / 10

    if "yes" in str(row.get("Have you worked on international development projects?", "")).lower():
        score += 1

    # normalizar 0-5
    return min(round(score,1), 5)

# =========================
# 🚀 MAIN
# =========================

if data_file and tor_text:

    # LOAD DATA
    if data_file.name.endswith(".csv"):
        df = pd.read_csv(data_file, engine="python", on_bad_lines="skip")
    else:
        df = pd.read_excel(data_file)

    # CLEAN
    df = df.drop_duplicates(subset="Email Address")

    # SCORE
    df["score"] = df.apply(lambda x: score_candidate(x, tor_text), axis=1)

    df = df.sort_values("score", ascending=False)

    # =========================
    # 📄 TOR SUMMARY
    # =========================

    st.header("📄 ToR Summary")

    summary, days, deliverables, roles = extract_tor_info(tor_text)

    col1, col2 = st.columns(2)

    with col1:
        st.write("### Project Overview")
        st.write(summary)

        st.write("### Duration")
        st.write(days)

    with col2:
        st.write("### Deliverables")
        for d in deliverables:
            st.write(f"- {d}")

        st.write("### Profiles Required")
        for r in roles:
            st.write(f"- {r}")

    # =========================
    # 👥 EXPERTS (MOSAIC)
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

else:
    st.info("Upload both database and ToR")
