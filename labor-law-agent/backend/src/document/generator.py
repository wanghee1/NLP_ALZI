"""노동법 서류 DOCX 생성기.

docxtpl 로 템플릿에 필드값을 주입해 docx 를 만든다.
순수 로직 계층(src/document)이라 전송 계층(api/)에 의존하지 않는다 (architecture).

보안(security 규칙):
  - 생성물(docx/pdf)은 tempfile 임시 디렉터리에만 만들고 디스크에 영구 보관하지 않는다.
  - 필드값(이름·주소 등 개인정보)을 로그에 출력하지 않는다.
  - 응답/다운로드 후 즉시 삭제할 수 있도록 cleanup 경로를 제공한다
    (cleanup_files 함수 + generated_document 컨텍스트매니저).
"""

from __future__ import annotations

import os
import shutil
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date
from pathlib import Path

from docxtpl import DocxTemplate

from config.settings import TEMPLATE_DIR
from src.document.fields import DOC_TYPES, WAGE_COMPLAINT_FIELD_NAMES
from src.document.pdf_converter import convert_to_pdf

# 하위 호환을 위한 상수 (wage_complaint 전용)
TEMPLATE_FILENAME = "wage_complaint_template.docx"
_OUTPUT_DOCX_NAME = "wage_complaint.docx"


def _build_context_for(
    doc: DocxTemplate, field_values: dict, field_names: list[str]
) -> dict[str, str]:
    """모든 템플릿 변수에 기본값을 보장한 렌더 컨텍스트를 만든다.

    누락 변수로 docxtpl(Jinja2)이 에러내지 않도록 3중 안전망을 둔다:
      1) field_names 의 변수명을 모두 "" 로 초기화
      2) 전달받은 field_values 로 덮어쓰기 (None 은 "" 로 정규화)
      3) 템플릿이 실제로 쓰는 미선언 변수까지 훑어 누락분을 "" 로 보강
    """
    context: dict[str, str] = {name: "" for name in field_names}
    for key, value in field_values.items():
        context[key] = "" if value is None else str(value)

    for var in doc.get_undeclared_template_variables():
        context.setdefault(var, "")

    # 작성일이 비어 있으면 오늘 날짜로 자동 채움 (공문서 형식)
    if not context.get("submit_date"):
        context["submit_date"] = date.today().strftime("%Y년 %m월 %d일")

    return context


def _build_context(doc: DocxTemplate, field_values: dict) -> dict[str, str]:
    """(하위 호환) wage_complaint 전용 컨텍스트 빌더."""
    return _build_context_for(doc, field_values, WAGE_COMPLAINT_FIELD_NAMES)


def generate_document(doc_type: str, field_values: dict) -> str:
    """문서 유형에 맞는 템플릿으로 DOCX 를 생성하고 경로를 반환한다.

    Args:
        doc_type: DOC_TYPES 키 (wage_complaint / unfair_dismissal / payment_demand)
        field_values: 템플릿 변수명 → 값 딕셔너리 (없는 변수는 빈칸 처리)

    Returns:
        생성된 docx 의 절대 경로 (임시 디렉터리 안).

    Raises:
        ValueError: 알 수 없는 doc_type.
        FileNotFoundError: 템플릿 파일이 없을 때.
    """
    if doc_type not in DOC_TYPES:
        raise ValueError(f"알 수 없는 문서 유형: {doc_type}")

    doc_info = DOC_TYPES[doc_type]
    template_path = Path(TEMPLATE_DIR) / doc_info["template"]
    if not template_path.exists():
        raise FileNotFoundError(f"템플릿을 찾을 수 없습니다: {template_path}")

    field_names = [name for name, _, _ in doc_info["fields"]]

    doc = DocxTemplate(str(template_path))
    context = _build_context_for(doc, field_values, field_names)
    doc.render(context)

    tmp_dir = tempfile.mkdtemp(prefix="labor_doc_")
    out_path = os.path.join(tmp_dir, f"{doc_type}.docx")
    doc.save(out_path)
    return out_path


def generate_complaint_docx(field_values: dict) -> str:
    """(하위 호환) 임금체불 진정서 DOCX 를 생성한다."""
    return generate_document("wage_complaint", field_values)


def cleanup_files(*paths: str) -> None:
    """생성 산출물(docx/pdf)과 그 임시 디렉터리를 삭제한다 (security: 즉시 삭제).

    예외가 나도 가능한 만큼 정리한다(부분 실패가 다음 정리를 막지 않게).
    """
    parents: set[str] = set()
    for path in paths:
        if not path:
            continue
        parents.add(os.path.dirname(path))
        try:
            os.remove(path)
        except OSError:
            pass  # 이미 없거나 권한 문제 — 남은 정리를 계속한다

    # docx/pdf 가 모였던 임시 디렉터리가 비었으면 함께 제거
    for parent in parents:
        if parent and os.path.isdir(parent):
            shutil.rmtree(parent, ignore_errors=True)


@contextmanager
def generated_document(doc_type: str, field_values: dict) -> Iterator[tuple[str, str]]:
    """docx 생성 → pdf 변환 후 (docx_path, pdf_path) 를 내주고, 종료 시 반드시 삭제한다.

    정상·예외 어느 경로로 나가도 finally 에서 삭제가 보장된다 (security 규칙).
    """
    docx_path = generate_document(doc_type, field_values)
    pdf_path = ""
    try:
        pdf_path = convert_to_pdf(docx_path)
        yield docx_path, pdf_path
    finally:
        cleanup_files(docx_path, pdf_path)


@contextmanager
def generated_complaint(field_values: dict) -> Iterator[tuple[str, str]]:
    """(하위 호환) 임금체불 진정서 생성 컨텍스트매니저."""
    with generated_document("wage_complaint", field_values) as paths:
        yield paths
