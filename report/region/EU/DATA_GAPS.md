# 데이터 갭 — 권역 비교 리포트(EU) 기준

> 항목별 국가 비교 화면(매력도 탭)을 만들며 발견한 데이터 결손/불일치 정리.
> 데이터 수집 프롬프트([data/schema/country_prompt.md](../../../data/schema/country_prompt.md)) 보강용.

## 1. 시계열 결손 (비교 차트 핵심 제약)

프롬프트 5번은 "수치+추세 항목은 timeseries 필수"이지만 실제론 **독일(DE)만** 4개 매력도 항목 전부 시계열 보유. ES·PL은 시장규모만 있음.

| 매력도 항목 | ES | DE | PL | 영향 |
|---|---|---|---|---|
| 오토금융/리스 시장규모 | ✓ | ✓ | ✓ | OK |
| 오토금융 성장률(CAGR) | ✗ | ✓ | ✗ | ES·PL은 추이선 못 그림 → 단일점 |
| 금융 이용률(신차) | ✗ | ✓ | ✗ | 〃 |
| 평균 금리/APR | ✗ | ✓ | ✗ | 〃 |

→ **수집 시 매력도 score 항목은 국가 불문 timeseries(2021–2030) 의무화.** 단일값만 있으면 비교 차트에서 한 점으로만 찍혀 트렌드 비교 불가.

## 2. 통화 단위 불일치 (절대값 비교 불가)

시장규모 단위가 국가마다 다름 → 한 차트에 겹치면 절대 비교 무의미. 현재 샘플은 데모 환율로 GBP 환산.

| 국가 | 원 단위 |
|---|---|
| ES | EUR_M |
| DE | USD_M |
| PL | PLN_M |

→ **수집 시 금액 항목에 통화 명시는 유지하되**, 비교를 위해 다음 중 택1 필요:
- (a) 수집 단계에서 공통통화(EUR 또는 GBP) 환산값 필드 추가 (`value_base_eur` 등)
- (b) 리포트 엔진이 환율 테이블로 환산 (환율 출처·기준일 메타 필요)
- 현재 `internal_latest.json`에 FX가 있는지 확인하고, 없으면 환율 기준일 포함해 추가.

## 3. 권역(region) 레벨 집계 필드 부재

PR2 디자인 시안이 요구하나 JSON에 없는 필드 (요약 카드용):
- `region_market_total` — 권역 시장규모 합산(공통통화)
- `region_primary_risk` — 권역 단위 주요 리스크 요약 1줄
- `region_avg_similarity` — 평균 재사용률 (현재 샘플은 계산으로 대체)

→ 국가 데이터가 아니라 **권역 리포트 엔진(region_engine.py) 산출 단계**에서 생성하는 게 맞음. 수집 프롬프트가 아니라 엔진 과제.

## 4. 차트 보강용으로 있으면 좋은 데이터 (선택)

- **세그먼트 분해 시계열**: 신차/중고차/리스/렌팅 별 시장규모 추이 (현재는 합산 단일 시계열)
- **출처 연도(as-of)**: 각 timeseries point가 실측인지 추정인지 point별 플래그 (현재는 timeseries 전체 `estimated` 단일 플래그)
- **신뢰구간**: 전망(forecast)의 상/하한 — 전망 불확실성 표현용 (선택)

## 5. 최저자본금 — difficulty축이나 점수 미반영 (난이도 탭에서 발견)

`최저자본금`은 axis=difficulty인데 value가 텍스트("EFC €5M / 회사법…")라 엔진이 정규화 못 해
business_contributions에 기여 0. 3국 값 형식도 제각각(텍스트/숫자/텍스트) → 막대 비교 불가.

→ country_prompt에 `value_segments` 객체로 세그먼트별 숫자 병기하도록 추가함(해소).
  예: {"b2b_lease":5000,"consumer_credit":5000000,"unit":"EUR"}

## 6. 권역 인사이트·뉴스 — 별도 프롬프트 필요 (해소)

권역 종합 인사이트와 뉴스(지정학·금융·자동차·신용)는 country가 아닌 권역 차원.
→ `data/schema/region_prompt.md` 신규 작성. 국가 뉴스는 country_prompt의 news 배열로 추가.
  뉴스 출처는 category별 지정(Reuters/FT/Automotive News/Moody's 등).

## 우선순위 / 현황

| 순위 | 항목 | 담당 | 상태 |
|---|---|---|---|
| P0 | 매력도 score 항목 전부 timeseries 의무화 (§1) | 수집 프롬프트 | ✅ 반영 |
| P0 | 금액 항목 공통통화 환산 기준 확정 (§2) | 엔진 + internal FX | ✅ FX 테이블 존재(internal_latest) + value_base_eur 병기 규칙 |
| P1 | 권역 집계 필드 (§3) | region_engine | ⏳ 시장합산·평균유사도는 엔진 계산, primary_risk는 region_prompt |
| P2 | 세그먼트 분해·point별 출처 (§4) | 수집 프롬프트(선택) | ✅ 선택 항목으로 반영 |
| P1 | 최저자본금 숫자화 (§5) | 수집 프롬프트 | ✅ value_segments 반영 |
| P1 | 권역 인사이트·뉴스 (§6) | region_prompt | ✅ 신규 프롬프트 작성 |
