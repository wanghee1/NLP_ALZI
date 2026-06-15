"""애플리케이션 설정.

.env 를 로딩하고 전역 상수를 한곳에서 정의한다.
설정값·매직넘버를 코드 곳곳에 흩뿌리지 않기 위함이다 (coding-conventions).
"""

import os

from dotenv import load_dotenv

load_dotenv()

# CORS 허용 오리진 (프론트 개발 서버)
FRONTEND_ORIGIN: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")

# 업로드 제한 (계약서 PDF — Phase 2 에서 사용)
MAX_UPLOAD_MB: int = 10
ALLOWED_UPLOAD_TYPES: set[str] = {"application/pdf"}

# 최저임금 (계약서 위반 탐지에서 LLM 프롬프트에 주입)
MIN_WAGE_YEAR: int = 2026
MIN_WAGE_HOURLY: int = 10_320       # 2026년 시간급 최저임금
MIN_WAGE_MONTHLY: int = 2_156_880   # 209시간 기준 월 환산액

# 외부 API 키 (미설정 시 빈 문자열)
# OPENAI_API_KEY 는 '임베딩 전용'이다 (text-embedding-3-small). 채팅 LLM 은 Anthropic 사용.
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
LAW_API_KEY: str = os.getenv("LAW_API_KEY", "")
DATA_GO_KR_API_KEY: str = os.getenv("DATA_GO_KR_API_KEY", "")

# RAG / 벡터스토어 (Phase 2 — 적재 및 검색 공용)
# 임베딩은 OpenAI 유지 (ChromaDB 에 이 모델로 적재됨 — 바꾸면 검색이 깨짐).
EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
VECTORSTORE_DIR: str = os.getenv("VECTORSTORE_DIR", "./data/vectorstore")
CHROMA_COLLECTION: str = os.getenv("CHROMA_COLLECTION", "labor_law")

# LLM (쿼리 변환·답변 생성 — Anthropic Claude). 버전 명시 ID (alias 금지).
LLM_MODEL: str = os.getenv("LLM_MODEL", "claude-sonnet-4-6")

# 검색 (RAG) — 거리 임계값 초과 시 '못 찾음' 처리 (cosine distance 기준)
RETRIEVAL_DISTANCE_THRESHOLD: float = float(os.getenv("RETRIEVAL_DISTANCE_THRESHOLD", "0.6"))
RETRIEVAL_TOP_K: int = int(os.getenv("RETRIEVAL_TOP_K", "3"))

# 문서 생성 (Phase 4 — docxtpl 템플릿 + LibreOffice PDF 변환)
TEMPLATE_DIR: str = os.getenv("TEMPLATE_DIR", "./data/templates")
# LibreOffice 실행 파일. 환경에 따라 "libreoffice" 또는 절대경로일 수 있다.
SOFFICE_BIN: str = os.getenv("SOFFICE_BIN", "soffice")
# 임시 작업 디렉터리는 코드에서 tempfile 로 동적 생성한다 (디스크 영구 보관 X — security).
