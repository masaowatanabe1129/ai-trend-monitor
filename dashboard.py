import streamlit as st
import json
import glob
import os
from collections import Counter
import re

st.set_page_config(page_title="AI Coding Trend Monitor", layout="wide")

st.title("🤖 AI Coding Trend Monitor")

# =========================
# 最新JSON読み込み
# =========================

files = sorted(glob.glob("data/*.json"), reverse=True)

if not files:
    st.warning("No data found")
    st.stop()

latest_file = files[0]

with open(latest_file, encoding="utf-8") as f:
    articles = json.load(f)

# =========================
# トレンド抽出
# =========================

text = ""

for a in articles:
    text += a["title"] + " "

words = re.findall(r"[a-zA-Z]{4,}", text.lower())

stopwords = [
    "with","from","that","this","using","openai",
    "model","models","research"
]

words = [w for w in words if w not in stopwords]

trend = Counter(words).most_common(10)

# =========================
# レイアウト
# =========================

col1, col2 = st.columns([2,1])

# =========================
# ニュース一覧
# =========================

with col1:

    st.header("📰 Latest AI Coding News")

    for article in articles:

        title = article["title"]
        link = article["link"]

        analysis = article.get("analysis", {})

        summary = analysis.get("summary_200j", "")

        with st.container():

            st.subheader(title)

            if summary:
                st.write(summary)

            st.link_button("Read article", link)

            st.divider()

# =========================
# トレンド
# =========================

with col2:

    st.header("📈 Trends")

    for word,count in trend:

        st.write(f"{word} ({count})")

    st.divider()

    st.header("📊 Stats")

    st.write("Articles:", len(articles))
    st.write("Source file:", os.path.basename(latest_file))
