from google.adk.agents.llm_agent import Agent
from google.adk.models.lite_llm import LiteLlm
MODEL_GEMINI_2_0_FLASH = "gemini-2.0-flash"

def generate_report(clause: str, comparison_results: list) -> str:
    print(f"--- Tool: generate_report called for clause: {clause} ---")
    return [
  {
    "clause": "Confidentiality",
    "similarity": 0.95,
    "risk": "low",
    "feedback": "pretty standard clause",
  },
]


report_agent = Agent(
    model=LiteLlm(model=MODEL_GEMINI_2_0_FLASH),
    name="report_agent",
    instruction="You are the Report Agent. Use 'generate_report' only.",
    description="Handles report generation and returns the report.",
    tools=[generate_report],
)