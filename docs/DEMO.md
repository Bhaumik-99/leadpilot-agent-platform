# Demo script

## 1. Start the API

```bash
uvicorn app.api.main:app --reload
```

## 2. Show the API docs

Open `/docs` and call `/health`.

## 3. Start a lead

Send:

> We are a furniture manufacturer in Gurgaon.

The agent should ask for missing qualification details.

## 4. Continue the conversation

Send:

> We have 15 salespeople and need CRM + WhatsApp follow-ups.

The lead should now have a higher score and richer structured state.

## 5. Ask pricing

Send:

> What is the price?

The answer is grounded in the local knowledge base.

## 6. Run evaluation

```bash
pytest -q
```

Then call:

```text
POST /v1/evaluation/run/pricing_sensitive
```

## 7. Show MCP tools

Call `/v1/mcp/tools` to show the registered FastMCP tools.
