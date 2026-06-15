"""대화형 필드 수집 상태 머신.

세션 mode 에 따라 사용자 메시지를 분기 처리하며, 필수 필드를 하나씩 모은다.

순수 로직 계층(src/document)이라 전송 계층(api/)·세션 저장소에 의존하지 않는다 (architecture).
세션 dict 를 인자로 받아 제자리에서 갱신하고, 결과(reply/mode/done)를 돌려준다.
개인정보(collected 값)는 로그에 출력하지 않는다 (security).
"""

from __future__ import annotations

import re

from src.document.fields import COMMON_FIELD_ALIAS, COMMON_FIELDS, DOC_TYPES

# ── 필드별 '쉬운 말' 질문 (문서 유형별) ──────────────────────────────────────
# 키는 fields.py 의 변수명과 정확히 일치해야 한다.
QUESTIONS_MAP: dict[str, dict[str, str]] = {
    "wage_complaint": {
        "worker_name":       "먼저, 본인 성함이 어떻게 되세요?",
        "worker_address":    "연락받으실 주소를 알려주세요. (도로명 또는 지번 주소)",
        "worker_mobile":     "휴대전화 번호를 알려주세요. (예: 010-1234-5678)",
        "employer_name":     "사장님(사업주) 성함이 어떻게 되세요?",
        "company_name":      "일하던 가게나 회사 이름이 뭐예요?",
        "company_address":   "그 가게(회사)는 어디에 있어요? 주소를 알려주세요.",
        "hire_date":         "언제부터 일을 시작하셨어요? (예: 2025-09-01)",
        "resign_date":       "마지막으로 일한 날이 언제예요? 아직 일하고 있다면 '건너뛰기'라고 해주세요. (예: 2025-12-31)",
        "employment_status": "지금도 거기서 일하세요, 아니면 그만두셨어요?",
        "unpaid_total":      "못 받은 임금이 모두 얼마예요? (예: 300,000원)",
        "job_description":   "회사에서 어떤 일을 하셨어요? (예: 서빙, 배달, 편의점 알바)",
        "payday":            "임금은 매월 며칠에 받기로 했나요? (예: 매월 25일)",
        "detail_content":    "어떤 일이 있었는지 편하게 적어주세요. (언제, 얼마를, 어떻게 못 받았는지)",
    },
    "unfair_dismissal": {
        "worker_name":       "먼저, 본인 성함이 어떻게 되세요?",
        "worker_address":    "연락받으실 주소를 알려주세요. (도로명 또는 지번 주소)",
        "worker_phone":      "연락받을 전화번호를 알려주세요. (예: 010-1234-5678)",
        "employer_name":     "사장님(사업주) 성함이 어떻게 되세요?",
        "company_name":      "일하던 가게나 회사 이름이 뭐예요?",
        "company_address":   "그 가게(회사)는 어디에 있어요? 주소를 알려주세요.",
        "hire_date":         "언제부터 일을 시작하셨어요? (예: 2025-09-01)",
        "dismissal_date":    "언제 해고 통보를 받았어요? (예: 2025-12-01)",
        "dismissal_method":  "해고를 어떻게 통보받으셨어요?",
        "dismissal_reason":  "회사가 해고 이유를 뭐라고 했어요?",
        "job_description":   "회사에서 어떤 일을 담당하셨어요? (예: 영업, 서빙, 배달, 사무보조)",
        "detail_content":    "왜 이 해고가 부당하다고 생각하는지 편하게 적어주세요. (상황, 이유, 경위)",
    },
    "payment_demand": {
        "worker_name":    "먼저, 본인 성함이 어떻게 되세요?",
        "worker_address": "본인 주소를 알려주세요. (도로명 또는 지번 주소)",
        "worker_phone":   "연락받을 전화번호를 알려주세요. (예: 010-1234-5678)",
        "employer_name":  "사장님(사업주) 성함이 어떻게 되세요?",
        "company_name":   "일하던 가게나 회사 이름이 뭐예요?",
        "company_address":"그 가게(회사)는 어디에 있어요? 주소를 알려주세요.",
        "work_period":    "언제부터 언제까지 일했어요? (예: 2025-01-01 ~ 2025-12-31)",
        "unpaid_total":   "못 받은 금액이 얼마예요? (예: 500,000원)",
        "worker_account": "입금받을 계좌를 알려주세요. (은행명 / 계좌번호)",
    },
}

