import feedparser
import json
import os
import re
from collections import Counter
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

    # news
    "https://www.marktechpost.com/feed/",
    "https://www.artificialintelligence-news.com/feed/",
    "https://venturebeat.com/category/ai/feed/",

    # github
    "https://mshibanami.github.io/GitHubTrendingRSS/daily/all.xml",
]

KEYWORDS = [

    # coding AI
    "code generation",
    "ai coding",
    "developer ai",
    "ai programming",

    # models
    "gpt",
    "claude",
    "gemini",
    "llama",

    # frameworks
    "langchain",
    "llm agent",
    "rag",

    # tools
    "copilot",
    "cursor",
]

MAX_FEED_ARTICLES = 10
MAX_ARTICLES = 20

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ========= HTML除去 =========

def clean_html(text):

    if not text:
        return ""

    text = re.sub("<.*?>", "", text)
    text = text.replace("\n", " ")
    return text.strip()


# ========= AI関連判定 =========

def is_ai_related(text):

    text = text.lower()

    for keyword in KEYWORDS:
        if keyword in text:
            return True

    return False


# ========= RSS取得 =========

def fetch_articles():

    articles = []
    today = datetime.now(timezone.utc) - timedelta(days=1)

    for url in RSS_FEEDS:

        try:

            print(f"Fetching RSS: {url}")

            feed = feedparser.parse(
                url,
                request_headers={"User-Agent": "AI-Trend-Monitor"}
            )

            print(f"Entries found: {len(feed.entries)}")

            for entry in feed.entries[:MAX_FEED_ARTICLES]:

                try:

                    if "published" in entry:

                        published = parser.parse(entry.published)

                        if published < today:
                            continue

                    title = entry.title

                    summary = ""

                    if "summary" in entry:
                        summary = entry.summary
                    elif "description" in entry:
                        summary = entry.description

                    summary = clean_html(summary)[:500]

                    if "arxiv.org" not in url:

                        text = (title + " " + summary[:200]).lower()

                        if not is_ai_related(text):
                            continue

                    articles.append({
                        "title": title,
                        "link": entry.link,
                        "summary": summary
                    })

                except Exception as e:
                    print("Entry skipped:", e)
                    continue

        except Exception as e:
            print("Feed error:", e)
            continue

    print("Total collected:", len(articles))
    return articles


# ========= 重複削除 =========

def remove_duplicates(articles):

    seen = set()
    unique = []

    for article in articles:

        if article["link"] in seen:
            continue

        seen.add(article["link"])
        unique.append(article)

    return unique


# ========= GPT分析 =========

def analyze_article(article):

    prompt = f"""
記事をIT企業向けに分析してください

タイトル:
{article['title']}

概要:
{article['summary']}

JSONで出力:

{{
"tech_category":"",
"tech_maturity":"research/beta/production",
"si_business_fit":1-5,
"internal_poc_feasibility":1-5,
"importance_score":1-5,
"summary_200j":""
}}
"""

    try:

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role":"user","content":prompt}],
            temperature=0.3
        )

        content = response.choices[0].message.content

        try:
            return json.loads(content)

        except:
            return {"error":"json_parse","raw":content}

    except Exception as e:

        print("OpenAI error:", e)
        return {"error":"openai_failed"}


# ========= トレンド検出 =========

def detect_trends(articles):

    text = ""

    for a in articles:
        text += a["title"] + " " + a["summary"] + " "

    text = text.lower()

    words = re.findall(r"[a-zA-Z]{4,}", text)

    counter = Counter(words)

    trends = counter.most_common(20)

    return trends


# ========= 保存 =========

def save_results(results):

    os.makedirs("data", exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")

    filename = f"data/{today}.json"

    with open(filename,"w",encoding="utf-8") as f:
        json.dump(results,f,ensure_ascii=False,indent=2)


def save_trends(trends):

    os.makedirs("data", exist_ok=True)

    filename = "data/trends.json"

    with open(filename,"w") as f:
        json.dump(trends,f,indent=2)


# ========= main =========

def main():

    articles = fetch_articles()

    articles = remove_duplicates(articles)

    articles = articles[:MAX_ARTICLES]

    results = []

    for article in articles:

        try:

            analysis = analyze_article(article)

            results.append({
                "title":article["title"],
                "link":article["link"],
                "analysis":analysis
            })

        except Exception as e:

            print("Article skipped:", e)
            continue


    trends = detect_trends(articles)

    save_results(results)

    save_trends(trends)

    import shutil
    
    shutil.copy(
        f"data/{today}.json",
        "data/latest.json"
    )

    print("Finished")

if __name__ == "__main__":
    main()
