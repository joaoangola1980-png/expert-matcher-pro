import streamlit as st
import pandas as pd
import re
import PyPDF2
from docx import Document

st.set_page_config(page_title="Expert Matcher Pro", layout="wide")

st.title("🧠 Expert Matcher Pro")

# =========================
# 📂 FILE UPLOADS
# =========================

data_file = st.file_uploader("Upload Experts Database", type=["csv", "xlsx"])
tor_file = st.file_uploader("Upload ToR (PDF, Word, TXT)", type=["pdf", "docx", "txt"])

# =========================
# 📄 READ FILE FUNCTIONS
# =========================

def read_pdf(file):
    reader = PyPDF2.PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

def read_docx(file):
    doc = Document(file)
    return "\n".join([p.text for p in doc.paragraphs])

def read_txt(file):
    return file.read().decode("utf-8")

# =========================
# 🧠 EXTRACT TOR TEXT
# =========================

tor_text = ""

if tor_file is not None:
    if tor_file.type == "application/pdf":
        tor_text = read_pdf(tor_file)
    elif tor_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        tor_text = read_docx(tor_file)
    elif tor_file.type == "text/plain":
        tor_text = read_txt(tor_file)

    st.success("ToR loaded successfully ✅")

# DEBUG (mostrar parte do ToR)
if tor_text:
    st.subheader("📄 ToR Preview")
    st.write(tor_text[:1000])

# =========================
# 🧩 HELPER FUNCTIONS
# =========================

def parse_experience(val):
    if pd.isna(val):
        return 0
    val = str(val)
    if "20+" in val:
        return 20
    if "16" in val:
        return 16
    if "11" in val:
        return 11
    nums = re.findall(r"\d+", val)
    return int(nums[0]) if nums else 0

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

    for kw in keywords:
        if kw in text and kw in tor_text:
            score += 10

    exp = parse_experience(row.get("Total years of relevant professional experience", ""))
    score += exp

    if str(row.get("Have you worked on international development projects?", "")).lower() == "yes":
        score += 10

    return score

# =========================
# 🚀 MAIN LOGIC
# =========================

if data_file is not None and tor_text:

    # Load data
    if data_file.name.endswith(".csv"):
        df = pd.read_csv(data_file)
    else:
        df = pd.read_excel(data_file)

    st.success(f"Loaded {len(df)} experts")

    # Clean
    df = df.drop_duplicates(subset="Email Address")

    st.info(f"After deduplication: {len(df)} experts")

    # Score
    df["score"] = df.apply(lambda x: score_candidate(x, tor_text), axis=1)

    # Sort
    df_sorted = df.sort_values("score", ascending=False)

    # =========================
    # 🏆 TOP EXPERTS
    # =========================

    st.subheader("🏆 Top Experts")

    top5 = df_sorted.head(5)

    for _, row in top5.iterrows():
        st.markdown(f"""
        ### {row['First Name']} {row['Last Name']}
        📧 {row['Email Address']}  
        ⭐ Score: {row['score']}  

        **Expertise:** {row['Primary Area of Expertise']}

        ---
        """)

    # =========================
    # 📊 FULL TABLE
    # =========================

    st.subheader("📊 Full Ranking")

    st.dataframe(df_sorted[[
        "First Name",
        "Last Name",
        "Email Address",
        "Primary Area of Expertise",
        "score"
    ]])
