#!/usr/bin/env python3
"""FastAPI 백엔드 서버 - 동적 보고서 렌더링 & 데이터 제공
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import json
import os
import sys
from pathlib import Path

# 프로젝트 경로 설정
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
REPORT_DIR = PROJECT_ROOT / "report"
ENGINE_DIR = PROJECT_ROOT / "engine"

# 동적 import를 위해 경로 추가
sys.path.insert(0, str(ENGINE_DIR))
from report_renderer import render_report

app = FastAPI(
    title="Hyundai Capital Global Market Entry API",
    description="동적 보고서 렌더링 및 시장 진출 분석 API",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def load_json(path):
    """JSON 파일 로드"""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return None

# ============================================================================
# 데이터 API
# ============================================================================

@app.get("/api/data/country/{code}")
def get_country_data(code: str, version: str = None):
    """국가별 데이터 조회"""
    code = code.upper()
    if version:
        path = DATA_DIR / "country" / code / f"{code}_{version}.json"
    else:
        path = DATA_DIR / "country" / code / f"{code}_latest.json"

    data = load_json(path)
    if data is None:
        raise HTTPException(status_code=404, detail=f"국가 {code} 데이터를 찾을 수 없습니다")
    return data

@app.get("/api/data/internal")
def get_internal_data():
    """내부 공통 데이터 조회 (가중치, 규칙 등)"""
    path = DATA_DIR / "internal" / "internal_latest.json"
    data = load_json(path)
    if data is None:
        raise HTTPException(status_code=404, detail="내부 데이터를 찾을 수 없습니다")
    return data

@app.get("/api/data/schema/country")
def get_country_schema():
    """국가 데이터 스키마 조회"""
    path = DATA_DIR / "schema" / "country_schema.md"
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return {"content": f.read(), "format": "markdown"}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="스키마를 찾을 수 없습니다")

# ============================================================================
# 보고서 API
# ============================================================================

@app.get("/api/report/country/{code}", response_class=HTMLResponse)
def get_country_report(code: str, version: str = None):
    """국가 진단 보고서 조회 (HTML)"""
    code = code.upper()

    # 보고서 JSON 찾기
    if version:
        report_path = REPORT_DIR / "country" / code / f"{code}_rpt_{version}.json"
    else:
        # 최신 보고서 찾기
        country_dir = REPORT_DIR / "country" / code
        if not country_dir.exists():
            raise HTTPException(status_code=404, detail=f"국가 {code}의 보고서가 없습니다")

        reports = sorted(country_dir.glob(f"{code}_rpt_*.json"), reverse=True)
        if not reports:
            raise HTTPException(status_code=404, detail=f"국가 {code}의 보고서가 없습니다")
        report_path = reports[0]

    if not report_path.exists():
        raise HTTPException(status_code=404, detail="보고서를 찾을 수 없습니다")

    # HTML 렌더링
    try:
        report_json = load_json(report_path)
        if not report_json:
            raise HTTPException(status_code=500, detail="보고서 로드 실패")

        # Jinja2 렌더링
        from jinja2 import Environment, FileSystemLoader

        env = Environment(loader=FileSystemLoader(PROJECT_ROOT / "report" / "templates"))

        # 필터 등록
        env.filters['format_num'] = lambda v, d=1: f"{int(v):,}" if d == 0 else f"{v:,.{d}f}"
        env.filters['tier_color'] = lambda t: {1: "success", 2: "info", 3: "warning", 4: "error"}.get(t, "secondary")
        env.filters['tier_label'] = lambda t: {1: "높음", 2: "중간", 3: "낮음", 4: "매우낮음"}.get(t, "미정")
        env.filters['quadrant_emoji'] = lambda q: {"즉시 진출": "🚀", "선별 진출": "⚡", "기회 탐색": "🔍", "JV/제휴 필요": "🤝"}.get(q, "📊")

        template = env.get_template("report_template.html")
        html = template.render(report=report_json)

        return html
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"보고서 렌더링 실패: {str(e)}")

@app.get("/api/report/country/{code}/json")
def get_country_report_json(code: str, version: str = None):
    """국가 진단 보고서 조회 (JSON)"""
    code = code.upper()

    if version:
        report_path = REPORT_DIR / "country" / code / f"{code}_rpt_{version}.json"
    else:
        country_dir = REPORT_DIR / "country" / code
        if not country_dir.exists():
            raise HTTPException(status_code=404, detail=f"국가 {code}의 보고서가 없습니다")

        reports = sorted(country_dir.glob(f"{code}_rpt_*.json"), reverse=True)
        if not reports:
            raise HTTPException(status_code=404, detail=f"국가 {code}의 보고서가 없습니다")
        report_path = reports[0]

    if not report_path.exists():
        raise HTTPException(status_code=404, detail="보고서를 찾을 수 없습니다")

    data = load_json(report_path)
    if data is None:
        raise HTTPException(status_code=500, detail="보고서 로드 실패")

    return data

@app.get("/api/report/available-countries")
def get_available_countries():
    """사용 가능한 국가 목록"""
    countries = {}
    country_dir = REPORT_DIR / "country"

    if country_dir.exists():
        for code_dir in country_dir.iterdir():
            if code_dir.is_dir():
                code = code_dir.name
                reports = sorted(code_dir.glob(f"{code}_rpt_*.json"), reverse=True)
                if reports:
                    countries[code] = {
                        "code": code,
                        "latest": reports[0].name,
                        "versions": [r.name for r in reports]
                    }

    return {"countries": countries}

# ============================================================================
# 렌더링 API
# ============================================================================

@app.post("/api/render/report/{code}")
def render_country_report(code: str, version: str = None):
    """보고서 렌더링 요청"""
    code = code.upper()

    # 기존 보고서 JSON 찾기
    if version:
        report_path = REPORT_DIR / "country" / code / f"{code}_rpt_{version}.json"
    else:
        country_dir = REPORT_DIR / "country" / code
        if not country_dir.exists():
            raise HTTPException(status_code=404, detail=f"국가 {code}의 보고서가 없습니다")

        reports = sorted(country_dir.glob(f"{code}_rpt_*.json"), reverse=True)
        if not reports:
            raise HTTPException(status_code=404, detail=f"국가 {code}의 보고서가 없습니다")
        report_path = reports[0]

    if not report_path.exists():
        raise HTTPException(status_code=404, detail="보고서 JSON을 찾을 수 없습니다")

    try:
        # HTML로 렌더링
        output_path = REPORT_DIR / "samples" / f"{report_path.stem}.html"
        render_report(str(report_path), str(output_path))

        return {
            "status": "success",
            "report_id": report_path.stem,
            "html_path": str(output_path),
            "message": "보고서가 성공적으로 렌더링되었습니다"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"렌더링 실패: {str(e)}")

# ============================================================================
# 헬스 체크
# ============================================================================

@app.get("/health")
def health_check():
    """API 헬스 체크"""
    return {
        "status": "healthy",
        "service": "Hyundai Capital Market Entry API",
        "version": "1.0.0"
    }

@app.get("/")
def root():
    """API 루트"""
    return {
        "message": "Hyundai Capital Global Market Entry Analysis API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "health": "/health",
            "data": {
                "country": "/api/data/country/{code}",
                "internal": "/api/data/internal",
                "schema": "/api/data/schema/country"
            },
            "report": {
                "html": "/api/report/country/{code}",
                "json": "/api/report/country/{code}/json",
                "available": "/api/report/available-countries",
                "render": "POST /api/render/report/{code}"
            }
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
