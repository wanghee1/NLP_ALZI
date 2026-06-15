"""FastAPI 의존성 / 세션 저장소.

세션은 DB 없이 in-memory 딕셔너리로 관리한다 (architecture: 세션·상태).
- security: 대화/개인정보를 영구 저장하지 않는다. 메모리에만 두고, 흐름 종료·취소 시 비운다.
- 서버 재시작/`--reload` 시 세션이 사라지는 것은 정상 동작이다 (영속화하지 않음).
- TODO: 운영에서 세션 만료(TTL) 처리 추가.
"""

from __future__ import annotations

# in-memory 세션 저장소 {session_id: 세션 dict}
_session_store: dict[str, dict] = {}


def _new_session() -> dict:
    """문서 수집 흐름을 표현하는 기본 세션 구조."""
    return {
        "mode": "chat",           # chat | collecting | confirming | editing | shared_confirm
        "doc_type": None,         # 예: "wage_complaint"
        "collected": {},          # 필드명 -> 값
        "pending_fields": [],     # 아직 물어볼 필드 목록
        "total_fields": 0,        # 진행도 분모
        "edit_target": None,      # 수정 중 필드명 / "__choosing__" / None
        "choice_retry": None,     # 선택지 재질문 대상 필드
        "validation_retry": {},   # 날짜·금액 검증 재시도 카운터 {field: count}
        "pdf_bytes": None,        # 생성된 PDF 바이트 (다운로드 직후 즉시 비움 — security)
        "shared_fields": {},      # 문서 간 공유 수집값 (세션 메모리에만, 만료 시 소멸 — security)
    }


def get_session(session_id: str) -> dict:
    """세션을 반환한다. 없으면 새로 만들어 저장한다."""
    session = _session_store.get(session_id)
    if session is None:
        session = _new_session()
        _session_store[session_id] = session
    return session


def reset_doc_flow(session_id: str) -> None:
    """문서 수집 흐름 상태를 초기화한다 (완료·취소 시 개인정보 즉시 비움 — security).

    shared_fields 는 다음 문서에서 재사용하므로 보존한다.
    세션 자체가 만료되거나 서버가 재시작되면 함께 소멸한다.
    """
    session = _session_store.get(session_id)
    if session is None:
        return
    preserved_shared = session.get("shared_fields", {})
    session.update(_new_session())
    session["shared_fields"] = preserved_shared
