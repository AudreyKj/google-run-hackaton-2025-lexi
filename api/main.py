from fastapi import FastAPI, Request
from agents import init_session

# ==== API Endpoint ====
@app.post("/analyze-contract")
async def analyze_contract(request: Request):
    data = await request.json()
    contract_text = data.get("contract_text")
    if not contract_text:
        return {"error": "Missing contract_text"}

    # Build content for ADK
    content = types.Content(role="user", parts=[types.Part(text=f"Analyze this contract by extracting clauses, comparing them with standard clauses, and generating a report: {contract_text}")])

    print("Running agent...")
    final_response = None

    # Ensure session exists
    await init_session()

    async for event in runner.run_async(user_id=USER_ID, session_id=SESSION_ID, new_message=content):
        if event.is_final_response() and event.content and event.content.parts:
            final_response = event.content.parts[0].text
            break

    return {"result": final_response}
