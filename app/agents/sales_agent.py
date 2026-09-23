import uuid
from typing import Any

from app.config import Settings
from app.models.domain import AgentRequest, AgentResponse, Channel, Lead, LeadStatus, Message
from app.services.knowledge import retrieve
from app.services.llm import LLMClient
from app.services.scoring import extract_facts, score_lead, update_status
from app.storage.repository import Repository


class SalesAgent:
    def __init__(self, repo: Repository, settings: Settings):
        self.repo = repo
        self.llm = LLMClient(settings)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        trace_id = f"TR-{uuid.uuid4().hex[:10]}"
        lead = self.repo.get_lead(request.lead_id) if request.lead_id else None
        if not lead:
            lead = Lead(id=f"LD-{uuid.uuid4().hex[:8].upper()}")

        for field in ("name", "company", "phone", "email"):
            value = getattr(request, field)
            if value:
                setattr(lead, field, value)
        lead.channel = request.channel
        lead = extract_facts(request.message, lead)
        lead.score, reasons = score_lead(lead)
        lead = update_status(lead)
        self.repo.save_lead(lead)
        self.repo.add_message(Message(lead_id=lead.id, role="user", content=request.message, channel=request.channel))

        context = retrieve(request.message)
        actions: list[dict[str, Any]] = []
        missing = self._missing_fields(lead)
        reply = self._fallback_reply(lead, request.message, missing, context)

        decision = await self.llm.structured_decision(
            "You are a sales qualification agent. Return JSON with keys reply, intent, "
            "needs_human, followup_hours. Never invent pricing or capabilities. Ask at most "
            "two useful questions at a time.",
            self._prompt(lead, request.message, context, missing),
        )
        if decision and decision.get("reply"):
            reply = str(decision["reply"])
            if decision.get("needs_human"):
                lead.status = LeadStatus.human_handoff
                actions.append({"tool": "handoff_to_human", "reason": "LLM requested human handoff"})
            if decision.get("followup_hours"):
                actions.append({"tool": "schedule_followup", "hours": int(decision["followup_hours"])})

        if lead.score >= 70 and "schedule_followup" not in {a.get("tool") for a in actions}:
            actions.append({"tool": "schedule_followup", "hours": 24})

        self.repo.save_lead(lead)
        self.repo.add_message(Message(lead_id=lead.id, role="assistant", content=reply, channel=request.channel))
        self.repo.audit(lead.id, "agent.turn", {"trace_id": trace_id, "score_reasons": reasons, "actions": actions})
        return AgentResponse(lead_id=lead.id, reply=reply, lead=lead, actions=actions, trace_id=trace_id)

    @staticmethod
    def _missing_fields(lead: Lead) -> list[str]:
        missing = []
        if not lead.company:
            missing.append("company")
        if not lead.requirements:
            missing.append("primary requirement")
        if not lead.team_size:
            missing.append("team size")
        if not lead.budget:
            missing.append("budget")
        return missing

    @staticmethod
    def _fallback_reply(lead: Lead, message: str, missing: list[str], context: list) -> str:
        lower = message.lower()
        if any(x in lower for x in ["price", "pricing", "cost"]):
            pricing = next((d.text for d in context if d.id == "pricing"), "Pricing depends on scope.")
            return f"{pricing} Could you share your team size and the main sales workflow you want to automate?"
        if lead.score >= 70:
            return "Thanks — I have enough context to qualify this as a strong sales lead. What is the main workflow you want automated first, and would you like a demo?"
        if missing:
            questions = missing[:2]
            return "I can help with that. To recommend the right setup, could you share " + " and ".join(questions) + "?"
        return "Got it. I have captured the requirement. What outcome would make this automation successful for your team?"

    @staticmethod
    def _prompt(lead: Lead, message: str, context: list, missing: list[str]) -> str:
        knowledge = "\n".join(f"- {d.title}: {d.text}" for d in context)
        return f"Lead: {lead.model_dump_json()}\nMissing: {missing}\nUser: {message}\nKnowledge:\n{knowledge}"
