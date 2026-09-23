# LeadPilot

**LeadPilot** is an agentic SME sales platform built to demonstrate production-style agent engineering: FastAPI services, FastMCP tool servers, structured lead state, grounded retrieval, multi-turn conversations, CRM actions, and an evaluation harness.

It is intentionally designed around a concrete sales workflow rather than a generic chatbot.

## Why this project

- Inbound lead qualification across web, WhatsApp/email-compatible channels and voice-ready abstractions.
- FastAPI API layer.
- FastMCP CRM/workflow tools.
- Custom agent loop with optional OpenAI structured-output reasoning.
- Local RAG-style knowledge retrieval for grounded answers.
- Persistent SQLite CRM state.
- Multi-turn evaluation scenarios and regression checks.
- Trace/audit events for debugging agent decisions.

## Architecture

```text
Inbound Lead
    |
    v
FastAPI Gateway
    |
    v
Sales Agent -----> Knowledge Retrieval
    |
    +-------------> FastMCP Tools
    |                  + create_lead
    |                  + update_lead_score
    |                  + schedule_followup
    |                  + search_company_knowledge
    |                  + handoff_to_human
    |
    v
SQLite CRM + Audit Log
    |
    v
Evaluation Harness
```

## Quick start

Python 3.11+ is recommended.

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
uvicorn app.api.main:app --reload
```

API docs: `http://127.0.0.1:8000/docs`

## Try the agent

```bash
curl -X POST http://127.0.0.1:8000/v1/agent/respond \
  -H "Content-Type: application/json" \
  -d '{"message":"Hi, we are a furniture manufacturer in Gurgaon with 15 salespeople. We need a CRM and want pricing.","channel":"whatsapp"}'
```

The response includes the lead ID, structured lead state, actions, and an execution trace ID.

## Run the evaluation harness

```bash
pytest -q
```

Or run a scenario through the API:

```bash
curl -X POST http://127.0.0.1:8000/v1/evaluation/run/pricing_sensitive
```

## Run FastMCP

FastMCP 4 is used for the tool server. The MCP server can be run using the FastMCP CLI:

```bash
fastmcp run app/mcp/server.py:mcp
```

## Optional LLM mode

Set `OPENAI_API_KEY` in `.env`. The agent will use structured JSON output for the final response decision. Without a key, LeadPilot runs its deterministic fallback policy so the demo and tests still work locally.

## Project structure

```text
app/
├── agents/       # agent orchestration and conversation policy
├── api/          # FastAPI HTTP endpoints
├── evaluation/   # multi-turn agent evaluation harness
├── mcp/          # FastMCP tool server
├── models/       # Pydantic domain models
├── services/     # scoring, retrieval, LLM adapter
└── storage/      # SQLite repository + audit log

tests/            # API, MCP and scoring tests
```

## Roadmap

1. WhatsApp Business API adapter.
2. Email ingestion and outbound provider.
3. Voice adapter (STT -> agent -> TTS).
4. Redis-backed session state.
5. PostgreSQL + pgvector production storage.
6. Human approval tool for high-impact CRM actions.
7. Agent trace dashboard.
8. Dev-pipeline agent: requirement -> plan -> implementation -> PR review.
9. Golden conversation regression suite with LLM-as-judge.

## Engineering notes

Secrets belong in environment variables; do not commit `.env` or API keys. FastAPI's settings pattern supports environment-based configuration, and FastMCP provides native tool testing through its client and pytest ecosystem.
