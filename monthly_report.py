import os
import json
from datetime import datetime
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
target_month = today.strftime("%Y-%m")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ========= データ読み込み =========
all_articles = []

for file in os.listdir(DATA_DIR):
    if file.startswith(target_month) and file.endswith(".json"):
        with open(os.path.join(DATA_DIR, file), "r", encoding="utf-8") as f:
            all_articles.extend(json.load(f))

if not all_articles:
    print("No data for this month.")
    exit()

# ========= 集計 =========
categories = []
importance = []

for item in all_articles:
    analysis = item.get("analysis", {})
    categories.append(analysis.get("tech_category", "unknown"))
    importance.append(analysis.get("importance_score", 0))

top_categories = Counter(categories).most_common(5)
avg_importance = round(sum(importance)/len(importance), 2)

# ========= GPTで戦略要約生成 =========
summary_prompt = f"""
以下は今月のAI技術動向データです。

主要カテゴリ: {top_categories}
平均重要度: {avg_importance}

IT企業向けに
1. 今月の技術傾向
2. 事業インパクト
3. 来月の注視ポイント

を日本語で500文字程度でまとめてください。
"""

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": summary_prompt}],
    temperature=0.4
)

monthly_summary = response.choices[0].message.content

# ========= PDF生成 =========
output_file = f"{OUTPUT_DIR}/AI_Monthly_Report_{target_month}.pdf"

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

elements.append(Paragraph(f"AI戦略レポート（月次） {target_month}", title_style))
elements.append(Spacer(1, 0.3 * inch))
elements.append(Paragraph("■ 戦略サマリ", base_style))
elements.append(Spacer(1, 0.2 * inch))
elements.append(Paragraph(monthly_summary.replace("\n", "<br/>"), base_style))

doc.build(elements)

print(f"Generated: {output_file}")
