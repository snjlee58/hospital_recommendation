"""
OpenAI client wrapper for hospital recommendation service
"""
import os
from typing import List, Dict, Any
from openai import OpenAI
from dotenv import load_dotenv


class OpenAIClient:
    """OpenAI client wrapper for hospital recommendation service"""
    
    def __init__(self):
        """Initialize OpenAI client with API key"""
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY is not set in the environment.")
        
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o"
    
    def get_embedding(self, text: str) -> List[float]:
        """
        Get embedding for text using text-embedding-3-small model
        
        Args:
            text: Text to embed
            
        Returns:
            List[float]: Embedding vector
        """
        try:
            response = self.client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error generating embedding: {str(e)}")
            return []
    
    def chat_completion(self, messages: List[Dict[str, str]], temperature: float = 0.3) -> str:
        """
        Get chat completion from OpenAI
        
        Args:
            messages: List of message dictionaries
            temperature: Temperature for response generation
            
        Returns:
            str: Generated response
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error in chat completion: {str(e)}")
            return ""
    
    def analyze_with_rag(self, hospital_name: str, review_summary: str, user_query: str) -> str:
        """
        Perform RAG analysis for hospital evaluation
        
        Args:
            hospital_name: Name of the hospital
            review_summary: Summary of hospital reviews
            user_query: User's query/requirements
            
        Returns:
            str: RAG analysis result
        """
        from app.ai.prompt_manager import PromptManager
        
        prompt = PromptManager.get_rag_analysis_prompt(hospital_name, review_summary, user_query)
        
        messages = [
            {"role": "system", "content": "당신은 의료 서비스 분석 전문가입니다. 리뷰 내용을 바탕으로 객관적이고 신뢰할 수 있는 분석을 제공해주세요."},
            {"role": "user", "content": prompt}
        ]
        
        return self.chat_completion(messages, temperature=0.3) 