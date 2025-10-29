import os
import json
import requests
import re
import pdfplumber

API_KEY = os.getenv("GOOGLE_API_KEY")
MODEL_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

STANDARD_DOCS_FOLDER = "data/standard_docs_data"
OUTPUT_JSON_FILE = "./employment_standard_clauses.json"

PROMPT = (
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
)

def extract_text_from_pdf(filepath):
    """Extract text from a PDF file using pdfplumber."""
    with pdfplumber.open(filepath) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages)

def analyze_document(text):
    """Call Gemini API to extract clauses from the text."""
    if not API_KEY:
        raise ValueError("GOOGLE_API_KEY environment variable not set.")
    headers = {
        "Content-Type": "application/json",
        "X-goog-api-key": API_KEY
    }

    data = {
        "contents": [
            {
                "parts": [
                    {"text": PROMPT + "\n\n" + text}
                ]
            }
        ]
    }

    response = requests.post(MODEL_URL, headers=headers, json=data)
    response.raise_for_status()
    result = response.json()

    # print('API response:', result)
    
    # The generated content is usually in result['candidates'][0]['content'][0]['text']
    try:
        generated_text = result["candidates"][0]["content"]["parts"][0]["text"]
        cleaned = re.sub(r"^```json\s*|```$", "", generated_text.strip(), flags=re.MULTILINE)
        return json.loads(cleaned)
    except Exception as e:
        print("Failed to parse API response as JSON:", e)
        # print("Raw response:", result)
        return None

def main():
    all_clauses = []

    for filename in os.listdir(STANDARD_DOCS_FOLDER):
        if filename.lower().endswith(".pdf"):
            filepath = os.path.join(STANDARD_DOCS_FOLDER, filename)
            print(f"Processing: {filename}")
            text = extract_text_from_pdf(filepath)
            clauses = analyze_document(text)
            if clauses:
                all_clauses.extend(clauses)

    # Save all extracted clauses to JSON
    with open(OUTPUT_JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(all_clauses, f, ensure_ascii=False, indent=2)

    print(f"Extraction complete! Clauses saved to {OUTPUT_JSON_FILE}")

if __name__ == "__main__":
    main()


