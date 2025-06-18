from sentence_transformers import SentenceTransformer
EMBED_MODEL = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
def embed_texts(texts):
    return EMBED_MODEL.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
