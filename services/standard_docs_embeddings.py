from google.cloud import firestore, aiplatform
from vertexai.language_models import TextEmbeddingModel
from google import genai
from google.genai.types import EmbedContentConfig
from google.cloud.firestore_v1.vector import Vector
import os
import json

# ====== CONFIG ======
PROJECT_ID = "ai-legal-assistant-475417"
LOCATION = "us-central1"
MODEL_NAME = "gemini-embedding-001"  # or "text-embedding-004"
COLLECTION_NAME = "standard_docs"
STANDARD_DOCS_FOLDER = "data/extracted_standard_clauses"
# =====================

# Initialize Firestore and Vertex AI
db = firestore.Client(project=PROJECT_ID)
aiplatform.init(project=PROJECT_ID, location=LOCATION)
embedding_model = TextEmbeddingModel.from_pretrained(MODEL_NAME)

def embed_text(text: str):
    """Generate a vector embedding for the given text using Vertex AI."""
    client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
    response = client.models.embed_content(
        model="gemini-embedding-001",
        contents=[
            text
        ],
        config=EmbedContentConfig(
            task_type="SEMANTIC_SIMILARITY", 
            output_dimensionality=768, 
        ),
    )
    print(response)
    return response.embeddings[0].values

for filename in os.listdir(STANDARD_DOCS_FOLDER):
    if not filename.endswith(".json"):
        continue

    filepath = os.path.join(STANDARD_DOCS_FOLDER, filename)
    print(f"Uploading clauses to collection: {filename}")

    try:
        with open(filepath, "r") as f:
            clauses = json.load(f)

        # Sanity check
        if not isinstance(clauses, list):
            raise ValueError("Expected a list of clauses")

        collection_name = filename.replace(".json", "")
        clauses_ref = db.collection(collection_name)

        for clause in clauses:
            if not isinstance(clause, dict):
                print(f"⚠️ Skipping invalid clause entry: {clause}")
                continue

            text = clause.get("clause_text")
            embedding = embed_text(text)

            data = {
                "clause_id": clause.get("clause_id"),
                "clause_title": clause.get("clause_title"),
                "clause_text": text,
                "clause_type": clause.get("clause_type"),
                "embedding_field": Vector(embedding),
            }

            clauses_ref.add(data)

        print(f"✅ Uploaded {filename} successfully")

    except Exception as e:
        print(f"❌ Error uploading clauses from {filename}: {e}")

