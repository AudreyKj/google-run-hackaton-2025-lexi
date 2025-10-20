from google.adk.agents.llm_agent import Agent
from google.adk.models.lite_llm import LiteLlm
MODEL_GEMINI_2_0_FLASH = "gemini-2.0-flash"

# def extract_clauses() -> list:
#     print(f"--- Tool: extract_clauses called ---")
#     return [
#   {
#     "clause": "Confidentiality",
#     "id": 1
#   },
# ]

clause_extraction_agent = Agent(
    model=LiteLlm(model=MODEL_GEMINI_2_0_FLASH),
    name="clause_extraction_agent",
    instruction="You are the Clause Extraction Agent.",
    description="Handles clause extraction.",
)