"""law.go.kr 법령 Open API 응답 구조 탐색 스크립트 (일회성).

목적: 본 적재 코드(build_index.py)를 짜기 전에, 목록·본문 API가 실제로
어떤 XML 태그 구조로 응답하는지 콘솔에 그대로 출력해 **사람이 눈으로 확인**하기 위함이다.
(어느 태그에 법령 일련번호/조문 본문이 들어있는지는 문서만으로는 확실치 않아, 실제 응답을 봐야 한다.)

여기서는 청킹/임베딩/ChromaDB 등 파이프라인 본 구현은 하지 않는다. 응답 구조 확인 전용.

의존성: 표준 라이브러리 + python-dotenv 만 사용한다 (langchain/chromadb/httpx 등 추가 금지).
이 스크립트는 ingestion(일회성 실행) 계층이므로 런타임 요청 경로(api/)에 의존하지 않는다.

실행 방법:
    cd backend
    python -m src.ingestion.explore_law_api

사전 준비: backend/.env 에 LAW_API_KEY(=law.go.kr 신청 시 등록한 이메일 ID값) 설정.
"""

from __future__ import annotations

import os
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

from dotenv import load_dotenv

# --- 상수 (매직값을 코드 곳곳에 흩뿌리지 않기 위해 상단에 모음) ---
LIST_API_URL = "https://www.law.go.kr/DRF/lawSearch.do"
DETAIL_API_URL = "https://www.law.go.kr/DRF/lawService.do"
SEARCH_QUERY = "근로기준법"
LIST_PREVIEW_CHARS = 2500
DETAIL_PREVIEW_CHARS = 3500
REQUEST_TIMEOUT_SEC = 15

# MST(법령 마스터 일련번호) 후보 태그명 — 처음 잡히는 것을 사용한다.
# 문서마다 표기가 달라 실제 응답에서 확인이 필요하므로 후보를 순서대로 시도한다.
MST_CANDIDATE_TAGS = ("법령일련번호", "MST", "법령ID")


def _mask_oc(oc: str) -> str:
    """OC(=이메일 ID) 값을 로그에 그대로 노출하지 않도록 마스킹한다 (security 규칙).

    호출 성공 여부 위주로 출력하기 위해, 설정 여부와 길이만 드러나는 형태로 가린다.
    """
    if not oc:
        return "(미설정)"
    if len(oc) <= 2:
        return "*" * len(oc)
    return f"{oc[0]}{'*' * (len(oc) - 2)}{oc[-1]}"


def _http_get_text(url: str, params: dict[str, str]) -> str:
    """주어진 URL에 GET 요청을 보내고 응답 본문을 텍스트로 반환한다.

    표준 라이브러리(urllib)만으로 호출하며, 외부 I/O이므로 예외는 호출부에서 처리한다.
    """
    query = urllib.parse.urlencode(params)
    full_url = f"{url}?{query}"
    req = urllib.request.Request(full_url, headers={"User-Agent": "labor-law-agent-explore/0.1"})
    with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_SEC) as resp:
        charset = resp.headers.get_content_charset() or "utf-8"
        return resp.read().decode(charset, errors="replace")


def _extract_mst(list_xml: str) -> str | None:
    """목록 응답 XML에서 첫 번째 법령의 MST(일련번호)를 추출 시도한다.

    후보 태그명(MST_CANDIDATE_TAGS)을 순서대로 find 하여 처음 잡히는 값을 사용한다.
    못 찾으면 None을 반환하고, 호출부에서 태그명 확인 안내를 출력한다.
    """
    root = ET.fromstring(list_xml)
    for tag in MST_CANDIDATE_TAGS:
        # 트리 어디에 위치하든 첫 번째로 등장하는 후보 태그를 찾는다.
        elem = root.find(f".//{tag}")
        if elem is not None and elem.text and elem.text.strip():
            print(f"[정보] '{tag}' 태그에서 일련번호 추출 성공.")
            return elem.text.strip()
    return None


def main() -> int:
    """탐색 절차를 순서대로 실행한다. 각 단계 실패 시 어느 단계인지 명확히 출력한다."""
    load_dotenv()

    oc = os.getenv("LAW_API_KEY", "").strip()
    if not oc:
        print("[중단] LAW_API_KEY 가 .env 에 설정되어 있지 않다. backend/.env 를 확인하라.")
        return 1
    print(f"[정보] OC(LAW_API_KEY) 로드됨: {_mask_oc(oc)}")

    # --- 1단계: 목록 API 호출 ---
    print("\n" + "=" * 70)
    print(f"[1단계] 목록 API 호출 (query={SEARCH_QUERY})")
    print("=" * 70)
    list_params = {
        "OC": oc,
        "target": "law",
        "type": "XML",
        "query": SEARCH_QUERY,
    }
    try:
        list_xml = _http_get_text(LIST_API_URL, list_params)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        print(f"[실패] 1단계(목록 API 호출) 네트워크 오류: {type(exc).__name__}")
        return 1
    except Exception as exc:  # noqa: BLE001 - 탐색 스크립트라 예상 못한 오류도 단계 표기 후 종료
        print(f"[실패] 1단계(목록 API 호출) 예기치 못한 오류: {type(exc).__name__}")
        return 1

    print(f"\n--- 목록 응답 XML 앞 {LIST_PREVIEW_CHARS}자 (태그명 육안 확인용) ---\n")
    print(list_xml[:LIST_PREVIEW_CHARS])
    print("\n--- (목록 응답 미리보기 끝) ---")

    # --- 2단계: MST 추출 ---
    print("\n" + "=" * 70)
    print("[2단계] 첫 번째 법령의 MST(일련번호) 추출 시도")
    print("=" * 70)
    try:
        mst = _extract_mst(list_xml)
    except ET.ParseError as exc:
        print(f"[실패] 2단계(XML 파싱) 오류: {exc}")
        print("       위 목록 응답이 XML 형식이 맞는지(오류 메시지/HTML 여부) 확인하라.")
        return 1

    if mst is None:
        print(
            "[경고] MST 태그를 못 찾음. "
            f"시도한 후보 태그: {', '.join(MST_CANDIDATE_TAGS)}.\n"
            "       위 목록 응답에서 실제 일련번호 태그명을 확인하라."
        )
        return 1
    print(f"[정보] 추출한 MST 값: {mst}")

    # --- 3단계: 본문 API 호출 ---
    print("\n" + "=" * 70)
    print(f"[3단계] 본문 API 호출 (MST={mst})")
    print("=" * 70)
    detail_params = {
        "OC": oc,
        "target": "law",
        "type": "XML",
        "MST": mst,
    }
    try:
        detail_xml = _http_get_text(DETAIL_API_URL, detail_params)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        print(f"[실패] 3단계(본문 API 호출) 네트워크 오류: {type(exc).__name__}")
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"[실패] 3단계(본문 API 호출) 예기치 못한 오류: {type(exc).__name__}")
        return 1

    print(f"\n--- 본문 응답 XML 앞 {DETAIL_PREVIEW_CHARS}자 (조문 태그 구조 확인용) ---\n")
    print(detail_xml[:DETAIL_PREVIEW_CHARS])
    print("\n--- (본문 응답 미리보기 끝) ---")

    print("\n[완료] 탐색 종료. 위 목록/본문 응답의 태그 구조를 확인하라.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
