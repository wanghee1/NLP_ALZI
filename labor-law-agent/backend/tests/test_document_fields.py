"""
문서 생성 빈칸 검증 테스트.

각 서식에 샘플값을 채워 DocxTemplate 렌더 컨텍스트를 구성하고,
핵심 변수가 공백인지 확인한다. 모든 템플릿 변수에 대한 누락도 함께 리포트.

실행:
    cd backend
    python -m pytest tests/test_document_fields.py -v
  또는
    python tests/test_document_fields.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# src/ 를 import 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from docxtpl import DocxTemplate

from config.settings import TEMPLATE_DIR
from src.document.fields import DOC_TYPES
from src.document.generator import _build_context_for

# ── 샘플 필드값 (핵심 칸이 모두 채워졌는지 확인하는 기준값) ───────────────────

SAMPLE_FIELDS: dict[str, dict[str, str]] = {
    "wage_complaint": {
        "worker_name":       "홍길동",
        "worker_address":    "서울시 강남구 테헤란로 1길 10",
        "worker_mobile":     "010-1234-5678",
        "employer_name":     "김사장",
        "company_name":      "테스트 식당",
        "company_address":   "서울시 강남구 역삼동 100",
        "hire_date":         "2024-03-01",
        "resign_date":       "2025-01-15",
        "employment_status": "퇴직",
        "unpaid_total":      "1,200,000원",
        "job_description":   "서빙 및 홀 업무",
        "payday":            "매월 25일",
        "detail_content":    (
            "2024년 11월, 12월 월급 각 60만 원씩 합계 120만 원을 받지 못했습니다. "
            "사업주에게 여러 차례 요청했으나 응답이 없었습니다."
        ),
    },
    "unfair_dismissal": {
        "worker_name":      "홍길동",
        "worker_address":   "서울시 마포구 합정동 200",
        "worker_phone":     "010-9876-5432",
        "employer_name":    "이사장",
        "company_name":     "테스트 카페",
        "company_address":  "서울시 마포구 서교동 50",
        "hire_date":        "2023-06-01",
        "dismissal_date":   "2025-02-28",
        "dismissal_method": "구두",
        "dismissal_reason": "경영상 어려움",
        "job_description":  "바리스타 및 홀 서빙",
        "detail_content":   (
            "갑작스럽게 '내일부터 나오지 말라'는 말만 들었습니다. "
            "서면 통보 없이 해고됐으며, 30일 전 예고도 없었습니다."
        ),
    },
    "payment_demand": {
        "worker_name":    "홍길동",
        "worker_address": "서울시 용산구 한남동 30",
        "worker_phone":   "010-1111-2222",
        "employer_name":  "박사장",
        "company_name":   "테스트 편의점",
        "company_address":"서울시 용산구 이태원동 10",
        "work_period":    "2024-09-01 ~ 2025-01-31",
        "unpaid_total":   "800,000원",
        "worker_account": "국민은행 / 12345-67-890123",
    },
}

# ── 서식별 핵심 변수 목록 (빈칸이면 테스트 실패) ────────────────────────────

CRITICAL_VARS: dict[str, list[str]] = {
    "wage_complaint": [
        "worker_name", "worker_address", "worker_mobile",
        "employer_name", "company_name", "company_address",
        "hire_date", "unpaid_total", "employment_status",
        "job_description", "payday", "detail_content",
    ],
    "unfair_dismissal": [
        "worker_name", "worker_address", "worker_phone",
        "employer_name", "company_name", "company_address",
        "hire_date", "dismissal_date",
        "dismissal_method", "dismissal_reason",
        "job_description", "detail_content",
    ],
    "payment_demand": [
        "worker_name", "worker_address", "worker_phone",
        "employer_name", "company_name", "company_address",
        "work_period", "unpaid_total", "worker_account",
    ],
}

# ── 템플릿에 실제로 있는 변수 (에이전트 추출 결과 기반) ───────────────────────

KNOWN_TEMPLATE_VARS: dict[str, list[str]] = {
    "wage_complaint": [
        "worker_name", "worker_rrn", "worker_address", "worker_phone",
        "worker_mobile", "worker_email",
        "employer_name", "employer_phone", "employer_address",
        "company_name", "company_address", "company_phone", "employee_count",
        "hire_date", "resign_date",
        "unpaid_total", "unpaid_severance", "unpaid_other",
        "job_description", "payday", "detail_content",
        "submit_office", "submit_date",
    ],
    "unfair_dismissal": [
        "worker_name", "worker_phone", "worker_address",
        "company_name", "employer_name", "company_address", "company_phone", "employee_count",
        "hire_date", "dismissal_date",
        "job_description", "dismissal_method", "dismissal_reason",
        "detail_content", "labor_commission", "submit_date",
    ],
    "payment_demand": [
        "worker_name", "worker_phone", "worker_address",
        "employer_name", "company_name", "company_phone", "company_address",
        "work_period", "unpaid_total", "deadline_days",
        "worker_account", "submit_date",
    ],
}


def _build_and_check(doc_type: str) -> tuple[list[str], list[str]]:
    """
    샘플값으로 context 를 빌드하고 (blank_critical, blank_all) 를 반환한다.
    blank_critical: 핵심 변수 중 빈칸
    blank_all:      알려진 모든 템플릿 변수 중 빈칸
    """
    doc_info = DOC_TYPES[doc_type]
    template_path = Path(TEMPLATE_DIR) / doc_info["template"]
    field_names = [name for name, _, _ in doc_info["fields"]]

    doc = DocxTemplate(str(template_path))
    context = _build_context_for(doc, SAMPLE_FIELDS[doc_type], field_names)

    known = KNOWN_TEMPLATE_VARS[doc_type]
    blank_all      = [v for v in known if not context.get(v, "").strip()]
    blank_critical = [v for v in CRITICAL_VARS[doc_type] if not context.get(v, "").strip()]
    return blank_critical, blank_all


# ── pytest 테스트 ────────────────────────────────────────────────────────────

@pytest.mark.parametrize("doc_type", ["wage_complaint", "unfair_dismissal", "payment_demand"])
def test_no_critical_blanks(doc_type: str) -> None:
    """핵심 변수가 하나도 빈칸이 아니어야 한다."""
    blank_critical, blank_all = _build_and_check(doc_type)
    display = DOC_TYPES[doc_type]["display_name"]
    assert not blank_critical, (
        f"[{display}] 핵심 변수 빈칸: {blank_critical}\n"
        f"  전체 빈칸: {blank_all}"
    )


@pytest.mark.parametrize("doc_type", ["wage_complaint", "unfair_dismissal", "payment_demand"])
def test_fields_match_template_vars(doc_type: str) -> None:
    """fields.py 의 필수 변수명이 알려진 템플릿 변수 목록에 모두 포함되어야 한다."""
    required = [name for name, _, req in DOC_TYPES[doc_type]["fields"] if req]
    known    = set(KNOWN_TEMPLATE_VARS[doc_type])
    # submit_date 는 generator 가 자동으로 채우므로 제외
    missing = [f for f in required if f not in known and f != "employment_status"]
    display = DOC_TYPES[doc_type]["display_name"]
    assert not missing, (
        f"[{display}] fields.py 의 필수 필드가 템플릿에 없습니다: {missing}"
    )


# ── 독립 실행 리포트 ─────────────────────────────────────────────────────────

def _report() -> bool:
    all_ok = True
    for doc_type in ("wage_complaint", "unfair_dismissal", "payment_demand"):
        display = DOC_TYPES[doc_type]["display_name"]
        blank_critical, blank_all = _build_and_check(doc_type)

        print(f"\n{'='*55}")
        print(f"  {display} ({doc_type})")
        print(f"{'='*55}")
        if blank_all:
            print(f"  빈칸 전체 ({len(blank_all)}개): {blank_all}")
        else:
            print("  빈칸 전체: 없음")

        if blank_critical:
            print(f"  ❌ FAIL — 핵심 빈칸: {blank_critical}")
            all_ok = False
        else:
            print("  ✅ OK   — 모든 핵심 변수 채워짐")

    print(f"\n{'='*55}")
    print("최종:", "✅ 전체 통과" if all_ok else "❌ 일부 실패")
    return all_ok


if __name__ == "__main__":
    success = _report()
    sys.exit(0 if success else 1)
