# report/region — 권역 퀵윈(quick_win) 리포트

화면에서 **권역(예: 유럽=EU)** 을 선택하면 생성되는 출력물. 권역 내 베이스라인국을 기준으로
나머지 국가들을 일괄 스코어링하여 **퀵윈 후보**(적은 노력으로 빠르게 성과를 낼 국가)를 산출한다.

생성 엔진: `engine/region_engine.py` (단일국 엔진 `engine/scoring_engine.py`의 스코어링 로직 재사용)

---

## 1. 폴더/네이밍

```
report/region/
└── <REGION>/                       권역 코드 (EU | AMERICAS | APAC)
    ├── index.json                  버전 매니페스트 (화면 드롭다운 소스, 엔진이 자동 갱신)
    ├── <REGION>_rpt_<CREATED_AT>.json   조사·추천 실행 스냅샷 (불변)
    └── <REGION>_rpt_latest.json         최신 포인터 (화면 기본값)
예) report/region/EU/EU_rpt_2026-06-19T1200.json
```
- `<CREATED_AT>` = 추천 산출 시각, 정렬형 `YYYY-MM-DDTHHmm` (콜론 제거).
- country 리포트(`report/country/<CODE>/`)와 동일한 스냅샷+latest 규칙.

### 버전 관리 — 화면에서 버전 선택
- **선택 단위 = 보고서 스냅샷.** 엔진 실행 1회 = 불변 스냅샷 1개. 화면은 저장된 JSON을 그대로 렌더.
- 엔진이 실행될 때마다 같은 폴더의 **`index.json`을 자동 갱신**(같은 report_id면 덮어쓰고 `created_at` 내림차순 정렬, `latest` 포인터 갱신).
- 화면 흐름: `index.json` 읽기 → `versions[]`로 드롭다운(기본 `latest`) → 선택한 `file` 로드해 렌더.
  → 폴더 스캔·파일명 파싱 없이 파일 1개로 드롭다운 구성. freshness 신호등(🟢🟡🔴)도 `created_at`으로 계산.
- 각 보고서의 `based_on`(country/internal 버전 도장)으로 "이 버전이 어떤 데이터로 계산됐는지" 추적 → 재현성 확보.

```jsonc
// index.json
{
  "region": "EU",
  "latest": "EU_rpt_2026-06-19T1200",          // 기본 선택 포인터
  "versions": [                                  // created_at 내림차순
    { "report_id": "EU_rpt_2026-06-19T1200",
      "created_at": "2026-06-19T12:00:00+09:00",
      "file": "EU_rpt_2026-06-19T1200.json",     // 화면이 로드할 파일
      "report_type": "region_quickwin",
      "based_on": { "internal_version": "1.2",
                    "country_versions": { "DE": "DE_latest", "ES": "ES_latest", "PL": "PL_latest" } },
      "summary": { "candidate_count": 3, "quick_wins": ["ES","DE"],
                   "ranking": [ { "code": "ES", "rank": 1, "quick_win": true, "quick_win_score": 61.6 }, "..." ] } }
  ]
}
```

## 2. 실행

```bash
python3 engine/region_engine.py EU                 # 유럽 권역 퀵윈
python3 engine/region_engine.py EU "국외이전 제한"   # 확장 항목 토글(재계산)
```

입력: `data/country/*/*_latest.json`(같은 region·비베이스라인) + `data/internal/internal_latest.json`
출력: 위 권역 리포트 + `_latest` 포인터.

## 3. 퀵윈 판정 (quick_win)

베이스라인 재사용률(유사도)이 높아 **구축비·기간 절감폭이 크고**, 게이트가 모두 통과하며,
매력도가 일정 수준 이상이고 진입난이도가 과하지 않은 국가.

```
quick_win_score = w_sim·유사도 + w_attr·매력도 + w_ease·(100 − 난이도)
quick_win = 게이트 통과(FAIL 없음)
            AND 유사도 ≥ min_similarity
            AND 매력도 ≥ min_attractiveness
            AND 난이도 ≤ max_difficulty
            AND quick_win_score ≥ quick_win_score(임계)
```

