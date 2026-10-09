"""Skeleton bàn giao, chỉ trả pending. Thay MODULE và xử lý bằng dữ liệu thật."""
import json
import sys
from datetime import datetime, timezone

MODULE = "strategy"
input_payload = json.load(sys.stdin)
request = input_payload["request"]
data = {"metrics": [], "findings": [], "risks": []}
if MODULE == "industry":
    data.update(industry_code=request["industry_code"], peers=[])
if MODULE == "company":
    data.update(price_series=[], financials=[])
if MODULE == "strategy":
    data.update(theory_sources=[], rules=[], evidence_refs=[], conclusion={
        "label": "insufficient_data", "rationale": "Module chưa được triển khai.",
        "evidence_refs": [], "horizon": request["investment_horizon"]})
output = {
    "schema_version": request["schema_version"], "run_id": request["run_id"],
    "module": MODULE, "ticker": request["ticker"], "as_of_date": request["as_of_date"],
    "generated_at": datetime.now(timezone.utc).isoformat(), "status": "pending",
    "data": data, "sources": [], "warnings": ["Skeleton chưa có logic hoặc dữ liệu thật."], "errors": []}
json.dump(output, sys.stdout, ensure_ascii=False)
