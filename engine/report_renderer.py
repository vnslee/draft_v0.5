#!/usr/bin/env python3
"""동적 보고서 HTML 렌더링 엔진 v1.0
- JSON 보고서를 Jinja2 템플릿으로 HTML로 변환
- 현대캐피탈 CI 기반 Kinetic Enterprise 디자인 적용
"""
import json, os, sys
from jinja2 import Environment, FileSystemLoader

BASE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE)
TEMPLATES_DIR = os.path.join(PROJECT_ROOT, "report", "templates")
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)

def format_number(val, decimals=1):
    """숫자 포맷팅 (1000.5 -> 1,000.5)"""
    if not isinstance(val, (int, float)):
        return str(val)
    if decimals > 0:
        return f"{val:,.{decimals}f}"
    else:
        return f"{int(val):,}"

def get_tier_color(tier):
    """Tier 레벨에 따른 색상 반환"""
    return {1: "success", 2: "info", 3: "warning", 4: "error"}.get(tier, "secondary")

def get_tier_label(tier):
    """Tier 레벨에 따른 신뢰도 라벨"""
    return {1: "높음", 2: "중간", 3: "낮음", 4: "매우낮음"}.get(tier, "미정")

def get_quadrant_emoji(quadrant):
    """사분면에 따른 이모지"""
    return {
        "즉시 진출": "🚀",
        "선별 진출": "⚡",
        "기회 탐색": "🔍",
        "JV/제휴 필요": "🤝"
    }.get(quadrant, "📊")

def render_report(report_path, output_path=None):
    """JSON 보고서를 HTML로 렌더링"""
    report = load(report_path)

    # 템플릿 환경 설정
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
    env.filters['format_num'] = format_number
    env.filters['tier_color'] = get_tier_color
    env.filters['tier_label'] = get_tier_label
    env.filters['quadrant_emoji'] = get_quadrant_emoji

    template = env.get_template("report_template.html")

    # 렌더링
    html = template.render(report=report)

    # 출력 경로 결정
    if output_path is None:
        report_id = report.get("report_id", "report")
        output_path = os.path.join(PROJECT_ROOT, "report", "samples", f"{report_id}.html")

    # 출력 디렉토리 생성
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✓ 보고서 렌더링 완료: {output_path}")
    return output_path

if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("사용법: python3 report_renderer.py <보고서JSON경로> [출력경로]")

    report_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None

    if not os.path.exists(report_path):
        raise SystemExit(f"[오류] 보고서 파일을 찾을 수 없음: {report_path}")

    render_report(report_path, output_path)
