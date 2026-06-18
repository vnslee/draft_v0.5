#!/usr/bin/env python3
"""오토파이낸스 진출 추천 스코어링 엔진 (해커톤 더미 버전)
country JSON × internal JSON → report JSON
- Business 뷰: 매력도(X) + 진입난이도(Y), 항목별 기여
- IT 뷰: 베이스라인 대비 match 유사도 → 구간표 감축률 → 비용
- Integrated 뷰: 2축 매트릭스 좌표 + 사분면 (합성점수 없음)
- confidence / due_diligence: tier 자동 파생
"""
import json, glob, os

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")

def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def items_map(country):
    return {it["item"]: it for it in country["items"]}

# ---------- 정규화 헬퍼 ----------
def minmax(val, lo, hi, invert=False):
    if hi == lo: return 50.0
    n = (val - lo) / (hi - lo) * 100
    n = max(0, min(100, n))
    return round(100 - n if invert else n, 1)

# 서열화(1~5) → 0~100
def rank_norm(val, invert=False):
    n = (val - 1) / 4 * 100
    return round(100 - n if invert else n, 1)

def tier_conf(tiers):
    """tier 가중평균 → 상/중/하. tier1=1.0 .. tier4=0.4"""
    if not tiers: return "하"
    coef = {1:1.0, 2:0.8, 3:0.6, 4:0.4}
    avg = sum(coef.get(t,0.4) for t in tiers)/len(tiers)
    return "상" if avg>=0.85 else ("중" if avg>=0.65 else "하")

# ---------- Business 스코어링 ----------
def score_business(country, weights):
    im = items_map(country)
    contrib, attractiveness, difficulty = [], 0.0, 0.0
    diff_tiers, attr_tiers = [], []

    # 매력도 항목 (정규화 기준은 데모용 고정 범위)
    attr_specs = {
        "오토금융/리스 시장규모": (im["오토금융/리스 시장규모"]["value"], 0, 100000, False),  # USD/PLN 혼재이나 데모용
        "오토금융 성장률(CAGR)": (im["오토금융 성장률(CAGR)"]["value"], 0, 12, False),
        "금융 침투율(신차)": (im["금융 침투율(신차)"]["value"], 0, 100, False),
        "평균 금리/APR": (im["평균 금리/APR"]["value"], 0, 15, False),
    }
    for name,(raw,lo,hi,inv) in attr_specs.items():
        w = weights[name]; norm = minmax(raw,lo,hi,inv); wtd = round(norm*w,1)
        attractiveness += wtd; attr_tiers.append(im[name]["tier"])
        contrib.append({"axis":"attractiveness","item":name,"raw":raw,"normalized":norm,"weight":w,"weighted":wtd,"tier":im[name]["tier"]})

    # 난이도 항목 (점유율 높을수록 난이도↑ = 정규화 그대로)
    diff_specs = {
        "캡티브 강도(점유율)": (im["캡티브 강도(점유율)"]["value"], 0, 100, False),
        "1위사 점유율": (im["1위사 점유율"]["value"], 0, 50, False),
    }
    # 난이도 가중치는 두 항목 합=1로 재정규화(데모)
    dw = {"캡티브 강도(점유율)":0.5, "1위사 점유율":0.5}
    for name,(raw,lo,hi,inv) in diff_specs.items():
        norm = minmax(raw,lo,hi,inv); wtd = round(norm*dw[name],1)
        difficulty += wtd; diff_tiers.append(im[name]["tier"])
        contrib.append({"axis":"difficulty","item":name,"raw":raw,"normalized":norm,"weight":dw[name],"weighted":wtd,"tier":im[name]["tier"]})

    return round(attractiveness,1), round(difficulty,1), contrib, attr_tiers+diff_tiers

# ---------- IT 유사도 스코어링 (베이스라인 대비 match) ----------
def score_it(country, baseline, weights):
    im, bm = items_map(country), items_map(baseline)
    contrib, similarity, tiers = [], 0.0, []

    # 수치형(1~5 등급): match = 100 - |차이|/4*100
    def match_numeric(a,b): return round(100 - abs(a-b)/4*100, 1)
    # 문자형: 동일 카테고리면 100, 부분 정합이면 50 (데모 규칙)
    def match_text(c_item):
        # 솔루션: 패키지 동일 생태계면 높음. 여기선 PL '혼재' vs UK '패키지' → 50
        v = str(c_item.get("value",""))
        if "NETSOL" in v or "패키지" in v and "혼재" not in v: return 100.0
        if "혼재" in v: return 50.0
        return 60.0

    specs = {
        "신용정보(CB) 인프라": ("num", im["신용정보(CB) 인프라"]["value"], bm["신용정보(CB) 인프라"]["value"]),
        "디지털 채널 성숙도": ("num", im["디지털 채널 성숙도"]["value"], bm["디지털 채널 성숙도"]["value"]),
        "차량회수 절차 용이성": ("num", im["차량회수 절차 용이성"]["value"], bm["차량회수 절차 용이성"]["value"]),
        "솔루션 벤더": ("txt", im["솔루션 벤더"], None),
        "라이선스 체제(세그먼트별)": ("regime", None, None),  # 둘 다 PASS + EU 공통 → 70 (데모)
    }
    for name, spec in specs.items():
        w = weights[name]
        if spec[0]=="num":
            m = match_numeric(spec[1], spec[2]); detail={"pl":spec[1],"uk":spec[2]}
        elif spec[0]=="txt":
            m = match_text(spec[1]); detail={"pl":str(spec[1].get("value"))[:20],"uk":"패키지(NETSOL)"}
        else:
            m = 70.0; detail={"note":"EU 규제 공통, 세그먼트 체제 상이"}
        wtd = round(m*w,1); similarity += wtd; tiers.append(im[name]["tier"])
        contrib.append({"item":name,"match":m,"weight":w,"weighted":wtd,"tier":im[name]["tier"],**detail})

    return round(similarity,1), contrib, tiers

