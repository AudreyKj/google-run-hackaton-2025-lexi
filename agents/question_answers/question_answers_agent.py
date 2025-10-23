from google.adk.agents.llm_agent import Agent
from google.adk.agents.llm_agent import LlmAgent
from utils import MODEL_GEMINI_2_0_FLASH

question_answers_agent = LlmAgent(
    model=MODEL_GEMINI_2_0_FLASH,
    name="question_answers",
    instruction="You are the Question Answering Agent.",
    description="Handles question answering.",
)