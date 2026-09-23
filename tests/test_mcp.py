import pytest
from fastmcp.client import Client

from app.mcp.server import mcp


@pytest.mark.asyncio
async def test_mcp_tools_are_exposed():
    async with Client(mcp) as client:
        tools = await client.list_tools()
    names = {tool.name for tool in tools}
    assert {"create_lead", "update_lead_score", "schedule_followup", "search_company_knowledge", "handoff_to_human"} <= names
