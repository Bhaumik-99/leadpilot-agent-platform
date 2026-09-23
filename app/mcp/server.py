from datetime import datetime, timedelta, timezone

from fastmcp import FastMCP

from app.config import get_settings
from app.models.domain import Lead, LeadStatus
from app.services.knowledge import retrieve
from app.storage.repository import Repository

mcp = FastMCP("LeadPilot CRM Tools")
_repo = Repository(get_settings().database_path)


@mcp.tool
def create_lead(name: str | None = None, company: str | None = None, phone: str | None = None, email: str | None = None) -> dict:
    """Create a new CRM lead and return its identifier."""
    import uuid
    lead = Lead(id=f"LD-{uuid.uuid4().hex[:8].upper()}", name=name, company=company, phone=phone, email=email)
    _repo.save_lead(lead)
    _repo.audit(lead.id, "lead.created", {"company": company, "name": name})
    return {"lead_id": lead.id, "status": "created"}


@mcp.tool
def update_lead_score(lead_id: str, score: int, reason: str) -> dict:
    """Update a lead score and lifecycle status."""
    lead = _repo.get_lead(lead_id)
    if not lead:
        return {"error": "lead_not_found", "lead_id": lead_id}
    lead.score = max(0, min(score, 100))
    lead.status = LeadStatus.qualified if lead.score >= 70 else LeadStatus.qualifying if lead.score >= 45 else LeadStatus.nurture
    _repo.save_lead(lead)
    _repo.audit(lead.id, "lead.scored", {"score": lead.score, "reason": reason})
    return {"lead_id": lead.id, "score": lead.score, "status": lead.status.value, "reason": reason}


@mcp.tool
def schedule_followup(lead_id: str, hours: int = 24, reason: str = "sales follow-up") -> dict:
    """Schedule a follow-up and return the planned time."""
    if not _repo.get_lead(lead_id):
        return {"error": "lead_not_found", "lead_id": lead_id}
    when = datetime.now(timezone.utc) + timedelta(hours=max(1, hours))
    _repo.audit(lead_id, "followup.scheduled", {"when": when.isoformat(), "reason": reason})
    return {"lead_id": lead_id, "scheduled_for": when.isoformat(), "reason": reason}


@mcp.tool
def search_company_knowledge(query: str) -> dict:
    """Retrieve relevant product/company knowledge for grounded answers."""
    docs = retrieve(query)
    return {"results": [{"id": d.id, "title": d.title, "text": d.text} for d in docs]}


@mcp.tool
def handoff_to_human(lead_id: str, reason: str) -> dict:
    """Mark a lead for human sales handoff."""
    lead = _repo.get_lead(lead_id)
    if not lead:
        return {"error": "lead_not_found", "lead_id": lead_id}
    lead.status = LeadStatus.human_handoff
    _repo.save_lead(lead)
    _repo.audit(lead.id, "lead.handoff", {"reason": reason})
    return {"lead_id": lead_id, "status": "human_handoff", "reason": reason}
