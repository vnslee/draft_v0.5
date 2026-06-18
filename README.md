# draft_v0.5

## 폴더 구조

```
draft_v0.5/
├── app/
│   ├── back/                       # 백엔드 애플리케이션
│   │   └── app.py                  # FastAPI 서버
│   └── front/                      # 프론트엔드 애플리케이션
│       └── index.html              # 메인 페이지
├── data/
│   ├── country/                    # 국가별 데이터
│   │   ├── PL/                     # 폴란드
│   │   │   ├── PL_2026-06-18T1432.json
│   │   │   └── PL_latest.json
│   │   └── UK/                     # 영국
│   │       └── UK_latest.json
│   ├── internal/                   # 내부 공통 데이터
│   │   └── internal_latest.json
│   ├── sample/                     # 샘플 데이터
│   │   └── sample.md
│   ├── schema/                     # 데이터 스키마 정의
│   │   ├── country_prompt.md       # 국가별 프롬프트
│   │   └── country_schema.md       # 국가별 스키마
│   └── README.md
├── engine/                         # 스코어링 엔진
│   └── scoring_engine.py           # 점수 계산 로직
├── report/
│   ├── country/                    # 국가별 리포트
│   │   ├── PL/                     # 폴란드 리포트
│   │   │   └── PL_rpt_2026-06-18T1500.json
│   │   └── README.md
│   └── region/                     # 지역별 리포트
│       └── README.md
├── spec/
│   └── web_design.md               # 웹 디자인 명세서
└── README.md
```

## 파일 네이밍 규칙

파일명은 **생성일시(YYYYMMDDHHmm).json**만 사용한다. 경로 자체가 식별자 역할을 하므로 prefix 불필요.

```
{생성일시}.json
```

### data 하위 예시

| 파일 경로 | API 경로 |
|-----------|----------|
| `data/country/PL/PL_latest.json` | `/api/data/country/PL` |
| `data/country/PL/PL_2026-06-18T1432.json` | `/api/data/country/PL?version=2026-06-18T1432` |
| `data/country/UK/UK_latest.json` | `/api/data/country/UK` |
| `data/internal/internal_latest.json` | `/api/data/internal` |
| `data/schema/country_schema.md` | `/api/data/schema/country` |

### report 하위 예시

| 파일 경로 | API 경로 |
|-----------|----------|
| `report/country/PL/PL_rpt_2026-06-18T1500.json` | `/api/report/country/PL` |
| `report/region/202606191012.json` | `/api/report/region` |

### 생성일시 형식

- `YYYYMMDDHHmm` (연월일시분, 12자리)
- 예: `202606191012` = 2026년 06월 19일 10시 12분

## 아키텍처

```
[Front (app/front)]  →  [Back (app/back)]  →  [File System (data/, report/)]
```

- **프론트엔드**: 백엔드 API를 호출하여 데이터/리포트 조회
- **백엔드 (Python)**: FastAPI 기반, API 요청을 받아 파일 시스템에서 조건에 맞는 JSON을 탐색·응답
- **데이터 접근**: 프론트 → 백엔드 API 경유 (프론트가 파일에 직접 접근하지 않음)

### API 설계 (Path 기반 — 폴더 구조와 1:1 매핑)

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/data/country/PL` | 폴란드 최신 데이터 조회 |
| GET | `/api/data/country/PL?version=2026-06-18T1432` | 폴란드 특정 버전 조회 |
| GET | `/api/data/country/UK` | 영국 데이터 조회 |
| GET | `/api/data/internal` | 내부 공통 데이터 조회 |
| GET | `/api/data/schema/country` | 국가별 스키마 조회 |
| GET | `/api/report/country/PL` | 폴란드 리포트 조회 |
| GET | `/api/report/region` | 지역별 리포트 조회 |
