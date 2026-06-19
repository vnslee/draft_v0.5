# report/region — 권역 퀵윈(quick_win) 리포트

화면에서 **권역(예: 유럽=EU)** 을 선택하면 생성되는 출력물. 권역 내 베이스라인국을 기준으로
나머지 국가들을 일괄 스코어링하여 **퀵윈 후보**(적은 노력으로 빠르게 성과를 낼 국가)를 산출한다.

생성 엔진: `engine/region_engine.py` (단일국 엔진 `engine/scoring_engine.py`의 스코어링 로직 재사용)

---

## 1. 폴더/네이밍

```
report/region/
└── <REGION>/                       권역 코드 (EU | AMERICAS | APAC)
    ├── <REGION>_rpt_<CREATED_AT>.json   조사·추천 실행 스냅샷
    └── <REGION>_rpt_latest.json         최신 포인터 (화면이 읽음)
예) report/region/EU/EU_rpt_2026-06-19T1200.json
```
- `<CREATED_AT>` = 추천 산출 시각, 정렬형 `YYYY-MM-DDTHHmm` (콜론 제거).
- country 리포트(`report/country/<CODE>/`)와 동일한 스냅샷+latest 규칙.

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

## 5. 예시 결과 (EU, 2026-06-19)

| rank | 국가 | 퀵윈 | QW점수 | 매력도 | 난이도 | 유사도 | 구축비(절감) | 사분면 |
|---|---|---|---|---|---|---|---|---|
| 1 | ES 스페인 | ★ | 58.5 | 44.6 | 60.0 | 82.2 | 3000 (40%↓) | JV/제휴 필요 |
| 2 | PL 폴란드 | – | 53.2 | 47.5 | 71.2 | 73.4 | 3500 (30%↓) | JV/제휴 필요 |
| 3 | DE 독일 | – | 51.0 | 31.5 | 42.5 | 64.0 | 4000 (20%↓) | 기회 탐색 |

> 베이스라인: 영국(UK). 스페인은 유사도 82.2로 재사용률 최고·게이트 무장애 → 권역 유일 퀵윈.
> 폴란드는 진입난이도(은행계 집중) 과다, 독일은 매력도(저성장)로 임계 미달.