# ── 선택지 필드 (문서 유형별) ──────────────────────────────────────────────
# options: 프론트에 버튼으로 표시할 표준 보기값
# synonyms: 자유 입력을 표준값으로 정규화하는 동의어 목록 (부분 문자열 매칭)
# retry_msg: 첫 번째 미매칭 시 재질문 문구
CHOICE_FIELDS_MAP: dict[str, dict[str, dict]] = {
    "wage_complaint": {
        "employment_status": {
            "options": ["재직", "퇴직"],
            "synonyms": {
                "퇴직": ["그만둠", "그만뒀", "그만두", "퇴사", "나왔", "나옴", "그만났", "관뒀", "그만다녔"],
                "재직": ["다님", "다니는", "다니고", "다녀", "재직중", "재직", "일함", "일하고", "아직 다"],
            },
            "retry_msg": "재직 중이신가요, 아니면 퇴직하셨나요?",
        },
        "contract_method": {
            "options": ["서면", "구두"],
            "synonyms": {
                "서면": ["서류", "종이로", "계약서로", "문서로", "서면으로", "서면"],
                "구두": ["말로", "구두로", "구두", "말했", "말로만"],
            },
            "retry_msg": "근로계약을 서면(종이 계약서)으로 하셨나요, 아니면 구두(말)로 하셨나요?",
        },
        # business_type 제거: 템플릿에 없는 ghost field
    },
    "unfair_dismissal": {
        "dismissal_method": {
            "options": ["구두", "문자", "이메일", "서면"],
            "synonyms": {
                "구두": ["말로", "말했", "직접", "면담", "대화", "통화"],
                "문자": ["문자", "카톡", "카카오", "sms", "메시지", "메세지"],
                "이메일": ["이메일", "메일", "email"],
                "서면": ["서면", "공문", "서류", "문서"],
            },
            "retry_msg": "해고 통보 방법을 알려주세요. 구두/문자/이메일/서면 중 하나로 답해주세요.",
        },
    },
    "payment_demand": {},
}

# ── 날짜·금액 검증 ────────────────────────────────────────────────────────────
_DATE_FIELDS  = {"hire_date", "dismissal_date", "resign_date"}
_AMOUNT_FIELDS = {"unpaid_total", "unpaid_severance", "unpaid_other"}
_MAX_DATE_RETRY   = 2   # 초과 시 원값 그대로 저장
_MAX_AMOUNT_RETRY = 1


def _validate_date(value: str) -> tuple[bool, str]:
    """월 1–12, 일 1–31 범위만 체크. 명백한 오류(17월·32일 등)만 차단."""
    m = re.search(r'(\d{4})[.\-/년]\s*(\d{1,2})[.\-/월]\s*(\d{1,2})', value)
    if m:
        month = int(m.group(2))
        day   = int(m.group(3))
        if not (1 <= month <= 12):
            return False, (
                f"입력하신 날짜에서 월이 {month}인데 맞는지 확인해 주세요. "
                "올바른 날짜를 다시 알려주세요. (예: 2025-03-15)"
            )
        if not (1 <= day <= 31):
            return False, (
                f"입력하신 날짜에서 일이 {day}인데 맞는지 확인해 주세요. "
                "올바른 날짜를 다시 알려주세요. (예: 2025-03-15)"
            )
    return True, ""


def _validate_amount(value: str) -> tuple[bool, str]:
    """숫자가 전혀 없으면 안내 (한 번만)."""
    if not re.search(r'\d', value):
        return False, "금액을 숫자로 알려주세요. (예: 500,000원 또는 500000)"
    return True, ""


# ── 취소 키워드 ───────────────────────────────────────────────────────────────
# "그만" 단독 포함 금지: "그만둠/그만뒀어요" 등 정상 답변이 오인되지 않도록.
_CANCEL = (
    "취소",
    "그만할래", "그만 할래",
    "그만둘래", "그만 둘래",
    "그만하겠", "그만 하겠",
    "안 할래", "안할래",
    "안 할게", "안할게",
    "중단",
    "처음부터",
)

