import streamlit as st
import pandas as pd
import re

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

    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    df = df.drop_duplicates(subset="Email Address")

    df["score"] = df.apply(lambda x: score_candidate(x, tor_text), axis=1)

    top = df.sort_values("score", ascending=False).head(5)

    st.subheader("🏆 Top Experts")

    for _, row in top.iterrows():
        st.write(f"""
        **{row['First Name']} {row['Last Name']}**  
        Email: {row['Email Address']}  
        Score: {row['score']}  
        """)

    st.dataframe(df)
