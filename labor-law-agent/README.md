# 알바·계약직 노동 법률 AI 에이전트

근로기준법·최저임금법 기반 RAG 챗봇, 계약서 위반 분석, 내용증명·진정서 자동 생성 MVP.

## 기술 스택

- **Backend**: Python 3.11, FastAPI, LangChain + ChromaDB, GPT-4o
- **Frontend**: React 18 + Vite

## 프로젝트 구조

```
labor-law-agent/
├── backend/   # FastAPI 서버, RAG 파이프라인, 문서 생성
└── frontend/  # React 채팅 UI
```

## 백엔드 실행

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
cp .env.example .env         # API 키 입력
uvicorn main:app --reload --port 8000
```

API 문서: http://localhost:8000/docs

## 프론트엔드 실행

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

UI: http://localhost:5173

## 주요 기능

1. **노동법 Q&A** — 최저임금·주휴수당·해고 등 채팅 기반 질의응답
2. **계약서 분석** — PDF 업로드 → 위반 조항 자동 탐지
3. **문서 생성** — 내용증명·진정서·표준근로계약서 DOCX/PDF 출력
