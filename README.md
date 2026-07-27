# 테마 주식 리서치 에이전트 (Theme-Stock-Research)

사용자가 입력한 **주식 테마** 또는 **국내 종목명**을 공개 정보로 조사해, 근거가 확인된 KRX 상장 보통주 후보와 기본 비교 정보를 정리해 주는 리서치 보조 도구입니다.

국내(KRX) 분석을 항상 우선 제공하며, 전일 미국 시장의 동일 테마 흐름·미국 Peer Company·글로벌 운용사 동향은 국내 결과를 보완하는 **참고 정보**로만 다룹니다. 참고 정보 수집이 실패해도 국내 보고서 생성은 중단되지 않습니다.

> 본 서비스는 정보 제공 및 리서치 보조 도구이며, 특정 종목의 매수·매도·보유를 권유하거나 투자 결과를 보장하지 않습니다.

## 주요 기능

- **테마 정의** — 입력된 테마의 의미와 종목 포함 기준을 정리
- **후보 종목 선정** — 공시·IR·공식 자료 기반으로 근거가 확인된 KRX 보통주 후보 선정 (최대 `top_n`개)
- **기본 정량 비교** — 최근 종가·시가총액·기본 재무 지표 비교
- **뉴스·공시** — 종목별 최근 이슈와 출처 정리
- **가격·거래량 분석 / 리스크 요약** — 공개 자료 기반 확장 분석 (Phase 2)
- **해외 참고 정보** — 미국 선행 동향, 미국 Peer Company, 운용사 동향 (Phase 3)
- **출처 관리·보고서 생성** — 주요 데이터에 출처를 연결하고 Markdown 보고서로 조합

## 입력값

| 항목    | 설명                           | 제약                  |
| ------- | ------------------------------ | --------------------- |
| `theme` | 분석할 테마명 또는 국내 종목명 | 비어 있지 않은 문자열 |
| `top_n` | 비교할 종목 수                 | 1~10 사이의 정수      |

입력이 없거나 의미가 모호하면 임의로 분석하지 않고 입력을 다시 요청합니다.

## 아키텍처

```
theme-stock-research/
├── backend/          # FastAPI 기반 리서치 API
│   └── app/
│       ├── api/          # 요청·응답 경계 (research, dart)
│       ├── services/     # 기능 분해 명세 F-01~F-07 처리
│       ├── data_sources/ # KRX, DART, OpenAI 등 외부 데이터 접근 계층
│       ├── models/       # 요청·결과·출처 데이터 모델, 오류 정의
│       └── config/       # 환경설정·로그 설정
├── frontend/         # React + Vite + TypeScript 화면
│   └── src/
│       ├── pages/        # 리서치 화면 단위
│       ├── components/   # 입력·후보·비교·출처 표시 단위
│       ├── api/          # 백엔드 통신 경계
│       └── types/        # 응답 데이터 타입
├── docs/             # 요구사항 정의서, MVP 실행 계획, 기능 분해 명세
└── scripts/, shared/ # 공용 스크립트·자산
```

## 기술 스택

- **Backend** — Python, FastAPI, Uvicorn
- **Frontend** — React, Vite, TypeScript
- **외부 데이터** — OpenDART(공시), OpenAI(테마 후보·참고 정보 탐색)

## 시작하기

### 사전 준비

```bash
cp .env.example .env
```

`.env`에 필요한 키를 입력합니다.

| 변수                     | 설명                                                           |
| ------------------------ | -------------------------------------------------------------- |
| `DART_API_KEY`           | OpenDART API 키                                                |
| `OPENAI_API_KEY`         | OpenAI API 키                                                  |
| `OPENAI_THEME_MODEL`     | 테마 후보 탐색 모델 (기본 `gpt-4o-mini`)                       |
| `OPENAI_REFERENCE_MODEL` | 미국 참고 정보 탐색 모델 (기본 `gpt-4o-mini`)                  |
| `VITE_API_BASE_URL`      | 프론트엔드가 사용할 백엔드 주소 (기본 `http://localhost:8000`) |

> 실제 API 키·토큰·계정 정보는 `.env`에만 작성하고 저장소에 커밋하지 않습니다.

### 백엔드 실행

```bash
cd backend
make install   # 의존성 설치
make run        # 개발 서버 실행 (http://127.0.0.1:8000)
make test       # 단위·통합 테스트
make check      # 테스트 + 문법 검사
```

### 프론트엔드 실행

```bash
cd frontend
npm install
npm run dev      # 개발 서버 (http://localhost:5173)
npm run build    # 프로덕션 빌드
npm run preview  # 빌드 결과 미리보기
```

## API

| 메서드 | 경로                      | 설명                                                   |
| ------ | ------------------------- | ------------------------------------------------------ |
| `POST` | `/research`               | `theme`, `top_n`을 받아 국내 리서치 보고서 생성        |
| `GET`  | `/dart/companies/resolve` | 국내 종목명 또는 6자리 종목코드를 DART 고유번호로 해석 |

`POST /research` 요청 예시:

```json
{
  "theme": "2차전지",
  "top_n": 5
}
```

응답은 구조화된 `report` 객체와 `markdown` 보고서 텍스트를 함께 반환합니다.

## 개발 단계 (Roadmap)

| 단계    | 범위                                                               | 상태      |
| ------- | ------------------------------------------------------------------ | --------- |
| Phase 1 | 입력 검증, 테마 정의, 후보 선정, 기본 비교, 뉴스·공시, 출처·보고서 | 구현 완료 |
| Phase 2 | 가격·거래량 분석, 리스크 요약                                      | 진행 중   |
| Phase 3 | 미국 선행 동향, 미국 Peer Company, 글로벌 운용사 동향 (참고 정보)  | 예정      |

자세한 요구사항과 작업 분해 구조는 [`docs/`](docs/) 디렉터리를 참고하세요.

- [요구사항 정의서](docs/requirements.md)
- [MVP 실행 계획](docs/MVP-plan.md)
- [기능 분해 명세](docs/function-breakdown.md)
