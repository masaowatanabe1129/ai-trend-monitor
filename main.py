import feedparser
import requests
import json
import os
from datetime import datetime
from openai import OpenAI

# ========= 設定 =========
RSS_FEEDS = [
    "https://openai.com/blog/rss",
    "https://www.anthropic.com/news/rss",
]

KEYWORDS = ["agent", "rag", "llm", "multimodal", "ai"]

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ========= RSS取得 =========
def fetch_articles():
    articles = []

    for url in RSS_FEEDS:
        print(f"Fetching RSS: {url}")

        feed = feedparser.parse(url)

        print(f"Entries found: {len(feed.entries)}")

        for entry in feed.entries:
            articles.append({
                "title": entry.title,
                "link": entry.link,
                "summary": entry.summary if "summary" in entry else ""
            })

    print(f"Total articles: {len(articles)}")
    return articles

# ========= GPT分類 =========
def analyze_article(article):
    prompt = f"""
    次の記事をIT企業向けに分析してください。
    記事タイトル: {article['title']}
    概要: {article['summary']}

    以下のJSON形式で出力してください:
    {{
        "tech_category": "",
        "tech_maturity": "research/beta/production",
        "si_business_fit": 1-5,
        "internal_poc_feasibility": 1-5,
        "importance_score": 1-5,
        "summary_200j": ""
    }}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    content = response.choices[0].message.content

    try:
        return json.loads(content)
    except:
        return {"error": "JSON parse error", "raw": content}

# ========= 保存 =========
def save_results(results):
    today = datetime.now().strftime("%Y-%m-%d")
    os.makedirs("data", exist_ok=True)
    filename = f"data/{today}.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

# ========= 実行 =========
def main():
    articles = fetch_articles()
    results = []

    for article in articles:
        analysis = analyze_article(article)
        results.append({
            "title": article["title"],
            "link": article["link"],
            "analysis": analysis
        })

    save_results(results)

if __name__ == "__main__":
    main()
