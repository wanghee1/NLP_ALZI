"""FastAPI 애플리케이션 진입점.

CORS 설정 + 라우터 등록만 담당하는 얇은 진입점이다.
backend/ 디렉터리에서 `uvicorn main:app --reload` 로 실행한다
(그래야 `from config...`, `from api...` import 가 풀린다).

Phase 4-B: chat + document(다운로드) 라우터 + 헬스체크. contract 라우터는 해당 기능 Phase에서 추가.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import chat, contract, document
from config.settings import FRONTEND_ORIGIN

app = FastAPI(title="Labor Law AI Agent", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(contract.router)
app.include_router(document.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