# ── 문서 유형별 트리거 키워드 ──────────────────────────────────────────────
_TRIGGER_MAP: dict[str, tuple[str, ...]] = {
    "wage_complaint": (
        "작성해", "작성 해", "작성해주", "작성 부탁",
        "문서 만들", "문서만들", "진정서 작성", "진정서작성",
        "진정서 만들", "진정서만들", "만들어줘", "만들어 주",
        "임금체불 진정", "임금 진정",
    ),
    "payment_demand": (
        "내용증명", "내용 증명",
    ),
    "unfair_dismissal": (
        "부당해고 구제신청", "부당해고구제신청",
        "구제신청서", "부당해고 신청",
    ),
}

_CONFIRM = ("맞아요", "맞아", "네", "예", "확인", "좋아요", "응", "ok", "오케이")
_EDIT    = ("고칠래", "고치", "수정", "바꿀래", "바꿔", "틀렸", "다시")
_SKIP    = ("모르겠", "잘 몰라", "몰라", "없어요", "없음", "건너뛰", "스킵", "skip", "패스")

_CHOOSING = "__choosing__"  # confirming 단계에서 '어떤 항목 고칠지' 선택 대기 표시


# ── 헬퍼 ─────────────────────────────────────────────────────────────────────

def _contains(message: str, keywords: tuple[str, ...]) -> bool:
    return any(k in message for k in keywords)


def _get_labels(session: dict) -> dict[str, str]:
    doc_type = session.get("doc_type", "wage_complaint")
    fields = DOC_TYPES.get(doc_type, DOC_TYPES["wage_complaint"])["fields"]
    return {name: label for name, label, _ in fields}


def _required_fields(doc_type: str) -> list[str]:
    return [name for name, _label, req in DOC_TYPES[doc_type]["fields"] if req]


def _ordered_collected(session: dict) -> list[str]:
    """수집된 필드를 필수 필드 정의 순서대로 나열한다 (요약·수정 메뉴용)."""
    doc_type = session.get("doc_type", "wage_complaint")
    collected = session["collected"]
    return [f for f in _required_fields(doc_type) if f in collected]


def _current_field(session: dict) -> str | None:
    pending = session["pending_fields"]
    return pending[0] if pending else None


def _get_choices(session: dict) -> list[str]:
    """현재 pending 필드가 선택지형이면 보기 목록을 반환한다."""
    field = _current_field(session)
    if field is None:
        return []
    doc_type = session.get("doc_type", "wage_complaint")
    choice_fields = CHOICE_FIELDS_MAP.get(doc_type, {})
    if field in choice_fields:
        return choice_fields[field]["options"]
    return []


def _result(
    session: dict,
    reply: str,
    *,
    done: bool = False,
    field_values: dict | None = None,
) -> dict:
    out: dict = {"reply": reply, "mode": session["mode"], "done": done}
    if field_values is not None:
        out["field_values"] = field_values
    choices = _get_choices(session)
    if choices:
        out["choices"] = choices
    return out


def _normalize_choice(field: str, message: str, doc_type: str = "wage_complaint") -> str | None:
    """선택지 필드 입력을 표준값으로 정규화한다. 매칭 안 되면 None."""
    choice_fields = CHOICE_FIELDS_MAP.get(doc_type, {})
    info = choice_fields.get(field)
    if not info:
        return None
    msg = message.lower()
    for standard, synonyms in info["synonyms"].items():
        if msg == standard:
            return standard
        for syn in synonyms:
            if syn in msg:
                return standard
    return None


def get_doc_type_from_trigger(message: str) -> str | None:
    """사용자 메시지에서 문서 유형 트리거를 감지하고 doc_type 을 반환한다."""
    msg = (message or "").strip()
    for doc_type, keywords in _TRIGGER_MAP.items():
        if _contains(msg, keywords):
            return doc_type
    return None


