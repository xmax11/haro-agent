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


def is_relevant_query(text: str) -> bool:
    if not text:
        return False
    lower = text.lower()
    return any(keyword in lower for keyword in NICHE_KEYWORDS)


def extract_queries(email_body: str):
    """
    Extract individual HARO queries from a HARO email body.
    Assumes blocks starting with 'Summary:' as usual HARO format.
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

        queries.append({
            "title": summary.group(1).strip() if summary else "",
            "publication": category.group(1).strip() if category else "",
            "query": query.group(1).strip() if query else ""
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
