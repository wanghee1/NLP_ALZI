"""국가법령정보센터 Open API 클라이언트 (일회성 적재용, 동기 호출).

근로기준법, 최저임금법 등 주요 노동 법령의 목록·본문을 수집한다.
API 문서: https://www.law.go.kr/LSW/openapiInfo.do

표준 라이브러리(urllib)만으로 호출한다 (탐색 스크립트와 일관, httpx 등 미추가).
ingestion 계층이므로 런타임 요청 경로(api/)에 의존하지 않는다 (architecture 규칙).
OC 인증값(=LAW_API_KEY)은 settings 에서 로딩하고, 로그에는 마스킹해 노출한다 (security 규칙).
"""

from __future__ import annotations

import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

from config.settings import LAW_API_KEY

LIST_API_URL = "https://www.law.go.kr/DRF/lawSearch.do"
DETAIL_API_URL = "https://www.law.go.kr/DRF/lawService.do"
REQUEST_TIMEOUT_SEC = 15


def _mask(value: str) -> str:
    """OC(이메일 ID) 등 식별값을 로그에 그대로 노출하지 않도록 마스킹한다."""
    if not value:
        return "(미설정)"
    if len(value) <= 2:
        return "*" * len(value)
    return f"{value[0]}{'*' * (len(value) - 2)}{value[-1]}"


def _http_get_text(url: str, params: dict[str, str]) -> str:
    """GET 요청 후 응답 본문을 텍스트로 반환한다 (외부 I/O — 예외는 호출부에서 처리)."""
    full_url = f"{url}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(full_url, headers={"User-Agent": "labor-law-agent-ingest/0.1"})
    with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_SEC) as resp:
        charset = resp.headers.get_content_charset() or "utf-8"
        return resp.read().decode(charset, errors="replace")


def fetch_law_list(query: str) -> list[dict[str, str]]:
    """목록 API를 호출해 검색어에 해당하는 법령 목록을 반환한다.

    Args:
        query: 검색어 (예: '근로기준법')

    Returns:
        [{"법령명", "MST", "법령구분명"}, ...]. 결과 없으면 빈 리스트.

    Raises:
        RuntimeError: 인증 실패 등 API가 정상 목록을 주지 않은 경우.
    """
    if not LAW_API_KEY:
        raise RuntimeError("LAW_API_KEY 미설정 — backend/.env 를 확인하라.")

    params = {"OC": LAW_API_KEY, "target": "law", "type": "XML", "query": query}
    try:
        xml = _http_get_text(LIST_API_URL, params)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        raise RuntimeError(f"목록 API 네트워크 오류: {type(exc).__name__}") from exc

    try:
        root = ET.fromstring(xml)
    except ET.ParseError as exc:
        # 인증 실패 시 <Response><result>...</result></Response> 형태가 오기도 한다.
        raise RuntimeError(f"목록 응답 파싱 실패(OC={_mask(LAW_API_KEY)}): {exc}") from exc

    # 정상 응답이면 resultCode=00. 그 외(인증 실패 등)는 명확히 알린다.
    result_code = root.findtext("resultCode")
    if result_code is not None and result_code != "00":
        raise RuntimeError(
            f"목록 API 비정상 응답(OC={_mask(LAW_API_KEY)}, "
            f"resultMsg={root.findtext('resultMsg')})"
        )

    laws: list[dict[str, str]] = []
    for law in root.findall("law"):
        name = (law.findtext("법령명한글") or "").strip()
        mst = (law.findtext("법령일련번호") or "").strip()
        kind = (law.findtext("법령구분명") or "").strip()
        if name and mst:
            laws.append({"법령명": name, "MST": mst, "법령구분명": kind})
    return laws


def fetch_law_body(mst: str) -> str:
    """본문 API를 호출해 법령 전문 XML 문자열을 반환한다.

    Args:
        mst: 법령 마스터 일련번호 (목록의 법령일련번호)

    Returns:
        본문 XML 원문 (파싱은 parser.parse_articles 에 위임).

    Raises:
        RuntimeError: 네트워크 오류.
    """
    if not LAW_API_KEY:
        raise RuntimeError("LAW_API_KEY 미설정 — backend/.env 를 확인하라.")

    params = {"OC": LAW_API_KEY, "target": "law", "type": "XML", "MST": mst}
    try:
        return _http_get_text(DETAIL_API_URL, params)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        raise RuntimeError(f"본문 API 네트워크 오류(MST={mst}): {type(exc).__name__}") from exc
