"""Lấy snapshot VCI; lưu nguyên bytes + URL/body/thời điểm/SHA256 trước xử lý.

API tham khảo cấu trúc công khai của vnstock (xem SOURCES.md); không phụ thuộc vnstock.
BCTC từ API là candidate: không đoán phạm vi hợp nhất hoặc bản điều chỉnh hồi tố.
"""
import calendar
import datetime as dt
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from concurrent.futures import ThreadPoolExecutor
from .contract import TZ, day, now, number, write_json

IQ = "https://iq.vietcap.com.vn/api/iq-insight-service"
CHART = "https://trading.vietcap.com.vn/api/chart/OHLCChart/gap-chart"
FIELDS = {
    "balance": {"current_assets": ("bsa1", "CURRENT ASSETS"), "cash": ("bsa2", "Cash and cash equivalents"),
                "inventory": ("bsa15", "Inventories, Net"), "assets": ("bsa53", "Total Assets"),
                "liabilities": ("bsa54", "Liabilities"), "current_liabilities": ("bsa55", "Current liabilities"),
                "short_debt": ("bsa56", "Short-term borrowings"), "long_debt": ("bsa71", "Long-term borrowings"),
                "equity_total": ("bsa78", "Owner's Equity"), "noncontrolling_interest": ("bsa210", "Minority interests")},
    "income": {"revenue": ("isa3", "Net sales"), "gross_profit": ("isa5", "Gross Profit"),
               "interest_expense": ("isa8", "Interest expenses"), "pretax_profit": ("isa16", "Net accounting profit/(loss) before tax"),
               "net_profit": ("isa20", "Net profit/(loss) after tax"), "parent_profit": ("isa22", "Attributable to parent company"),
               "basic_eps": ("isa23", "EPS basic (VND)")},
    "cashflow": {"cfo": ("cfa18", "Net cash inflows/(outflows) from operating activities"),
                 "capex_cash": ("cfa19", "Purchases of fixed assets and other long term assets")}
}
SECTIONS = {"balance": "BALANCE_SHEET", "income": "INCOME_STATEMENT", "cashflow": "CASH_FLOW"}

def _fetch(url, target, payload=None, timeout=20):
    req = Request(url, data=json.dumps(payload).encode() if payload is not None else None,
                  headers={"User-Agent": "Mozilla/5.0", "Content-Type": "application/json",
                           "Referer": "https://trading.vietcap.com.vn/", "Origin": "https://trading.vietcap.com.vn"})
    with urlopen(req, timeout=timeout) as response:
        body = response.read()
    target.write_bytes(body)
    write_json(target.with_name(target.stem + ".meta.json"),
               {"url": url, "retrieved_at": now(), "sha256": hashlib.sha256(body).hexdigest(), "request_body": payload})
    result = json.loads(body)
    if isinstance(result, dict) and (result.get("successful") is False or result.get("status", 200) != 200):
        raise ValueError(f"API báo lỗi: {result.get('msg')}")
    return result

def fetch_vci(request, raw_dir, timeout=20):
    raw_dir = Path(raw_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)
    ticker = request["ticker"]
    start, end = day(request["period_start"]), day(request["period_end"])
    # Ngày hiện tại có thể chưa đóng cửa: chỉ lấy đến hôm qua, không giả close intraday.
    end = min(end, dt.datetime.now(TZ).date() - dt.timedelta(days=1))
    to_stamp = int(dt.datetime.combine(end + dt.timedelta(days=1), dt.time(), TZ).timestamp())
    count = (end - start).days + 20
    jobs = {"metadata": (f"{IQ}/v1/company/{ticker}/financial-statement/metrics", None),
            "prices": (CHART, {"timeFrame": "ONE_DAY", "symbols": [ticker], "to": to_stamp, "countBack": max(count, 1)})}
    jobs.update({k: (f"{IQ}/v1/company/{ticker}/financial-statement?section={section}", None) for k, section in SECTIONS.items()})
    jobs["news"] = (IQ + "/v1/news?" + urlencode({"ticker": ticker, "fromDate": start.strftime("%Y%m%d"),
                    "toDate": request["as_of_date"].replace("-", ""), "languageId": 1, "page": 0, "size": 50}), None)
    result, errors = {}, []
    def task(name):
        url, payload = jobs[name]
        try: return name, _fetch(url, raw_dir / (name + ".json"), payload, timeout), None
        except Exception as exc: return name, None, f"{name}: {type(exc).__name__}: {exc}"
    with ThreadPoolExecutor(max_workers=3) as executor:
        for name, value, error in executor.map(task, jobs):
            if error: errors.append(error)
            else: result[name] = value
    write_json(raw_dir / "collection_errors.json", errors)
    return result, errors

