from google.adk.agents.llm_agent import LlmAgent
from utils.constants import MODEL_GEMINI_2_0_FLASH


clause_comparison_agent = LlmAgent(
    model=MODEL_GEMINI_2_0_FLASH,
    name="clause_comparison_agent",
    description="Compares an extracted clause with the retrieved standard clauses to determine similarity and differences.",
    instruction=(
        "You are the Clause Comparison Agent.\n"
        "Process data from {retrieval_result}."
        "Your task is to compare each user clause (from extractor_result) with the retrieved standard clauses"
        "(from standard_clause_retriever_agent).\n\n"
        "For each clause, perform the following steps:\n"
        "1️- Evaluate the **semantic similarity** between the user clause and each retrieved standard clause.\n"
        "2️- Select the **most similar** standard clause.\n"
        "3️- Compute a **similarity_score** between 0 and 1 (1.0 = identical meaning, 0.0 = unrelated).\n"
        "4️- Generate a **matching_difference** summary (1–2 sentences) describing how the user's clause "
        "differs in intent, strictness, or scope from the standard clause.\n\n"
        "Focus on meaningful legal differences, e.g.:\n"
        "- 'User clause is more permissive than standard clause.'\n"
        "- 'User clause adds confidentiality obligations not found in the standard clause.'\n"
        "- 'Clauses are identical in intent.'\n\n"
        "Return output as a JSON array with the following structure:\n\n"
        "[\n"
        "  {\n"
        "     \"clause_id\": \"C1\",\n"
        "    \"clause_title\": \"Confidentiality\",\n"
        "    \"clause_text\": \"The employee can disclose information.\",\n"
        "    \"clause_type\": \"confidentiality\",\n"
        "    \"contract_type\": \"NDA\",\n"
        "    \"matching_standard_clauses\": [\n"
        "      \"The employee shall not disclose...\",\n"
        "    ],\n"
        "    \"matching_difference\": \"User clause is more permissive than standard clause.\",\n"
        "    \"similarity_score\": 0.75\n"
        "  }\n"
        "]\n\n"
        "Keep the JSON strictly valid. Do not include commentary or explanations outside the JSON."
    ),
    output_key="comparison_result",
)
