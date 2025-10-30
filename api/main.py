from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from google.genai import types
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from agents.root_agent import root_agent
import PyPDF2

APP_NAME = "Lexi"
app = FastAPI()

# Add rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Enable CORS for the specified frontend origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://lexi-ai-legal-assistant-142471449149.us-west1.run.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

async def create_session(session_id: str, user_id: str):
    session_service = InMemorySessionService()

    # Create the specific session where the conversation will happen
    await session_service.create_session(
        app_name=APP_NAME,
        user_id=user_id,
        session_id=session_id
    )
    print(f"Session created: App='{APP_NAME}', User='{user_id}', Session='{session_id}'")
    return session_service

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/contracts/analyze")
@limiter.limit("4/minute")
async def analyze_contract(
    request: Request,
    file: UploadFile = File(...),
    session_id: str = Form(...),
    user_id: str = Form(...)
):
    session_service = await create_session(session_id, user_id)

    runner = Runner(
        agent=root_agent, 
        app_name=APP_NAME,
        session_service=session_service
    )

    extracted_text = None
    if file is not None:
        # Read PDF file and extract text
        try:
            pdf_reader = PyPDF2.PdfReader(file.file)
            extracted_text = "\n".join(page.extract_text() or "" for page in pdf_reader.pages)
        except Exception as e:
            def error_stream():
                yield f"data: {{\"error\": \"Failed to extract text from PDF\"}}\n\n"
            return StreamingResponse(error_stream(), media_type="text/event-stream")

    contract_input = extracted_text
    if not contract_input:
        def error_stream():
            yield "data: {\"error\": \"Missing contract_text or PDF file\"}\n\n"
        return StreamingResponse(error_stream(), media_type="text/event-stream")

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

    import json
    async def event_stream():
        try:
            async for event in runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=content,
            ):
                if event.content and event.content.parts:
                    text = event.content.parts[0].text
                    if text:
                        # Remove markdown code block formatting if present
                        if text.strip().startswith('```json'):
                            text = text.strip()[7:]
                        if text.strip().startswith('```'):
                            text = text.strip()[3:]
                        if text.strip().endswith('```'):
                            text = text.strip()[:-3]
                        try:
                            parsed = json.loads(text)
                            yield f'data: {json.dumps({"result": parsed})}\n\n'
                        except Exception:
                            # fallback to string if not valid JSON
                            safe_cleaned = text.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", " ")
                            yield f'data: {{"result": "{safe_cleaned}"}}\n\n'
        except Exception as agent_error:
            import traceback
            error_message = f"Agent execution failed: {str(agent_error)}"
            tb = traceback.format_exc()
            print(error_message)
            print(tb)
            yield f'data: {{"error": "{error_message}"}}\n\n'

    return StreamingResponse(event_stream(), media_type="text/event-stream")

