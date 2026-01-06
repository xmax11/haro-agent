import re

# High-authority niche keywords (business + tech + energy + consumer)
NICHE_KEYWORDS = [
    # Business & Finance
    "business", "budget", "budgeting", "small business", "startup",
    "entrepreneur", "founder", "scaling", "cash flow", "financial planning",
    "cost of living", "inflation", "personal finance", "saving money",
    "household expenses", "economy", "economic trends", "market trends",
    "productivity", "leadership", "remote work", "future of work",

    # Technology & Digital Transformation
    "ai", "artificial intelligence", "automation", "cloud",
    "digital transformation", "cybersecurity", "data", "saas",
    "workflow automation", "tech trends", "digital payments", "fintech",

    # Energy, Utilities & Sustainability
    "electricity", "energy", "power", "utility", "utilities",
    "renewable", "solar", "smart meter", "smart home",
    "energy efficiency", "energy saving", "electricity prices",
    "electricity rates", "billing", "digital billing", "online billing",
    "sustainability", "climate", "carbon footprint", "green energy",
    "energy crisis", "energy policy", "public utilities", "infrastructure",
    "smart city",

    # Consumer Behavior
    "consumer", "consumer behavior", "consumer rights"
]

# Excluded niches (betting, casino, gambling)
EXCLUDED_KEYWORDS = [
    "betting", "casino", "gambling", "poker", "blackjack", "roulette",
    "sportsbook", "sports betting", "online casino", "slot machine",
    "lottery", "bingo", "wager", "wagering", "odds", "bookmaker",
    "bet", "punt", "stakes", "jackpot"
]


def is_excluded_query(text: str) -> bool:
    """
    Check if query contains excluded keywords (betting, casino, gambling).
    Returns True if query should be excluded.
    """
    if not text:
        return False
    lower = text.lower()
    return any(keyword in lower for keyword in EXCLUDED_KEYWORDS)


def is_relevant_query(text: str) -> bool:
    if not text:
        return False
    
    # First check if it's excluded (betting/casino)
    if is_excluded_query(text):
        return False
    
    # Then check if it matches our niche keywords
    lower = text.lower()
    return any(keyword in lower for keyword in NICHE_KEYWORDS)


def extract_queries(email_body: str):
    """
    Extract individual HARO queries from a HARO email body.
    Assumes blocks starting with 'Summary:' as usual HARO format.
    Each query block has its own 'Email:' address.
    """
    blocks = re.split(r"(?=Summary:)", email_body, flags=re.IGNORECASE)
    queries = []

    for block in blocks:
        if len(block.strip()) < 20:
            continue

        summary = re.search(r"Summary:(.*)", block, re.IGNORECASE)
        category = re.search(r"Category:(.*)", block, re.IGNORECASE)
        query = re.search(r"Query:(.*?)(?=Requirements:|$)", block,
                          re.IGNORECASE | re.DOTALL)
        # Extract reply-to address from this query block
        reply_to_match = re.search(r"Email:\s*([^\s]+)", block, re.IGNORECASE)
        reply_to = reply_to_match.group(1).strip() if reply_to_match else None

        queries.append({
            "title": summary.group(1).strip() if summary else "",
            "publication": category.group(1).strip() if category else "",
            "query": query.group(1).strip() if query else "",
            "reply_to": reply_to
        })

    return queries


def parse_haro_email(email_body: str):
    """
    Extract all queries and filter them by niche relevance.
    Returns only the ones worth pitching.
    """
    all_queries = extract_queries(email_body)
    relevant = []

    for q in all_queries:
        if is_relevant_query(q["query"]):
            relevant.append(q)

    return relevant
