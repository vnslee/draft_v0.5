#!/usr/bin/env python3
"""JSON 보고서 → HTML 동적 페이지 생성기
- 전체, 비즈니스, IT 탭
- 각 탭별 상세 정보 + 시각화
"""
import json, sys, os
from datetime import datetime

def load_report(json_path):
    with open(json_path, encoding="utf-8") as f:
        return json.load(f)

def render_html(report):
    target = report["target"]
    baseline = report["baseline"]
    created = report["created_at"]

    # 비즈니스 데이터
    biz = report["views"]["business"]["ranking"][0]
    it = report["views"]["it"]["ranking"][0]
    intg = report["views"]["integrated"]["ranking"][0]
    gates = report["gate_result"][target]["checks"]
    dd = report["due_diligence"]

    # HTML 생성
    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>오토파이낸스 진출 분석 | {target} vs {baseline}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f5f7fa; color: #333; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}

        /* 헤더 */
        .header {{ background: white; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        .header h1 {{ font-size: 28px; margin-bottom: 10px; }}
        .meta {{ display: flex; gap: 30px; font-size: 14px; color: #666; }}
        .meta-item {{ display: flex; flex-direction: column; }}
        .meta-label {{ font-weight: 600; color: #333; margin-bottom: 4px; }}

        /* 탭 */
        .tabs {{ display: flex; gap: 0; background: white; border-radius: 8px 8px 0 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        .tab {{ flex: 1; padding: 16px; text-align: center; cursor: pointer; border: none; background: #f5f7fa; font-size: 16px; font-weight: 500; transition: all 0.3s; }}
        .tab:hover {{ background: #e8ecf1; }}
        .tab.active {{ background: white; color: #0066cc; border-bottom: 3px solid #0066cc; }}

        /* 콘텐츠 */
        .tab-content {{ display: none; background: white; border-radius: 0 0 8px 8px; padding: 30px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        .tab-content.active {{ display: block; }}

        /* 카드 */
        .card {{ background: #f5f7fa; border-radius: 8px; padding: 20px; margin-bottom: 20px; }}
        .card h3 {{ font-size: 18px; margin-bottom: 15px; }}

        /* 스코어 */
        .score-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 20px; }}
        .score-box {{ background: white; padding: 20px; border-radius: 8px; border-left: 4px solid #0066cc; }}
        .score-label {{ font-size: 14px; color: #666; margin-bottom: 8px; }}
        .score-value {{ font-size: 32px; font-weight: bold; color: #0066cc; }}
        .score-note {{ font-size: 12px; color: #999; margin-top: 8px; }}

        /* 게이트 */
        .gate-check {{ display: flex; align-items: center; padding: 12px; margin-bottom: 10px; background: #f0f9ff; border-radius: 6px; border-left: 3px solid #10b981; }}
        .gate-check.fail {{ background: #fef2f2; border-left-color: #ef4444; }}
        .gate-status {{ font-weight: 600; margin-right: 10px; }}
        .gate-status.pass {{ color: #10b981; }}
        .gate-status.fail {{ color: #ef4444; }}

        /* 기여도 */
        .contrib-item {{ border-bottom: 1px solid #e5e7eb; }}
        .contrib-item:last-child {{ border-bottom: none; }}
        .contrib-header {{ display: flex; justify-content: space-between; align-items: center; padding: 12px; cursor: pointer; user-select: none; transition: background 0.2s; }}
        .contrib-header:hover {{ background: #f9fafb; }}
        .contrib-header.active {{ background: #f0f7ff; }}
        .contrib-header-left {{ display: flex; align-items: center; gap: 10px; flex: 1; }}
        .contrib-toggle {{ font-size: 12px; color: #999; min-width: 20px; text-align: center; }}
        .contrib-name {{ flex: 1; font-weight: 500; }}
        .contrib-bar {{ width: 150px; height: 20px; background: #e5e7eb; border-radius: 4px; overflow: hidden; margin: 0 20px; }}
        .contrib-fill {{ height: 100%; background: #0066cc; transition: width 0.3s; }}
        .contrib-value {{ font-weight: 600; min-width: 60px; text-align: right; }}
        .contrib-body {{ display: none; padding: 12px 12px 12px 32px; background: #f9fafb; border-left: 3px solid #0066cc; }}
        .contrib-body.active {{ display: block; }}
        .contrib-detail {{ font-size: 13px; color: #555; margin-bottom: 8px; line-height: 1.5; }}
        .contrib-compare {{ font-size: 12px; color: #0066cc; margin-top: 8px; padding-top: 8px; border-top: 1px solid #e5e7eb; font-style: italic; }}

        /* DD */
        .dd-item {{ display: flex; gap: 15px; padding: 12px; background: #fff8e1; border-radius: 6px; margin-bottom: 10px; border-left: 3px solid #f59e0b; }}
        .dd-icon {{ font-size: 20px; }}
        .dd-content {{ flex: 1; }}
        .dd-title {{ font-weight: 600; margin-bottom: 4px; }}
        .dd-action {{ font-size: 12px; color: #666; }}

        /* 테이블 */
        table {{ width: 100%; border-collapse: collapse; }}
        th {{ background: #f5f7fa; padding: 12px; text-align: left; font-weight: 600; border-bottom: 2px solid #e5e7eb; }}
        td {{ padding: 12px; border-bottom: 1px solid #e5e7eb; }}
        tr:hover {{ background: #f9fafb; }}

        /* 색상 */
        .text-success {{ color: #10b981; }}
        .text-warning {{ color: #f59e0b; }}
        .text-danger {{ color: #ef4444; }}
        .badge {{ display: inline-block; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600; }}
        .badge-info {{ background: #dbeafe; color: #0c63e4; }}
        .badge-warning {{ background: #fef3c7; color: #92400e; }}
    </style>
</head>
<body>
    <div class="container">
        <!-- 헤더 -->
        <div class="header">
            <h1>🇵🇱 {target} 자동금융 진출 분석</h1>
            <div class="meta">
                <div class="meta-item">
                    <span class="meta-label">대상</span>
                    <span>{target}</span>
                </div>
                <div class="meta-item">
                    <span class="meta-label">베이스라인</span>
                    <span>{baseline}</span>
                </div>
                <div class="meta-item">
                    <span class="meta-label">지역</span>
                    <span>{report["region"]}</span>
                </div>
                <div class="meta-item">
                    <span class="meta-label">생성일</span>
                    <span>{created}</span>
                </div>
            </div>
        </div>

        <!-- 탭 -->
        <div class="tabs">
            <button class="tab active" data-tab="overview">📊 전체</button>
            <button class="tab" data-tab="business">💼 비즈니스</button>
            <button class="tab" data-tab="it">💻 IT</button>
        </div>

        <!-- 전체 탭 -->
        <div id="overview" class="tab-content active">
            {render_overview(intg, biz, it, gates, dd)}
        </div>

        <!-- 비즈니스 탭 -->
        <div id="business" class="tab-content">
            {render_business(biz, gates)}
        </div>

        <!-- IT 탭 -->
        <div id="it" class="tab-content">
            {render_it(it)}
        </div>
    </div>

    <script>
        document.addEventListener('DOMContentLoaded', function() {{
            // 탭 기능
            const tabs = document.querySelectorAll('.tab');
            tabs.forEach(tab => {{
                tab.addEventListener('click', function() {{
                    const tabName = this.getAttribute('data-tab');

                    // 모든 탭 콘텐츠 숨기기
                    document.querySelectorAll('.tab-content').forEach(c => {{
                        c.classList.remove('active');
                    }});

                    // 모든 탭 버튼 비활성화
                    document.querySelectorAll('.tab').forEach(t => {{
                        t.classList.remove('active');
                    }});

                    // 선택된 탭 표시
                    document.getElementById(tabName).classList.add('active');
                    this.classList.add('active');
                }});
            }});

            // 아코디언 기능 - 기여도 항목
            const headers = document.querySelectorAll('.contrib-header');
            headers.forEach(header => {{
                header.addEventListener('click', function() {{
                    const body = this.nextElementSibling;
                    const toggle = this.querySelector('.contrib-toggle');
                    const isActive = this.classList.contains('active');

                    // 다른 항목 닫기 (같은 섹션 내에서)
                    const parent = this.closest('.card');
                    if (parent) {{
                        parent.querySelectorAll('.contrib-header').forEach(h => {{
                            if (h !== this) {{
                                h.classList.remove('active');
                                h.nextElementSibling?.classList.remove('active');
                                h.querySelector('.contrib-toggle').textContent = '▶';
                            }}
                        }});
                    }}

                    // 현재 항목 토글
                    if (isActive) {{
                        this.classList.remove('active');
                        body?.classList.remove('active');
                        toggle.textContent = '▶';
                    }} else {{
                        this.classList.add('active');
                        body?.classList.add('active');
                        toggle.textContent = '▼';
                    }}
                }});
            }});
        }});
    </script>
</body>
</html>"""
    return html

def render_overview(intg, biz, it, gates, dd):
    html = """
    <!-- 사분면 & 점수 -->
    <div class="score-grid">
        <div class="score-box">
            <div class="score-label">📍 사분면</div>
            <div class="score-value" style="font-size: 24px;">""" + intg["quadrant"] + """</div>
        </div>
        <div class="score-box">
            <div class="score-label">매력도</div>
            <div class="score-value">""" + str(intg["attractiveness"]) + """</div>
        </div>
        <div class="score-box">
            <div class="score-label">진입난이도</div>
            <div class="score-value">""" + str(intg["difficulty"]) + """</div>
        </div>
        <div class="score-box">
            <div class="score-label">IT 유사도</div>
            <div class="score-value">""" + str(intg["similarity"]) + """%</div>
        </div>
    </div>

    <!-- 판정 -->
    <div class="card">
        <h3>📋 판정</h3>
        <p style="font-size: 16px; line-height: 1.6; color: #333;">""" + intg["verdict"] + """</p>
    </div>

    <!-- 게이트 체크 -->
    <div class="card">
        <h3>✅ 게이트 체크 (""" + str(len([g for g in gates if g["result"]=="PASS"])) + """/""" + str(len(gates)) + """ PASS)</h3>
    """
    for gate in gates:
        status_class = "pass" if gate["result"] == "PASS" else "fail"
        html += f"""
        <div class="gate-check {status_class}">
            <span class="gate-status {status_class}">{gate["result"]}</span>
            <span>{gate["item"]}</span>
            <span style="color: #999; font-size: 12px;">({gate.get('scope', 'N/A')})</span>
        </div>
        """
    html += """
    </div>

    <!-- Due Diligence -->
    <div class="card">
        <h3>⚠️ 추가 실사 항목 (""" + str(len(dd)) + """개)</h3>
    """
    for item in dd:
        html += f"""
        <div class="dd-item">
            <div class="dd-icon">⚠️</div>
            <div class="dd-content">
                <div class="dd-title">{item["item"]}</div>
                <div class="dd-action">{item["action"]}</div>
            </div>
            <span class="badge badge-warning">Tier {item["tier"]}</span>
        </div>
        """
    html += """
    </div>
    """
    return html

def render_business(biz, gates):
    html = f"""
    <div class="score-grid">
        <div class="score-box">
            <div class="score-label">매력도 점수</div>
            <div class="score-value">{biz["score"]}</div>
        </div>
        <div class="score-box">
            <div class="score-label">진입난이도</div>
            <div class="score-value">{biz["difficulty"]}</div>
        </div>
        <div class="score-box">
            <div class="score-label">사분면</div>
            <div class="score-value" style="font-size: 18px;">{biz["quadrant"]}</div>
        </div>
        <div class="score-box">
            <div class="score-label">신뢰도</div>
            <div class="score-value" style="font-size: 24px; color: #f59e0b;">{biz["confidence"]}</div>
        </div>
    </div>

    <!-- 게이트 -->
    <div class="card">
        <h3>✅ 비즈니스 게이트</h3>
    """
    for gate in gates:
        html += f"""
        <div class="gate-check" style="background: #f0f9ff; border-left-color: #10b981;">
            <span class="gate-status pass">{gate["result"]}</span>
            <span>{gate["item"]}</span>
        </div>
        """
    html += """
    </div>

    <!-- 기여도 -->
    <div class="card">
        <h3>📊 항목별 기여도</h3>
    """
    attr_items = [c for c in biz["contributions"] if c["axis"] == "attractiveness"]
    diff_items = [c for c in biz["contributions"] if c["axis"] == "difficulty"]

    html += "<h4 style='margin-top: 15px; margin-bottom: 10px; color: #10b981;'>📈 매력도 (Attractiveness)</h4>"
    for item in attr_items:
        html += f"""
        <div class="contrib-item">
            <div class="contrib-header">
                <div class="contrib-header-left">
                    <span class="contrib-toggle">▶</span>
                    <div>
                        <div class="contrib-name">{item["item"]}</div>
                    </div>
                </div>
                <div class="contrib-bar">
                    <div class="contrib-fill" style="width: {item['normalized']}%;"></div>
                </div>
                <div class="contrib-value">{item["weighted"]}</div>
            </div>
            <div class="contrib-body">
                <div class="contrib-detail">{item["insight_detail"]}</div>
                <div class="contrib-compare">{item["insight_compare"]}</div>
            </div>
        </div>
        """

    html += "<h4 style='margin-top: 15px; margin-bottom: 10px; color: #ef4444;'>📉 진입난이도 (Difficulty)</h4>"
    for item in diff_items:
        html += f"""
        <div class="contrib-item">
            <div class="contrib-header">
                <div class="contrib-header-left">
                    <span class="contrib-toggle">▶</span>
                    <div>
                        <div class="contrib-name">{item["item"]}</div>
                    </div>
                </div>
                <div class="contrib-bar">
                    <div class="contrib-fill" style="width: {item['normalized']}%; background: #ef4444;"></div>
                </div>
                <div class="contrib-value">{item["weighted"]}</div>
            </div>
            <div class="contrib-body">
                <div class="contrib-detail">{item["insight_detail"]}</div>
                <div class="contrib-compare">{item["insight_compare"]}</div>
            </div>
        </div>
        """
    html += """
    </div>
    """
    return html

def render_it(it):
    html = f"""
    <div class="score-grid">
        <div class="score-box">
            <div class="score-label">베이스라인 대비 유사도</div>
            <div class="score-value">{it["similarity"]}%</div>
        </div>
        <div class="score-box">
            <div class="score-label">비용 절감률</div>
            <div class="score-value" style="color: #10b981;">{int(it["cost"]["discount"]*100)}%</div>
        </div>
        <div class="score-box">
            <div class="score-label">구축 비용</div>
            <div class="score-value">£{it["cost"]["build"]}M</div>
        </div>
        <div class="score-box">
            <div class="score-label">구축 기간</div>
            <div class="score-value">{it["cost"]["months"]}개월</div>
        </div>
    </div>

    <!-- 비용 상세 -->
    <div class="card">
        <h3>💰 비용 분석</h3>
        <table>
            <tr>
                <th>항목</th>
                <th>값</th>
            </tr>
            <tr>
                <td>베이스라인 구축비</td>
                <td>£{it["cost"]["baseline_build"]}M</td>
            </tr>
            <tr>
                <td>할인율</td>
                <td>{int(it["cost"]["discount"]*100)}%</td>
            </tr>
            <tr>
                <td>최종 구축비</td>
                <td style="font-weight: 600;">£{it["cost"]["build"]}M</td>
            </tr>
            <tr>
                <td>구축 기간</td>
                <td>{it["cost"]["months"]}개월</td>
            </tr>
            <tr>
                <td>연간 유지비</td>
                <td>£{it["cost"]["maintenance_yr"]}M</td>
            </tr>
        </table>
    </div>

    <!-- 기여도 -->
    <div class="card">
        <h3>📊 기술 항목별 유사도</h3>
    """
    for item in it["contributions"]:
        flag_badge = f"<span class='badge badge-warning' style='margin-left: 10px;'>{item['flag']}</span>" if item.get("flag") else ""
        html += f"""
        <div class="contrib-item">
            <div class="contrib-header">
                <div class="contrib-header-left">
                    <span class="contrib-toggle">▶</span>
                    <div>
                        <div class="contrib-name">{item["item"]}{flag_badge}</div>
                    </div>
                </div>
                <div class="contrib-bar">
                    <div class="contrib-fill" style="width: {item['match']}%;"></div>
                </div>
                <div class="contrib-value">{item["match"]}%</div>
            </div>
            <div class="contrib-body">
                <div class="contrib-detail">{item["insight_detail"]}</div>
                <div class="contrib-compare">{item["insight_compare"]}</div>
            </div>
        </div>
        """
    html += """
    </div>
    """
    return html

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법: python3 gen_report_html.py <report_json_path> [output_html_path]")
        sys.exit(1)

    json_path = sys.argv[1]
    html_path = sys.argv[2] if len(sys.argv) > 2 else json_path.replace(".json", ".html")

    print(f"📄 JSON 읽기: {json_path}")
    report = load_report(json_path)

    print("🎨 HTML 생성 중...")
    html = render_html(report)

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ 완료: {html_path}")
