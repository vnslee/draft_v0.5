# data 폴더 — 파일 구성 & Naming 규칙

오토파이낸스 진출 추천 엔진의 데이터 저장 규칙. 모든 데이터는 **버전 스냅샷**으로 쌓이며, 화면은 `*_latest.json`만 읽는다.

---

## 1. 폴더 구조

```
data/
├── country/                      국가별 외부 리서치 데이터 (조사 버튼으로 갱신)
│   ├── PL/
│   │   ├── PL_2026-06-18T1432.json
│   │   ├── PL_2026-05-02T0910.json
│   │   └── PL_latest.json        ← 최신 포인터 (화면이 읽음)
│   ├── VN/
│   │   ├── VN_2026-06-10T0800.json
│   │   └── VN_latest.json
│   └── UK/                        베이스라인국도 동일 구조 (is_baseline:true)
│       ├── UK_2026-06-01T0900.json
│       └── UK_latest.json
│
├── internal/                     자사 자산·계산 파라미터 (사람이 관리)
│   ├── internal_v1.2_2026-06-01.json
│   ├── internal_v1.1_2026-03-15.json
│   └── internal_latest.json      ← 최신 포인터
│
└── report/                       추천 결과 (추천 실행으로 생성, 출력물)
    ├── rpt_2026-06-18T1500.json
    ├── rpt_2026-06-10T0930.json
    └── rpt_latest.json            ← 최신 포인터
```

---

## 2. Naming 규칙

### 2-1. 국가 식별 = ISO 3166-1 alpha-2 코드
- 폴더·파일 모두 **2자리 국가코드 대문자** 사용: `PL`(폴란드), `VN`(베트남), `UK`(영국), `US`(미국), `KR`(한국).
- 국가명(한글·영문) 대신 코드를 쓰는 이유: 짧고, 충돌 없고, 정렬 깔끔.
- country JSON 내부에도 `"code": "PL"` 필드를 둬 **파일명과 내용이 매칭**되게 한다.

### 2-2. country 스냅샷
```
country/<CODE>/<CODE>_<FETCHED_AT>.json
예) country/PL/PL_2026-06-18T1432.json
```
- `<FETCHED_AT>` = 조사 시각, **정렬 가능한 형식** `YYYY-MM-DDTHHmm` (콜론 없이 시·분 붙여씀).
  - 콜론(`:`)은 일부 OS에서 파일명 금지 문자 → 제거.
  - 사전순 정렬 = 시간순 정렬이 되도록 ISO 순서 유지.
- 조사 버튼 1회 = 스냅샷 1개 생성 + `<CODE>_latest.json` 갱신.

### 2-3. internal 스냅샷
```
internal/internal_v<MAJOR>.<MINOR>_<DATE>.json
예) internal/internal_v1.2_2026-06-01.json
```
- 시맨틱 버전 + 날짜(`YYYY-MM-DD`).
  - **MINOR 업**: 자산 추가(진출국 발생)·파라미터 값 변경 (예: v1.2 → v1.3)
  - **MAJOR 업**: 구조 변경(필드 추가/삭제) (예: v1.x → v2.0)
- 갱신 때마다 스냅샷 1개 + `internal_latest.json` 갱신.

### 2-4. 최신 포인터
- 화면·계산은 항상 `*_latest.json`을 읽는다 (최신 스냅샷의 복사본).
- 과거 스냅샷은 이력·버전 비교·추천 도장 추적용으로만 보관.

### 2-5. report (추천 결과 / 출력물)
```
report/rpt_<CREATED_AT>.json
예) report/rpt_2026-06-18T1500.json
```
- country·internal이 **입력**이라면 report는 그것들을 계산한 **출력**.
- `<CREATED_AT>` = 추천 산출 시각, country와 동일한 정렬형(`YYYY-MM-DDTHHmm`).
- 추천 실행 1회 = 스냅샷 1개 + `rpt_latest.json` 갱신.
- 내부 `based_on`에 사용된 country 버전들 + internal 버전을 박아 **재현성** 확보.
- 보고서 3종(Business·IT·통합)은 파일을 쪼개지 않고 **한 report에 담아 화면에서 뷰 전환** (데이터는 하나, 뷰는 여럿 원칙).

report JSON 핵심 필드:
```json
{
  "report_id": "rpt_2026-06-18T1500",
  "created_at": "2026-06-18T15:00:00+09:00",
  "target_segment": "개인 신차",
  "based_on": {                                  // ★ 재현성 도장
    "country_versions": { "PL": "PL_2026-06-18T1432", "VN": "VN_2026-06-10T0800" },
    "internal_version": "internal_v1.2_2026-06-01",
    "schema_version": "1.0"
  },
  "gate_failed": [ { "code": "XX", "reason": "외환 송금 봉쇄", "tier": 1 } ],
  "ranking": [
    { "code": "PL", "rank": 1, "attractiveness": 78, "difficulty": 42,
      "similarity": 76,
      "cost": { "build": 3500, "months": 12, "discount": 0.30, "baseline": "UK" },
      "confidence": "중", "quadrant": "선별 진출" }
  ],
  "due_diligence": [ { "code": "PL", "item": "캡티브 점유율", "tier": 3, "action": "협회 통계 확인" } ]
}
```

---

## 3. 버전 트리거 요약

| 데이터 | 새 버전 생기는 계기 | 갱신 주체 | 파일명 키 |
|---|---|---|---|
| country | 조사 버튼 (국가별·독립) | AI 리서치 | `<CODE>_<FETCHED_AT>` |
| internal | 진출/자산 추가·파라미터 변경 | 사람(PMO·재무) | `v<MAJOR>.<MINOR>_<DATE>` |
| report | 추천 실행 | 엔진(계산) | `rpt_<CREATED_AT>` |

---

## 4. 아티팩트 데모 주의

React 아티팩트는 파일시스템·localStorage 사용 불가 → 실제 폴더 누적 안 됨.
데모에서는 메모리(state)로 동일 구조를 흉내:

```js
versions = {
  "PL": [
    { id: "PL_2026-06-18T1432", fetchedAt: "2026-06-18T14:32+09:00", data: {...} },
    { id: "PL_2026-05-02T0910", fetchedAt: "...", data: {...} }
  ],
  "VN": [ ... ]
};
internalVersions = [
  { id: "internal_v1.2_2026-06-01", data: {...} }
];
```
- 조사 = 해당 국가 배열에 push (최신이 화면, 과거는 드롭다운)
- `latest` = 각 배열의 최신(또는 선택) 항목
- 새로고침 시 소멸 — 데모용. 실제 배포(자체 서버)에선 위 폴더 구조가 정석.

---

## 5. 국가코드 참조 (자주 쓰는 것)

| 코드 | 국가 | 권역 |
|---|---|---|
| UK | 영국 | EU (베이스라인) |
| US | 미국 | AMERICAS (베이스라인) |
| KR | 한국 | APAC |
| AU | 호주 | APAC (베이스라인) |
| PL | 폴란드 | EU |
| VN | 베트남 | APAC |
| MX | 멕시코 | AMERICAS |
| DE | 독일 | EU |
| ID | 인도네시아 | APAC |
| BR | 브라질 | AMERICAS |

## 6. 기타
> sample 폴더는 말그대로 샘플 데이터 이므로 참고만 하고, 실제 데이터로 사용하지 않음