"""Hàm tích hợp Người 5: request -> envelope; CLI và replay snapshot."""
import argparse
import json
import re
from pathlib import Path
from .contract import envelope, validate_request, validate_company_output, write_json, eligible
from .providers import fetch_vci, load_snapshot, normalize_vci, load_verified_bundle
from .metrics import calculate_metrics, describe_metrics

def analyze_company(request, *, raw_dir=None, snapshot_dir=None, verified_bundle=None, timeout=20, pending=False):
    out=envelope(request)
    if pending:
        out["warnings"].append("Chưa có dữ liệu thật; pending chỉ dùng kiểm tích hợp")
        return out
    try: validate_request(request)
    except (ValueError, TypeError) as exc:
        out["status"]="error";out["errors"].append(str(exc));return out
    safe_run=re.sub(r"[^a-zA-Z0-9_-]","_",request["run_id"])
    root=Path(snapshot_dir or raw_dir or f"company/raw/{safe_run}_{request['ticker']}")
    try:
        if snapshot_dir: raw,errors=load_snapshot(root)
        else:
            if any(root.glob("*.json")):
                raise ValueError("raw_dir đã có snapshot; chọn thư mục mới hoặc --snapshot để không ghi đè dữ liệu gốc")
            raw,errors=fetch_vci(request,root,timeout)
        out["errors"].extend(errors)
        bundle=normalize_vci(raw,root,request)
        if verified_bundle:
            checked=load_verified_bundle(verified_bundle,request)
            for k in ("price_series","financials","news","sources","warnings"):
                bundle.setdefault(k,[]).extend(checked.get(k,[]))
        for key in ("price_series","financials","news"):
            out["data"][key]=bundle.get(key,[])
        all_financials=out['data']['financials']
        out['data']['financial_candidates']=[r for r in all_financials if not r.get('verified') or r.get('statement_scope')=='unknown']
        out['data']['financials']=[r for r in all_financials if r.get('verified') is True and r.get('statement_scope') in ('consolidated','separate')]
        out["sources"]=bundle.get("sources",[])
        out["warnings"].extend(bundle.get("warnings",[]))
        # Giá trùng cùng phiên xung đột bị loại; bản verified spot được ưu tiên rõ ràng.
        by_date={}
        for row in out["data"]["price_series"]:
            if not request["period_start"]<=row["date"]<=request["period_end"]: continue
            old=by_date.get(row["date"])
            if old and old.get("close") != row.get("close") and not row.get("basis_verified"):
                raise ValueError(f"Giá trùng xung đột {row['date']}")
            if not old or row.get("basis_verified"): by_date[row["date"]]=row
        out["data"]["price_series"]=sorted(by_date.values(),key=lambda r:r["date"])
        out["data"]["metrics"],warnings=calculate_metrics(request,out["data"]["financials"],out["data"]["price_series"],out["sources"])
        out["warnings"].extend(warnings)
        out["data"]["findings"],out["data"]["risks"]=describe_metrics(out["data"]["metrics"])
        out["data"]["industry_code"]=request["industry_code"]
        out["data"]["industry_name"]=request["industry_name"]
        out["data"]["financial_basis"]=request.get("financial_basis","annual")
        out["data"]["statement_scope"]=request.get("statement_scope","consolidated")
        out["data"]["coverage"]={
            "prices_count":len(out["data"]["price_series"]),
            "financial_records_count":len(out["data"]["financials"]),
            "financial_candidates_count":len(out['data']['financial_candidates']),
            "verified_financial_records_count":sum(r.get("verified") is True for r in out["data"]["financials"]),
            "metrics_available":sum(m["value"] is not None for m in out["data"]["metrics"]),
            "news_count":len(out["data"]["news"])}
        out["warnings"].append("Sàn và ngành được giữ theo request chung của nhóm; chưa kiểm độc lập việc phân loại trong lần chạy này")
        periods={}
        for r in out['data']['financials']+out['data']['financial_candidates']:
            for sid in r['source_refs']:periods.setdefault(sid,[]).append((r['period_start'],r['period_end']))
        for r in out['data']['price_series']:
            for sid in r['source_refs']:periods.setdefault(sid,[]).append((r['date'],r['date']))
        for source in out['sources']:
            dates=periods.get(source['source_id'],[])
            source['data_period_start']=min((s for s,e in dates),default=None)
            source['data_period_end']=max((e for s,e in dates),default=None)
        out["warnings"].append("Candidate BCTC chưa đối chiếu được giữ để nghiên cứu; chỉ verified=true, đúng scope/kỳ và nguồn công bố hợp lệ mới vào metrics")
        sources={s["source_id"]:s for s in out["sources"]}
        for s in out["sources"]:
            if not eligible(s,request["as_of_date"]):
                out["warnings"].append(f"{s['source_id']}: ngày công bố thiếu/chưa kiểm/sau ngày chốt; loại khỏi tính chỉ số")
        valid_news=[n for n in out["data"]["news"] if n.get("source_refs") and all(eligible(sources[r],request["as_of_date"]) for r in n["source_refs"])]
        complete = (bool(out["data"]["price_series"]) and bool(valid_news)
                    and all(m["value"] is not None for m in out["data"]["metrics"]) and not out["errors"])
        has_data=bool(out["data"]["price_series"] or out["data"]["financials"] or valid_news)
        out["status"]="ok" if complete else "partial" if has_data else "error"
        valid,issues=validate_company_output(out)
        if not valid:
            messages=out["errors"]+["Output vi phạm contract: "+"; ".join(issues)]
            out=envelope(request,"error")
            out["errors"]=messages
    except Exception as exc:
        out["status"]="error";out["errors"].append(f"{type(exc).__name__}: {exc}")
    out["warnings"]=sorted(set(out["warnings"]))
    return out

def main():
    parser=argparse.ArgumentParser(description="Module doanh nghiệp - Người 3")
    parser.add_argument("--request",required=True,help="request.json chung do Người 5 tạo")
    parser.add_argument("--snapshot",help="Thư mục raw để tái lập, không gọi mạng")
    parser.add_argument("--raw-dir",help="Thư mục mới lưu bytes gốc khi gọi mạng")
    parser.add_argument("--verified-bundle",help="Bundle normalized đã kiểm PDF")
    parser.add_argument("--pending",action="store_true")
    parser.add_argument("--timeout",type=int,default=20)
    parser.add_argument("-o","--output",default="company.json")
    args=parser.parse_args()
    request=json.loads(Path(args.request).read_text(encoding="utf-8"))
    out=analyze_company(request,snapshot_dir=args.snapshot,raw_dir=args.raw_dir,
                        verified_bundle=args.verified_bundle,timeout=args.timeout,pending=args.pending)
    write_json(args.output,out)
    print(json.dumps({"status":out["status"],"output":args.output,"coverage":out["data"].get("coverage"),"errors":out["errors"]},ensure_ascii=False))
    return 2 if out["status"]=="error" else 0

if __name__=="__main__": raise SystemExit(main())
