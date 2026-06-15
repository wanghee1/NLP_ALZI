"""API 요청·응답 Pydantic 모델 정의.

chat, contract, document 엔드포인트에서 공유하는 스키마를 모아둔다.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ── 공통 ────────────────────────────────────────────────────────────────────

class DocumentType(str, Enum):
    NOTICE_OF_CLAIM = "notice_of_claim"       # 내용증명
    COMPLAINT = "complaint"                    # 진정서
    STANDARD_CONTRACT = "standard_contract"   # 표준근로계약서


# ── /chat ───────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    session_id: str = Field(..., description="프론트에서 발급한 대화 세션 ID")
    message: str = Field(..., min_length=1, description="사용자 입력 메시지")
    doc_type: str | None = Field(default=None, description="문서 선택 화면에서 명시적으로 전달된 문서 유형")


class LegalGround(BaseModel):
    law_name: str = Field(..., description="법령명 (예: 근로기준법)")
    article: str = Field(..., description="조문표기 (예: 제55조)")
    title: str = Field(..., description="조문 제목 (예: 휴일)")
    plain: str = Field(..., description="LLM 이 작성한 쉬운 해석 (1~2문장)")
    original: str = Field(..., description="검색된 조문 원문 그대로 (코드 삽입, LLM 재작성 아님)")


class ChatResponse(BaseModel):
    session_id: str
    reply: str                                         # consultation 과 동일 (프론트 호환)
    sources: list[str] = Field(default_factory=list)  # 조문 인용 목록 (코드 생성, 거리순)
    legal_grounds: list[LegalGround] = Field(default_factory=list)  # 근거 법조문 (프론트 토글용)
    suggest_document: bool = False
    document_type: str | None = None
    # 문서 수집 흐름(Phase 4-B) 표현용
    mode: str = "chat"  # chat | onboarding | collecting | confirming
    doc_ready: bool = False  # 생성된 PDF 다운로드 가능 여부
    download_url: str | None = None  # doc_ready=True 일 때 PDF 다운로드 경로
    choices: list[str] = Field(default_factory=list)  # 선택지형 질문일 때 보기 목록


# ── /contract/analyze ───────────────────────────────────────────────────────

class ViolationItem(BaseModel):
    type: str = Field(..., description="'위법' | '불리' | '누락'")
    clause: str = Field(..., description="문제되는 조항 원문 또는 누락 항목명")
    issue: str = Field(..., description="알기 쉬운 문제 설명 (단정 금지, 가능성 표현)")
    law_hint: str = Field(..., description="RAG 검색용 법 쟁점 키워드 (5-B에서 사용)")
    severity: str = Field(..., description="'높음' | '중간' | '낮음'")
    suggestion: str = Field(default="", description="구체적 수정·추가 제안 (가능하면 예시 문구 포함)")


class ContractAnalysisResponse(BaseModel):
    violations: list[ViolationItem]
    analyzed: bool = Field(..., description="텍스트 추출 성공 여부")
    message: str = Field(default="", description="스캔 PDF 등 분석 불가 시 안내 메시지")
    used_vision: bool = Field(default=False, description="비전 OCR 경로를 사용한 경우 True")


# ── /document/generate ──────────────────────────────────────────────────────

class DocumentGenerateRequest(BaseModel):
    session_id: str
    doc_type: DocumentType
    fields: dict[str, Any] = Field(
        default_factory=dict,
        description="템플릿에 채워 넣을 필드 값 (field_extractor가 자동 추출하거나 사용자가 제공)",
    )


class DocumentGenerateResponse(BaseModel):
    doc_id: str
    doc_type: DocumentType
    download_url: str


# ── /document/download/{doc_id} ─────────────────────────────────────────────
# 응답은 FileResponse이므로 별도 Pydantic 모델 없음
