import json
import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def load_persona(path="persona.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


PERSONA = load_persona()


def truncate_text(text: str, max_chars: int = 3500) -> str:
    if not text:
        return ""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n\n...[TRUNCATED]..."


def generate_pitch(query: dict) -> str:
    safe_query = truncate_text(query.get("query", ""), max_chars=3500)

    system_msg = (
        f"You are {PERSONA['name']}, {PERSONA['title']} at "
        f"{PERSONA['company']} ({PERSONA['website']}). "
        f"Respond as a credible expert, concise and quotable."
    )

    user_prompt = f"""
Publication: {query.get('publication', '')}
Title: {query.get('title', '')}

Query (truncated for safety):
{safe_query}

Write a concise HARO pitch:
- 2 short paragraphs max
- Include 1 clear, quotable sentence
- Stay relevant to consumer utilities, energy, digital billing, personal finance, technology, or business
- Do NOT make up fake data or case studies
- End with this signature:

{PERSONA['name']}
{PERSONA['title']}
{PERSONA['company']}
{PERSONA['website']}
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=350
        )
    except Exception as e:
        print("⚠️ 70B model failed, switching to 8B:", e)

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=350
        )

    # Groq client returns .choices[0].message.content
    content = response.choices[0].message["content"]
    return content.strip()
