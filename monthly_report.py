import os
import json
from datetime import datetime, timedelta
from collections import Counter
from openai import OpenAI
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase import pdfmetrics

# ========= 設定 =========
DATA_DIR = "data"
OUTPUT_DIR = "reports"
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

today = datetime.now()
current_month = today.strftime("%Y-%m")
last_month_date = today.replace(day=1) - timedelta(days=1)
last_month = last_month_date.strftime("%Y-%m")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ========= データ読み込み =========
def load_month_data(target_month):
    articles = []
    if not os.path.exists(DATA_DIR):
        return articles

    for file in os.listdir(DATA_DIR):
        if file.startswith(target_month) and file.endswith(".json"):
            with open(os.path.join(DATA_DIR, file), "r", encoding="utf-8") as f:
                articles.extend(json.load(f))
    return articles

current_articles = load_month_data(current_month)
last_articles = load_month_data(last_month)

if not current_articles:
    print("No current month data.")
    exit()

# ========= 集計 =========
def extract_categories(articles):
    categories = []
    for item in articles:
        analysis = item.get("analysis", {})
        categories.append(analysis.get("tech_category", "unknown"))
    return Counter(categories)

current_counter = extract_categories(current_articles)
last_counter = extract_categories(last_articles)

# ========= 差分検出 =========
trend_increase = []
trend_decrease = []
trend_new = []

for category, count in current_counter.items():
    last_count = last_counter.get(category, 0)
    if last_count == 0:
        trend_new.append(category)
    elif count > last_count:
        trend_increase.append((category, count - last_count))

for category, count in last_counter.items():
    if category not in current_counter:
        trend_decrease.append(category)

trend_increase = sorted(trend_increase, key=lambda x: x[1], reverse=True)[:5]

# ========= GPTで戦略分析 =========
analysis_prompt = f"""
以下はAIトレンドの月次変化データです。

今月カテゴリ件数: {current_counter}
先月カテゴリ件数: {last_counter}

急上昇分野: {trend_increase}
新規出現分野: {trend_new}
減少分野: {trend_decrease}

IT企業向けに
1. この変化の意味
2. 事業インパクト
3. 来月の戦略アクション

を600文字程度でまとめてください。
"""

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": analysis_prompt}],
    temperature=0.4
)

trend_summary = response.choices[0].message.content

# ========= PDF生成 =========
output_file = f"{OUTPUT_DIR}/AI_Monthly_Report_{current_month}.pdf"

pdfmetrics.registerFont(UnicodeCIDFont("HeiseiMin-W3"))

doc = SimpleDocTemplate(output_file)
elements = []

styles = getSampleStyleSheet()
base_style = ParagraphStyle(
    'Base',
    parent=styles['Normal'],
    fontName="HeiseiMin-W3",
    fontSize=11
)

title_style = ParagraphStyle(
    'Title',
    parent=styles['Heading1'],
    fontName="HeiseiMin-W3",
    fontSize=18
)

elements.append(Paragraph(f"AI戦略レポート（月次） {current_month}", title_style))
elements.append(Spacer(1, 0.3 * inch))

elements.append(Paragraph("■ トレンド変化分析", base_style))
elements.append(Spacer(1, 0.2 * inch))

elements.append(Paragraph(trend_summary.replace("\n", "<br/>"), base_style))

doc.build(elements)

print(f"Generated: {output_file}")
