"""Hợp đồng V1 từ tab Input Output chung; dùng thư viện chuẩn Python."""
import datetime as dt
import json
import math
import re
from pathlib import Path

TZ = dt.timezone(dt.timedelta(hours=7))

def now():
    return dt.datetime.now(TZ).isoformat(timespec="seconds")

def day(value):
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError(f"Ngày phải là YYYY-MM-DD: {value!r}")
    return dt.date.fromisoformat(value)

def number(value):
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"Số phải là number hữu hạn hoặc null: {value!r}")
    return value

def validate_request(request):
    required = ("schema_version", "run_id", "ticker", "exchange", "industry_code",
                "industry_name", "as_of_date", "period_start", "period_end",
                "investment_horizon", "language", "currency")
    for k in required:
        if not isinstance(request.get(k), str) or not request[k].strip():
            raise ValueError(f"Thiếu/sai input {k}; không tự đặt giá trị thay người 5")
    if request["schema_version"] != "1.0":
        raise ValueError("schema_version phải là 1.0")
    if not re.fullmatch(r"[A-Z][A-Z0-9]{1,9}", request["ticker"]):
        raise ValueError("ticker phải viết hoa, chỉ gồm chữ và số")
    if request["exchange"] not in ("HOSE", "HNX", "UPCOM"):
        raise ValueError("exchange phải là HOSE/HNX/UPCOM")
    if request["language"] != "vi" or request["currency"] != "VND":
        raise ValueError("language=vi, currency=VND")
    start, end, cutoff = [day(request[k]) for k in ("period_start", "period_end", "as_of_date")]
    if not start <= end <= cutoff:
        raise ValueError("Cần period_start <= period_end <= as_of_date")
    if cutoff > dt.datetime.now(TZ).date():
        raise ValueError("Không lấy dữ liệu tại ngày chốt tương lai")
    if request.get("financial_basis", "annual") not in ("annual", "quarterly", "ytd", "ttm"):
        raise ValueError("financial_basis: annual/quarterly/ytd/ttm")
    if request.get("statement_scope", "consolidated") not in ("consolidated", "separate"):
        raise ValueError("statement_scope: consolidated/separate")

def envelope(request, status="pending"):
    return {"schema_version": "1.0", "run_id": request.get("run_id"), "module": "company",
            "ticker": request.get("ticker"), "as_of_date": request.get("as_of_date"),
            "generated_at": now(), "status": status,
            "data": {"price_series": [], "financials": [], "metrics": [], "findings": [], "risks": [], "news": []},
            "sources": [], "warnings": [], "errors": []}

def eligible(source, cutoff):
    pub = source.get("published_at")
    return source.get("publication_date_verified") is True and pub is not None and day(pub) <= day(cutoff)

def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    temporary.replace(path)

