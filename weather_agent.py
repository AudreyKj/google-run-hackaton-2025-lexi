from google.adk.agents.llm_agent import Agent
from google.adk.models.lite_llm import LiteLlm  # Import LiteLlm for multi-model support
from google.adk.sessions import InMemorySessionService
from google.adk.tools.tool_context import ToolContext
from google.adk.runners import Runner
from typing import Optional
from google.genai import types
import os
import asyncio
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.genai import types # For creating response content
from typing import Optional
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext
from typing import Optional, Dict, Any # For type hints


from dotenv import load_dotenv

MODEL_GEMINI_2_0_FLASH = "gemini-2.0-flash"
APP_NAME = "multi-agents-weather-tutorial"

# @title 1. Define the before_tool_callback Guardrail

def block_paris_tool_guardrail(
    tool: BaseTool, args: Dict[str, Any], tool_context: ToolContext
) -> Optional[Dict]:
    """
    Checks if 'get_weather_stateful' is called for 'Paris'.
    If so, blocks the tool execution and returns a specific error dictionary.
    Otherwise, allows the tool call to proceed by returning None.
    """
    tool_name = tool.name
    agent_name = tool_context.agent_name # Agent attempting the tool call
    print(f"--- Callback: block_paris_tool_guardrail running for tool '{tool_name}' in agent '{agent_name}' ---")
    print(f"--- Callback: Inspecting args: {args} ---")

    # --- Guardrail Logic ---
    target_tool_name = "get_weather_stateful" # Match the function name used by FunctionTool
    blocked_city = "paris"

    # Check if it's the correct tool and the city argument matches the blocked city
    if tool_name == target_tool_name:
        city_argument = args.get("city", "") # Safely get the 'city' argument
        if city_argument and city_argument.lower() == blocked_city:
            print(f"--- Callback: Detected blocked city '{city_argument}'. Blocking tool execution! ---")
            # Optionally update state
            tool_context.state["guardrail_tool_block_triggered"] = True
            print(f"--- Callback: Set state 'guardrail_tool_block_triggered': True ---")

            # Return a dictionary matching the tool's expected output format for errors
            # This dictionary becomes the tool's result, skipping the actual tool run.
            return {
                "status": "error",
                "error_message": f"Policy restriction: Weather checks for '{city_argument.capitalize()}' are currently disabled by a tool guardrail."
            }
        else:
             print(f"--- Callback: City '{city_argument}' is allowed for tool '{tool_name}'. ---")
    else:
        print(f"--- Callback: Tool '{tool_name}' is not the target tool. Allowing. ---")


    # If the checks above didn't return a dictionary, allow the tool to execute
    print(f"--- Callback: Allowing tool '{tool_name}' to proceed. ---")
    return None # Returning None allows the actual tool function to run

print("✅ block_paris_tool_guardrail function defined.")

