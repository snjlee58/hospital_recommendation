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

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>🏥 Hospital Request Assistant</title>
    <link href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css" rel="stylesheet">

  <style>
    body { font-family: 'Pretendard', sans-serif; background:white; display:flex; flex-direction:column; align-items:center; margin:0; height:100vh; }
    .chat-container { width:100%; max-width:900px; background:white; border-radius:8px; display:flex; flex-direction:column; height:82%; margin-top:1rem; }
    .messages { 
        display: flex;
        flex-direction: column;
        flex:1; 
        padding:1rem; 
        overflow-y:auto; 
    }
    .message { 
        display: inline-block;
        max-width:70%; 
        margin-bottom:.75rem; 
        padding:.75rem 1rem; 
        border-radius:16px; 
        line-height:1.4; 
    }
    .message.user { 
        align-self: flex-end;
        word-wrap: break-word;
        background: #f4f4f4; 
        color:#0d0d0d; 
        margin-left:auto;
    }
    .message.assistant { background:white; color:#333; max-width:100%; margin-right:auto;}
    .input-area { 
        display:flex; 
        align-items: flex-center;
        border:1px solid #e1e4e8; 
        border-radius: 24px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.05);
        padding:1rem; 
    }
    .input-area input { 
        flex:1; border:none; 
        border-radius: 24px;
    }
    .input-area input:focus { 
        outline:none; 
    }
    .input-area button { 
        width: 44px;
        height: 44px;
        border-radius: 50%;
        display: flex;
        background:#000000; 
        border:none; 
        align-items:center;
        justify-content:center;
        color:white; 
    }
    .input-area button:hover { background:#494949; }
  </style>

</head>
<body>
  <h1 style="margin-top:2rem;">HosPT</h1>
  <div class="chat-container">
    <div class="messages" id="msgs">
      {% for msg in messages %}
        <div class="message {{ 'user' if msg.role=='user' else 'assistant' }}">
          {{ msg.content|safe }}
        </div>
      {% endfor %}
    </div>
    <form class="input-area" method="post">
        <input name="user_input" placeholder="증상이나 요청사항을 입력하세요…" autocomplete="off" required>
        <button type="submit">
            <svg width="205px" height="205px" viewBox="-4.8 -4.8 33.60 33.60" fill="none" xmlns="http://www.w3.org/2000/svg"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"> <path d="M12 5V19M12 5L6 11M12 5L18 11" stroke="#ffffff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"></path> </g></svg>
        </button>
    </form>
  </div>
  <script>
    // scroll to bottom on load
    const msgs = document.getElementById('msgs');
    msgs.scrollTop = msgs.scrollHeight;
  </script>
</body>
</html>
"""

def call_openai_api(user_input):
    """Send user input to OpenAI and return the assistant reply."""
    data = {"model": MODEL, "messages": messages}
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
    response_json = response.json()
    reply = response_json["choices"][0]["message"]["content"].strip()
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
        (f"<br><a href='{h['url']}' target='_blank'>{h['url']}</a>" if h.get('url') else '')

        for h in hospitals
    ])

@app.route("/", methods=["GET", "POST"])
def chat():
    if request.method == "POST":
        user_input = request.form["user_input"]
        # Show the user bubble
        messages.append({"role": "user", "content": user_input})

        # Call LLM + DB lookup
        reply = call_openai_api(user_input)
        data = extract_json_from_reply(reply)

        if data:
            # you returned JSON: turn into HTML list or whatever
            city, district, hospital_type, department = (
              data.get("city"), 
              data.get("district"),
              data.get("hospital_type"), 
              data.get("department_name")
            )
            hospitals = search_hospitals(city, district, hospital_type, department, db_engine)
            result_text = format_hospital_results(hospitals)
            messages.append({"role": "assistant", "content": result_text})
        else:
            # LLM asked a follow-up
            messages.append({"role":"assistant","content": reply})

    # on both GET and POST, render the chat history
    return render_template_string(HTML_TEMPLATE, messages=[{"role": "assistant", "content": '증상이나 요청사항을 입력하세요…'}]+messages[1:]) # skip the system prompt

if __name__ == "__main__":
    app.run(debug=True)