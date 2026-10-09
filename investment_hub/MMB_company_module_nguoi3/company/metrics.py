"""Công thức nhất quán; không thay dữ liệu thiếu bằng 0, không tự annualize."""
import datetime as dt
import statistics
from .contract import day, eligible, number

def calculate_metrics(request, financials, prices, sources):
    source_map = {s["source_id"]: s for s in sources}
    warnings, output = [], []
    scope = request.get("statement_scope", "consolidated")
    basis = request.get("financial_basis", "annual")
    def usable(row):
        refs = row.get("source_refs", [])
        return (row.get("verified") is True and row.get("statement_scope") == scope
                and row["period_end"] <= request["period_end"] and row.get("value") is not None
                and refs and all(r in source_map and eligible(source_map[r], request["as_of_date"]) for r in refs))
    records = [r for r in financials if usable(r)]
    def get(item, start, end, frequency):
        hits = [r for r in records if r["item_id"] == item and r["period_start"] == start
                and r["period_end"] == end and r.get("frequency") == frequency]
        if not hits: return None
        # Bản công bố mới nhất tại ngày chốt; không nhận hai số xung đột cùng timestamp.
        rank = lambda r: max(source_map[s]["published_at"] for s in r["source_refs"])
        hits.sort(key=rank, reverse=True)
        if any(r["value"] != hits[0]["value"] and rank(r) == rank(hits[0]) for r in hits[1:]):
            warnings.append(f"Số liệu xung đột {item}/{end}; không tính"); return None
        return hits[0]
    groups = sorted({(r["period_start"], r["period_end"]) for r in records
                     if r["item_id"] == "revenue" and r.get("frequency") == basis}, key=lambda p: p[1])
    start, end = groups[-1] if groups else (None, None)
    if basis == "ttm":
        # Chỉ 4 quý standalone liên tiếp, đã xác minh từng quý; không cộng lũy kế.
        quarters = sorted({(r["period_start"], r["period_end"]) for r in records
                           if r["item_id"] == "revenue" and r.get("frequency") == "quarterly"},key=lambda p:p[1])[-4:]
        if len(quarters) == 4 and all(day(quarters[i][1])+dt.timedelta(days=1)==day(quarters[i+1][0]) for i in range(3)):
            start, end = quarters[0][0], quarters[-1][1]
            for item in ("revenue", "gross_profit", "net_profit", "parent_profit", "cfo", "capex_cash"):
                rows = [get(item,s,e,"quarterly") for s,e in quarters]
                if all(rows):
                    records.append({"record_id": f"company_derived_ttm_{item}", "item_id": item,
                        "value": sum(r["value"] for r in rows), "period_start": start, "period_end": end,
                        "frequency": "ttm", "source_refs": sorted({s for r in rows for s in r["source_refs"]}),
                        "unit": "VND", "statement_scope": scope, "verified": True,
                        "input_refs": [r["record_id"] for r in rows]})
        else:
            start, end = None, None
            warnings.append("TTM thiếu 4 quý standalone liên tiếp đã xác minh; không cộng YTD hoặc annual")
    opening = (day(start)-dt.timedelta(days=1)).isoformat() if start else None
    def flow(item): return get(item,start,end,basis) if start else None
    def at(item, date): return get(item,date,date,"point_in_time") if date else None
    balance_dates = sorted({r["period_end"] for r in records if r.get("frequency")=="point_in_time" and r["item_id"]=="assets"})
    latest_balance = balance_dates[-1] if balance_dates else None
    def point(item): return at(item,latest_balance)
    def v(row): return row["value"] if row else None
    def add(metric, name, unit, frequency, s, e, formula, inputs, fn, reason=None):
        values = [v(r) for r in inputs]
        value = None
        missing_reason = reason
        if not reason and all(x is not None for x in values):
            try:
                value = fn(*values)
                if value is not None: number(value)
                else: missing_reason = "Mẫu số không dương hoặc chỉ số không có ý nghĩa"
            except (ZeroDivisionError, ValueError, OverflowError): missing_reason = "Phép tính không hợp lệ"
        elif not reason: missing_reason = "Thiếu đầu vào đã xác minh đúng kỳ/phạm vi/ngày chốt"
        refs = sorted({sid for r in inputs if r for sid in r["source_refs"]})
        output.append({"metric_id":"company_"+metric, "name":name, "value":value, "unit":unit,
            "frequency":frequency, "period_start":s, "period_end":e, "source_refs":refs,
            "formula_id":"company_formula_"+formula, "statement_scope":scope,
            "input_refs":sorted({ref for r in inputs if r for ref in r.get("input_refs",[r["record_id"]])}), "missing_reason":missing_reason})
        if value is None: warnings.append(f"company_{metric}: {missing_reason}")
    divide = lambda a,b: a/b if b>0 else None
    for item,label in (("revenue","Doanh thu thuần"),("net_profit","LNST toàn tập đoàn"),
                       ("parent_profit","LNST thuộc cổ đông công ty mẹ"),("cfo","Dòng tiền hoạt động kinh doanh"),
                       ("basic_eps","EPS cơ bản theo BCTC")):
        add(item,label,"VND/share" if item=="basic_eps" else "VND",basis,start,end,"reported",[flow(item)],lambda x:x)
    add("gross_margin","Biên lợi nhuận gộp","ratio",basis,start,end,"gross_margin",[flow("gross_profit"),flow("revenue")],divide)
    add("net_margin","Biên lợi nhuận ròng toàn tập đoàn","ratio",basis,start,end,"net_margin",[flow("net_profit"),flow("revenue")],divide)
    add("roa","ROA: LNST toàn tập đoàn / tài sản bình quân","ratio",basis,start,end,"roa_avg",
        [flow("net_profit"),at("assets",opening),at("assets",end)],lambda p,a,b:divide(p,(a+b)/2))
    add("roe","ROE: LN cổ đông mẹ / vốn cổ đông mẹ bình quân","ratio",basis,start,end,"roe_parent_avg",
        [flow("parent_profit"),at("equity_total",opening),at("noncontrolling_interest",opening),at("equity_total",end),at("noncontrolling_interest",end)],
        lambda p,e0,n0,e1,n1:divide(p,((e0-n0)+(e1-n1))/2))
    add("cfo_to_profit","CFO / LNST toàn tập đoàn","ratio",basis,start,end,"cfo_to_profit",[flow("cfo"),flow("net_profit")],divide)
    add("free_cash_flow","FCF = CFO + chi tiền CAPEX (CAPEX mang dấu âm)","VND",basis,start,end,"fcf_cash",[flow("cfo"),flow("capex_cash")],
        lambda c,k:c+k if k<=0 else None)
    def previous(date):
        if not date: return None
        d=day(date)
        try: return d.replace(year=d.year-1).isoformat()
        except ValueError: return d.replace(year=d.year-1,day=28).isoformat()
    for item,label in (("revenue","Tăng trưởng doanh thu cùng kỳ"),("parent_profit","Tăng trưởng LNST cổ đông mẹ cùng kỳ")):
        old=get(item,previous(start),previous(end),basis) if start else None
        add(item+"_growth_yoy",label,"ratio",basis,start,end,"growth_yoy",[flow(item),old],lambda a,b:a/b-1 if b>0 else None)
    financial_sector = request["industry_code"].startswith(("83","87")) or request.get("company_type") in ("bank","insurance","securities")
    reason="Công thức doanh nghiệp phi tài chính không áp dụng trực tiếp cho ngành tài chính" if financial_sector else None
    add("current_ratio","Hệ số thanh toán hiện hành","x","point_in_time",latest_balance,latest_balance,"current_ratio",[point("current_assets"),point("current_liabilities")],divide,reason)
    add("quick_ratio","Thanh toán nhanh = (TSNH - tồn kho)/nợ ngắn hạn","x","point_in_time",latest_balance,latest_balance,"quick_ratio",
        [point("current_assets"),point("inventory"),point("current_liabilities")],lambda a,i,l:divide(a-i,l),reason)
    add("liabilities_to_assets","Tổng nợ phải trả / tài sản","ratio","point_in_time",latest_balance,latest_balance,"liabilities_to_assets",[point("liabilities"),point("assets")],divide)
    add("debt_to_equity","Vay và nợ thuê tài chính / tổng VCSH","x","point_in_time",latest_balance,latest_balance,"debt_to_equity",
        [point("short_debt"),point("long_debt"),point("equity_total")],lambda a,b,e:divide(a+b,e),reason)
    add("net_debt","Nợ vay ròng (không trừ tiền gửi kỳ hạn)","VND","point_in_time",latest_balance,latest_balance,"net_debt",
        [point("short_debt"),point("long_debt"),point("cash")],lambda a,b,c:a+b-c,reason)
    price_rows=[p for p in prices if request["period_start"]<=p["date"]<=request["period_end"] and p["close"] is not None
                and all(s in source_map and eligible(source_map[s],request["as_of_date"]) for s in p["source_refs"])]
    safe_prices=[]
    for p in price_rows:
        later_snapshot=any(source_map[s]['retrieved_at'][:10] > request['as_of_date'] for s in p['source_refs'])
        if later_snapshot and not (p.get('adjustment_basis')=='unadjusted' and p.get('basis_verified') is True):
            warnings.append('Chuỗi giá điều chỉnh tải sau ngày chốt có nguy cơ nhìn trước sự kiện; chỉ giữ dữ liệu gốc, không dùng cho metrics')
        else: safe_prices.append(p)
    price_rows=safe_prices
    price_rows.sort(key=lambda p:p["date"])
    latest=price_rows[-1] if price_rows else None
    price_input={"record_id":"company_price_latest", "value":latest["close"],"source_refs":latest["source_refs"],"input_refs":latest["source_refs"]} if latest else None
    price_date=latest["date"] if latest else None
    add("close","Giá cuối phiên gần nhất theo nguồn","VND/share","daily",price_date,price_date,"reported",[price_input],lambda x:x)
    vols=[p for p in price_rows[-20:] if p["volume"] is not None]
    volume_input={"record_id":"company_volume_20_sessions", "value":statistics.mean([p["volume"] for p in vols]),
                  "source_refs":sorted({s for p in vols for s in p["source_refs"]}),
                  "input_refs":sorted({s for p in vols for s in p["source_refs"]})} if len(vols)==20 else None
    add("avg_volume_20","Khối lượng bình quân 20 phiên có giao dịch","shares","20_sessions",
        price_rows[-20]["date"] if len(price_rows)>=20 else None,price_date,"avg_volume_20",[volume_input],lambda x:x)
    spot_valid = latest and latest.get("adjustment_basis") in ("unadjusted", "adjusted_to_latest_session") and latest.get("basis_verified") is True
    eps=flow('basic_eps')
    eps_basis_valid=eps and eps.get('per_share_basis_verified') is True and eps.get('share_basis_valid_through','0000-01-01')>= (price_date or '9999-12-31')
    pe_reason = None if basis in ("annual","ttm") and spot_valid and eps_basis_valid else "Cần EPS annual/TTM và giá cùng cơ sở cổ phiếu được xác minh tới phiên định giá"
    add("pe","P/E theo EPS annual/TTM đã xác minh","x",basis,start,end,"pe",[price_input,flow("basic_eps")],divide,pe_reason)
    shares_dates = sorted({r["period_end"] for r in records if r["item_id"]=="shares_outstanding" and r.get("frequency")=="point_in_time" and r["period_end"]<= (price_date or "0000-01-01")})
    share_date=shares_dates[-1] if shares_dates else None
    shares=at("shares_outstanding",share_date)
    # Số cổ phiếu phải xác nhận hiệu lực đúng phiên; không dùng vốn điều lệ / mệnh giá.
    share_valid=shares and shares.get("valid_through") is not None and shares["valid_through"] >= (price_date or "9999-12-31")
    add("market_cap","Vốn hóa tại phiên giá","VND","daily",price_date,price_date,"market_cap",[price_input,shares],lambda p,n:p*n if n>0 else None,
        None if spot_valid and share_valid else "Thiếu giá spot hoặc số cổ phiếu có hiệu lực đã xác minh tại phiên")
    add("pb","P/B theo VCSH cổ đông mẹ gần nhất","x","point_in_time",latest_balance,latest_balance,"pb",
        [price_input,shares,point("equity_total"),point("noncontrolling_interest")],lambda p,n,e,m:divide(p*n,e-m) if n>0 else None,
        None if spot_valid and share_valid else "Thiếu giá spot hoặc số cổ phiếu có hiệu lực đã xác minh tại phiên")
    if latest and (day(request["period_end"])-day(price_date)).days>7:
        warnings.append("Giá cuối phiên cách period_end hơn 7 ngày; cần kiểm tra ngừng giao dịch/lỗi nguồn")
    if end and (day(request["period_end"])-day(end)).days>270:
        warnings.append("Kỳ chỉ số lợi nhuận cách period_end hơn 270 ngày; không gọi là lợi nhuận TTM mới nhất")
    return output, sorted(set(warnings))

