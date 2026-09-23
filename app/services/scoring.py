import re

from app.models.domain import Lead, LeadStatus


def score_lead(lead: Lead) -> tuple[int, list[str]]:
    score = 10
    reasons: list[str] = []
    if lead.company:
        score += 15
        reasons.append("company identified")
    if lead.team_size:
        score += min(20, lead.team_size)
        reasons.append("team size identified")
    if lead.budget:
        score += 20
        reasons.append("budget identified")
    if lead.requirements:
        score += min(20, len(lead.requirements) * 7)
        reasons.append("requirements identified")
    if lead.email or lead.phone:
        score += 10
        reasons.append("contact information available")
    if lead.location:
        score += 5
        reasons.append("location identified")
    return min(score, 100), reasons


def extract_facts(text: str, lead: Lead) -> Lead:
    lowered = text.lower()
    lead = lead.model_copy(deep=True)
    if not lead.company:
        match = re.search(r"(?:company|business|firm)\s+(?:is|called)?\s*([A-Za-z0-9&. -]{3,50})", text, re.I)
        if match:
            lead.company = match.group(1).strip(" .,")
    if not lead.location:
        cities = ["gurgaon", "gurugram", "delhi", "noida", "mumbai", "bangalore", "hyderabad", "jaipur"]
        for city in cities:
            if city in lowered:
                lead.location = city.title()
                break
    if not lead.team_size:
        match = re.search(r"(?:team|people|employees|salespeople)\D{0,10}(\d{1,4})", lowered)
        if match:
            lead.team_size = int(match.group(1))
    if not lead.budget:
        match = re.search(r"(?:budget|₹|rs\.?|inr)\s*([\d,]+(?:\.\d+)?)\s*(k|l|lakh|lakhs|cr|crore)?", lowered)
        if match:
            lead.budget = match.group(0).strip()
    known = [
        "crm", "whatsapp", "lead management", "automation", "sales", "inventory", "erp",
        "follow-up", "follow up", "pricing", "demo", "integration",
    ]
    for item in known:
        if item in lowered and item not in lead.requirements:
            lead.requirements.append(item)
    return lead


def update_status(lead: Lead) -> Lead:
    lead = lead.model_copy(deep=True)
    if lead.score >= 70:
        lead.status = LeadStatus.qualified
    elif lead.score >= 45:
        lead.status = LeadStatus.qualifying
    else:
        lead.status = LeadStatus.nurture
    return lead
