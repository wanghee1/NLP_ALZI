"""근로계약서 PDF 텍스트 추출 및 이미지 렌더링.

PyMuPDF(fitz)를 사용하며 디스크에 파일을 쓰지 않는다 (security).
스캔 이미지 PDF처럼 추출 텍스트가 사실상 없는 경우 ScannedPdfError 를 발생시킨다.
"""

from __future__ import annotations

import fitz  # PyMuPDF


class ScannedPdfError(ValueError):
    """텍스트 레이어가 없는 이미지 전용 PDF."""


_MIN_TEXT_LENGTH = 100   # 이 글자 수 미만이면 스캔 PDF로 간주
_MAX_VISION_PAGES = 5    # 비전 OCR 시 처리할 최대 페이지 수 (비용/시간 가드)
_VISION_DPI = 150        # 텍스트 인식 가능 해상도. 200dpi 대비 토큰 ~30% 절감


def extract_text(file_bytes: bytes) -> str:
    """PDF bytes 에서 텍스트를 추출하여 반환한다.

    Args:
        file_bytes: PDF 원본 바이트 (메모리에서 직접 읽음, 디스크 저장 없음)

    Returns:
        추출된 전체 텍스트 (페이지 사이는 줄바꿈으로 구분)

    Raises:
        ScannedPdfError: 추출된 텍스트가 _MIN_TEXT_LENGTH 미만인 경우
        ValueError: PDF 파일 자체가 손상되거나 파싱 불가인 경우
    """
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
    except Exception as exc:
        raise ValueError("PDF 파일을 열 수 없습니다.") from exc

    pages: list[str] = []
    for page in doc:
        pages.append(page.get_text())
    doc.close()

    text = "\n".join(pages).strip()

    if len(text) < _MIN_TEXT_LENGTH:
        raise ScannedPdfError(
            "텍스트를 읽을 수 없는 PDF입니다. "
            "스캔 이미지 PDF는 현재 지원하지 않습니다."
        )

    return text


def render_pages_to_images(
    file_bytes: bytes,
    max_pages: int = _MAX_VISION_PAGES,
) -> list[bytes]:
    """PDF 의 각 페이지를 PNG 바이트로 렌더링한다.

    메모리에서만 처리하며 디스크에 저장하지 않는다 (security).
    앞 max_pages 페이지만 렌더링하여 토큰·시간 비용을 제한한다.

    Args:
        file_bytes: PDF 원본 바이트
        max_pages: 최대 처리 페이지 수 (기본 5)

    Returns:
        페이지별 PNG 바이트 리스트

    Raises:
        ValueError: PDF 파일 자체가 손상되거나 파싱 불가인 경우
    """
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
    except Exception as exc:
        raise ValueError("PDF 파일을 열 수 없습니다.") from exc

    images: list[bytes] = []
    page_count = min(len(doc), max_pages)
    try:
        for i in range(page_count):
            pix = doc[i].get_pixmap(dpi=_VISION_DPI)
            images.append(pix.tobytes("png"))
            del pix  # 픽셀맵 즉시 해제
    finally:
        doc.close()

    return images