def is_doc_trigger(message: str) -> bool:
    """사용자 메시지가 문서 작성 트리거인지 판단한다 (라우트에서 chat 모드일 때 사용)."""
    return get_doc_type_from_trigger(message) is not None


# ── 화면 텍스트 ──────────────────────────────────────────────────────────────

def _question_text(session: dict) -> str:
    """현재 필드 질문. 일반 수집에선 진행도 prefix, 수정 모드에선 질문만."""
    field = _current_field(session)
    if field is None:
        return ""
    doc_type = session.get("doc_type", "wage_complaint")
    questions = QUESTIONS_MAP.get(doc_type, {})
    labels = _get_labels(session)
    question = questions.get(field, f"{labels.get(field, field)}을(를) 알려주세요.")
    if session.get("edit_target"):
        return question
    asked = session["total_fields"] - len(session["pending_fields"]) + 1
    return f"({asked}/{session['total_fields']}) {question}"


def _summary_text(session: dict) -> str:
    labels = _get_labels(session)
    lines = ["이렇게 정리했어요 ✓\n"]
    for i, field in enumerate(_ordered_collected(session), start=1):
        value = session["collected"].get(field, "")
        lines.append(f"{i}. {labels.get(field, field)}: {value if value else '(빈칸)'}")
    lines.append("\n맞으면 문서를 만들게요 — [맞아요] 라고 해주세요. 고칠 게 있으면 [고칠래요] 라고 해주세요.")
    return "\n".join(lines)


def _edit_menu(session: dict) -> str:
    labels = _get_labels(session)
    return "\n".join(f"{i}. {labels.get(f, f)}" for i, f in enumerate(_ordered_collected(session), start=1))


# ── 공통 필드 공유 ───────────────────────────────────────────────────────────

def _canonical_to_doc_field(canonical: str, doc_type: str) -> str:
    """canonical 이름 → 해당 문서의 실제 필드명 (worker_contact 등 별칭 해소)."""
    return COMMON_FIELD_ALIAS.get(doc_type, {}).get(canonical, canonical)


def _prefill_from_shared(session: dict) -> dict:
    """shared_fields 값을 collected 에 자동 채우고, 필수 필드는 pending_fields 에서 제거한다.

    반환: {실제필드명: 값} — pending 에서 제거된(필수) 필드만. 확인 UI 표시에 사용.
    옵셔널 공통 필드(company_phone 등)는 collected 에만 조용히 채우고 반환값엔 포함 안 함.
    """
    doc_type = session.get("doc_type", "wage_complaint")
    shared = session.get("shared_fields", {})
    all_doc_fields = {name for name, _, _ in DOC_TYPES[doc_type]["fields"]}
    prefilled: dict[str, str] = {}

    for canonical in COMMON_FIELDS:
        actual = _canonical_to_doc_field(canonical, doc_type)
        if actual not in all_doc_fields:
            continue
        value = shared.get(canonical, "")
        if not value:
            continue
        session["collected"][actual] = value
        if actual in session["pending_fields"]:
            session["pending_fields"].remove(actual)
            prefilled[actual] = value
    return prefilled


def _save_to_shared(session: dict) -> None:
    """collected 의 공통 필드 값을 shared_fields 에 갱신한다.

    collected 에 없는 canonical 은 건드리지 않는다.
    예: 내용증명(hire_date 없음)을 거쳐도 앞서 저장된 hire_date 가 보존된다.
    """
    doc_type = session.get("doc_type", "wage_complaint")
    collected = session.get("collected", {})
    shared = session.setdefault("shared_fields", {})

    for canonical in COMMON_FIELDS:
        actual = _canonical_to_doc_field(canonical, doc_type)
        if actual in collected:
            value = collected[actual]
            if value:  # 빈 값으로 기존 공유값을 덮어쓰지 않는다
                shared[canonical] = value


# ── 상태 전환 ────────────────────────────────────────────────────────────────

