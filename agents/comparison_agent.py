from google.adk.agents.llm_agent import Agent
from google.adk.models.lite_llm import LiteLlm
MODEL_GEMINI_2_0_FLASH = "gemini-2.0-flash"

def compare_clauses() -> list:
    print(f"--- Tool: compare_clauses called ---")

comparison_agent = Agent(
    model=LiteLlm(model=MODEL_GEMINI_2_0_FLASH),
    name="comparison_agent",
    instruction="You are the Comparison Agent. Use compare_clauses only.",
    description="Handles clause comparison.",
    tools=[compare_clauses],
)