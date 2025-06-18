# 🏥 Hospital Recommendation AI Service

병원 추천 AI 서비스는 사용자의 증상과 선호사항을 분석하여 적합한 병원을 추천하는 웹 애플리케이션입니다.

## 📁 프로젝트 구조

```
hospital_recommendation/
├── app/                          # 메인 애플리케이션 패키지
│   ├── __init__.py
│   ├── main.py                   # 애플리케이션 진입점
│   ├── web/                      # 웹 인터페이스
│   │   ├── __init__.py
│   │   ├── routes.py             # Flask 라우트
│   │   └── templates.py          # HTML 템플릿
│   ├── core/                     # 핵심 비즈니스 로직
│   │   ├── __init__.py
│   │   ├── hospital_search.py    # 병원 검색 엔진
│   │   ├── rag_analyzer.py       # RAG 분석기
│   │   └── similarity_calculator.py # 유사도 계산기
│   ├── ai/                       # AI 관련 컴포넌트
│   │   ├── __init__.py
│   │   ├── prompt_manager.py     # 프롬프트 관리
│   │   └── openai_client.py      # OpenAI 클라이언트
│   └── utils/                    # 유틸리티 함수
│       ├── __init__.py
│       └── database.py           # 데이터베이스 연결
├── run_app.py                    # 애플리케이션 실행 파일
└── README.md
```

## 🚀 시작하기

### 1. 환경 설정

```bash
# 필요한 패키지 설치
pip install flask openai python-dotenv sqlalchemy faiss-cpu numpy requests

# 환경 변수 설정 (.env 파일)
OPENAI_API_KEY=your_openai_api_key_here
DATABASE_URL=your_database_url_here
```

### 2. 애플리케이션 실행

```bash
# 새로운 구조로 실행
python run_app.py

# 또는 직접 실행
python -m app.main
```

### 3. 웹 브라우저에서 접속

```
http://localhost:5000
```

## 🔧 주요 기능

### 1. 자연어 처리
- 사용자의 증상과 요구사항을 자연어로 입력받아 분석
- 위치, 병원 종별, 진료과목, 의료장비 등 자동 추출

### 2. 병원 검색
- 데이터베이스에서 조건에 맞는 병원 검색
- 위치, 병원 종별, 진료과목 기반 필터링

### 3. 유사도 계산
- OpenAI 임베딩을 사용한 벡터 유사도 계산
- FAISS를 활용한 고속 유사도 검색

### 4. RAG 분석
- 병원 리뷰 데이터를 기반으로 한 정성적 분석
- 사용자 요구사항과 병원의 적합성 평가

## 📊 기술 스택

- **Backend**: Python, Flask
- **AI/ML**: OpenAI GPT-4, OpenAI Embeddings, FAISS
- **Database**: SQLAlchemy
- **Frontend**: HTML, CSS, Bootstrap
- **Vector Search**: FAISS

## 🔄 리팩토링 내용

### 기존 파일 → 새로운 구조
- `chatGPT_api.py` → `app/web/routes.py` + `app/web/templates.py`
- `system_prompt.py` → `app/ai/prompt_manager.py`
- `test.py` → `app/core/rag_analyzer.py` + `app/core/similarity_calculator.py`
- `hospital_search.py` → `app/core/hospital_search.py`

### 개선사항
1. **모듈화**: 기능별로 명확하게 분리
2. **클래스 기반 설계**: 객체지향적 구조로 개선
3. **의존성 주입**: 컴포넌트 간 느슨한 결합
4. **에러 처리**: 더 나은 예외 처리
5. **타입 힌트**: 코드 가독성 향상
6. **문서화**: 상세한 docstring 추가

## 🧪 테스트

```bash
# 유사도 계산 테스트
python -c "from app.core.similarity_calculator import SimilarityCalculator; print('SimilarityCalculator imported successfully')"

# RAG 분석 테스트
python -c "from app.core.rag_analyzer import RAGAnalyzer; print('RAGAnalyzer imported successfully')"

# 웹 애플리케이션 테스트
python -c "from app.web.routes import HospitalRecommendationApp; print('HospitalRecommendationApp imported successfully')"
```

## 📝 라이선스

© 2025 Hospital Recommendation AI
