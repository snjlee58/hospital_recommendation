# Hospital Recommendation AI

이 프로젝트는 사용자로부터 자연어로 입력받은 증상과 선호사항을 분석하여 적합한 병원을 추천하는 웹 애플리케이션입니다. OpenAI API를 활용해 텍스트 임베딩 및 정성적 분석을 수행하고, PostgreSQL 데이터베이스에서 병원 정보를 조회합니다.

---

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
│
├── database/                     # 데이터 수집·처리 및 벡터DB 관리
│   ├── api/
│   │   ├── hospital_openapi/     # 공공병원 OpenAPI 래퍼
│   │   │   ├── api_config.py     # API 설정
│   │   │   ├── api.py            # API 연결
│   │   │   ├── get_equipment_info_api.py # 장비 정보 api
│   │   │   ├── get_hospital_grades_batch_info_api.py # 평가등급 정보 API
│   │   │   ├── get_operating_hours_info_api.py # 운영시간 정보 API
│   │   │   ├── main.py
│   │   │   └── retrieve_detail_info_api.py
│   │   └── naver_api/            # 네이버 블로그 크롤러 & API
│   │       ├── naver_api.py      # 네이버 블로그 API 연결
│   │       └── naver_blog_crawler.py # 네이버 블로그 크롤러
│   │
│   └── utils/                    # 데이터 전처리 · 임베딩 · LLM 헬퍼
│       ├── chunking_prompt.py    # LLM 청킹용 시스템 프롬프트
│       ├── data_utils.py         # JSON→DataFrame, 클렌징 등 헬퍼
│       ├── db_utils.py           # DB 헬퍼
│       ├── embedding_utils.py    # 임베딩 래퍼 (MiniLM)
│       └── llm_utils.py          # llm 연결
│
├── run_app.py                    # 전체 앱 실행 파일
└── README.md                     # 프로젝트 개요 및 실행 방법
```

## 개요

- 사용자 자연어 입력 기반 병원 추천
- PostgreSQL에서 병원 메타데이터 조회
- FAISS로 벡터 유사도 기반 후보군 탐색
- GPT 기반 RAG 방식으로 리뷰 종합 분석

---

## 환경 설정

### 요구 사항

- Python 3.8 이상
- PostgreSQL (NEON 등 클라우드 DB 지원)
- OpenAI API Key

### 환경 변수

루트 디렉토리에 `.env` 파일을 생성하고 다음과 같이 입력합니다:

```env
DATABASE_URL=your_postgresql_connection_string
OPENAI_API_KEY=your_openai_api_key

---

## 설치 및 실행

```bash
# 필수 패키지 설치
pip install flask openai python-dotenv sqlalchemy faiss-cpu numpy requests beautifulsoup4

# 애플리케이션 실행
python run_app.py
```

이후 브라우저에서 아래 주소로 접속합니다:

```
http://localhost:5000
```

---

## 디렉토리 구조

```plaintext
hospital_recommendation/
├── app/
│   ├── main.py
│   ├── web/
│   │   ├── routes.py
│   │   └── templates.py
│   ├── core/
│   │   ├── hospital_search.py
│   │   ├── rag_analyzer.py
│   │   └── similarity_calculator.py
│   ├── ai/
│   │   ├── prompt_manager.py
│   │   └── openai_client.py
│   └── utils/
│       └── database.py
├── run_app.py
└── README.md
```

---

## 주요 기능

### 자연어 분석

- 사용자 입력에서 위치, 병원 종별, 진료과목 등 정보 추출

### 병원 검색

- PostgreSQL 기반 병원 메타데이터 조회
- 조건 필터링 (예: '서울시', '정형외과')

### 임베딩 기반 유사도 검색

- Sentence-Transformers 기반 임베딩 생성
- FAISS로 유사 리뷰 검색

### RAG 기반 리뷰 분석

- 병원 리뷰 + 웹 검색 결과 종합
- GPT-4o 기반 병원 강점/약점, 추천도 분석

---

## 테스트

```bash
# 유사도 계산기 테스트
python -c "from app.core.similarity_calculator import SimilarityCalculator"

# RAG 분석기 테스트
python -c "from app.core.rag_analyzer import RAGAnalyzer"

# 웹 라우터 테스트
python -c "from app.web.routes import HospitalRecommendationApp"
```

---

## 리팩토링 내용

### 기존 → 새로운 구조 변경

| 기존 파일명          | 변경 후 위치                          |
|---------------------|---------------------------------------|
| `chatGPT_api.py`    | `app/web/routes.py`, `templates.py`   |
| `system_prompt.py`  | `app/ai/prompt_manager.py`            |
| `test.py`           | `rag_analyzer.py`, `similarity_calculator.py` |
| `hospital_search.py`| `app/core/hospital_search.py`         |

### 개선 사항

- 기능별로 디렉토리 분리 (웹, 코어 로직, AI)
- 클래스 기반 로직 적용
- 예외 처리 강화
- 타입 힌트 적용
- 문서화 및 주석 보완

---

## 라이선스

본 프로젝트는 비상업적 목적에 한해 자유롭게 사용할 수 있습니다. 상업적 이용이나 외부 배포 시 라이선스 조건이 추후 별도 안내될 수 있습니다.