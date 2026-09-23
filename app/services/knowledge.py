from dataclasses import dataclass


@dataclass(frozen=True)
class Document:
    id: str
    title: str
    text: str


DOCUMENTS = [
    Document("pricing", "Pricing", "LeadPilot CRM automation starts at ₹2,999/month for small teams. Custom plans are available for larger sales teams and integrations."),
    Document("features", "Features", "LeadPilot supports lead capture, qualification, follow-ups, CRM updates, WhatsApp workflows, email workflows and human handoff."),
    Document("integrations", "Integrations", "Common integrations include WhatsApp Business API, email, webhooks and CRM systems. Custom integrations can be scoped after a technical call."),
    Document("demo", "Demo", "A sales demo can be scheduled after the lead shares company size, current workflow and the primary sales bottleneck."),
]


def retrieve(query: str, k: int = 3) -> list[Document]:
    tokens = {t.lower() for t in query.replace("?", " ").replace(",", " ").split() if len(t) > 2}
    ranked = []
    for doc in DOCUMENTS:
        words = set(doc.text.lower().split())
        overlap = len(tokens & words)
        ranked.append((overlap, doc))
    ranked.sort(key=lambda x: x[0], reverse=True)
    return [doc for score, doc in ranked[:k] if score > 0] or DOCUMENTS[:1]
