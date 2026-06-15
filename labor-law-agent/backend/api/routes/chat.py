"""채팅 라우트 — 노동법 Q&A + 문서 수집 흐름 디스패치.

api/ 계층은 얇은 어댑터다. 비즈니스 로직(검색·수집·생성)은 src/ 에 위임하고
여기서는 세션 상태에 따라 어디로 보낼지 분기·호출만 한다 (architecture: 계층 분리).

- mode == "chat" 이고 문서 트리거 아님 → src.rag.chain.answer (RAG Q&A)
- 수집 흐름 중이거나 트리거 → src.document.collector.handle_message (상태 머신)
- collector 가 done 을 주면 → generator/pdf_converter 로 PDF 생성 후 다운로드 링크 제공
"""

import logging

from fastapi import APIRouter

from api.deps import get_session, reset_doc_flow
from api.schemas import ChatRequest, ChatResponse
from src.document import collector
from src.document.fields import DOC_TYPES
from src.document.generator import cleanup_files, generate_document
from src.document.pdf_converter import convert_to_pdf
from src.rag import chain

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat")


def _finalize_document(session_id: str, session: dict, result: dict) -> ChatResponse:
    """collector 가 done 을 주면 PDF 를 만들고 다운로드 링크를 실어 응답한다."""
    field_values = result.get("field_values", {})
    doc_type = session.get("doc_type", "wage_complaint")
    try:
        docx_path = generate_document(doc_type, field_values)
        pdf_path = convert_to_pdf(docx_path)
    except Exception as exc:  # noqa: BLE001 - 생성 실패도 친화 메시지로
        logger.error("문서 생성 실패: %s", type(exc).__name__)
        reset_doc_flow(session_id)
        return ChatResponse(
            session_id=session_id,
            reply="문서를 만드는 중 문제가 생겼어요. 잠시 후 다시 시도해 주세요.",
            mode="chat",
        )

    # PDF 바이트를 메모리로 읽고, 디스크 파일(docx·pdf·tmpdir)을 즉시 삭제한다.
    # 파일 경로 대신 바이트를 세션에 보관 → 경로 소멸·서버 재시작과 무관하게 다운로드 가능.
    # 다운로드 직후 바이트도 비워 디스크·메모리 모두 흔적을 남기지 않는다 (security).
    try:
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
    except OSError as exc:
        logger.error("PDF 읽기 실패: %s", type(exc).__name__)
        reset_doc_flow(session_id)
        cleanup_files(docx_path, pdf_path)
        return ChatResponse(
            session_id=session_id,
            reply="문서를 만드는 중 문제가 생겼어요. 잠시 후 다시 시도해 주세요.",
            mode="chat",
        )

    cleanup_files(docx_path, pdf_path)  # docx + pdf + tmpdir 즉시 삭제

    session["collected"] = {}
    session["pending_fields"] = []
    session["edit_target"] = None
    session["mode"] = "chat"
    session["pdf_bytes"] = pdf_bytes

    return ChatResponse(
        session_id=session_id,
        reply=result["reply"] + "\n문서가 준비됐어요. 아래에서 PDF를 받으세요.",
        mode="chat",
        doc_ready=True,
        download_url=f"/document/download/{session_id}",
    )


@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    session = get_session(request.session_id)
    mode = session.get("mode", "chat")
    try:
        if mode in ("collecting", "confirming", "editing", "shared_confirm"):
            # ① 수집 흐름 진행 중 → 트리거·doc_type 검사 없이 상태 머신에 바로 위임.
            #    수집 중 답변에 "부당해고" 같은 말이 있어도 새 흐름으로 튀지 않는다.
            result = collector.handle_message(session, request.message)
        elif request.doc_type:
            # ② 프론트에서 명시적 doc_type 전달 → 메시지 기반 트리거 재해석 건너뜀.
            #    "시작하기" 메시지가 wage_complaint 트리거로 오인되지 않는다.
            result = collector.handle_message(session, request.message, doc_type=request.doc_type)
        elif collector.is_doc_trigger(request.message):
            # ③ 메시지 트리거 → 키워드에서 문서 유형 판별 후 온보딩
            triggered_doc_type = collector.get_doc_type_from_trigger(request.message) or "wage_complaint"
            result = collector.handle_message(session, request.message, doc_type=triggered_doc_type)
        else:
            # ④ 일반 노동법 Q&A
            answer = chain.answer(request.message)
            return ChatResponse(
                session_id=request.session_id,
                reply=answer["consultation"],
                sources=answer["sources"],
                legal_grounds=answer["legal_grounds"],
                mode="chat",
                suggest_document=answer.get("suggest_document", False),
                document_type=answer.get("document_type"),
            )
    except Exception as exc:  # noqa: BLE001
        # 사용자에겐 친화 메시지, 서버 로그엔 예외 '타입'만 (PII/키 비노출 — security)
        logger.error("chat 처리 실패: %s", type(exc).__name__)
        return ChatResponse(
            session_id=request.session_id,
            reply="일시적 오류가 발생했어요. 잠시 후 다시 시도해 주세요.",
            mode=session.get("mode", "chat"),
        )

    # 수집 흐름 결과 처리
    if result.get("done"):
        return _finalize_document(request.session_id, session, result)

    return ChatResponse(
        session_id=request.session_id,
        reply=result["reply"],
        mode=result["mode"],
        choices=result.get("choices", []),
    )
