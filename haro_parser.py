import re

# High-authority niche keywords (business + tech + energy + consumer)
NICHE_KEYWORDS = [
    # Business & Finance
    "business", "budget", "budgeting", "small business", "startup",
    "entrepreneur", "founder", "scaling", "cash flow", "financial planning",
    "cost of living", "inflation", "personal finance", "saving money",
    "household expenses", "economy", "economic trends", "market trends",
    "productivity", "leadership", "remote work", "future of work",
    "subscription management", "recurring payments", "digital wallets",
    "investing", "stocks", "cryptocurrency", "financial technology", "wealth management",
    "financial literacy", "expense tracking", "payment apps", "fintech apps",
    "cost optimization", "business strategy", "economic development",

    # Technology & Digital Transformation
    "ai", "artificial intelligence", "automation", "cloud",
    "digital transformation", "cybersecurity", "data", "saas",
    "workflow automation", "tech trends", "digital payments", "fintech",
    "iot", "smart devices", "home automation", "smart home",
    "mobile apps", "online services", "payment apps", "digital innovation",
    "big data", "machine learning", "blockchain", "tech adoption", "remote tech",
    "app development", "digital workflow", "cloud computing", "software solutions",
    "emerging technologies", "tech infrastructure", "IT solutions", "smart gadgets",

    # Energy, Utilities & Sustainability
    "electricity", "energy", "power", "utility", "utilities",
    "renewable", "solar", "wind", "hydro", "smart meter", "smart home",
    "energy efficiency", "energy saving", "electricity prices",
    "electricity rates", "billing", "digital billing", "online billing",
    "sustainability", "climate", "carbon footprint", "green energy",
    "energy crisis", "energy policy", "public utilities", "infrastructure",
    "smart city", "load shedding", "energy consumption", "grid management",
    "energy technology", "energy apps", "metering solutions", "demand response",
    "electric vehicles", "battery storage", "power management", "smart grids",
    "home energy management", "eco-friendly energy", "renewable adoption",

    # Consumer Behavior & Lifestyle
    "consumer", "consumer behavior", "consumer rights",
    "household management", "money saving tips", "budgeting habits",
    "financial literacy", "daily expenses", "energy habits", "utility management",
    "lifestyle tech", "eco-friendly living", "cost-conscious behavior",
    "smart spending", "home efficiency", "digital lifestyle", "app usage trends",
    "shopping habits", "subscription services", "home budgeting",
    "personal finance management", "financial planning", "habit tracking",
    "cost reduction", "consumer trends", "behavioral insights", "lifestyle apps",

    # Emerging Markets & Global Trends
    "emerging markets", "developing countries", "global trends",
    "international comparisons", "digital adoption", "fintech adoption",
    "energy solutions abroad", "utility access", "tech in developing countries",
    "household tech trends", "global electricity trends", "cross-country analysis",
    "economic development", "financial inclusion", "energy inclusion",
    "mobile payment adoption", "digital literacy", "smart city trends",
    "energy efficiency worldwide", "international case studies", "market adoption",
    "cross-border innovation", "global consumer behavior",

    # Policy, Regulation & Economics
    "energy policy", "electricity regulation", "public utilities",
    "tariff structures", "subsidies", "energy economics",
    "price inflation", "market regulations", "utility governance",
    "policy impact", "renewable incentives", "infrastructure development",
    "government programs", "energy reforms", "economic policy",
    "legislation", "regulatory compliance", "environmental policy",
    "climate regulations", "utility pricing", "policy analysis",
    "tax incentives", "budget policy", "fiscal policy", "international policy",

    # Smart Home & Internet of Things (IoT)
    "home automation", "smart appliances", "connected home", "iot devices",
    "energy tracking", "home security", "automation apps", "remote monitoring",
    "smart thermostats", "connected utilities", "smart lighting",
    "household sensors", "tech-enabled living", "smart hubs",
    "data-driven home management", "AI in home", "smart gadget adoption",
    "smart energy solutions", "smart grids", "home innovation", "automation trends",

    # Sustainability & Environment
    "renewable energy", "solar power", "wind energy", "carbon footprint",
    "energy efficiency", "green tech", "eco-friendly solutions",
    "climate change", "sustainable living", "environmental responsibility",
    "green homes", "carbon reduction", "eco-conscious behavior",
    "smart cities", "environmental policy", "sustainable tech",
    "clean energy adoption", "green innovation", "energy conservation",
    "eco apps", "green initiatives", "sustainable households",

    # Finance & Tech in Emerging Markets
    "fintech adoption", "mobile payments", "digital banking", "financial inclusion",
    "recurring payments", "digital wallets", "microfinance", "mobile money",
    "billing solutions", "utility tech", "smart payment apps",
    "cross-border fintech trends", "digital infrastructure", "cashless solutions",
    "economic empowerment", "digital transformation emerging markets",
    "financial literacy", "payment automation", "app-based payments", "online banking"
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
