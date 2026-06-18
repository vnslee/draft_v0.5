# draft_v0.5

## 폴더 구조

```
draft_v0.5/
├── app/
│   ├── back/                       # 백엔드 애플리케이션
│   └── front/                      # 프론트엔드 애플리케이션
├── data/
│   ├── countries/                  # 국가별 데이터
│   │   ├── AU/                     # 호주
│   │   │   ├── external/
│   │   │   └── internal/
│   │   ├── BR/                     # 브라질
│   │   │   ├── external/
│   │   │   └── internal/
│   │   ├── CA/                     # 캐나다
│   │   │   ├── external/
│   │   │   └── internal/
│   │   ├── CN/                     # 중국
│   │   │   ├── external/
│   │   │   └── internal/
│   │   ├── DE/                     # 독일
│   │   │   ├── external/
│   │   │   └── internal/
│   │   ├── ID/                     # 인도네시아
│   │   │   ├── external/
│   │   │   └── internal/
│   │   ├── IN/                     # 인도
│   │   │   ├── external/
│   │   │   └── internal/
│   │   ├── IT/                     # 이탈리아
│   │   │   ├── external/
│   │   │   └── internal/
│   │   ├── KR/                     # 한국
│   │   │   ├── external/
│   │   │   └── internal/
│   │   ├── UK/                     # 영국
│   │   │   ├── external/
│   │   │   │   ├── biz/           # 비즈니스 데이터
│   │   │   │   └── it/            # IT 데이터
│   │   │   └── internal/
│   │   │       ├── biz/           # 비즈니스 데이터
│   │   │       └── it/            # IT 데이터
│   │   └── US/                     # 미국
│   │       ├── external/
│   │       └── internal/
│   └── rulesets/                   # 규칙셋
├── report/
│   ├── country/                    # 국가별 리포트
│   └── region/                     # 지역별 리포트
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
| `data/countries/AU/external/202606191012.json` | `/api/data/countries/AU/external` |
| `data/countries/AU/internal/202606191012.json` | `/api/data/countries/AU/internal` |
| `data/countries/UK/external/biz/202606191012.json` | `/api/data/countries/UK/external/biz` |
| `data/countries/UK/internal/it/202606191012.json` | `/api/data/countries/UK/internal/it` |
| `data/rulesets/202606191012.json` | `/api/data/rulesets` |

### report 하위 예시

| 파일 경로 | API 경로 |
|-----------|----------|
| `report/country/202606191012.json` | `/api/report/country` |
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
| GET | `/api/data/countries/AU/external` | 호주 외부 데이터 조회 |
| GET | `/api/data/countries/AU/internal` | 호주 내부 데이터 조회 |
| GET | `/api/data/countries/UK/external/biz` | 영국 외부 비즈니스 데이터 조회 |
| GET | `/api/data/countries/UK/internal/it` | 영국 내부 IT 데이터 조회 |
| GET | `/api/data/rulesets` | 규칙셋 조회 |
| GET | `/api/report/country` | 국가별 리포트 조회 |
| GET | `/api/report/region` | 지역별 리포트 조회 |
