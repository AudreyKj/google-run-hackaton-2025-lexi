from fastapi import FastAPI, Request
from google.adk.agents.llm_agent import Agent
from google.adk.runners import Runner
from google.adk.models.lite_llm import LiteLlm
from google.adk.sessions import InMemorySessionService
from google.genai import types
import asyncio

app = FastAPI()

# ==== Example agent setup ====
MODEL = "gemini-2.0-flash"
APP_NAME = "legal-assistant"

# ==== Session setup ====
session_service = InMemorySessionService()
SESSION_ID = "session_001"
USER_ID = "user_001"

async def init_session():
    await session_service.create_session(
        user_id=USER_ID,
        session_id=SESSION_ID,
        app_name=APP_NAME,
        state={}  # initial empty state
    )

# ==== Your ADK agents (defined elsewhere) ====
from agents.clause_extraction_agent import clause_extraction_agent 
from agents.comparison_agent import comparison_agent
from agents.report_agent import report_agent

# ==== Root orchestrator ====
root_agent = Agent(
    name="contract_analyzer",
    model=LiteLlm(model=MODEL),
    description="Extract clauses, compares clauses with standards, and generates a report.",
    sub_agents=[clause_extraction_agent, comparison_agent, report_agent],
)

runner = Runner(agent=root_agent, app_name=APP_NAME, session_service=session_service)

# ==== API Endpoint ====
@app.post("/analyze-contract")
async def analyze_contract(request: Request):
    data = await request.json()
    contract_text = data.get("contract_text")
    if not contract_text:
        return {"error": "Missing contract_text"}

    # Build content for ADK
    content = types.Content(role="user", parts=[types.Part(text=f"Analyze this contract by extracting clauses, comparing them with standard clauses, and generating a report: {contract_text}")])

    print("Running agent...")
    final_response = None

    # Ensure session exists
    await init_session()

    async for event in runner.run_async(user_id=USER_ID, session_id=SESSION_ID, new_message=content):
        if event.is_final_response() and event.content and event.content.parts:
            final_response = event.content.parts[0].text
            break

    return {"result": final_response}
