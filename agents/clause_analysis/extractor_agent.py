from google.adk.agents.llm_agent import LlmAgent
from utils import MODEL_GEMINI_2_0_FLASH

extractor_agent = LlmAgent(
    model=MODEL_GEMINI_2_0_FLASH,
    name="extractor_agent",
    instruction=(
        "You are the Clause Extraction Agent. "
        "Your task is to analyze a legal document or contract text "
        "and extract its clauses as structured data. "
        "For each clause you find, identify: \n"
        "1️clause_id — a unique short identifier (e.g., C1, C2, ...)\n"
        "2️clause_title — if the clause has a heading, return it; otherwise infer a short descriptive title\n"
        "3️clause_text — the exact text of the clause\n"
        "4️clause_type — categorize it (e.g., 'termination', 'confidentiality', 'payment', 'liability', etc.)\n\n"
        "Return the result as a JSON array like this:\n"
        "[\n"
        "  {\n"
        '    "clause_id": "C1",\n'
        '    "clause_title": "Confidentiality",\n'
        '    "clause_text": "The employee shall not disclose...",\n'
        '    "clause_type": "confidentiality"\n'
        "  },\n"
        "  ...\n"
        "]\n\n"
        "If the input text seems incomplete, still extract any partial clauses you can identify. "
        "Do not summarize or rephrase — only extract exact text segments."
    ),
    description="Extracts and classifies clauses from legal contract text for downstream analysis.",
)
