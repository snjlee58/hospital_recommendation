"""
Similarity calculation functionality for hospital recommendation
"""
import numpy as np
import faiss
from typing import List, Dict, Any
from app.ai.openai_client import OpenAIClient


class SimilarityCalculator:
    """Calculate similarity between user queries and hospital reviews"""
    
    def __init__(self, openai_client: OpenAIClient = None):
        """
        Initialize similarity calculator
        
        Args:
            openai_client: OpenAI client instance (optional)
        """
        self.openai_client = openai_client or OpenAIClient()
    
    def normalize_vector(self, vec: np.ndarray) -> np.ndarray:
        """
        L2 normalize vector for cosine similarity calculation
        
        Args:
            vec: Input vector
            
        Returns:
            np.ndarray: Normalized vector
        """
        norm = np.linalg.norm(vec)
        return vec / norm if norm != 0 else vec
    
    def parse_embedding(self, raw_embedding) -> List[float]:
        """
        Parse embedding from database format
        
        Args:
            raw_embedding: Raw embedding from database
            
        Returns:
            List[float]: Parsed embedding values
        """
        if isinstance(raw_embedding, str):
            # String format: "[0.1, 0.2, 0.3]"
            raw_embedding = raw_embedding.strip('[]')
            return [float(x.strip()) for x in raw_embedding.split(',')]
        else:
            # Already a list or array
            return list(raw_embedding)
    
    def calculate_similarity(self, query: str, hospital_reviews: List[Dict[str, Any]], 
                           top_k: int = 30) -> List[Dict[str, Any]]:
        """
        Calculate similarity between query and hospital reviews
        
        Args:
            query: User query
            hospital_reviews: List of hospital review data
            top_k: Number of top results to return
            
        Returns:
            List[Dict[str, Any]]: Similarity results
        """
        if not hospital_reviews:
            print("No hospital reviews provided")
            return []
        
        # Generate query embedding
        query_embedding = self.openai_client.get_embedding(query)
        if not query_embedding:
            print("Failed to generate query embedding")
            return []
        
        # Normalize query embedding
        query_embedding = self.normalize_vector(np.array(query_embedding)).astype('float32').reshape(1, -1)
        
        # Process hospital review embeddings
        embeddings = []
        metadata = []
        
        for review in hospital_reviews:
            try:
                embedding_values = self.parse_embedding(review['embedding'])
                normalized = self.normalize_vector(np.array(embedding_values))
                embeddings.append(normalized.astype('float32'))
                
                metadata.append({
                    'hospital_id': str(review['hospital_id']),
                    'name': str(review['name']),
                    'review': str(review['review'])
                })
            except Exception as e:
                print(f"Error parsing embedding for hospital_id {review['hospital_id']}: {str(e)}")
                continue
        
        if not embeddings:
            print("No valid embeddings found")
            return []
        
        # Convert to numpy array
        embeddings = np.vstack(embeddings).astype('float32')
        
        # Create FAISS index and search
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
        index.add(embeddings)
        similarities, indices = index.search(query_embedding, min(top_k, len(embeddings)))
        
        # Format results
        results = []
        for i, (sim, idx) in enumerate(zip(similarities[0], indices[0])):
            hospital_info = metadata[idx]
            results.append({
                'rank': i + 1,
                'hospital_id': hospital_info['hospital_id'],
                'name': hospital_info['name'],
                'review': hospital_info['review'],
                'similarity': round(float(sim), 4)
            })
        
        return results 