def _start_onboarding(session: dict, doc_type: str = "wage_complaint") -> dict:
    if doc_type not in DOC_TYPES:
        doc_type = "wage_complaint"
    doc_info = DOC_TYPES[doc_type]
    required = _required_fields(doc_type)

    session["doc_type"]          = doc_type
    session["collected"]         = {}
    session["pending_fields"]    = required.copy()
    session["total_fields"]      = len(required)
    session["edit_target"]       = None
    session["choice_retry"]      = None
    session["validation_retry"]  = {}
    session["mode"]              = "collecting"
    # 이전 shared_confirm 임시 키 초기화
    session.pop("_shared_prefilled", None)
    session.pop("_remaining_fields_after_shared", None)
    session.pop("_edit_return_mode", None)

    # ── 공통 필드 자동 채움 (두 번째 이후 문서) ──────────────────────────────
    shared = session.get("shared_fields", {})
    if shared:
        prefilled = _prefill_from_shared(session)
        if prefilled:
            # pending_fields 에는 doc-specific 필드만 남은 상태
            session["_shared_prefilled"]             = [f for f in required if f in prefilled]
            session["_remaining_fields_after_shared"] = session["pending_fields"].copy()
            session["total_fields"]                   = len(session["pending_fields"])
            session["pending_fields"]                 = []   # 확인 전까지 비워 둠
            session["mode"]                           = "shared_confirm"

            labels = _get_labels(session)
            lines = [f"{doc_info['display_name']} 작성을 도와드릴게요.\n앞서 알려주신 정보를 그대로 쓸게요:\n"]
            for f in session["_shared_prefilled"]:
                value = session["collected"].get(f, "")
                lines.append(f"· {labels.get(f, f)}: {value if value else '(빈칸)'}")
            lines.append("\n맞으면 [네, 맞아요], 고칠 게 있으면 [수정할게요]")
            result = _result(session, "\n".join(lines))
            result["choices"] = ["네, 맞아요", "수정할게요"]
            return result

    reply = (
        f"{doc_info['display_name']} 작성을 도와드릴게요. "
        f"약 {len(required)}가지만 여쭤볼게요 (1분이면 돼요).\n"
        "입력하신 정보는 문서를 만들 때만 쓰고 끝나면 바로 사라져요. "
        "따로 저장하지 않아요.\n\n" + _question_text(session)
    )
    return _result(session, reply)


def _to_confirming(session: dict, prefix: str = "") -> dict:
    session["mode"]         = "confirming"
    session["edit_target"]  = None
    session["choice_retry"] = None
    return _result(session, prefix + _summary_text(session))


def _handle_collecting(session: dict, message: str) -> dict:
    field = _current_field(session)
    if field is None:
        return _to_confirming(session)

    doc_type = session.get("doc_type", "wage_complaint")
    choice_fields = CHOICE_FIELDS_MAP.get(doc_type, {})

    # 선택지 필드: 표준값으로 정규화 시도
    if field in choice_fields:
        normalized = _normalize_choice(field, message, doc_type)
        if normalized:
            message = normalized
            session["choice_retry"] = None
        elif session.get("choice_retry") == field:
            # 두 번째 미매칭 → raw 그대로 저장하고 계속 진행
            session["choice_retry"] = None
        else:
            # 첫 번째 미매칭 → 재질문
            session["choice_retry"] = field
            return _result(session, choice_fields[field]["retry_msg"])

    # 스킵어는 빈칸으로 저장
    is_skip = _contains(message, _SKIP)
    value = "" if is_skip else message

    # ── 날짜·금액 검증 (스킵 제외) ──────────────────────────────────────────
    if value and not is_skip:
        retry = session.setdefault("validation_retry", {})
        retry_count = retry.get(field, 0)

        if field in _DATE_FIELDS:
            valid, err_msg = _validate_date(value)
            if not valid:
                if retry_count < _MAX_DATE_RETRY:
                    retry[field] = retry_count + 1
                    return _result(session, err_msg)
                # 재시도 초과: 원값 그대로 저장하고 계속 (사용자에게 이미 안내됨)
                retry.pop(field, None)

        elif field in _AMOUNT_FIELDS:
            valid, err_msg = _validate_amount(value)
            if not valid:
                if retry_count < _MAX_AMOUNT_RETRY:
                    retry[field] = retry_count + 1
                    return _result(session, err_msg)
                retry.pop(field, None)

        else:
            retry.pop(field, None)

    session["collected"][field] = value
    session["pending_fields"].pop(0)
    session["choice_retry"] = None

    # 수정 모드: 한 필드만 채우고 원래 단계로 복귀
    if session.get("edit_target"):
        session["edit_target"] = None
        return_mode = session.pop("_edit_return_mode", None)
        if return_mode == "shared_confirm":
            return _to_shared_confirm(session, prefix="수정했어요. ")
        return _to_confirming(session, prefix="수정했어요. ")

    if not session["pending_fields"]:
        return _to_confirming(session)
    return _result(session, _question_text(session))


