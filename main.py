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
以下のAIニュースのタイトルを日本語で簡潔に要約してください。

タイトル:
{article["title"]}

出力:
2〜3行の日本語要約
"""
    
    try:

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role":"user","content":prompt}]
        )
    
        content = response.choices[0].message.content.strip()
    
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

# ========= trend summary =========

def generate_trend_summary(articles):

    text = "\n".join(a["title"] for a in articles)

    prompt = f"""
あなたはAI業界アナリストです。

以下は今日のAIニュースです。

{text}

日本語で分析してください。

出力:

【今日のAI業界サマリー】

【主要トレンド】

【AI企業の動き】

【研究トレンド】

簡潔に書いてください。
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":prompt}]
    )

    summary = response.choices[0].message.content

    with open("data/trend_summary.txt","w") as f:
        f.write(summary)

# ========= ランキング作成 =========

def generate_topic_ranking(articles):

    text = "\n".join(a["title"] for a in articles)

    prompt = f"""
以下は今日のAIニュースです。

{text}

ニュースからAI技術トピックを抽出してください。

例
Agent
RAG
AI coding
Open source LLM
Multimodal

出力形式(JSON):

[
{{"topic":"Agent","count":5}},
{{"topic":"RAG","count":3}}
]

最大5個。
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":prompt}]
    )

    import json

    try:
        ranking = json.loads(response.choices[0].message.content)
    except:
        ranking = []

    with open("data/topic_ranking.json","w") as f:
        json.dump(ranking,f)

# ========= GitHub AIツール取得 =========

def fetch_github_ai_tools():

    import requests

    url = "https://api.github.com/search/repositories"

    params = {
        "q":"AI agent OR LLM OR AI coding",
        "sort":"stars",
        "order":"desc",
        "per_page":5
    }

    r = requests.get(url,params=params)

    data = r.json()

    repos = []

    for repo in data.get("items",[]):

        repos.append({
            "name":repo["name"],
            "url":repo["html_url"],
            "stars":repo["stargazers_count"]
        })

    import json

    with open("data/github_ai.json","w") as f:
        json.dump(repos,f)

# ========= トレンド履歴を更新 =========

def update_trend_history():

    import json
    import os
    from datetime import datetime

    today = datetime.now().strftime("%Y-%m-%d")

    with open("data/topic_ranking.json") as f:
        today_topics = json.load(f)

    history_file = "data/topic_history.json"

    if os.path.exists(history_file):
        with open(history_file) as f:
            history = json.load(f)
    else:
        history = {}

    history[today] = today_topics

    with open(history_file,"w") as f:
        json.dump(history,f)

# ========= main =========

def main():

    today = datetime.now().strftime("%Y-%m-%d")   # ←これ追加

    articles = fetch_articles()

    articles = remove_duplicates(articles)

    articles = articles[:MAX_ARTICLES]

    results = []

    for article in articles:

        try:

            analysis = analyze_article(article)

            results.append({
                "title": article["title"],
                "link": article["link"],
                "analysis": analysis
            })

        except Exception as e:

            print("Article skipped:", e)
            continue


    trends = detect_trends(articles)
    
    save_results(results)
    
    save_trends(trends)
    
    generate_trend_summary(articles)
    
    generate_topic_ranking(articles)
    
    fetch_github_ai_tools()
    
    update_trend_history()

    import shutil
    
    shutil.copy(
        f"data/{today}.json",
        "data/latest.json"
    )

    print("Finished")

if __name__ == "__main__":
    main()
