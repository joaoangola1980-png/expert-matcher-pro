import streamlit as st
import pandas as pd
import re
import PyPDF2
from docx import Document

st.title("🧠 Expert Matcher Pro")

uploaded_file = st.file_uploader("Upload Experts Database", type=["csv", "xlsx"])
tor_text = st.text_area("Paste Terms of Reference (ToR)")

def parse_experience(val):
    if pd.isna(val):
        return 0
    val = str(val)
    if "20+" in val:
        return 20
    nums = re.findall(r"\d+", val)
    return int(nums[0]) if nums else 0

def score_candidate(row, tor_text):
    text = (
        str(row.get("Primary Area of Expertise", "")) + " " +
        str(row.get("Brief Professional Profile", ""))
    ).lower()

    score = 0

    keywords = ["data", "system", "mis", "digital", "government"]

    for kw in keywords:
        if kw in text and kw in tor_text.lower():
            score += 10

    exp = parse_experience(row.get("Total years of relevant professional experience", ""))
    score += exp

    return score

if uploaded_file and tor_text:

   tor_file = st.file_uploader(
    "Upload ToR (PDF, Word, TXT)", 
    type=["pdf", "docx", "txt"]
)

tor_text = ""

if tor_file is not None:

    if tor_file.type == "application/pdf":
        tor_text = read_pdf(tor_file)

    elif tor_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        tor_text = read_docx(tor_file)

    elif tor_file.type == "text/plain":
        tor_text = tor_file.read().decode("utf-8")

    st.success("ToR loaded successfully ✅")
def read_pdf(file):
    reader = PyPDF2.PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text


def read_docx(file):
    doc = Document(file)
    return "\n".join([p.text for p in doc.paragraphs])

if tor_text:
    st.write("### 📄 Extracted ToR Preview")
    st.write(tor_text[:1000])  # primeiros 1000 caracteres
