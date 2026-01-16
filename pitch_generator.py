import json
import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def load_persona(path="persona.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


BASE_PERSONA = load_persona()


def truncate_text(text: str, max_chars: int = 3500) -> str:
    if not text:
        return ""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n\n...[TRUNCATED]..."


def generate_dynamic_persona(query: dict) -> dict:
    """
    Generate a dynamic expert persona based on the query's niche/topic.
    This makes the responder appear as an expert in the specific field.
    """
    safe_query = truncate_text(query.get("query", ""), max_chars=1500)
    safe_title = query.get("title", "")[:200]
    
    persona_prompt = f"""
Based on this HARO query, create a professional expert persona that would be credible for responding:

Title: {safe_title}
Query: {safe_query[:800]}

Generate a JSON object with:
- "name": A professional first name (use "{BASE_PERSONA['name']}" as the name)
- "title": A specific expert title relevant to the query topic (e.g., "Energy Efficiency Specialist", "Personal Finance Advisor", "Digital Transformation Consultant")
- "company": A credible company name (use "{BASE_PERSONA['company']}" format, or create a relevant one)
- "website": Use exactly "{BASE_PERSONA['website']}" as the website URL
- "expertise": One sentence describing their specific expertise in the query's domain

Make the title and expertise highly relevant to the query topic. Be specific and credible.
Respond ONLY with valid JSON, no other text.
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a persona generator. Respond only with valid JSON."},
                {"role": "user", "content": persona_prompt}
            ],
            temperature=0.7,
            max_tokens=300
        )
        persona_json = response.choices[0].message.content.strip()
        
        # Remove markdown code blocks if present
        if persona_json.startswith("```"):
            persona_json = persona_json.split("```")[1]
            if persona_json.startswith("json"):
                persona_json = persona_json[4:]
        persona_json = persona_json.strip()
        
        dynamic_persona = json.loads(persona_json)
        
        # Ensure base fields exist - always use base website
        dynamic_persona["name"] = dynamic_persona.get("name", BASE_PERSONA["name"])
        dynamic_persona["company"] = dynamic_persona.get("company", BASE_PERSONA["company"])
        dynamic_persona["website"] = BASE_PERSONA["website"]  # Always use base website
        
        return dynamic_persona
        
    except Exception as e:
        print(f"⚠️ Failed to generate dynamic persona, using base persona: {e}")
        return BASE_PERSONA


def generate_pitch(query: dict) -> str:
    safe_query = truncate_text(query.get("query", ""), max_chars=3500)
    
    # Generate dynamic persona based on query niche
    persona = generate_dynamic_persona(query)
    
    expertise_note = ""
    if "expertise" in persona:
        expertise_note = f" Your expertise: {persona['expertise']}"
    
    system_msg = (
        f"You are {persona['name']}, {persona['title']} at "
        f"{persona['website']}.{expertise_note} "
        f"Write like a real human expert - direct, conversational, and helpful. No marketing fluff or buzzwords."
    )

    user_prompt = f"""
Publication: {query.get('publication', '')}
Title: {query.get('title', '')}

Query:
{safe_query}

Write a direct, human-sounding response that answers the query:
- Be direct and to the point - answer the question asked, no fluff
- Use natural, conversational language like you're talking to a colleague
- Keep it short (1-2 short paragraphs maximum)
- Include one clear, quotable sentence that directly addresses their question
- Sound human and easy to understand - avoid corporate jargon
- Do NOT make up fake data, statistics, or case studies
- Do NOT add unnecessary background or sales pitches
- Just answer what they're asking for in a helpful, expert way
- IMPORTANT: Write complete, full sentences - do not cut off mid-sentence

End with this complete signature:

{persona['name']}
{persona['title']}
{persona['website']}
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=600
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
            max_tokens=600
        )

    # Groq client returns .choices[0].message.content
    content = response.choices[0].message.content
    return content.strip()
