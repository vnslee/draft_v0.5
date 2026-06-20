# AI 리서치 — 권역(Region) 인사이트 + 뉴스 프롬프트

> 권역 비교 리포트 상단(요약 탭)에 들어갈 **권역 종합 인사이트**와 **권역 뉴스**를 생성한다.
> country 조사(country_prompt.md)가 끝난 뒤, 그 country.json들을 입력으로 권역 한 벌을 생성.
> **점수·랭킹·사분면·비용은 엔진(region_engine.py)이 계산** — 이 프롬프트는 정성 인사이트와 뉴스만 담당.

---

## 1. 역할 분담 (무엇을 AI가, 무엇을 엔진이)

| 산출물 | 담당 |
|---|---|
| 국가별 점수(매력도/난이도/유사도)·랭킹·사분면·구축비·퀵윈 판정 | **엔진** (계산) |
| 권역 시장규모 합산·평균 재사용률 | **엔진** (각국 값 집계) |
| **권역 종합 인사이트**(진출 전략 서술) | **AI (이 프롬프트)** |
| **권역 뉴스**(지정학·금융·자동차·신용 동향) | **AI (이 프롬프트)** |
| 국가별 뉴스 | country_prompt.md (국가 조사 시) |

→ 이 프롬프트는 **숫자를 만들지 않는다.** 엔진이 준 랭킹·사분면을 참고해 "왜 이렇게 나왔는지, 권역 차원에서 무엇을 주의할지"를 서술한다.

---

## 2. 리서치 프롬프트 (그대로 사용)

```
역할: 너는 20년차 글로벌 오토파이낸스 진출 컨설턴트다.
권역: {REGION}  (EU | AMERICAS | APAC)
베이스라인국: {BASELINE}  (예: UK)
후보국 및 엔진 산출 요약:
{COUNTRY_SUMMARY}
  - 각 국가의 code, 매력도, 난이도, 유사도, 사분면, 퀵윈 여부, 구축비를 표로 제공
타깃 세그먼트: {SEGMENT}

아래를 조사·작성해 지정된 JSON 스키마로만 출력하라. 순수 JSON만(설명·마크다운·코드펜스 금지).

[1] region_insight (권역 종합 인사이트)
- 4~6문장. 권역 전체 진출 전략 관점.
- 반드시 포함: ① 권역 시장 전반 흐름(규모·성장·금리환경)
  ② 퀵윈 국가가 왜 우선인지(엔진 랭킹·사분면 근거로 해석)
  ③ 권역 공통 리스크 1~2개(규제 변화·캡티브 집중·지정학 등)
  ④ 단계적 진입 시퀀스 제안(예: A국 렌팅 우선 → B국 확장)
- 엔진이 준 숫자와 모순되지 않게. 숫자를 새로 만들지 말 것.

[2] region_primary_risk (권역 주요 리스크 1줄)
- 요약 카드용 한 줄. {title, detail} 형태. 가장 시급한 권역 리스크.

[3] region_news (권역 뉴스 배열 — 권역 + 글로벌)
- 최근 6개월 내, 권역 전체 또는 글로벌 차원에서 권역에 영향 주는 뉴스 4~10건.
- 각 객체: {date, title, summary(1문장), category, source, url, impact, scope, countries}
  - category: geopolitical | finance | auto_market | auto_finance | credit_abs
  - impact: positive | negative | neutral (진출 관점)
  - scope: region | global
    - region: 해당 권역에 한정된 동향(예: EU 규제, 권역 OEM 생산)
    - global: 권역을 넘어 전 세계 오토파이낸스/자동차/지정학에 파급되는 동향
      (예: 호르무즈 해협 긴장·유가, 글로벌 공급망·반도체, 美 기준금리, 환율,
       원자재·리튬, 글로벌 무역분쟁·관세)
  - countries: 영향받는 후보국 code 배열. 권역 전체면 ["ALL"], 글로벌이면 ["GLOBAL"].
- 구성 권장: 권역 뉴스 3~6건 + 글로벌 뉴스 2~4건 (글로벌은 권역 진출에 실질적 함의가
  있는 것만 — 단순 헤드라인 X, "왜 이 권역에 중요한지"가 summary에 드러나야 함).
- ★ category별 지정 출처에서만 인용. 아래 [뉴스 출처 가이드] 준수.
  출처 불명·블로그성 기사 제외. source(매체명)·url 필수.

[출력 형식]
{
  "region": "{REGION}",
  "baseline": "{BASELINE}",
  "schema_version": "1.0",
  "generated_by": "ai",
  "region_insight": "...",
  "region_primary_risk": {"title": "...", "detail": "..."},
  "region_news": [
    {"date": "...", "title": "...", "summary": "...", "category": "geopolitical",
     "source": "...", "url": "...", "impact": "negative", "scope": "region", "countries": ["ALL"]},
    {"date": "...", "title": "호르무즈 해협 긴장 고조로 유가 급등", "summary": "유가 상승이 권역 신차 수요·할부 연체에 미치는 함의", "category": "geopolitical",
     "source": "...", "url": "...", "impact": "negative", "scope": "global", "countries": ["GLOBAL"]}
  ]
}
```

---

## 3. 뉴스 출처 가이드 (category → 지정 매체)

country_prompt.md와 **동일 출처**를 사용한다. 권역 뉴스는 권역 전반 동향에 집중.

| category | 지정 출처 |
|---|---|
| **geopolitical** (지정학 리스크) | Reuters · Bloomberg · AP (Associated Press) |
| **finance** (거시·금융 리스크) | Financial Times (FT) · Wall Street Journal (WSJ) |
| **auto_market** (자동차 시장·OEM·생산·전동화) | Automotive News / Automotive News Europe · Just Auto · Ward's(WardsAuto) · 독일 Automobilwoche · Nikkei Asia |
| **auto_finance** (할부·리스·연체·중고잔가) | Auto Finance News · American Banker · Cox Automotive / Manheim(Manheim Used Vehicle Value Index) · S&P Global Mobility(구 IHS Markit) |
| **credit_abs** (신용·ABS 리스크, 정량) | Moody's · S&P · Fitch 의 auto loan ABS·딜린퀀시 리포트 |

★ 지정 출처 외 매체는 원칙적으로 제외.

---

## 4. 운영 팁
- **입력 순서**: country 조사 N개국 완료 → region_engine.py로 점수/랭킹 산출 → 그 요약을 {COUNTRY_SUMMARY}로 넣어 이 프롬프트 실행.
- **뉴스 최신성**: date 6개월 경과 뉴스는 교체. impact는 진출 관점(positive=진입 기회, negative=리스크).
- **병합**: 산출된 JSON의 region_insight/region_primary_risk/region_news를 region_engine 리포트에 병합(엔진이 자동생성한 region_insight는 AI본으로 대체 가능).