def _resolve_edit_choice(session: dict, message: str) -> str | None:
    """수정 메뉴 입력(번호 또는 항목명)을 필드명으로 해석한다."""
    fields = _ordered_collected(session)
    labels = _get_labels(session)
    text = message.strip()
    # "1", "1번", "2번째" 등 숫자 접두 패턴을 모두 허용
    m = re.match(r'^(\d+)', text)
    if m:
        idx = int(m.group(1)) - 1
        return fields[idx] if 0 <= idx < len(fields) else None
    for field in fields:
        label = labels.get(field, field)
        if text and (text in label or label in text):
            return field
    return None


def _handle_confirming(session: dict, message: str) -> dict:
    # 1) '어떤 항목 고칠지' 선택 대기 중
    if session.get("edit_target") == _CHOOSING:
        field = _resolve_edit_choice(session, message)
        if field is None:
            return _result(session, "어떤 항목을 고칠지 번호나 항목 이름으로 알려주세요.\n" + _edit_menu(session))
        labels = _get_labels(session)
        session["edit_target"] = field
        session["pending_fields"] = [field]
        session["mode"] = "collecting"
        return _result(session, f"'{labels.get(field, field)}' 항목을 다시 입력할게요.\n" + _question_text(session))

    # 2) 수정 요청
    if _contains(message, _EDIT):
        session["edit_target"] = _CHOOSING
        session["mode"] = "editing"
        return _result(session, "어떤 항목을 고칠까요? 번호나 항목 이름으로 알려주세요.\n" + _edit_menu(session))

    # 3) 확인 → 생성 단계로 (라우트가 generator 호출)
    if _contains(message, _CONFIRM):
        _save_to_shared(session)   # 다음 문서를 위해 공통 필드 공유 저장소에 갱신
        doc_type = session.get("doc_type", "wage_complaint")
        doc_info = DOC_TYPES.get(doc_type, DOC_TYPES["wage_complaint"])
        return _result(
            session,
            f"정보 확인 완료! {doc_info['display_name']} 만들고 있어요. 잠시만요…",
            done=True,
            field_values=dict(session["collected"]),
        )

    # 4) 인식 못 함
    return _result(session, "문서를 만들까요? [맞아요] 또는 [고칠래요] 로 답해주세요.")


# ── shared_confirm 단계 ──────────────────────────────────────────────────────

def _to_shared_confirm(session: dict, prefix: str = "") -> dict:
    """수정 완료 후 shared_confirm 화면으로 복귀한다."""
    session["mode"]         = "shared_confirm"
    session["edit_target"]  = None
    session["choice_retry"] = None
    prefilled_fields = session.get("_shared_prefilled", [])
    labels = _get_labels(session)
    lines = ["앞서 알려주신 정보를 그대로 쓸게요:\n"]
    for f in prefilled_fields:
        value = session["collected"].get(f, "")
        lines.append(f"· {labels.get(f, f)}: {value if value else '(빈칸)'}")
    lines.append("\n맞으면 [네, 맞아요], 고칠 게 있으면 [수정할게요]")
    result = _result(session, prefix + "\n".join(lines))
    result["choices"] = ["네, 맞아요", "수정할게요"]
    return result


