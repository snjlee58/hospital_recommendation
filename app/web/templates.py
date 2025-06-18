"""
HTML templates for hospital recommendation web interface
"""

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

    /* ─── result "cards" ───────────────────────────────────────── */
    .result-card {
        background: #fff;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 0.75rem;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    .result-card h4 {
        margin: 0;
        font-size: 1.1rem;
        font-weight: 600;
    }
    .result-card p {
        margin: 0.25rem 0;
        font-size: 0.9rem;
        color: #4b5563;
    }
    .result-card a {
        color: #2563eb;
        text-decoration: none;
    }
    .result-card a:hover {
        text-decoration: underline;
    }
    
    /* RAG analysis specific styles */
    .similarity-score {
        color: #ff6f61;
        font-weight: bold;
    }
    .analysis-section {
        background: #f8f9fa;
        padding: 10px;
        border-radius: 5px;
        margin-top: 10px;
    }
  </style>
</head>

<body>
  <h1 style="margin-top:2rem;">HosPT</h1>
 <form action="/reset" method="post" id="reset-form" style="position:fixed; top:16px; left:16px; margin:0; padding:0; z-index:1000;">
  <button type="submit" style="
      background: none;
      border: none;
      padding: 0;
      cursor: pointer;
      width: 40px;
      height: 40px;
  ">

    <!-- replace this SVG with your own -->
    <svg viewBox="-7.92 -7.92 39.84 39.84" xmlns="http://www.w3.org/2000/svg" id="create-note" class="icon glyph" fill="#000000"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"><path d="M20.71,3.29a2.91,2.91,0,0,0-2.2-.84,3.25,3.25,0,0,0-2.17,1L9.46,10.29s0,0,0,0a.62.62,0,0,0-.11.17,1,1,0,0,0-.1.18l0,0L8,14.72A1,1,0,0,0,9,16a.9.9,0,0,0,.28,0l4-1.17,0,0,.18-.1a.62.62,0,0,0,.17-.11l0,0,6.87-6.88a3.25,3.25,0,0,0,1-2.17A2.91,2.91,0,0,0,20.71,3.29Z"></path><path d="M20,22H4a2,2,0,0,1-2-2V4A2,2,0,0,1,4,2h8a1,1,0,0,1,0,2H4V20H20V12a1,1,0,0,1,2,0v8A2,2,0,0,1,20,22Z" style="fill:#231f20"></path></g></svg>
  </button>
  </form>
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


def format_hospital_results(hospitals):
    """
    Convert hospital analysis results to HTML formatted string
    
    Args:
        hospitals: List of hospital analysis results
        
    Returns:
        str: HTML formatted hospital results
    """
    if not hospitals:
        return "검색 결과가 없습니다."
    
    # Check if hospitals have RAG analysis (new format)
    if 'rag_analysis' in hospitals[0]:
        # New format with RAG analysis
        result = []
        for h in hospitals:
            # 이미지와 URL이 있는 경우에만 표시
            image_html = ''
            if h.get('image_url'):
                image_html = f'<img src="{h["image_url"]}" alt="{h["name"]}" class="hospital-image" style="max-width: 200px; margin-bottom: 10px;">'
            
            url_html = ''
            if h.get('url'):
                url_html = f'<p><a href="{h["url"]}" target="_blank" class="btn btn-outline-primary btn-sm">병원 홈페이지</a></p>'
            
            # RAG 분석 결과의 줄바꿈을 HTML <br> 태그로 변환
            analysis_html = h["rag_analysis"].replace('\n', '<br>')
            
            hospital_info = (
                '<div class="result-card">'
                + image_html
                + f'<h4>{h["name"]}</h4>'
                + f'<p>{h["address"]}<br>☎ {h["tel"]}</p>'
                + url_html
                + f'<p class="similarity-score">유사도 점수: {h["similarity"]}</p>'
                + '<div class="analysis-section">'
                + '<h5>AI 분석 결과:</h5>'
                + analysis_html
                + '</div>'
                + '</div>'
            )
            result.append(hospital_info)
        
        return "".join(result)
    else:
        # Legacy format - simple card format (from chatGPT_api.py)
        cards = []
        for h in hospitals:
            url_link = f"<a href='{h.get('url')}' target='_blank'>{h['url']}</a>" if h.get('url') else ""
            cards.append(f"""
              <div class="result-card">
                <h4>{h['name']}</h4>
                <p>{h['address']}</p>
                <p>☎ {h['tel']}</p>
                <p>{url_link}</p>
              </div>
            """)

        return "\n".join(cards) 