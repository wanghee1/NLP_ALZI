"""DOCX → PDF 변환기 (LibreOffice headless).

시스템에 설치된 LibreOffice(soffice)를 subprocess 로 호출해 docx 를 pdf 로 변환한다.
순수 로직 계층이라 전송 계층(api/)에 의존하지 않는다 (architecture).

보안: 개인정보가 담긴 필드값/문서 내용을 로그에 출력하지 않는다 (종료코드만 보고).
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from config.settings import SOFFICE_BIN

# 변환이 지나치게 오래 걸리면(설치 문제 등) 멈추지 않도록 상한을 둔다.
_CONVERT_TIMEOUT_SEC = 120


def convert_to_pdf(docx_path: str) -> str:
    """docx 를 같은 임시 디렉터리에 pdf 로 변환하고 그 경로를 반환한다.

    Args:
        docx_path: 변환할 docx 경로

    Returns:
        생성된 pdf 경로 (docx 와 같은 디렉터리, 확장자만 .pdf).

    Raises:
        RuntimeError: LibreOffice 미설치/실행 실패/PDF 미생성 등.
    """
    docx = Path(docx_path)
    if not docx.exists():
        raise RuntimeError(f"변환할 docx 가 없습니다: {docx_path}")

    out_dir = docx.parent

    # 동시 변환 충돌 방지를 위해 호출마다 별도 LibreOffice 프로파일 디렉터리를 쓴다.
    # (기본 프로파일을 공유하면 병렬/연속 호출 시 잠금 충돌이 날 수 있다.)
    profile_dir = tempfile.mkdtemp(prefix="lo_profile_")
    try:
        cmd = [
            SOFFICE_BIN,
            "--headless",
            f"-env:UserInstallation={Path(profile_dir).as_uri()}",
            "--convert-to",
            "pdf",
            "--outdir",
            str(out_dir),
            str(docx),
        ]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=_CONVERT_TIMEOUT_SEC,
            )
        except FileNotFoundError as exc:
            # SOFFICE_BIN 을 찾지 못함 — 설치/경로 문제
            raise RuntimeError(
                f"LibreOffice 실행 파일('{SOFFICE_BIN}')을 찾지 못했습니다. "
                "LibreOffice 설치 여부나 SOFFICE_BIN 환경변수를 확인하세요."
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("PDF 변환이 시간 내에 끝나지 않았습니다.") from exc

        if result.returncode != 0:
            # stderr 원문에는 경로 등이 섞일 수 있어 종료코드만 노출한다.
            raise RuntimeError(f"PDF 변환 실패 (soffice 종료코드 {result.returncode}).")

        pdf_path = out_dir / f"{docx.stem}.pdf"
        if not pdf_path.exists():
            raise RuntimeError("PDF 변환 실패: 출력 파일이 생성되지 않았습니다.")

        return str(pdf_path)
    finally:
        # 프로파일 디렉터리는 내부용이므로 항상 정리한다.
        shutil.rmtree(profile_dir, ignore_errors=True)
