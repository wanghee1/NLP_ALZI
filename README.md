<div align="center">

# ALZI

### 아르바이트·계약직 근로자를 위한 노동법 AI Agent

**노동법 상담 · 근로계약서 분석 · 공식 문서 생성**

`2026.06.03 ~ 2026.06.15`  
`NLP Final Project`

</div>

---

## Overview

**ALZI**는 아르바이트생과 계약직 근로자가 노동법 관련 문제를 쉽게 확인하고 대응할 수 있도록 만든 AI Agent입니다.

사용자의 질문에 대해 실제 법령을 검색해 상담을 제공하고,  
근로계약서 위험 분석과 임금체불 진정서·부당해고 구제신청서·내용증명 생성까지 지원합니다.

단순 정보 제공이 아니라

**상담 → 계약서 분석 → 공식 문서 생성**

까지 하나의 흐름으로 연결하는 것을 목표로 했습니다.

---

## Key Features

### 노동법 상담
- HyDE 기반 질의 변환
- ChromaDB를 활용한 관련 법령 검색
- 검색된 법령을 근거로 상담 답변 생성
- 근거 부족 시 답변 제한

### 근로계약서 분석
- PDF 텍스트 추출
- 위법·불리·누락 가능성이 있는 조항 분석
- LLM 판단과 법적 근거 검색을 결합한 구조

### 공식 문서 생성
- 상황에 맞는 문서 타입 결정
- 필요한 정보를 대화형으로 수집
- docxtpl 기반 DOCX 생성
- LibreOffice Headless를 이용한 PDF 변환

---

## My Role

저는 **공식 문서 생성 기능**을 중심으로 개발했습니다.

- 문서 타입별 필수 필드 구조화
- 대화형 필드 수집 상태머신 구현
- docxtpl 기반 템플릿 값 주입
- 문서별 변수명 정합성 관리
- 공통 사용자 정보 재사용 구조 설계
- 생성 파일 및 개인정보 처리 로직 개선

---

## Trouble Shooting

### 문서마다 달라지는 변수명 문제

문서 템플릿, `fields.py`, `collector.py`에서 사용하는 변수명이 일치하지 않아  
일부 문서가 빈칸으로 생성되는 문제가 발생했습니다.

예를 들어 같은 연락처 정보가 문서에 따라

```text
worker_mobile
worker_phone
```

처럼 다르게 사용되었습니다.

이를 해결하기 위해 문서별 필드를 `fields.py`에서 통합 관리하고,  
공통 값에는 canonical name을 부여한 뒤 문서별 변수명과 연결하는 alias 구조를 적용했습니다.

```text
사용자 정보
   ↓
canonical field
   ↓
alias mapping
   ↓
template variable
```

이를 통해 문서마다 다른 변수명으로 발생하던 매핑 오류를 줄였습니다.

---

### 상태 기반 라우팅 개선

초기에는 `collecting`, `confirming` 등 특정 상태만 문서 수집기로 전달했습니다.

하지만 새로운 상태가 추가될 때마다 라우팅 조건도 수정해야 해  
누락에 따른 오류가 발생할 가능성이 있었습니다.

이를

```text
mode == chat
→ 일반 상담

mode != chat
→ document collector
```

구조로 변경해 새로운 문서 상태가 추가되어도  
라우팅 로직을 반복 수정하지 않도록 개선했습니다.

---

## 🛠️ Tech Stack

| Category | Technology |
|---|---|
| Frontend | React 18, Vite |
| Backend | Python 3.11, FastAPI, Uvicorn |
| LLM | Claude |
| Embedding | OpenAI text-embedding-3-small |
| Vector DB | ChromaDB |
| PDF Parsing | PyMuPDF |
| Document | docxtpl, LibreOffice Headless |
| Data | 국가법령정보 OPEN API |

---

## Architecture

```text
Frontend
React + Vite
     │
     ▼
FastAPI
     │
     ├── RAG
     ├── Contract Analysis
     ├── Document Generation
     └── LLM
```

백엔드는 HTTP 요청을 처리하는 `api` 계층과  
실제 비즈니스 로직을 담당하는 `src` 계층을 분리해 구성했습니다.

---

## Result

- 단일 챗봇에서 상담 → 계약서 분석 → 문서 생성 흐름 구현
- HyDE + RAG 기반 노동법 검색
- 계약서 위험 분석 기능 구현
- 대화형 공식 문서 생성 상태머신 구현
- 개인정보가 포함된 생성 파일을 임시 저장 후 삭제하도록 처리

---

## What I Learned

AI 서비스에서는 답변을 잘 생성하는 것만큼  
**근거 없는 답변을 하지 않도록 제한하고, 사용자 행동까지 연결하는 구조**가 중요하다는 점을 배웠습니다.

또한 문서 생성 기능을 구현하며  
필드 정의, 상태 관리, 데이터 정합성, 예외 처리 같은 세부 구현이  
서비스의 안정성과 완성도를 좌우한다는 것을 경험했습니다.

---

<div align="center">

### ALZI

**노동법 정보를 실제 대응으로 연결합니다.**

</div>
