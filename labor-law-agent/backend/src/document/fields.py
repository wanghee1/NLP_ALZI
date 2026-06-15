"""문서 템플릿 필드 정의.

각 문서 유형의 필드 목록과 메타데이터를 한곳에 모은다.
- 변수명은 docxtpl 템플릿의 {{변수}} 와 정확히 일치해야 한다.
- 한글라벨/필수여부는 대화형 수집에서 "쉬운 말 질문" 생성에 재사용한다.

순수 데이터 정의이므로 어떤 전송/생성 계층에도 의존하지 않는다 (architecture).
"""

from __future__ import annotations

# (변수명, 한글라벨, 필수여부)
# ─ 변수명은 docxtpl 템플릿의 {{변수}} 와 반드시 동일해야 한다 ─
WAGE_COMPLAINT_FIELDS: list[tuple[str, str, bool]] = [
    ("worker_name",       "진정인 성명",      True),
    ("worker_address",    "진정인 주소",      True),
    ("worker_mobile",     "진정인 휴대전화",   True),   # 연락처 필수
    ("worker_phone",      "진정인 전화번호",   False),
    ("worker_email",      "진정인 이메일",     False),
    ("worker_rrn",        "주민등록번호",      False),  # MVP: 안 받음, 빈칸
    ("employer_name",     "사업주 성명",      True),
    ("employer_phone",    "사업주 연락처",    False),
    ("employer_address",  "사업주 주소",      False),
    ("company_name",      "사업장명",         True),
    ("company_address",   "사업장 주소",      True),
    ("company_phone",     "사업장 전화번호",   False),
    ("employee_count",    "근로자 수",        False),
    ("hire_date",         "입사일",           True),
    ("resign_date",       "퇴사일",           True),   # 템플릿에 있음 — 재직 시 건너뛰기 가능
    ("employment_status", "퇴직/재직 여부",   True),
    ("unpaid_total",      "체불임금 총액",    True),
    ("unpaid_severance",  "체불 퇴직금액",    False),
    ("unpaid_other",      "기타 체불금액",    False),
    ("job_description",   "업무 내용",        True),   # 진정서 핵심 항목
    ("payday",            "임금 지급일",      True),   # 진정서 핵심 항목
    ("contract_method",   "근로계약 방법",    False),
    ("detail_content",    "상세 내용",        True),
    ("submit_office",     "제출 노동청",      False),
    ("submit_date",       "작성일",           False),
    # business_type 제거: 템플릿에 없는 ghost field
]

UNFAIR_DISMISSAL_FIELDS: list[tuple[str, str, bool]] = [
    ("worker_name",       "신청인 성명",             True),
    ("worker_address",    "신청인 주소",             True),
    ("worker_phone",      "신청인 연락처",            True),   # 연락처 필수
    ("worker_mobile",     "신청인 휴대전화",          False),
    ("employer_name",     "피신청인(사업주) 성명",    True),
    ("company_name",      "사업장명",                True),
    ("company_address",   "사업장 주소",             True),
    ("company_phone",     "사업장 전화번호",          False),
    ("employee_count",    "근로자 수",               False),
    ("hire_date",         "입사일",                  True),
    ("dismissal_date",    "해고 통보일",             True),
    ("dismissal_method",  "해고 통보 방법",           True),   # 템플릿 변수 — 핵심
    ("dismissal_reason",  "해고 사유",               True),
    ("job_description",   "담당 업무",               True),   # 구제신청서 필수
    ("detail_content",    "신청 이유",               True),
    ("labor_commission",  "관할 노동위원회",          False),
    ("submit_date",       "작성일",                  False),
]

# payment_demand 변수명은 템플릿의 {{변수}} 와 정확히 일치:
# worker_name / worker_address / worker_phone / employer_name / company_name /
# company_address / company_phone / work_period / unpaid_total /
# deadline_days / worker_account / submit_date
PAYMENT_DEMAND_FIELDS: list[tuple[str, str, bool]] = [
    ("worker_name",    "발신인(근로자) 성명",    True),   # 구 sender_name
    ("worker_address", "발신인 주소",            True),   # 구 sender_address
    ("worker_phone",   "발신인 연락처",          True),   # 연락처 필수
    ("employer_name",  "수신인(사업주) 성명",    True),   # 구 receiver_name
    ("company_name",   "사업장명",               True),
    ("company_address","사업장(수신인) 주소",    True),   # 구 receiver_address
    ("company_phone",  "사업장 전화번호",        False),
    ("work_period",    "근무 기간",              True),
    ("unpaid_total",   "체불 금액",              True),
    ("worker_account", "계좌 정보",              True),
    ("deadline_days",  "지급 기한",              False),  # 구 demand_deadline
    ("submit_date",    "작성일",                 False),
    # detail_content 제거: 내용증명 템플릿에 없음
]

# 빠른 조회용 — 변수명 목록 (generator 기본값 채우기에 사용)
WAGE_COMPLAINT_FIELD_NAMES: list[str] = [name for name, _label, _required in WAGE_COMPLAINT_FIELDS]

DOC_TYPES: dict[str, dict] = {
    "wage_complaint": {
        "fields": WAGE_COMPLAINT_FIELDS,
        "template": "wage_complaint_template.docx",
        "display_name": "임금체불 진정서",
    },
    "unfair_dismissal": {
        "fields": UNFAIR_DISMISSAL_FIELDS,
        "template": "unfair_dismissal_template.docx",
        "display_name": "부당해고 구제신청서",
    },
    "payment_demand": {
        "fields": PAYMENT_DEMAND_FIELDS,
        "template": "payment_demand_template.docx",
        "display_name": "내용증명",
    },
}

# ── 문서 간 공통 필드 ────────────────────────────────────────────────────────
# canonical 이름 기준. phone 은 문서마다 변수명이 달라 worker_contact 로 통일.
COMMON_FIELDS: list[str] = [
    "worker_name",
    "worker_address",
    "worker_contact",    # wage_complaint → worker_mobile / 나머지 → worker_phone
    "employer_name",
    "company_name",
    "company_address",
    "company_phone",
    "hire_date",         # payment_demand 엔 없음 — _prefill_from_shared 에서 자동 스킵
]

# canonical → 각 문서의 실제 필드명 (canonical 과 다른 것만 명시)
COMMON_FIELD_ALIAS: dict[str, dict[str, str]] = {
    "wage_complaint": {
        "worker_contact": "worker_mobile",
    },
    "unfair_dismissal": {
        "worker_contact": "worker_phone",
    },
    "payment_demand": {
        "worker_contact": "worker_phone",
    },
}
