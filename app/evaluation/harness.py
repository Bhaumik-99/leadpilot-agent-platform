from dataclasses import dataclass

from app.agents.sales_agent import SalesAgent
from app.models.domain import AgentRequest, Channel, EvaluationResult


@dataclass(frozen=True)
class Scenario:
    id: str
    name: str
    messages: list[str]
    required_behaviors: list[str]
    forbidden_behaviors: list[str]


SCENARIOS = [
    Scenario(
        id="pricing_sensitive",
        name="Pricing-sensitive buyer",
        messages=[
            "We are a furniture manufacturer in Gurgaon.",
            "We have 15 salespeople and need CRM plus WhatsApp follow-ups.",
            "What is the price?",
        ],
        required_behaviors=["retain_context", "capture_team_size", "capture_requirement", "ground_pricing"],
        forbidden_behaviors=["invent_pricing"],
    ),
]


class EvaluationHarness:
    def __init__(self, agent: SalesAgent):
        self.agent = agent

    async def run(self, scenario: Scenario) -> dict:
        lead_id = None
        transcript = []
        for message in scenario.messages:
            response = await self.agent.handle(
                AgentRequest(lead_id=lead_id, channel=Channel.web, message=message)
            )
            lead_id = response.lead_id
            transcript.append({"user": message, "agent": response.reply})

        lead = self.agent.repo.get_lead(lead_id) if lead_id else None
        all_text = " ".join(item["agent"].lower() for item in transcript)
        checks = {
            "retain_context": bool(lead and lead.location == "Gurgaon"),
            "capture_team_size": bool(lead and lead.team_size == 15),
            "capture_requirement": bool(lead and "crm" in lead.requirements and "whatsapp" in lead.requirements),
            "ground_pricing": "₹2,999" in all_text or "2999" in all_text,
            "invent_pricing": "₹0" in all_text or "free forever" in all_text,
        }
        required = [checks[x] for x in scenario.required_behaviors]
        forbidden = [checks[x] for x in scenario.forbidden_behaviors]
        passed = all(required) and not any(forbidden)
        score = round(100 * sum(required) / max(len(required), 1), 2)
        return EvaluationResult(
            scenario_id=scenario.id,
            passed=passed,
            score=score,
            checks=checks,
            transcript=transcript,
            notes=["Forbidden behavior detected."] if any(forbidden) else [],
        ).model_dump(mode="json")
