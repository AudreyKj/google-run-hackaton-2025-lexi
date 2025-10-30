import re
import unicodedata
from typing import Optional
from google.genai import types
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from utils.constants import BLOCKLIST

def block_keyword_guardrail(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """
    Blocks LLM calls if the latest user message contains sensitive or risky keywords.
    Now includes normalization, regex matching, and category-based filters.
    """
    agent_name = callback_context.agent_name
    print(f"--- Callback: block_keyword_guardrail running for agent: {agent_name} ---")

    # Extract the latest user message
    last_user_message_text = ""
    if llm_request.contents:
        for content in reversed(llm_request.contents):
            if content.role == "user" and content.parts:
                text = getattr(content.parts[0], "text", "")
                if text:
                    last_user_message_text = text
                    break

    print(f"--- Callback: Inspecting last user message: '{last_user_message_text[:100]}...' ---")

    # Normalize text: handle accented chars, weird spacing, etc.
    normalized_text = unicodedata.normalize("NFKC", last_user_message_text)
    normalized_text = re.sub(r"\s+", " ", normalized_text).strip()
    normalized_text_upper = normalized_text.upper()

    # Check each category and pattern
    for category, patterns in BLOCKLIST.items():
        for pattern in patterns:
            if re.search(pattern, normalized_text_upper):
                matched = re.findall(pattern, normalized_text_upper)[0]
                print(f"--- Callback: Found '{matched}' in category '{category}'. Blocking LLM call! ---")
                callback_context.state["guardrail_block_keyword_triggered"] = True

                # Return a polite blocked response
                return LlmResponse(
                    content=types.Content(
                        role="model",
                        parts=[
                            types.Part(
                                text=(
                                    f"I cannot process this request because it contains sensitive or risky content."
                                )
                            )
                        ],
                    )
                )

    print(f"--- Callback: No blocked keywords found. Allowing LLM call for {agent_name}. ---")
    return None


print("✅ block_keyword_guardrail function defined for multi-agent app.")
