def generate_trend_summary(articles):

    text = "\n".join(
        f"{a['title']}"
        for a in articles
    )

    prompt = f"""
あなたはAI業界のアナリストです。

以下は今日のAIニュースです。

{text}

次の形式で日本語で分析してください。

【今日のAI業界サマリー】

【主要トレンド】
箇条書き3〜5個

【AI企業の動き】
OpenAI / Google / Anthropic / Metaなど

【研究トレンド】
論文や研究の動き

簡潔に書いてください。
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":prompt}]
    )

    summary = response.choices[0].message.content

    with open("data/trend_summary.txt","w") as f:
        f.write(summary)
