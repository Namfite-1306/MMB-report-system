"""Adapters for members 1–4. Original handoff outputs remain in native_output."""
import copy
import datetime as dt
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def messages(items):
    return [x if isinstance(x, str) else x.get("message", json.dumps(x, ensure_ascii=False)) for x in items]


def envelope(request, name):
    return {"schema_version": "1.0", "run_id": request["run_id"], "module": name,
            "ticker": request["ticker"], "as_of_date": request["as_of_date"],
            "generated_at": now(), "status": "partial", "data": {},
            "sources": [], "warnings": [], "errors": []}


def canonical(request, name, native):
    out = envelope(request, name)
    out.update(status=native["status"], warnings=messages(native.get("warnings", [])),
               errors=messages(native.get("errors", [])), native_output=copy.deepcopy(native))
    out["data"] = copy.deepcopy(native.get("data") or {})
    out["sources"] = copy.deepcopy(native.get("sources", []))
    ids = {x["source_id"]: name + ":" + x["source_id"] for x in out["sources"]}
    ids.update({x["metric_id"]: name + ":" + x["metric_id"] for x in out["data"].get("metrics", [])})

    def rename(node):
        if isinstance(node, list):
            for item in node:
                rename(item)
        elif isinstance(node, dict):
            for key, value in node.items():
                if key in ("source_id", "metric_id") and isinstance(value, str):
                    node[key] = ids.get(value, value)
                elif key in ("source_refs", "evidence_refs") and isinstance(value, list):
                    node[key] = [ids.get(x, x) for x in value]
                else:
                    rename(value)
    rename(out["data"])
    rename(out["sources"])
    out["id_map"] = ids
    for key in ("metrics", "findings", "risks"):
        out["data"].setdefault(key, [])
    # Preserve records outside cutoff in native_output; omit them from usable tables.
    for key in ("metrics", "financials"):
        records = out["data"].get(key, [])
        kept = [r for r in records if r["period_end"] <= request["as_of_date"]]
        if len(kept) != len(records):
            out["warnings"].append(f"{key}: đã loại {len(records)-len(kept)} dòng sau ngày chốt; giữ trong native_output.")
        if key in out["data"]:
            out["data"][key] = kept
    valid_ids = {s["source_id"] for s in out["sources"]} | {m["metric_id"] for m in out["data"]["metrics"]}
    for key in ("findings", "risks"):
        out["data"][key] = [r for r in out["data"][key] if all(x in valid_ids for x in r.get("evidence_refs", []))]
    if out["warnings"] and out["status"] == "ok":
        out["status"] = "partial"
    return out


def macro(request):
    from macro_module.core import build_macro_result, load_json
    payload = {**request, "industry": request["industry_name"],
               "analysis_period": {"start_date": request["period_start"], "end_date": request["period_end"]}}
    native = build_macro_result(payload, load_json(ROOT / "data/verified_macro_data.json"),
                                load_json(ROOT / "config/industry_mapping.json"))
    converted = copy.deepcopy(native)
    for s in converted["sources"]:
        s.update(published_at=s.get("publication_date"),
                 retrieved_at=s["access_date"] + "T00:00:00+07:00",
                 publication_date_verified=bool(s.get("publication_date")), locator=s.get("data_period"))
        s["retrieved_at_precision"] = "date_only_in_handoff"
    d = converted["data"]
    d["metrics"] = [{**x, "metric_id": x["indicator_id"], "formula_id": None,
                      "source_refs": [x["source_id"]] if x.get("source_id") else []}
                     for x in d.get("indicators", [])]
    d["findings"] = [{"text": x["statement"], "evidence_refs": x.get("indicator_ids", [])}
                     for x in d.get("macro_summary", {}).get("observations", [])]
    d["risks"] = [{"text": x.get("statement", x.get("text", str(x))),
                   "evidence_refs": x.get("source_ids", [])} for x in d.get("risks", [])]
    out = canonical(request, "macro", converted)
    out["native_output"] = native
    return out


