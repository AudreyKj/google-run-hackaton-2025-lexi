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


def find_similar_clauses(
    clause: dict,
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
            limit=1
        )
        results = list(vector_query.stream())

        # Extract only the clause_texts
        similar_clauses = [
            r.to_dict().get("clause_text", "")
            for r in results
            if r.to_dict().get("clause_text")
        ]

        # Remove any clause that is identical to the input
        filtered_clauses = [c for c in similar_clauses if c.strip() != clause_text.strip()]
        print("Filtered similar clauses:", filtered_clauses)

        if filtered_clauses:
            return filtered_clauses
        else:
            return "No suitable standard clause found."

    except Exception as e:
        print("⚠️ Firestore vector search failed, fallback to empty list:", e)
        return "No suitable standard clause found."

find_similar_clauses({"clause_id": "C1",
        "clause_title": "Confidentiality",
        "clause_text": "The employee shall not disclose...",
        "clause_type": "confidentiality",
        "contract_type": "NDA",
        "country": "Germany"
})