def _handle_shared_confirm(session: dict, message: str) -> dict:
    prefilled_fields = session.get("_shared_prefilled", [])
    labels = _get_labels(session)

    # 1) 수정할 항목 선택 대기 중
    if session.get("edit_target") == _CHOOSING:
        text = message.strip()
        m = re.match(r'^(\d+)', text)
        chosen = None
        if m:
            idx = int(m.group(1)) - 1
            chosen = prefilled_fields[idx] if 0 <= idx < len(prefilled_fields) else None
        else:
            for f in prefilled_fields:
                label = labels.get(f, f)
                if text and (text in label or label in text):
                    chosen = f
                    break
        if chosen is None:
            edit_menu = "\n".join(
                f"{i+1}. {labels.get(f, f)}: {session['collected'].get(f, '')}"
                for i, f in enumerate(prefilled_fields)
            )
            return _result(session, "어떤 항목을 고칠지 번호나 항목 이름으로 알려주세요.\n" + edit_menu)
        session["edit_target"]       = chosen
        session["_edit_return_mode"] = "shared_confirm"
        session["pending_fields"]    = [chosen]
        session["mode"]              = "collecting"
        return _result(session, f"'{labels.get(chosen, chosen)}' 항목을 다시 입력할게요.\n" + _question_text(session))

    # 2) 수정 요청
    if _contains(message, _EDIT):
        session["edit_target"] = _CHOOSING
        edit_menu = "\n".join(
            f"{i+1}. {labels.get(f, f)}: {session['collected'].get(f, '')}"
            for i, f in enumerate(prefilled_fields)
        )
        return _result(session, "어떤 항목을 고칠까요? 번호나 항목 이름으로 알려주세요.\n" + edit_menu)

    # 3) 확인 → doc-specific 필드 수집으로 이어가기
    if _contains(message, _CONFIRM):
        remaining = list(session.get("_remaining_fields_after_shared", []))
        session["pending_fields"] = remaining
        session["total_fields"]   = len(remaining)
        session["mode"]           = "collecting"
        if not remaining:
            return _to_confirming(session)
        return _result(session, _question_text(session))

    # 4) 인식 못함
    result = _result(session, "앞서 알려주신 정보를 그대로 쓸까요? [네, 맞아요] 또는 [수정할게요]")
    result["choices"] = ["네, 맞아요", "수정할게요"]
    return result


# ── 진입점 ──────────────────────────────────────────────────────────────────

def handle_message(session: dict, user_message: str, doc_type: str = "wage_complaint") -> dict:
    """수집 흐름의 한 턴을 처리한다.

    Returns:
        {"reply": str, "mode": str, "done": bool, "choices"?: list[str], "field_values"?: dict}
        done=True 이면 field_values 로 문서를 생성하라는 신호 (라우트가 처리).
    """
    message = (user_message or "").strip()
    mode = session["mode"]

    # 선택지형 필드에서는 보기 매칭을 취소 검사보다 먼저 수행.
    # 보기 매칭 성공 시 취소 검사를 완전히 건너뛴다 ("그만둠" → 퇴직으로 처리).
    if mode == "collecting":
        field = _current_field(session)
        session_doc_type = session.get("doc_type", "wage_complaint")
        choice_fields = CHOICE_FIELDS_MAP.get(session_doc_type, {})
        if field and field in choice_fields and _normalize_choice(field, message, session_doc_type) is not None:
            return _handle_collecting(session, message)

    # 취소 검사 — 명확한 의도 표현만 허용
    if mode != "chat" and _contains(message, _CANCEL):
        session.update({
            "mode": "chat", "doc_type": None, "collected": {},
            "pending_fields": [], "total_fields": 0,
            "edit_target": None, "choice_retry": None, "validation_retry": {},
        })
        session.pop("_shared_prefilled", None)
        session.pop("_remaining_fields_after_shared", None)
        session.pop("_edit_return_mode", None)
        return _result(session, "문서 작성을 멈췄어요. 다른 궁금한 점이 있으면 언제든 물어보세요.")

    if mode == "chat":
        return _start_onboarding(session, doc_type)
    if mode == "collecting":
        return _handle_collecting(session, message)
    if mode in ("confirming", "editing"):
        return _handle_confirming(session, message)
    if mode == "shared_confirm":
        return _handle_shared_confirm(session, message)

    session["mode"] = "chat"
    return _result(session, "무엇을 도와드릴까요?")
