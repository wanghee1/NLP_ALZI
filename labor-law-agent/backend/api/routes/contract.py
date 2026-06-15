"""계약서 분석 엔드포인트 — Phase 5-A.

POST /contract/analyze: PDF 업로드 → 텍스트 추출(또는 비전 OCR) → Claude 위험 조항 탐지.

보안 규칙 (security.md):
- 크기 + 매직넘버로 파일 검증. content_type 은 보조 참고만 (octet-stream 허용).
- 업로드 bytes·계약서 텍스트는 메모리에서만 처리, 디스크 저장 없음.
- 계약서 내용을 로그에 출력하지 않음.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, File, HTTPException, UploadFile

from api.schemas import ContractAnalysisResponse, ViolationItem
from config.settings import MAX_UPLOAD_MB
from src.contract.analyzer import analyze_contract_from_pdf
from src.contract.pdf_parser import ScannedPdfError

router = APIRouter()
logger = logging.getLogger(__name__)

_MAX_BYTES = MAX_UPLOAD_MB * 1024 * 1024
_PDF_MAGIC = b"%PDF"


def _validate_pdf(file_bytes: bytes, content_type: str | None) -> None:
    """크기·매직넘버 검증. content_type 은 참고용으로만 로깅한다."""
    if len(file_bytes) > _MAX_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"파일 크기가 {MAX_UPLOAD_MB}MB를 초과합니다.",
        )
    # 처음 1024바이트 안에 %PDF 시그니처가 있는지 확인
    # (BOM·공백이 앞에 붙은 PDF도 허용)
    if _PDF_MAGIC not in file_bytes[:1024]:
        logger.info("업로드 거부: PDF 매직넘버 없음 (content_type=%s)", content_type)
        raise HTTPException(
            status_code=400,
            detail="PDF 파일만 업로드할 수 있습니다.",
        )


@router.post("/contract/analyze", response_model=ContractAnalysisResponse)
async def analyze_contract_route(
    file: UploadFile = File(...),
) -> ContractAnalysisResponse:
    """업로드된 PDF 계약서에서 위법·불리·누락 조항을 탐지한다.

    - 크기 초과(10MB) 또는 PDF 아닌 파일이면 400 반환.
    - 텍스트 PDF: PyMuPDF 직접 추출 후 분석 (빠른 경로).
    - 스캔/이미지 PDF: Claude 비전 OCR 로 텍스트 추출 후 동일 분석 흐름.
    - 비전으로도 읽을 수 없으면 analyzed=False + 안내 메시지 반환.
    - 계약서 내용은 메모리에서만 처리하며 디스크에 저장하지 않는다.
    """
    file_bytes = await file.read()

    _validate_pdf(file_bytes, file.content_type)

    try:
        raw_violations, used_vision = analyze_contract_from_pdf(file_bytes)
    except ScannedPdfError as exc:
        return ContractAnalysisResponse(
            violations=[],
            analyzed=False,
            message=str(exc),
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="PDF 파일을 읽을 수 없습니다.")

    violations = [ViolationItem(**item) for item in raw_violations]

    return ContractAnalysisResponse(
        violations=violations,
        analyzed=True,
        used_vision=used_vision,
        message="" if violations else "위법·불리·누락 조항이 발견되지 않았습니다.",
    )
