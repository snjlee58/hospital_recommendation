"""
Web routes for hospital recommendation service
"""
import re
import json
import requests
from flask import Flask, request, render_template_string
from app.ai.prompt_manager import PromptManager
from app.ai.openai_client import OpenAIClient
from app.core.hospital_search import HospitalSearchEngine
from app.core.rag_analyzer import RAGAnalyzer
from app.utils.database import get_database_connection
from app.web.templates import HTML_TEMPLATE, format_hospital_results


class HospitalRecommendationApp:
    """Main application class for hospital recommendation service"""
    
    def __init__(self):
        """Initialize the application"""
        self.app = Flask(__name__)
        self.openai_client = OpenAIClient()
        self.search_engine = HospitalSearchEngine()
        self.rag_analyzer = RAGAnalyzer(self.openai_client, self.search_engine)
        self.messages = [PromptManager.get_system_prompt()]
        
        # Setup routes
        self.setup_routes()
    
    def setup_routes(self):
        """Setup Flask routes"""
        self.app.route("/", methods=["GET", "POST"])(self.chat)
    
    def call_openai_api(self, user_input: str) -> str:
        """
        Send user input to OpenAI and return the assistant reply
        
        Args:
            user_input: User's input text
            
        Returns:
            str: Assistant's reply
        """
        data = {
            "model": self.openai_client.model,
            "messages": self.messages
        }
        
        headers = {
            "Authorization": f"Bearer {self.openai_client.client.api_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions", 
            headers=headers, 
            json=data
        )
        
        response_json = response.json()
        reply = response_json["choices"][0]["message"]["content"].strip()
        
        return reply
    
    def extract_json_from_reply(self, reply: str) -> dict:
        """
        Try to extract JSON object from LLM reply
        
        Args:
            reply: LLM reply text
            
        Returns:
            dict: Extracted JSON data or None
        """
        match = re.search(r"\{.*\}", reply, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                return None
        return None
    
    def chat(self):
        """Main chat route handler"""
        if request.method == "POST":
            user_input = request.form["user_input"]
            # Show the user bubble
            self.messages.append({"role": "user", "content": user_input})

            # Call LLM + DB lookup
            reply = self.call_openai_api(user_input)
            data = self.extract_json_from_reply(reply)

            if data:
                # you returned JSON: turn into HTML list or whatever
                city, district, hospital_type, department = (
                  data.get("city"), 
                  data.get("district"),
                  data.get("hospital_type"), 
                  data.get("department_name")
                )
                hospitals = self.search_engine.search_hospitals(
                    city, district, hospital_type, department
                )
                print(f"Found {len(hospitals)} hospitals")

                if hospitals:
                    # Create analysis query
                    preference = data.get("preference", "")
                    explanation = data.get("explanation", "")
                    analysis_query = f"선호사항: {preference}\n추가 설명: {explanation}"
                    
                    # Perform RAG analysis
                    analyzed_hospitals = self.rag_analyzer.analyze_hospitals(
                        hospitals, analysis_query
                    )
                    
                    # Format and display results
                    result_text = format_hospital_results(analyzed_hospitals)
                    self.messages.append({"role": "assistant", "content": result_text})
                else:
                    self.messages.append({"role": "assistant", "content": "검색 결과가 없습니다."})
            else:
                # LLM asked a follow-up
                self.messages.append({"role":"assistant","content": reply})

        # on both GET and POST, render the chat history
        return render_template_string(
            HTML_TEMPLATE, 
            messages=[{"role": "assistant", "content": '증상이나 요청사항을 입력하세요…'}]+self.messages[1:]
        ) # skip the system prompt
    
    def run(self, debug: bool = True, host: str = "0.0.0.0", port: int = 5000):
        """
        Run the Flask application
        
        Args:
            debug: Enable debug mode
            host: Host to bind to
            port: Port to bind to
        """
        self.app.run(debug=debug, host=host, port=port)


# Create global app instance
app = HospitalRecommendationApp().app


if __name__ == "__main__":
    hospital_app = HospitalRecommendationApp()
    hospital_app.run() 