def load_snapshot(raw_dir):
    raw_dir = Path(raw_dir)
    data, errors = {}, []
    for name in ("metadata", "balance", "income", "cashflow", "prices", "news"):
        p = raw_dir / (name + ".json")
        if not p.exists():
            errors.append(f"snapshot thiếu {p.name}"); continue
        try:
            meta = json.loads((raw_dir / (name + ".meta.json")).read_text(encoding="utf-8"))
            b = p.read_bytes()
            if hashlib.sha256(b).hexdigest() != meta["sha256"]:
                raise ValueError("SHA256 khác snapshot gốc")
            data[name] = json.loads(b)
        except Exception as exc: errors.append(f"{name}: {exc}")
    return data, errors

def _source(name, meta, published_at=None, locator=None, date_verified=False):
    return {"source_id": name, "title": "VCI: " + name, "url": meta["url"], "published_at": published_at,
            "retrieved_at": meta["retrieved_at"], "locator": locator, "publication_date_verified": date_verified,
            "verification_method": "provider publicDate / completed market session" if date_verified else "chưa xác minh",
            "raw_sha256": meta.get("sha256")}

def normalize_vci(raw, raw_dir, request):
    """Giữ candidate BCTC, chỉ dữ liệu có scope/value verified mới vào phép tính."""
    raw_dir = Path(raw_dir)
    bundle = {"ticker": request["ticker"], "sources": [], "price_series": [], "financials": [], "news": [], "warnings": []}
    def meta(name):
        return json.loads((raw_dir / (name + ".meta.json")).read_text(encoding="utf-8"))
    mapping = raw.get("metadata", {}).get("data", {})
    for kind in SECTIONS:
        dataset = raw.get(kind, {}).get("data", {})
        if not dataset: continue
        labels = {x["field"]: x["titleEn"] for x in mapping.get(SECTIONS[kind], [])}
        for table, frequency in (("years", "annual"), ("quarters", "quarterly")):
            for row in dataset.get(table, []):
                if row.get("ticker") != request["ticker"]:
                    raise ValueError("Ticker BCTC từ API khác request")
                year, q = int(row["yearReport"]), int(row["lengthReport"])
                if table == "quarters" and q not in (1, 2, 3, 4): continue
                end_month = 12 if table == "years" else q * 3
                end = dt.date(year, end_month, calendar.monthrange(year, end_month)[1]).isoformat()
                history_start = (day(request["period_start"]) - dt.timedelta(days=740)).isoformat()
                if end > request["period_end"] or end < history_start: continue
                start = f"{year}-01-01" if table == "years" else f"{year}-{(q - 1) * 3 + 1:02d}-01"
                if kind == "balance": start = end
                # LCTT quý trên API không đủ metadata để kết luận standalone/YTD.
                record_frequency = "unknown" if kind == "cashflow" and table == "quarters" else frequency
                pub = row.get("publicDate")
                pub = pub[:10] if isinstance(pub, str) else None
                if pub is not None:
                    try: day(pub)
                    except ValueError: pub = None
                sid = f"company_src_vci_{kind}_{table}_{year}_{q}"
                bundle["sources"].append(_source(sid, meta(kind), pub, f"data.{table}; yearReport={year},lengthReport={q}", pub is not None))
                for item, (field, title) in FIELDS[kind].items():
                    if labels.get(field) != title:
                        bundle["warnings"].append(f"Không map {field}: metadata khác cấu trúc doanh nghiệp thông thường"); continue
                    value = number(row.get(field))
                    bundle["financials"].append({"record_id": f"company_vci_{kind}_{table}_{year}_{q}_{item}",
                        "item_id": item, "value": value, "unit": "VND/share" if item == "basic_eps" else "VND",
                        "frequency": "point_in_time" if kind == "balance" else record_frequency,
                        "period_start": start, "period_end": end, "statement_scope": "unknown", "verified": False,
                        "source_refs": [sid], "raw_field": field,
                        "exclusion_reason": "Chưa đối chiếu PDF/phạm vi/đơn vị/kỳ; API hiện tại có thể đã restate lịch sử"})
    if "prices" in raw:
        rows = raw["prices"]
        if isinstance(rows, dict): rows = rows.get("data", [])
        if rows:
            data = rows[0]
            if data.get("symbol") != request["ticker"]: raise ValueError("Ticker giá khác request")
            arrays = [data.get(k, []) for k in ("t", "c", "v")]
            if len({len(a) for a in arrays}) != 1: raise ValueError("Các mảng OHLC không cùng độ dài")
            today = dt.datetime.now(TZ).date().isoformat()
            for timestamp, close, volume in zip(*arrays):
                date = dt.datetime.fromtimestamp(int(timestamp), TZ).date().isoformat()
                if not request["period_start"] <= date <= request["period_end"] or date >= today: continue
                sid = f"company_src_price_{date}"
                bundle["sources"].append(_source(sid, meta("prices"), date, f"HPG/OHLC t={timestamp}".replace("HPG",request["ticker"]), True))
                bundle["price_series"].append({"date": date, "close": number(close), "volume": number(volume),
                    "adjustment_basis": "provider_adjusted_unspecified", "source_refs": [sid],
                    "price_unit": "VND", "volume_unit": "shares"})
            bundle["warnings"].append("VCI raw close đã là VND; không nhân 1.000. Chưa xác minh đầy đủ cách điều chỉnh cổ tức/chia tách; không dùng cho P/E/P/B/return.")
    if "news" in raw:
        contents = raw["news"].get("data", {}).get("content", [])
        for row in contents:
            pub = row.get("publicDate")
            if not isinstance(pub, str): continue
            pub = pub[:10]
            try: day(pub)
            except ValueError: continue
            if not request["period_start"] <= pub <= request["as_of_date"]: continue
            news_id = str(row.get("newsId", row.get("id")))
            sid = "company_src_news_" + re.sub(r"[^a-zA-Z0-9_]", "_", news_id)
            source = _source(sid, meta("news"), pub, "newsId=" + news_id, True)
            if row.get("newsSourceLink"): source["original_url"] = row["newsSourceLink"]
            bundle["sources"].append(source)
            bundle["news"].append({"news_id": "company_news_" + news_id, "title": row.get("newsTitle"),
                "published_at": pub, "source_refs": [sid], "content_verified": False})
        if len(contents) == 50 or raw["news"].get("data", {}).get("totalElements", 0) > len(contents):
            bundle["warnings"].append("Tin VCI chỉ lấy 50 mục trang đầu; không coi là toàn bộ tin trong kỳ")
    return bundle

