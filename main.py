import feedparser
import requests
import json
import os
import re
from datetime import datetime, timedelta, timezone
from dateutil import parser
from openai import OpenAI

# ========= 設定 =========
RSS_FEEDS = [

    # research
    "https://arxiv.org/rss/cs.AI",
    "https://arxiv.org/rss/cs.CL",
    "https://arxiv.org/rss/cs.LG",

    # companies
    "https://huggingface.co/blog/feed.xml",
    "https://deepmind.google/blog/rss.xml",

    # AI news
    "https://www.marktechpost.com/feed/",
    "https://www.artificialintelligence-news.com/feed/",

    # tech media
    "https://venturebeat.com/category/ai/feed/",

    # github
    "https://mshibanami.github.io/GitHubTrendingRSS/daily/all.xml",
    "https://github.com/topics/artificial-intelligence.atom"
]

KEYWORDS = [

    # LLM
    "llm",
    "large language model",
    "transformer",
    "rag",
    "agent",
    "agents",

    # generative
    "generative ai",
    "diffusion",
    "multimodal",

    # tools
    "vector database",
    "embedding",

    # companies / models
    "gpt",
    "claude",
    "gemini",
    "llama",
]

MAX_ARTICLES = 20

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ========= RSS取得 =========
def is_ai_related(text):

    text = text.lower()

    for keyword in KEYWORDS:
        if keyword in text:
            return True

    return False

# ========= 記事フィルタリング =========
def fetch_articles():
    articles = []
    today = datetime.now(timezone.utc) - timedelta(days=1)

    for url in RSS_FEEDS:
        print(f"Fetching RSS: {url}")

        feed = feedparser.parse(url, request_headers={
            "User-Agent": "Mozilla/5.0 (AI Trend Monitor)"
        })

        print(f"Entries found: {len(feed.entries)}")

        for entry in feed.entries:
            if "published" in entry:
                published = parser.parse(entry.published)

                if published < today:
                    continue

            title = entry.title
            if "summary" in entry:
                summary = entry.summary
            elif "description" in entry:
                summary = entry.description
            summary = clean_html(summary)
            summary = summary[:500]   # 長すぎ防止

            if "arxiv.org" not in url:
                text = (title + " " + summary[:200]).lower()
                if not is_ai_related(text):
                    continue
        
            articles.append({
                "title": title,
                "link": entry.link,
                "summary": summary
            })

    print(f"Total articles: {len(articles)}")
    return articles

# ========= HTML除去 =========
def clean_html(text):
    if not text:
        return ""
    text = re.sub("<.*?>", "", text)  # HTMLタグ削除
    text = text.replace("\n", " ").strip()
    return text

# ========= 記事重複削除 =========
def remove_duplicates(articles):

    seen = set()
    unique = []

    for article in articles:

        if article["link"] in seen:
            continue

        seen.add(article["link"])
        unique.append(article)

    return unique

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
    articles = remove_duplicates(fetch_articles())
    articles = articles[:MAX_ARTICLES]
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
