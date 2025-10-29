from fastapi import FastAPI, Request, UploadFile, File, Form
from google.genai import types
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from agents.core_orchestrator import core_orchestrator_agent
from utils.clean_agents_output import clean_agents_output
import PyPDF2

app = FastAPI()

SESSION_ID = "session_001"
USER_ID = "user_001"
APP_NAME = "Lexi"

async def create_session():
    session_service = InMemorySessionService()

    # Create the specific session where the conversation will happen
    await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID
    )
    print(f"Session created: App='{APP_NAME}', User='{USER_ID}', Session='{SESSION_ID}'")
    return session_service


@app.post("/analyze-contract")
async def analyze_contract(
    contract_text: str = Form(None),
    user_question: str = Form(None),
    file: UploadFile = File(None)
):
    session_service = await create_session()

    runner = Runner(
        agent=core_orchestrator_agent,  # The agent we want to run
        app_name=APP_NAME,    # Associates runs with our app
        session_service=session_service  # Uses our session manager
    )

    extracted_text = None
    if file is not None:
        # Read PDF file and extract text
        try:
            pdf_reader = PyPDF2.PdfReader(file.file)
            extracted_text = "\n".join(page.extract_text() or "" for page in pdf_reader.pages)
        except Exception as e:
            return {"error": f"Failed to extract text from PDF: {str(e)}"}

    # Prefer extracted PDF text, then contract_text from form
    contract_input = extracted_text or contract_text
    if not contract_input and not user_question:
        return {"error": "Missing contract_text, PDF file, or user_question"}

    if contract_input:
        content = types.Content(
            role="user",
            parts=[
                types.Part(
                    text=(
                        "The user has provided a contract for analysis.\n\n"
                        f"Contract text:\n{contract_input}\n\n"
                    )
                )
            ]
        )

    print("🧠 Running core orchestrator agent...")

    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=SESSION_ID,
        new_message=content,
    ):
        if event.is_final_response() and event.content and event.content.parts:
            final_response_text = event.content.parts[0].text
            cleaned_output = clean_agents_output(final_response_text)

    return {"result": cleaned_output}