가중치·임계는 `internal_latest.json`의 `quick_win_rules`에서 조정(사람이 관리).
기본값: 유사도 0.40 / 매력도 0.35 / ease(100−난이도) 0.25, 임계 score≥55·유사도≥60·매력도≥40·난이도≤65.
> ease 가중을 둔 이유: "퀵윈"은 최고 매력보다 **낮은 노력·높은 재사용·게이트 무장애**가 본질.

## 4. 리포트 핵심 필드

| 필드 | 설명 |
|---|---|
| `report_type` | `"region_quickwin"` |
| `region` / `baseline` | 대상 권역 / 기준 베이스라인 국가코드 |
| `quick_wins` | 퀵윈으로 판정된 국가코드 배열 |
| `region_insight` | 권역 종합 코멘트(도입부 앵커) |
| `ranking[]` | 국가별 결과. 퀵윈 우선 → quick_win_score 내림차순으로 `rank` |
| ┗ `quick_win` / `quick_win_score` | 퀵윈 여부 / 종합 점수 |
| ┗ `attractiveness`·`difficulty`·`similarity`·`ease`·`quadrant` | 2축+유사도 스코어와 사분면 |
| ┗ `gate_passed`·`gate_flag`·`gate_checks` | 게이트 통과 여부·저신뢰(FLAG) 존재·상세 |
| ┗ `cost` | 베이스라인 대비 절감 적용 구축비·기간·운영비 |
| ┗ `quick_win_reasons`·`blockers`·`verdict` | 퀵윈 근거 / 저해 요인 / 한줄 판정 |
| ┗ `business_contributions`·`it_contributions` | 항목별 기여(insight 2층 포함) |
| `gate_failed` | 게이트 FAIL로 진입 불가한 국가 |
| `due_diligence_summary` | 국가별 실사 필요 항목 수(tier≥3) |
| `based_on` | 재현성 도장: 사용한 country/baseline 버전·internal·schema |

## 5. 통화 정규화 (중요)

시장규모 등 금액 항목은 국가마다 단위가 다르다(PL=PLN_M, UK=GBP_M, DE=USD_M, ES=EUR_M).
그대로 비교하면 왜곡되므로, `internal.fx`(통화→base EUR 환산율, 사람이 관리)로 **base 통화(EUR_M)로
통일한 뒤** 정규화한다. 엔진은 `<CCY>_M` 단위를 자동 인식해 환산(`scoring_engine.to_base_money`).

```
DE 47000 USD_M → 43240 EUR_M (정규화 61.8)
PL 88100 PLN_M → 20263 EUR_M (정규화 28.9)
UK 55000 GBP_M → 64350 EUR_M (정규화 91.9, 베이스라인)
ES 18000 EUR_M → 18000 EUR_M (정규화 25.7)
```

## 6. 예시 결과 (EU, 2026-06-19)

| rank | 국가 | 퀵윈 | QW점수 | 매력도 | 난이도 | 유사도 | 구축비(절감) | 사분면 |
|---|---|---|---|---|---|---|---|---|
| 1 | ES 스페인 | ★ | 61.6 | 53.4 | 60.0 | 82.2 | 3000 (40%↓) | 선별 진출 |
| 2 | DE 독일 | ★ | 58.4 | 52.6 | 42.5 | 64.0 | 4000 (20%↓) | 즉시 진출 |
| 3 | PL 폴란드 | – | 56.3 | 56.3 | 71.2 | 73.4 | 3500 (30%↓) | 선별 진출 |

> 베이스라인: 영국(UK). 통화 정규화 적용 후 결과.
> 스페인(유사도 82.2 최고·40% 절감)과 독일(난이도 42.5 낮음·즉시 진출)이 퀵윈.
> 폴란드는 매력도는 가장 높으나 진입난이도 71.2(은행계 집중)로 임계(≤65) 초과 → 퀵윈 제외.
