from app.models.domain import Lead
from app.services.scoring import extract_facts, score_lead, update_status


def test_extracts_sales_facts():
    lead = Lead(id="LD-1")
    lead = extract_facts("We have a team of 15 in Gurgaon and need CRM automation", lead)
    assert lead.team_size == 15
    assert lead.location == "Gurgaon"
    assert "crm" in lead.requirements


def test_high_score_becomes_qualified():
    lead = Lead(id="LD-1", company="Acme", team_size=15, budget="₹50k", requirements=["crm"], email="a@b.com")
    score, _ = score_lead(lead)
    lead.score = score
    lead = update_status(lead)
    assert lead.status.value == "qualified"
    assert score >= 70
