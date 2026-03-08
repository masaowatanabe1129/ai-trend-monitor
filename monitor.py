def generate_trend_summary(articles):

    import json

    text = "\n".join(
        f"{a['title']} - {a.get('summary','')}"
        for a in articles
    )

    prompt = f"""
You are an AI industry analyst.

Below are today's AI news headlines.

{text}

Analyze the AI ecosystem today.

Output in this format:

## Major Developments
(key events)

## Emerging Trends
(technical trends like agents, RAG, coding AI)

## Company Activity
(OpenAI, Google, Anthropic etc)

## Research Signals
(arXiv or academic trends)

Keep it concise.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":prompt}]
    )

    summary = response.choices[0].message.content

    with open("data/trend_summary.txt","w") as f:
        f.write(summary)
