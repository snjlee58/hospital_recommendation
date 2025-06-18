"""
HTML templates for hospital recommendation web interface
"""

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
        .hospital-card {
            border: 1px solid #eee;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 15px;
            background: white;
        }
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


def format_hospital_results(hospitals):
    """
    Convert hospital analysis results to HTML formatted string
    
    Args:
        hospitals: List of hospital analysis results
        
    Returns:
        str: HTML formatted hospital results
    """
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
            '<div class="hospital-card">'
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