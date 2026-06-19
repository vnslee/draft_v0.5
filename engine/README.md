# engine/ — 진단 보고서 엔진

## 엔진 구성

| 파일 | 역할 |
|---|---|
| `scoring_engine.py` | 단일 국가 스코어링 로직 (매력도·난이도·유사도 계산). 다른 엔진이 import해서 사용. 직접 실행하지 않음. |
| `region_engine.py` | 권역 퀵윈 스코어링. **진입점.** JSON 생성 후 렌더까지 자동 호출. |
| `region_render_engine.py` | 권역 리포트 JSON → HTML 렌더링. `region_engine.py`가 자동 호출하므로 독립 실행은 재렌더 시에만. |
| `templates/region_report.html` | HTML 렌더링 셸 템플릿 (PR2 디자인, 모달 구조). 레이아웃·디자인 수정 시 이 파일만 편집. |

---

## 실행 방법

### 기본 실행 (권역 보고서 생성)

```bash
# 작업 디렉토리: 레포 루트
python3 engine/region_engine.py <REGION>

# 예시
python3 engine/region_engine.py EU
```

실행 결과:
```
report/region/EU/EU_rpt_<YYYYMMDDTHHMM>.json   ← 데이터 스냅샷 (불변)
report/region/EU/EU_rpt_<YYYYMMDDTHHMM>.html   ← 렌더링된 보고서 (화면에 서빙)
report/region/EU/EU_rpt_latest.json            ← 최신 포인터
report/region/EU/index.json                    ← 버전 매니페스트 (자동 갱신)
```

### 확장 항목 포함 실행

```bash
python3 engine/region_engine.py EU "국외이전 제한" "법인세율"
```

### HTML만 재렌더 (JSON은 그대로, 템플릿·디자인 변경 반영)

```bash
python3 engine/region_render_engine.py EU
python3 engine/region_render_engine.py EU 2026-06-19T1200   # 특정 버전
```

---

## 지원 권역 코드

| 코드 | 권역 |
|---|---|
| `EU` | 유럽 |
| `AMERICAS` | 미주 |
| `APAC` | 아시아·태평양 |

---

## 백엔드 연동 가이드

### 1. CLI 호출 (subprocess)

```python
import subprocess, os

def generate_region_report(region: str) -> dict:
    """권역 보고서 생성. JSON + HTML 모두 산출."""
    repo_root = "/path/to/repo"
    result = subprocess.run(
        ["python3", "engine/region_engine.py", region],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr)
    # 생성된 HTML 경로는 index.json에서 확인
    return {"stdout": result.stdout}
```

### 2. Python 직접 import

```python
import sys
sys.path.insert(0, "/path/to/repo/engine")
import region_engine

region_engine.run("EU")
# 또는 확장 항목 포함
region_engine.run("EU", extra_items=["국외이전 제한"])
```

### 3. 버전 목록 조회

```python
import json, os

def get_versions(region: str) -> dict:
    """index.json 반환 — 드롭다운 소스."""
    path = f"report/region/{region}/index.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)
```

반환 예시:
```json
{
  "region": "EU",
  "latest": "EU_rpt_2026-06-19T1200",
  "versions": [
    {
      "report_id": "EU_rpt_2026-06-19T1200",
      "created_at": "2026-06-19T12:00:00+09:00",
      "file": "EU_rpt_2026-06-19T1200.json",
      "summary": {
        "candidate_count": 3,
        "quick_wins": ["ES", "DE"],
        "ranking": [...]
      }
    }
  ]
}
```

### 4. 보고서 HTML 서빙

```python
# FastAPI 예시
from fastapi import FastAPI
from fastapi.responses import FileResponse

app = FastAPI()

@app.get("/reports/{region}/{report_id}")
def serve_report(region: str, report_id: str):
    path = f"report/region/{region}/{report_id}.html"
    return FileResponse(path, media_type="text/html")
```

---

## 룰셋 수정 → 보고서 반영 흐름

퀵윈 가중치·임계값은 `data/internal/internal_latest.json`의 `quick_win_rules`에서 관리한다.
엔진 실행 시마다 이 파일을 읽으므로, 수정 후 보고서를 재생성하면 즉시 반영된다.

```
화면에서 룰셋 수정
→ PUT /api/internal/quick_win_rules  (internal_latest.json 업데이트)
→ POST /api/reports/{region}/run     (region_engine.py 실행)
→ 새 버전 HTML 생성 완료
```

수정 가능한 파라미터:

```json
{
  "quick_win_rules": {
    "weights": {
      "similarity": 0.4,       // 베이스라인 재사용률 가중치
      "attractiveness": 0.35,  // 시장 매력도 가중치
      "ease": 0.25             // 진입 용이성(100-난이도) 가중치
    },
    "thresholds": {
      "quick_win_score": 55,   // 퀵윈 최소 종합점수
      "min_similarity": 60,    // 최소 유사도
      "min_attractiveness": 40,// 최소 매력도
      "max_difficulty": 65     // 최대 허용 난이도
    }
  }
}
```

---

## 출력 파일 구조

```
report/region/
└── EU/
    ├── index.json                       # 버전 매니페스트 (백엔드가 읽어 드롭다운 구성)
    ├── EU_rpt_latest.json               # 최신 버전 JSON 포인터
    ├── EU_rpt_2026-06-19T1200.json      # 데이터 스냅샷 (불변)
    └── EU_rpt_2026-06-19T1200.html      # 렌더링된 보고서 (화면에 서빙)
```

- HTML은 버전별로만 생성 (`latest.html` 없음). 화면은 `index.json`으로 버전 목록을 구성하고 선택된 버전의 HTML을 서빙한다.
- JSON 스냅샷은 덮어쓰지 않는다. 같은 타임스탬프로 재실행하면 덮어쓴다.

---

## 의존성

```
Python 3.9+
표준 라이브러리만 사용 (json, os, sys, glob, shutil, html, datetime)
외부 패키지 없음
```

## 실행 환경

엔진은 **레포 루트를 기준**으로 경로를 계산한다. 반드시 레포 루트에서 실행하거나, subprocess `cwd`를 레포 루트로 지정해야 한다.

```bash
# 올바른 실행
cd /path/to/repo && python3 engine/region_engine.py EU

# subprocess에서
subprocess.run(["python3", "engine/region_engine.py", "EU"], cwd="/path/to/repo")
```
