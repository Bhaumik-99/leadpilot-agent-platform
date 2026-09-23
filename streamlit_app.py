import os
import uuid

import requests
import streamlit as st

API_URL = os.getenv("LEADPILOT_API_URL", "http://localhost:8000").rstrip("/")

st.set_page_config(page_title="LeadPilot Control Room", page_icon="🤖", layout="wide")

st.title("🤖 LeadPilot Control Room")
st.caption("Agentic SME sales platform — conversation, CRM state, tool traces, and evaluation.")

with st.sidebar:
    st.header("Connection")
    api_url = st.text_input("FastAPI URL", API_URL)
    if st.button("Check API"):
        try:
            r = requests.get(f"{api_url}/health", timeout=5)
            r.raise_for_status()
            st.success("API online")
        except requests.RequestException as exc:
            st.error(f"API unavailable: {exc}")

    st.divider()
    lead_id = st.text_input("Lead ID", st.session_state.get("lead_id", ""))
    if st.button("New lead"):
        lead_id = str(uuid.uuid4())
        st.session_state.lead_id = lead_id
        st.session_state.chat = []
        st.rerun()

if "lead_id" not in st.session_state:
    st.session_state.lead_id = lead_id
if "chat" not in st.session_state:
    st.session_state.chat = []

lead_id = st.session_state.lead_id

def post_json(path: str, payload: dict):
    response = requests.post(f"{api_url}{path}", json=payload, timeout=60)
    response.raise_for_status()
    return response.json()

def get_json(path: str):
    response = requests.get(f"{api_url}{path}", timeout=15)
    response.raise_for_status()
    return response.json()

tab_chat, tab_profile, tab_trace, tab_eval, tab_tools = st.tabs(
    ["💬 Live Chat", "👤 Lead Profile", "🔎 Agent Trace", "🧪 Evaluation", "🧰 MCP Tools"]
)

with tab_chat:
    st.subheader("Multi-turn agent conversation")

    for message in st.session_state.chat:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    prompt = st.chat_input("Message the sales agent…")
    if prompt:
        st.session_state.chat.append({"role": "user", "content": prompt})
        try:
            data = post_json(
                "/v1/agent/respond",
                {
                    "lead_id": lead_id,
                    "channel": "web",
                    "message": prompt,
                },
            )
            answer = data.get("message", "No response returned.")
            st.session_state.chat.append({"role": "assistant", "content": answer})
            st.rerun()
        except requests.RequestException as exc:
            st.error(f"Agent request failed: {exc}")

with tab_profile:
    st.subheader("CRM state")
    if not lead_id:
        st.info("Create or enter a lead ID.")
    else:
        try:
            data = get_json(f"/v1/leads/{lead_id}")
            lead = data["lead"]
            st.json(lead.model_dump() if hasattr(lead, "model_dump") else lead)
            history = data.get("history", [])
            if history:
                st.write("Conversation history")
                for item in history:
                    st.write(f"**{item.get('role', 'message')}** — {item.get('content', '')}")
            if st.button("Handoff to human", type="secondary"):
                post_json(f"/v1/leads/{lead_id}/handoff", {})
                st.success("Lead handed off.")
                st.rerun()
        except requests.HTTPError:
            st.info("Lead does not exist yet. Send a message in Live Chat to create it.")
        except requests.RequestException as exc:
            st.error(f"Could not load lead: {exc}")

with tab_trace:
    st.subheader("Auditable agent trace")
    if lead_id:
        try:
            data = get_json(f"/v1/leads/{lead_id}/audit")
            events = data.get("events", [])
            if not events:
                st.info("No audit events yet.")
            for event in events:
                with st.expander(f"{event['event']} · {event['created_at']}"):
                    st.json(event["payload"])
        except requests.RequestException as exc:
            st.error(f"Could not load trace: {exc}")
    else:
        st.info("Create a lead first.")

with tab_eval:
    st.subheader("Multi-turn evaluation harness")
    try:
        scenarios = get_json("/v1/evaluation/scenarios")
        for scenario in scenarios:
            st.markdown(f"**{scenario['id']}** — {scenario['description']}")
            if st.button("Run", key=f"eval-{scenario['id']}"):
                result = post_json(f"/v1/evaluation/run/{scenario['id']}", {})
                if result.get("passed"):
                    st.success("PASS")
                else:
                    st.error("FAIL")
                st.json(result)
    except requests.RequestException as exc:
        st.error(f"Evaluation unavailable: {exc}")

with tab_tools:
    st.subheader("FastMCP tool server")
    try:
        tools = get_json("/v1/mcp/tools").get("tools", [])
        for name in tools:
            st.code(name, language="text")
    except requests.RequestException as exc:
        st.error(f"Could not load MCP tools: {exc}")

st.caption("Run FastAPI first, then Streamlit. Set LEADPILOT_API_URL when the API is not local.")
