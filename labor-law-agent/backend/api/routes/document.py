"""문서 다운로드 엔드포인트.

생성된 진정서 PDF 를 내려준다. 생성 자체는 수집 흐름(/chat → collector → generator)에서
이뤄지며, PDF 바이트가 세션(pdf_bytes)에 in-memory 로 보관된다.

security: 디스크 파일은 생성 직후 즉시 삭제되어 이 시점엔 존재하지 않는다.
세션 바이트는 다운로드 응답 직전에 None 으로 비워 메모리에도 흔적을 남기지 않는다.
"""

from __future__ import annotations

import logging
from urllib.parse import quote

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from api.deps import get_session
from src.document.fields import DOC_TYPES

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/document")


@router.get("/download/{session_id}")
def download_document(session_id: str) -> Response:
    """세션 메모리에 보관된 PDF 바이트를 내려주고 즉시 비운다."""
    session = get_session(session_id)
    pdf_bytes: bytes | None = session.get("pdf_bytes")

    if not pdf_bytes:
        raise HTTPException(
            status_code=404,
            detail="다운로드할 문서가 없거나 만료되었습니다. 진정서를 다시 생성해 주세요.",
        )

    # 전송 전에 세션에서 즉시 비움 (security: 다운로드 후 메모리에 보관하지 않음)
    session["pdf_bytes"] = None

    doc_type = session.get("doc_type", "wage_complaint")
    display_name = DOC_TYPES.get(doc_type, DOC_TYPES["wage_complaint"])["display_name"]
    # RFC 6266: ASCII fallback + UTF-8 percent-encoded filename* for Korean characters
    encoded_name = quote(f"{display_name}.pdf", safe="")
    headers = {
        "Content-Disposition": f'attachment; filename="document.pdf"; filename*=UTF-8\'\'{encoded_name}'
    }
    return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)
