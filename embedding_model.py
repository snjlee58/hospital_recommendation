# embedding_model.py

import os
import numpy as np
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sentence_transformers import SentenceTransformer

# --------------------------
# Step 1: Load from Database
# --------------------------
def load_chunked_reviews():
    load_dotenv()
    print("Loaded DATABASE_URL:", os.getenv("DATABASE_URL"))
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("❌ DATABASE_URL not found in .env file")

    engine = create_engine(db_url)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT chunk_text FROM review_chunks WHERE chunk_text IS NOT NULL"))
        reviews = [row[0].strip() for row in result.fetchall()]
        print(f"Loaded {len(reviews)} text chunks from database.")
        return reviews

# --------------------------
# Step 2: Embed Reviews
# --------------------------
class EmbeddingModel:
    def __init__(self, model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"):
        print("Loading embedding model...")
        self.model = SentenceTransformer(model_name)

    def encode(self, texts):
        return self.model.encode(texts, convert_to_numpy=True, show_progress_bar=True)

# --------------------------
# Step 3: Save Results
# --------------------------
def save_outputs(texts, vectors, folder="data/embeddings"):
    os.makedirs(folder, exist_ok=True)
    np.save(os.path.join(folder, "review_embeddings.npy"), vectors)
    with open(os.path.join(folder, "review_texts.txt"), "w", encoding="utf-8") as f:
        for text in texts:
            f.write(text + "\n")
    print(f"Saved embeddings and texts to '{folder}/'")

# --------------------------
# Run Everything
# --------------------------
if __name__ == "__main__":
    reviews = load_chunked_reviews()
    if not reviews:
        print("No review chunks found. Exiting.")
        exit()

    model = EmbeddingModel()
    embeddings = model.encode(reviews)
    save_outputs(reviews, embeddings)