def validate_company_output(doc):
    """Trả (bool, errors); pending cũng phải đủ cấu trúc."""
    errors = []
    try:
        for k in ("schema_version", "run_id", "module", "ticker", "as_of_date", "generated_at",
                  "status", "data", "sources", "warnings", "errors"):
            if k not in doc:
                raise ValueError(f"Thiếu envelope.{k}")
        if doc["schema_version"] != "1.0" or doc["module"] != "company":
            raise ValueError("Sai version/module")
        if doc["status"] not in ("pending", "ok", "partial", "error"):
            raise ValueError("Sai status")
        for k in ("sources", "warnings", "errors"):
            if not isinstance(doc[k], list):
                raise ValueError(f"{k} phải là array")
        data = doc["data"]
        for k in ("price_series", "financials", "metrics", "findings", "risks"):
            if not isinstance(data.get(k), list):
                raise ValueError(f"data.{k} phải là array")
        sources = {}
        for source in doc["sources"]:
            for k in ("source_id", "title", "url", "published_at", "retrieved_at", "locator", "publication_date_verified"):
                if k not in source:
                    raise ValueError(f"Source thiếu {k}")
            sid = source["source_id"]
            if not sid.startswith("company_") or sid in sources:
                raise ValueError(f"ID nguồn sai/trùng: {sid}")
            if not re.match(r"https?://", source["url"]):
                raise ValueError(f"Nguồn phải có URL http(s): {sid}")
            if type(source["publication_date_verified"]) is not bool:
                raise ValueError("publication_date_verified phải boolean")
            if source["published_at"] is not None:
                day(source["published_at"])
            dt.datetime.fromisoformat(source["retrieved_at"])
            sources[sid] = source
        ids = set(sources)
        for section, id_key in (("metrics", "metric_id"), ("financials", "record_id")):
            for row in data[section]:
                rid = row[id_key]
                if not rid.startswith("company_") or rid in ids:
                    raise ValueError(f"ID sai/trùng: {rid}")
                ids.add(rid)
                number(row["value"])
                for k in ("unit", "period_start", "period_end", "source_refs"):
                    if k not in row:
                        raise ValueError(f"{rid} thiếu {k}")
                if row["period_start"] is not None: day(row["period_start"])
                if row["period_end"] is not None: day(row["period_end"])
                if section == "metrics":
                    for k in ("frequency", "formula_id"):
                        if k not in row: raise ValueError(f"{rid} thiếu {k}")
                else:
                    if row["statement_scope"] not in ("consolidated", "separate", "unknown"):
                        raise ValueError("Sai statement_scope")
                refs = row["source_refs"]
                if not isinstance(refs, list) or any(ref not in sources for ref in refs):
                    raise ValueError(f"{rid}: source_refs không hợp lệ")
                if section == "metrics" and row["value"] is not None:
                    if not refs or any(not eligible(sources[s], doc["as_of_date"]) for s in refs):
                        raise ValueError(f"{rid}: nguồn chưa đủ điều kiện ngày chốt")
        dates = set()
        for row in data["price_series"]:
            day(row["date"])
            if row["date"] in dates or row["date"] > doc["as_of_date"]:
                raise ValueError("Giá trùng phiên hoặc vượt ngày chốt")
            dates.add(row["date"])
            number(row["close"]); number(row["volume"])
            if row['close'] is not None and row['close'] <= 0:
                raise ValueError('Close phải dương hoặc null')
            if row['volume'] is not None and (row['volume'] < 0 or int(row['volume']) != row['volume']):
                raise ValueError('Khối lượng phải nguyên không âm hoặc null')
            if not row.get("source_refs") or any(r not in sources for r in row["source_refs"]):
                raise ValueError("Giá thiếu/sai nguồn")
            if "adjustment_basis" not in row: raise ValueError("Giá thiếu adjustment_basis")
        for section, key in (("findings", "finding_id"), ("risks", "risk_id")):
            for row in data[section]:
                if not row[key].startswith("company_") or not row.get("evidence_refs"):
                    raise ValueError("Nhận định/rủi ro thiếu ID hoặc bằng chứng")
                if any(ref not in ids for ref in row["evidence_refs"]):
                    raise ValueError("Nhận định/rủi ro có bằng chứng không tồn tại")
        for row in data["metrics"]:
            if any(ref not in ids for ref in row.get("input_refs", [])):
                raise ValueError(f"{row['metric_id']}: input_refs không tồn tại")
        if doc["status"] != "pending":
            if not doc["run_id"] or not doc["ticker"]: raise ValueError("Thiếu run_id/ticker")
            day(doc["as_of_date"])
            timestamp = dt.datetime.fromisoformat(doc["generated_at"])
            if timestamp.utcoffset() != dt.timedelta(hours=7): raise ValueError("generated_at phải +07:00")
        json.dumps(doc, allow_nan=False)
    except (ValueError, KeyError, TypeError, AttributeError) as exc:
        errors.append(str(exc))
    return not errors, errors