# ==== Guardrail Callback ====
def block_keyword_guardrail(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
    agent_name = callback_context.agent_name
    print(f"--- Callback: block_keyword_guardrail running for agent: {agent_name} ---")

    # Extract the last user message
    last_user_message_text = ""
    if llm_request.contents:
        for content in reversed(llm_request.contents):
            if content.role == 'user' and content.parts:
                if content.parts[0].text:
                    last_user_message_text = content.parts[0].text
                    break

    print(f"--- Inspecting last user message: '{last_user_message_text[:100]}...' ---")

    # Guardrail logic
    keyword_to_block = "BLOCK"
    if keyword_to_block in last_user_message_text.upper():
        print(f"--- Found '{keyword_to_block}'. Blocking LLM call! ---")
        callback_context.state["guardrail_block_keyword_triggered"] = True
        return LlmResponse(
            content=types.Content(
                role="model",
                parts=[types.Part(text=f"I cannot process this request because it contains the blocked keyword '{keyword_to_block}'.")],
            )
        )
    else:
        print(f"--- Keyword not found. Allowing LLM call. ---")
        return None

print("✅ block_keyword_guardrail function defined.")

# ==== Session Service & Stateful Session ====
session_service_stateful = InMemorySessionService()
SESSION_ID_STATEFUL = "session_state_demo_001"
USER_ID_STATEFUL = "user_state_demo"
initial_state = {"user_preference_temperature_unit": "Celsius"}

async def initialize_stateful_session():
    await session_service_stateful.create_session(
        app_name=APP_NAME,
        user_id=USER_ID_STATEFUL,
        session_id=SESSION_ID_STATEFUL,
        state=initial_state
    )
    print("\n--- Initial session created ---")

# ==== Tools ====
def extract_clauses(document: str) -> list:
    print(f"--- Tool: extract_clauses called ---")
    # Mock clause extraction logic
    clauses = [clause.strip() for clause in document.split('.') if clause.strip()]
    return clauses

def say_goodbye() -> str:
    print(f"--- Tool: say_goodbye called ---")
    return "Goodbye! Have a great day."

def get_weather_stateful(city: str, tool_context: ToolContext) -> dict:
    print(f"--- Tool: get_weather_stateful called for {city} ---")
    preferred_unit = tool_context.state.get("user_preference_temperature_unit", "Celsius")
    city_normalized = city.lower().replace(" ", "")
    mock_weather_db = {
        "newyork": {"temp_c": 25, "condition": "sunny"},
        "london": {"temp_c": 15, "condition": "cloudy"},
        "tokyo": {"temp_c": 18, "condition": "light rain"},
    }

    if city_normalized in mock_weather_db:
        data = mock_weather_db[city_normalized]
        temp_c = data["temp_c"]
        condition = data["condition"]
        temp_value = (temp_c * 9/5) + 32 if preferred_unit == "Fahrenheit" else temp_c
        temp_unit = "°F" if preferred_unit == "Fahrenheit" else "°C"
        report = f"The weather in {city.capitalize()} is {condition} with a temperature of {temp_value:.0f}{temp_unit}."
        tool_context.state["last_city_checked_stateful"] = city
        tool_context.state["last_weather_report"] = report
        print(f"--- Generated report: {report} ---")
        return {"status": "success", "report": report}
    else:
        return {"status": "error", "error_message": f"Sorry, I don't have weather information for '{city}'."}
    
def generate_report(topic: str) -> str:
    print(f"--- Tool: generate_report called for topic: {topic} ---")
    return f"This is a generated report on the topic: {topic}."

# ==== Sub-Agents ====
clause_extraction_agent = Agent(
    model=LiteLlm(model=MODEL_GEMINI_2_0_FLASH),
    name="clause_extraction_agent",
    instruction="You are the Clause Extraction Agent. Use 'extract_clauses' only.",
    description="Handles clause extraction.",
    tools=[extract_clauses],
)

comparison_agent = Agent(
    model=LiteLlm(model=MODEL_GEMINI_2_0_FLASH),
    name="comparison_agent",
    instruction="You are the Comparison Agent. Use compare clauses",
    description="Handles farewells.",
    tools=[say_goodbye],
)

report_generation_agent = Agent(
    model=LiteLlm(model=MODEL_GEMINI_2_0_FLASH),
    name="report_generation_agent",
    instruction="You are the Report Generation Agent. Use 'generate_report' only.",
    description="Handles report generation.",
    tools=[generate_report],
)

# ==== Root Agent with Guardrail Callback ====
root_agent_model_guardrail = Agent(
    name="weather_agent_v5_model_guardrail",
    model=LiteLlm(model=MODEL_GEMINI_2_0_FLASH),
    description="Handles weather, delegates greetings/farewells, includes input keyword guardrail.",
    instruction=(
        "You are the main Weather Agent. Provide weather using 'get_weather_stateful'. "
        "Delegate greetings to 'clause_extraction_agent' and farewells to 'comparison_agent'."
    ),
    tools=[get_weather_stateful],
    sub_agents=[clause_extraction_agent, comparison_agent],
    output_key="last_weather_report",
    before_model_callback=block_keyword_guardrail,
    before_tool_callback=block_paris_tool_guardrail
)

runner_root_model_guardrail = Runner(
    agent=root_agent_model_guardrail,
    app_name=APP_NAME,
    session_service=session_service_stateful
)

# ==== Helper for state access ====
async def get_stateful_session():
    return session_service_stateful.sessions[APP_NAME][USER_ID_STATEFUL][SESSION_ID_STATEFUL]

# ==== Agent Interaction Logic ====
async def call_agent_async(query: str, runner: Runner, user_id: str, session_id: str):
    print(f"\n>>> User Query: {query}")
    content = types.Content(role="user", parts=[types.Part(text=query)])
    final_response = "No response received."
    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
        if event.is_final_response() and event.content and event.content.parts:
            final_response = event.content.parts[0].text
            break
    print(f"<<< Agent Response: {final_response}")

# ==== Main Guardrail Test Flow ====
async def run_guardrail_test_conversation():
    print("\n--- Testing Tool Argument Guardrail ('Paris' blocked) ---")

    # Use the runner for the agent with both callbacks and the existing stateful session
    # Define a helper lambda for cleaner interaction calls
    interaction_func = lambda query: call_agent_async(
        query,
        runner_root_model_guardrail,
        USER_ID_STATEFUL,  # Use existing user ID
        SESSION_ID_STATEFUL  # Use existing session ID
    )

    # 1. Allowed city (Should pass both callbacks, use Fahrenheit state)
    print("--- Turn 1: Requesting weather in New York (expect allowed) ---")
    await interaction_func("What's the weather in New York?")

    # 2. Blocked city (Should pass model callback, but be blocked by tool callback)
    print("\n--- Turn 2: Requesting weather in Paris (expect blocked by tool guardrail) ---")
    await interaction_func("How about Paris?")  # Tool callback should intercept this

    # 3. Another allowed city (Should work normally again)
    print("\n--- Turn 3: Requesting weather in London (expect allowed) ---")
    await interaction_func("Tell me the weather in London.")


# ==== Entry Point ====
async def main():
    """Main function to run the guardrail test conversation."""
    # Initialize the stateful session first
    await initialize_stateful_session()
    
    # Run the guardrail test conversation
    await run_guardrail_test_conversation()
    
    print("\n--- Inspecting Final Session State (After Tool Guardrail Test) ---")
    # Use the session service instance associated with this stateful session
    final_session = await session_service_stateful.get_session(
        app_name=APP_NAME,
        user_id=USER_ID_STATEFUL,
        session_id=SESSION_ID_STATEFUL
    )
    if final_session:
        # Use .get() for safer access
        print(f"Tool Guardrail Triggered Flag: {final_session.state.get('guardrail_tool_block_triggered', 'Not Set (or False)')}")
        print(f"Last Weather Report: {final_session.state.get('last_weather_report', 'Not Set')}")  # Should be London weather if successful
        print(f"Temperature Unit: {final_session.state.get('user_preference_temperature_unit', 'Not Set')}")  # Should be Fahrenheit
        # print(f"Full State Dict: {final_session.state}")  # For detailed view
    else:
        print("\n❌ Error: Could not retrieve final session state.")

if __name__ == "__main__":
    print("Executing using 'asyncio.run()' (for standard Python scripts)...")
    try:
        # This creates an event loop, runs your async function, and closes the loop.
        asyncio.run(main())
    except Exception as e:
        print(f"An error occurred: {e}")
else:
    print("\n⚠️ Skipping tool guardrail test. Runner ('runner_root_tool_guardrail') is not available.")