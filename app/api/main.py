from fastapi import FastAPI, HTTPException

from app.agents.sales_agent import SalesAgent
from app.config import get_settings
from app.models.domain import AgentRequest
from app.storage.repository import Repository
from app.mcp.server import mcp

settings = get_settings()
repo = Repository(settings.database_path)
agent = SalesAgent(repo, settings)

app = FastAPI(title="LeadPilot API", version="0.1.0", description="Autonomous SME sales agent platform")


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


@app.get("/v1/mcp/tools")
async def mcp_tools():
    tools = await mcp.list_tools()
    return {"tools": [tool.name for tool in tools]}


from app.api.evaluation import router as evaluation_router
app.include_router(evaluation_router)
