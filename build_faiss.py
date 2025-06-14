import numpy as np
import faiss
import os

# --- Config ---
EMBEDDING_PATH = "data/embeddings/review_embeddings.npy"
TEXT_PATH = "data/embeddings/review_texts.txt"
FAISS_INDEX_PATH = "data/embeddings/faiss_review.index"

# --- Load embeddings ---
embeddings = np.load(EMBEDDING_PATH).astype('float32')

# --- Normalize for cosine similarity ---
faiss.normalize_L2(embeddings)

# --- Build FAISS index (Inner Product for cosine) ---
dimension = embeddings.shape[1]
index = faiss.IndexFlatIP(dimension)  # IP = Inner Product

# --- Add vectors ---
index.add(embeddings)
print(f"FAISS index built. Total vectors: {index.ntotal}")

# --- Save index ---
faiss.write_index(index, FAISS_INDEX_PATH)
print(f"FAISS index saved to: {FAISS_INDEX_PATH}")