def describe_metrics(metrics):
    """Chỉ diễn giải dữ liệu, không quyết định chiến lược đầu tư của người 4."""
    findings,risks=[],[]
    for m in metrics:
        value=m["value"]
        if value is None: continue
        label=f"{m['name']} ({m['period_start']} đến {m['period_end']})"
        rendered=f"{value*100:.2f}%" if m["unit"]=="ratio" else f"{value:,.2f} {m['unit']}"
        if m["metric_id"] in ("company_revenue_growth_yoy","company_parent_profit_growth_yoy","company_roa","company_roe","company_cfo_to_profit"):
            findings.append({"finding_id":"company_f_"+m["metric_id"].removeprefix("company_"),"text":label+": "+rendered,
                             "evidence_refs":[m["metric_id"]]})
        if m["metric_id"]=="company_free_cash_flow" and value<0:
            risks.append({"risk_id":"company_r_negative_fcf","text":"FCF trong kỳ âm: tiền hoạt động chưa bù chi mua sắm/xây dựng tài sản; cần đọc kế hoạch đầu tư và nguồn tài trợ.","evidence_refs":[m["metric_id"]]})
        if m["metric_id"]=="company_current_ratio" and value<1:
            risks.append({"risk_id":"company_r_current_liquidity","text":"Tài sản ngắn hạn thấp hơn nợ ngắn hạn tại kỳ đã kiểm; cần xem lịch trả nợ và khả năng chuyển tài sản thành tiền.","evidence_refs":[m["metric_id"]]})
    return findings,risks
