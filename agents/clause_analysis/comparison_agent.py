from google.adk.agents.llm_agent import Agent
from google.adk.models.lite_llm import LiteLlm
from utils import MODEL_GEMINI_2_0_FLASH

def compare_clauses() -> list:
    print(f"--- Tool: compare_clauses called ---")

comparison_agent = Agent(
    model=MODEL_GEMINI_2_0_FLASH,
    name="comparison_agent",
    instruction="You are the Comparison Agent. Use compare_clauses only.",
    description="Handles clause comparison.",
    tools=[compare_clauses],
)