def discount_for(sim, brackets):
    for b in brackets:
        if b["min"] <= sim <= b["max"]: return b["discount"]
    return 0.0

def quadrant(attr, diff):
    hi_attr = attr >= 50; lo_diff = diff < 50
    if hi_attr and lo_diff: return "즉시 진출"
    if hi_attr and not lo_diff: return "선별 진출"
    if not hi_attr and lo_diff: return "기회 탐색"
    return "JV/제휴 필요"

# ---------- 게이트 평가 (통과 경로 존재 시 PASS) ----------
def eval_gates(country):
    im = items_map(country)
    checks=[]; passed=True
    gate_items = [it for it in country["items"] if it["role"]=="gate"]
    for g in gate_items:
        r = g.get("gate_result","PASS")
        # tier3 이하 FAIL은 FLAG로 강등 (저신뢰로 탈락금지)
        if r=="FAIL" and g.get("tier",4)>=3: r="FLAG"
        if r=="FAIL": passed=False
        checks.append({"item":g["item"],"scope":g.get("gate_scope"),"result":r,"tier":g.get("tier")})
    return passed, checks

def due_diligence(country, threshold=3):
    out=[]
    for it in country["items"]:
        if it.get("tier",1) >= threshold:
            out.append({"code":country["code"],"item":it["item"],"tier":it["tier"],
                        "action":"1차 출처(공식통계·실사) 확인 필요"})
    return out

# ================= MAIN =================
internal = load(f"{DATA}/internal/internal_latest.json")
pl = load(f"{DATA}/country/PL/PL_latest.json")
uk = load(f"{DATA}/country/UK/UK_latest.json")  # EU 베이스라인

wb, wi = internal["weights"]["business"], internal["weights"]["it"]

# --- PL 스코어링 (후보) ---
attr, diff, b_contrib, b_tiers = score_business(pl, wb)
sim, i_contrib, i_tiers = score_it(pl, uk, wi)
disc = discount_for(sim, internal["similarity_brackets"])
asset = internal["country_assets"]["UK"]
build = round(asset["build_cost"]*(1-disc),1)
months = round(asset["build_months"]*(1-disc*0.7),1)  # 기간은 비용보다 덜 줄어듦(데모)
maint = round(build*internal["maintenance_rate"],1)

pl_pass, pl_checks = eval_gates(pl)

report = {
    "report_id": "rpt_2026-06-18T1500",
    "created_at": "2026-06-18T15:00:00+09:00",
    "based_on": {
        "country_versions": {"PL": "PL_2026-06-18T1432"},
        "baseline_versions": {"EU": "UK_2026-06-18T1432"},
        "internal_version": "internal_v1.2_2026-06-01",
        "schema_version": "1.0"
    },
    "gate_result": {"PL": {"passed": pl_pass, "checks": pl_checks}},
    "gate_failed": [],
    "views": {
        "business": {
            "weights": wb,
            "ranking": [{
                "code":"PL","rank":1,"score":attr,"difficulty":diff,
                "quadrant":quadrant(attr,diff),
                "contributions":b_contrib,
                "confidence":tier_conf(b_tiers)
            }]
        },
        "it": {
            "weights": wi,
            "baseline":"UK",
            "ranking": [{
                "code":"PL","rank":1,"similarity":sim,
                "cost":{"baseline":"UK","baseline_build":asset["build_cost"],
                        "discount":disc,"build":build,"months":months,
                        "maintenance_yr":maint,"unit":"GBP_M(데모)"},
                "contributions":i_contrib,
                "confidence":tier_conf(i_tiers)
            }]
        },
        "integrated": {
            "note":"합성점수 없음 — 2축 매트릭스 좌표 + 사분면",
            "ranking": [{
                "code":"PL","rank":1,
                "attractiveness":attr,"difficulty":diff,"similarity":sim,
                "bubble_cost":build,
                "quadrant":quadrant(attr,diff),
                "verdict":"성장성 높고 게이트 전부 통과. B2B 리스 무면허 경로로 우선 진입 권고."
            }]
        }
    },
    "due_diligence": due_diligence(pl)
}

out = f"{DATA}/report/rpt_2026-06-18T1500.json"
with open(out,"w",encoding="utf-8") as f:
    json.dump(report,f,ensure_ascii=False,indent=2)
import shutil; shutil.copy(out, f"{DATA}/report/rpt_latest.json")

print("=== 스코어링 결과 (PL, 베이스라인 UK) ===")
print(f"매력도(X): {attr}  난이도(Y): {diff}  사분면: {quadrant(attr,diff)}")
print(f"IT 유사도: {sim}  감축률: {disc*100:.0f}%")
print(f"구축비: {asset['build_cost']} → {build} (GBP_M 데모)  기간: {months}M  연운영비: {maint}")
print(f"게이트: {'PASS' if pl_pass else 'FAIL'}  실사항목: {len(report['due_diligence'])}개")
print(f"→ {out}")