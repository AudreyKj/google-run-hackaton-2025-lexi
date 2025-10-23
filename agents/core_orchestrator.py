from fastapi import FastAPI, Request
from google.adk.agents.llm_agent import Agent
from google.adk.runners import Runner
from google.adk.models.lite_llm import LiteLlm
from google.adk.sessions import InMemorySessionService
from agents.clause_analysis.clause_analysis_workflow_agent import clause_analysis_workflow_agent
from agents.question_answers.question_answers_agent import question_answers_agent
from utils import MODEL_GEMINI_2_0_FLASH

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

# ==== Root orchestrator =

core_orchestrator_agent = Agent(
    name="core_orchestrator",
    model=MODEL_GEMINI_2_0_FLASH,
    instruction=(
        "You are the central orchestrator for a multi-agent legal assistant. "
        "You coordinate between sub-agents depending on the user's intent. "
        "If the user uploads or provides a contract, you should trigger the clause analysis workflow. "
        "If the user asks a question (e.g. 'What does this clause mean?', 'Is this safe to sign?'), "
        "delegate it to the Question Answering Agent."
    ),
    sub_agents=[clause_analysis_workflow_agent, question_answers_agent],
)
