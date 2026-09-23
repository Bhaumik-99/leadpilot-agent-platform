from fastapi import FastAPI, HTTPException

from app.agents.sales_agent import SalesAgent
from app.api.evaluation import router as evaluation_router
from app.config import get_settings
from app.mcp.server import mcp
from app.models.domain import AgentRequest
from app.storage.repository import Repository

settings = get_settings()
repo = Repository(settings.database_path)
agent = SalesAgent(repo, settings)

app = FastAPI(
    title="LeadPilot API",
    version="0.1.0",
    description="Autonomous SME sales agent platform",
)
app.state.agent = agent
app.state.repo = repo


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "leadpilot"}


@app.post("/v1/agent/respond")
async def respond(request: AgentRequest):
    return await agent.handle(request)


@app.get("/v1/leads/{lead_id}")
async def get_lead(lead_id: str):
    lead = repo.get_lead(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return {"lead": lead, "history": repo.history(lead_id)}


@app.get("/v1/leads/{lead_id}/audit")
async def get_audit(lead_id: str):
    if not repo.get_lead(lead_id):
        raise HTTPException(status_code=404, detail="Lead not found")
    return {"events": repo.audit_history(lead_id)}


@app.post("/v1/leads/{lead_id}/handoff")
async def handoff(lead_id: str):
    lead = repo.get_lead(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    lead.status = "handoff"
    repo.save_lead(lead)
    repo.audit(lead_id, "human_handoff", {"reason": "Requested from dashboard"})
    return {"ok": True, "lead": lead}


@app.get("/v1/mcp/tools")
async def mcp_tools():
    tools = await mcp.list_tools()
    return {"tools": [tool.name for tool in tools]}


app.include_router(evaluation_router)
