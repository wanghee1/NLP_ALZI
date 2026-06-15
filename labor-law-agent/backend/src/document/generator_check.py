"""문서 생성 엔진 검증 스크립트 (일회성).

하드코딩한 임금체불 예시로 docx 생성 → pdf 변환이 실제로 되는지 확인한다.
사람이 결과물을 직접 열어볼 수 있도록, 임시 산출물을 보기용 출력 디렉터리에 '복사'하고
(삭제는 보류) 그 경로를 출력한다. 임시 디렉터리 원본은 정리한다.

실행:
    cd backend
    python -m src.document.generator_check

사전 준비: requirements 설치(docxtpl) + 시스템에 LibreOffice(soffice) 설치.
"""

from __future__ import annotations

import os
import shutil
import sys

from src.document.generator import cleanup_files, generate_complaint_docx
from src.document.pdf_converter import convert_to_pdf

# 결과물을 직접 열어보기 위한 출력 디렉터리 (data/ 하위라 .gitignore 에 포함됨).
_OUTPUT_DIR = "./data/_generated_check"

# 하드코딩 샘플 — 편의점 알바 임금체불 예시 (개인정보는 가상값).
SAMPLE_FIELD_VALUES = {
    "worker_name": "홍길동",
    "worker_address": "서울특별시 강남구 테헤란로 1길 10, 101호",
    "worker_mobile": "010-1234-5678",
    "worker_email": "hong@example.com",
    "employer_name": "김사장",
    "employer_phone": "010-9876-5432",
    "company_name": "행복편의점 역삼점",
    "company_address": "서울특별시 강남구 역삼로 5",
    "company_phone": "02-555-1234",
    "employee_count": "3",
    "hire_date": "2025-09-01",
    "resign_date": "2026-02-28",
    "unpaid_total": "300,000원",
    "employment_status": "퇴직",
    "job_description": "편의점 계산 및 진열 업무 (주 5일, 1일 5시간)",
    "payday": "매월 10일",
    "contract_method": "서면 근로계약서 작성",
    "detail_content": (
        "2026년 1월분 임금 30만원을 퇴사일까지 지급받지 못했습니다. "
        "여러 차례 지급을 요청했으나 사업주가 응하지 않고 있습니다."
    ),
    "submit_office": "서울지방고용노동청 강남지청",
    # submit_date 는 일부러 비워 자동 채움 동작 확인
}


def main() -> int:
    print("[문서 생성 검증] 샘플 필드로 docx → pdf 변환을 시도합니다.")

    docx_path = ""
    pdf_path = ""
    try:
        docx_path = generate_complaint_docx(SAMPLE_FIELD_VALUES)
        print(f"  docx 생성 OK: {docx_path}")
        pdf_path = convert_to_pdf(docx_path)
        print(f"  pdf 변환 OK : {pdf_path}")
    except (FileNotFoundError, RuntimeError) as exc:
        print(f"  [실패] {exc}")
        # 부분 생성물도 임시 디렉터리째 정리
        cleanup_files(docx_path, pdf_path)
        return 1

    # 결과물을 보기용 디렉터리로 복사 (원본 임시본은 이후 정리)
    os.makedirs(_OUTPUT_DIR, exist_ok=True)
    saved = []
    for src in (docx_path, pdf_path):
        dst = os.path.join(_OUTPUT_DIR, os.path.basename(src))
        shutil.copyfile(src, dst)
        saved.append(os.path.abspath(dst))

    # 임시 디렉터리 원본은 삭제 (보기용 복사본만 남긴다)
    cleanup_files(docx_path, pdf_path)

    print("\n[완료] 아래 파일을 직접 열어 확인하세요 (삭제 보류된 복사본):")
    for path in saved:
        print(f"  - {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