def load_verified_bundle(path, request):
    """Đường nhập chuẩn cho PDF/miner đã đối chiếu; bundle có ticker bắt buộc."""
    bundle = json.loads(Path(path).read_text(encoding="utf-8"))
    if bundle.get("ticker") != request["ticker"]: raise ValueError("Bundle có ticker khác request")
    for source in bundle.get('sources',[]):
        if source.get('raw_file'):
            base=Path(path).resolve().parent
            evidence=(base/source['raw_file']).resolve()
            if not evidence.is_relative_to(base):raise ValueError('raw_file phải nằm trong thư mục evidence bundle')
            if not source.get('raw_sha256') or hashlib.sha256(evidence.read_bytes()).hexdigest()!=source['raw_sha256']:
                raise ValueError(f"Evidence PDF thiếu/sai SHA256: {source['source_id']}")
    for row in bundle.get("financials", []):
        number(row["value"])
        day(row["period_start"]); day(row["period_end"])
        if row.get("statement_scope") not in ("consolidated", "separate"):
            raise ValueError("Bundle cần statement_scope đã kiểm")
        if row.get("unit") not in ("VND", "VND/share", "shares"):
            raise ValueError("Bundle chưa chuẩn hóa về VND/VND-share/shares")
        if type(row.get("verified")) is not bool:
            raise ValueError("Bundle cần cờ verified boolean cho mỗi BCTC")
    return bundle
