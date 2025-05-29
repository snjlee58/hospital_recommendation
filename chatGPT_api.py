import os
import re
import json
import requests
from flask import Flask, request, render_template_string
from dotenv import load_dotenv
from system_prompt import SYSTEM_PROMPT
from hospital_search import search_hospitals, load_database_url, create_db_engine

# Load environment variables
load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = "gpt-4o-mini"

db_url = load_database_url()
db_engine = create_db_engine(db_url)

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# Initialize Flask app and message history
app = Flask(__name__)
messages = [SYSTEM_PROMPT]

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>🏥 Hospital Request Assistant</title>

    <!-- Google Fonts Pretendard -->
    <link href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css" rel="stylesheet">
    <!-- Bootstrap -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">

    <style>
        body {
            font-family: 'Pretendard', sans-serif;
            background: linear-gradient(to bottom right, #f9fafb, #eef1f5);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }
        h1 {
            font-weight: 700;
            font-size: 2.5rem;
            color: #333;
        }
        .card {
            border: none;
            border-radius: 20px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.05);
            background: white;
        }
        .btn-primary {
            background-color: #ff6f61;
            border: none;
            font-weight: bold;
        }
        .btn-primary:hover {
            background-color: #ff8a75;
        }
        footer {
            margin-top: auto;
        }
    </style>
</head>

<body>
    <div class="container py-5">
        <h1 class="mb-4 text-center">🏥 병원 추천 AI 서비스</h1>
        <div class="card p-4 shadow-sm">
            <form method="post" class="mb-3">
                <div class="mb-3">
                    <label class="form-label"><b>증상이나 병원 요청사항을 입력하세요</b></label>
                    <input type="text" name="user_input" class="form-control rounded-3 p-2" placeholder="예) 왼쪽 팔이 저리고 두통이 있어. 강남구에 위치한 병원을 추천해줘." required>
                </div>
                <div class="d-grid gap-2">
                    <button type="submit" class="btn btn-primary btn-lg rounded-pill">제출하기</button>
                </div>
            </form>

            <h5 class="mt-4"> <b>AI 답변</b></h5>
            <div class="bg-light border rounded-4 p-4" style="min-height:180px; background-color: #fafafa;">
                {{ response | safe }}
            </div>
        </div>
    </div>

    <footer class="text-center py-4">
        <small class="text-muted">© 2025 Hospital Recommendation AI</small>
    </footer>
</body>
</html>
'''

def call_openai_api(user_input):
    """Send user input to OpenAI and return the assistant reply."""
    messages.append({"role": "user", "content": user_input})
    data = {"model": MODEL, "messages": messages}
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
    response_json = response.json()
    reply = response_json["choices"][0]["message"]["content"].strip()
    messages.append({"role": "assistant", "content": reply})
    return reply

def extract_json_from_reply(reply):
    """Try to extract JSON object from LLM reply."""
    match = re.search(r"\{.*\}", reply, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return None
    return None

def format_hospital_results(hospitals):
    """Convert hospital rows to HTML formatted string, excluding null URLs."""
    return "<br>\n".join([
        f"<b>{h['name']}</b><br>{h['address']}<br>☎ {h['tel']}" +
        (f"<br><a href='{h['url']}' target='_blank'>{h['url']}</a>" if h.get('url') else '') +
        "<hr>"
        for h in hospitals
    ])

@app.route("/", methods=["GET", "POST"])
def chat():
    reply = ""
    if request.method == "POST":
        user_input = request.form["user_input"]
        reply = call_openai_api(user_input)
        data = extract_json_from_reply(reply)

        if data:
            city = data.get("city")
            district = data.get("district")
            hospital_type = data.get("hospital_type")
            department = data.get("department_name")
            hospitals = search_hospitals(city, district, hospital_type, department, db_engine)
            result_text = format_hospital_results(hospitals)
            return render_template_string(HTML_TEMPLATE, response=result_text)

    return render_template_string(HTML_TEMPLATE, response=reply)

if __name__ == "__main__":
    app.run(debug=True)