def industry(request):
    from industry.analyzer import analyze_industry
    from industry.data_loader import SECTOR_MAP
    native = analyze_industry(request)
    out = canonical(request, "industry", native)
    actual = out["data"].get("industry_code")
    out["data"]["resolved_industry_code"] = actual
    out["data"]["industry_code"] = request["industry_code"]
    if actual != request["industry_code"]:
        out["warnings"].append(f"Mã ngành input {request['industry_code']} khác mã tra cứu {actual}; cần thống nhất phân loại.")
    if request["ticker"] not in SECTOR_MAP:
        out["data"].update(metrics=[], peers=[], findings=[], risks=[])
        out["warnings"].append("Mã chưa được ánh xạ ngành: không sử dụng các peer fallback khác ngành; dữ liệu gốc giữ trong native_output.")
    else:
        # Handoff peers lack source_refs per value; do not present them as validated strategy facts.
        out["warnings"].append("Peer ngành là bảng tĩnh bàn giao, thiếu source_refs từng giá trị; chưa dùng trực tiếp để định giá chiến lược.")
        peers = out["data"].get("peers", [])
        for peer in peers:
            peer["strategy_eligible"] = False
            if peer.get("valuation_date", "") > request["as_of_date"]:
                peer["excluded_from_strategy_reason"] = "valuation_date_after_cutoff"
        out["data"]["peers"] = [p for p in peers if p.get("valuation_date", "") <= request["as_of_date"]]
        if len(out["data"]["peers"]) != len(peers):
            out["warnings"].append("Đã loại peer có ngày định giá sau ngày chốt; giữ bản gốc trong native_output.")
    if out["warnings"] and out["status"] != "error":
        out["status"] = "partial"
    return out


def company(request):
    from company.analyzer import analyze_company
    if request["ticker"] == "HPG" and request["as_of_date"] <= "2026-10-09":
        native = analyze_company(request, snapshot_dir=ROOT / "company/examples/hpg_raw",
                                 verified_bundle=ROOT / "company/examples/hpg_verified.json")
        mode = "offline_hpg_handoff_snapshot"
    else:
        native = analyze_company(request, raw_dir=ROOT / "collected" / (request["run_id"] + "_" + now().replace(":", "-")), timeout=15)
        mode = "live_vietcap_collector_unverified_financial_candidates"
    out = canonical(request, "company", native)
    out["data"]["collection_mode"] = mode
    return out


