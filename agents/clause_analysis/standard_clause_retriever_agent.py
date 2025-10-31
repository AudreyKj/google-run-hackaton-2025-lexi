from google.adk.agents.llm_agent import Agent
from google import genai
from google.genai.types import EmbedContentConfig
from utils.constants import MODEL_GEMINI_2_0_FLASH
from google.cloud import firestore
from google.cloud.firestore_v1.base_vector_query import DistanceMeasure
from google.cloud.firestore_v1.vector import Vector
import numpy as np
import os

PROJECT_ID = "ai-legal-assistant-475417"

db = firestore.Client(project=PROJECT_ID)

API_KEY = os.getenv("GOOGLE_API_KEY")

def getEmbeddingForClause(clause_text: str):
    """
    Generate an embedding vector for a given clause using Gemini Embedding API.
    """
    if not clause_text:
        raise ValueError("Clause empty — cannot generate embedding.")
    
    # add clause type context to improve embedding quality
    client = genai.Client(api_key=API_KEY)
    response = client.models.embed_content(
        model="gemini-embedding-001",
        contents=[clause_text],
        config=EmbedContentConfig(
            task_type="SEMANTIC_SIMILARITY",
            output_dimensionality=768,
        ),
    )

    # ✅ Defensive check
    if not response.embeddings or not response.embeddings[0].values:
        raise ValueError("Empty embedding response from Gemini API.")

    embedding = response.embeddings[0].values
    return embedding


async def find_similar_clauses(
    clause: dict,
    collection_name: str = "employment_standard_clauses",
    top_k: int = 2
):
    """
    Compare a user clause against stored standard clauses in Firestore using vector similarity.

    1️⃣ Try Firestore vector search (`find_nearest`).
    2️⃣ If unavailable or fails, compute cosine similarity manually as a fallback.
    """

    # Extract metadata
    contract_type = clause.get("contract_type", "")
    clause_text = clause.get("clause_text", "")
    clause_id = clause.get("clause_id", "unknown")

    print(f"\n🔹 Comparing clause [{clause_id}] for contract type: {contract_type}")

    if not clause_text:
        print("⚠️ Skipping: Empty clause text.")
        return []

    # --- Step 1: Generate embedding ---
    try:
        user_embedding = getEmbeddingForClause(clause_text)
    except Exception as e:
        print("❌ Failed to generate embedding:", e)
        return []

    # --- Vector search attempt ---
    try:
        vector_query = db.collection("employment_standard_clauses").find_nearest(
            vector_field="embedding_field",
            query_vector=Vector(user_embedding),
            distance_measure=DistanceMeasure.COSINE,
            limit=top_k,
        )
        results = list(vector_query.stream())

        # Extract only the clause_texts
        similar_clauses = [
            r.to_dict().get("clause_text", "")
            for r in results
            if r.to_dict().get("clause_text")
        ]

        print(f"✅ Found {len(similar_clauses)} similar clauses.")
        return similar_clauses

    except Exception as e:
        print("⚠️ Firestore vector search failed, fallback to empty list:", e)
        return []

# --- Agent Definition ---
standard_clause_retriever_agent = Agent(
    model=MODEL_GEMINI_2_0_FLASH,
    name="standard_clause_retriever_agent",
    instruction=(
        "You are the Standard Clause Retrieval Agent. "
        "Process data from {extractor_result}."
        "Your role is to match each extracted clause with the most semantically similar "
        "standard clause from Firestore using the 'find_similar_clauses' tool.\n\n"
        "The current clause and matched clause cannot be identical.\n\n"
        "Return the result as a JSON array in the output_key:\n"
        "[\n"
        "  {\n"
        '    "clause_id": "C1",\n'
        '    "clause_title": "Confidentiality",\n'
        '    "clause_text": "The employee can disclose information.",\n'
        '    "clause_type": "confidentiality",\n'
        '    "contract_type": "NDA",\n'
        '    "matching_standard_clauses": [\n'
        '      "The employee shall not disclose...",\n'
        '    ]\n'
        "  }\n"
        "]\n\n"
        "This structured output will be used by the Comparator Agent for deeper analysis."
    ),
    description="Retrieves the most similar standard clauses from Firestore using embeddings.",
    output_key="retrieval_result",
    tools=[find_similar_clauses],
)
