import streamlit as st
import pandas as pd
import re
import PyPDF2
from docx import Document

st.set_page_config(page_title="Expert Matcher Pro", layout="wide")

st.title("🧠 Expert Matcher Pro")

# =========================
# 📂 UPLOAD FILES
# =========================

data_file = st.file_uploader("Upload Experts Database (Excel or CSV)", type=["csv", "xlsx"])
tor_file = st.file_uploader("Upload ToR (PDF, Word, TXT)", type=["pdf", "docx", "txt"])

# =========================
# 📄 READ FILE FUNCTIONS
# =========================

def read_pdf(file):
    try:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text
    except:
        return ""

def read_docx(file):
    try:
        doc = Document(file)
        return "\n".join([p.text for p in doc.paragraphs])
    except:
        return ""

def read_txt(file):
    try:
        return file.read().decode("utf-8")
    except:
        return ""

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

    if tor_text:
        st.success("ToR loaded successfully ✅")
    else:
        st.warning("Could not extract text from ToR")

# Preview ToR
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


def get_name(row):
    first = row.get('First Name') or row.get('First name') or ""
    last = row.get('Last Name') or row.get('Last name') or ""
    return f"{first} {last}".strip()


def score_candidate(row, tor_text):
    text = (
        str(row.get("Primary Area of Expertise", "")) + " " +
        str(row.get("Brief Professional Profile", ""))
    ).lower()

    tor_text = tor_text.lower()

    score = 0

    # 🔥 KEYWORD GROUPS (INTELIGENTE)
    keyword_groups = [
        ["data", "database", "data systems"],
        ["system", "information system", "mis"],
        ["digital", "it", "technology"],
        ["governance", "public administration"],
        ["social", "social protection"],
        ["analysis", "analytics", "evaluation"]
    ]

    for group in keyword_groups:
        if any(kw in tor_text for kw in group) and any(kw in text for kw in group):
            score += 15

    # EXPERIÊNCIA
    exp = parse_experience(row.get("Total years of relevant professional experience", ""))
    score += exp

    # EXPERIÊNCIA INTERNACIONAL
    if str(row.get("Have you worked on international development projects?", "")).lower() == "yes":
        score += 15

    return score

# =========================
# 🚀 MAIN LOGIC
# =========================

if data_file is not None and tor_text:

    # =========================
    # LOAD DATA (CSV + XLSX)
    # =========================
    try:
        if data_file.name.endswith(".csv"):
            df = pd.read_csv(
                data_file,
                encoding="utf-8",
                engine="python",
                on_bad_lines="skip"
            )

        elif data_file.name.endswith(".xlsx"):
            df = pd.read_excel(data_file, sheet_name=0)

        else:
            st.error("Unsupported file format")
            st.stop()

    except Exception as e:
        st.error(f"Error loading file: {e}")
        st.stop()

    st.success(f"Loaded {len(df)} experts")

    # =========================
    # CLEAN DATA
    # =========================

    if "Email Address" in df.columns:
        df = df.drop_duplicates(subset="Email Address")

    st.info(f"After cleaning: {len(df)} experts")

    # =========================
    # SCORING
    # =========================

    df["score"] = df.apply(lambda x: score_candidate(x, tor_text), axis=1)

    df_sorted = df.sort_values("score", ascending=False)

    # =========================
    # TOP EXPERTS
    # =========================

    st.subheader("🏆 Top Experts")

    top5 = df_sorted.head(5)

    for _, row in top5.iterrows():
        st.markdown(f"""
        ### {get_name(row)}
        📧 {row.get('Email Address','N/A')}  
        ⭐ Score: {row['score']}  

        **Expertise:** {row.get('Primary Area of Expertise','')}

        ---
        """)

    # =========================
    # FULL TABLE
    # =========================

    st.subheader("📊 Full Ranking")

    display_cols = [
        col for col in [
            "First Name",
            "Last Name",
            "Email Address",
            "Primary Area of Expertise",
            "score"
        ] if col in df.columns
    ]

    st.dataframe(df_sorted[display_cols])

else:
    st.info("⬆️ Please upload both the Experts Database and the ToR file")