def strategy(request, modules):
    from strategy_v2 import evaluate
    config = json.loads((ROOT / "strategy_rules_v2.json").read_text(encoding="utf-8"))
    out = envelope(request, "strategy")
    payload = {**request, "sector": request["industry_name"], "as_of": request["as_of_date"],
               "analysis_period": {"start": request["period_start"], "end": request["period_end"]},
               "investment_horizon_months": request.get("investment_horizon_months"), "is_demo": False,
               "macro": {"drivers": []}, "industry": {"peers": []}, "company": {}, "market": {}}
    company_module = modules["company"]
    sources = {s["source_id"]: s for s in company_module["sources"]}
    path_refs = {}

    def fact(row, path, negate=False):
        refs = row.get("source_refs", [])
        chosen = [sources.get(s) for s in refs]
        if row.get("value") is None or not chosen or any(not s or not s["publication_date_verified"]
                or not s["published_at"] or s["published_at"][:10] > request["as_of_date"] for s in chosen):
            return {"value": None}
        path_refs[path] = refs
        return {"value": -row["value"] if negate else row["value"], "unit": row["unit"],
                "period": row["period_end"], "observed_at": row["period_end"],
                "published_at": max(s["published_at"][:10] for s in chosen), "source": chosen[0]["url"]}

    rows = company_module["data"].get("financials", [])
    scope = request.get("statement_scope", "consolidated")
    rows = [r for r in rows if r.get("verified") is True and r.get("statement_scope") == scope]
    annual_ends = sorted({r["period_end"] for r in rows if r["item_id"] == "revenue" and r.get("frequency") == "annual"}, reverse=True)
    if request.get("financial_basis", "annual") == "annual" and len(annual_ends) >= 2:
        finance = {"period_type": "annual", "comparable_periods": False, "current": {}, "previous": {}}
        item_map = {"revenue": "revenue", "net_profit": "net_income", "equity_total": "equity", "assets": "assets",
                    "current_assets": "current_assets", "current_liabilities": "current_liabilities",
                    "interest_expense": "interest_expense", "cfo": "cfo", "capex_cash": "capex"}
        selected_periods = []
        for block, end in zip(("current", "previous"), annual_ends[:2]):
            selected = [r for r in rows if r["period_end"] == end and r.get("frequency") in ("annual", "point_in_time")]
            for r in selected:
                if r["item_id"] in item_map:
                    key = item_map[r["item_id"]]
                    finance[block][key] = fact(r, f"company.financial.{block}.{key}", key == "capex")
            revenue = next(r for r in selected if r["item_id"] == "revenue")
            selected_periods.append((revenue["period_start"], revenue["period_end"]))
        a, b = selected_periods
        finance["comparable_periods"] = a[0][5:] == b[0][5:] and a[1][5:] == b[1][5:] and int(a[0][:4]) == int(b[0][:4]) + 1
        if finance["comparable_periods"]:
            payload["company"]["financial"] = finance
    # Never claim provider_adjusted_unspecified is a verified adjusted return series.
    out["warnings"].append("Chưa có chuỗi giá điều chỉnh đã kiểm, benchmark total return, giả định DCF và peer có nguồn từng giá trị; các trụ cột thiếu dữ liệu được giữ nguyên trạng thái.")
    result = evaluate(payload, config)
    out["native_output"] = result
    out["strategy_input"] = payload
    out["errors"] = messages(result.get("errors", []))
    out["warnings"].extend(messages(result.get("warnings", [])))
    d = result.get("data") or {}
    rules = []
    evidence = set()
    for r in d.get("rules", []):
        refs = sorted({sid for path in r.get("evidence_refs", []) for sid in path_refs.get(path, [])})
        evidence.update(refs)
        rules.append({**r, "rule_id": "strategy:" + r["id"], "native_evidence_refs": r.get("evidence_refs", []),
                      "evidence_refs": refs, "input_metric_ids": refs,
                      "formula": config["modules"][r["id"]].get("formula"), "thresholds": None,
                      "theory_refs": {"macro":[], "industry":[], "fundamental":["valuation"], "value":["value","valuation"],
                                      "relative_valuation":["valuation"], "momentum":["momentum"], "risk":["portfolio"],
                                      "capm":["capm"], "news":["emh"]}.get(r["id"], [])})
    for t in config["theory_sources"]:
        out["sources"].append({"source_id": "strategy:theory_" + t["id"], "title": t["title"],
                               "url": t["url"], "retrieved_at": now(), "published_at": None,
                               "publication_date_verified": False, "locator": t.get("pages")})
    out["data"] = {"theory_sources": config["theory_sources"], "rules": rules, "evidence_refs": sorted(evidence),
                   "findings": [{"text": r["id"] + ": " + r["explanation"], "evidence_refs": r["evidence_refs"]} for r in rules],
                   "risks": [{"text": t, "evidence_refs": []} for t in (d.get("risks") or {}).get("methodological", [])],
                   "conclusion": {"label": "insufficient_data", "horizon": request["investment_horizon"],
                                  "rationale": (d.get("conclusion") or {}).get("explanation", "Cần số tháng đầu tư hợp lệ và dữ liệu đủ điều kiện."),
                                  "evidence_refs": sorted(evidence)}}
    out["status"] = "error" if out["errors"] else "partial"
    return out


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    body = json.load(sys.stdin)
    name = json.loads((ROOT / "adapter_config.json").read_text())["module"]
    try:
        result = strategy(body["request"], body["modules"]) if name == "strategy" else globals()[name](body["request"])
        print(json.dumps(result, ensure_ascii=False, allow_nan=False))
    except Exception as exc:
        result = envelope(body["request"], name)
        result.update(status="error", errors=[f"{type(exc).__name__}: {exc}"])
        result["data"] = {"metrics": [], "findings": [], "risks": []}
        if name == "industry":
            result["data"].update(industry_code=body["request"]["industry_code"], peers=[])
        if name == "company":
            result["data"].update(price_series=[], financials=[])
        print(json.dumps(result, ensure_ascii=False))
